# app/main.py
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from .database import get_db, engine
from .models import Base, User, Session as SessionModel, Reservation, WaitlistEntry
from .auth import get_password_hash, create_access_token, verify_password, get_current_user
from .schemas import RegisterIn, TokenOut, SessionOut, ReserveIn
from fastapi.security import OAuth2PasswordRequestForm
from uuid import UUID

app = FastAPI(title="Gym Reservations API")

# Base dir (raíz del repo asumiendo que uvicorn se ejecuta desde la raíz)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Montar carpeta frontend/static para servir assets públicos (css, js, components, data)
static_dir = os.path.join(base_dir, "frontend", "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    print(f"Warning: static dir not found at {static_dir}. Crea frontend/static con tus assets.")

# Montar carpeta frontend/pages para servir las páginas HTML desde /pages
pages_dir = os.path.join(base_dir, "frontend", "pages")
if os.path.isdir(pages_dir):
    app.mount("/pages", StaticFiles(directory=pages_dir), name="pages")
else:
    print(f"Warning: pages dir not found at {pages_dir}. Crea frontend/pages con tus HTML.")

# Servir la página HTML principal (UI)
@app.get("/ui")
def ui():
    index_path = os.path.join(base_dir, "frontend", "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return {"detail": "UI index not found. Crea frontend/index.html"}

# Dev helper: crear esquema y tablas si no existen (solo dev)
# Base.metadata.create_all(bind=engine)

@app.post("/auth/register", response_model=TokenOut)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    existing = db.execute(select(User).filter_by(email=payload.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email ya registrado")
    user = User(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=get_password_hash(payload.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/auth/login", response_model=TokenOut)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm provides form fields 'username' and 'password'
    user = db.execute(select(User).filter_by(email=form_data.username)).scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/sessions", response_model=list[SessionOut])
def list_sessions(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    rows = db.execute(select(SessionModel).offset(skip).limit(limit)).scalars().all()
    return rows

# Obtener una sesión por id (útil para detalle)
@app.get("/sessions/{session_id}", response_model=SessionOut)
def get_session(session_id: UUID, db: Session = Depends(get_db)):
    row = db.get(SessionModel, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session no encontrada")
    return row

@app.post("/reservations")
def create_reservation(payload: ReserveIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    with db.begin():
        sess_row = db.execute(select(SessionModel).filter_by(id=payload.session_id).with_for_update()).scalar_one_or_none()
        if not sess_row:
            raise HTTPException(status_code=404, detail="Session no encontrada")
        if sess_row.status != 'scheduled':
            raise HTTPException(status_code=400, detail="Session no está disponible")
        booked_count = db.execute(select(func.count()).select_from(Reservation).filter_by(session_id=payload.session_id, status='booked')).scalar_one()
        # overlapping check
        overlap_q = select(func.count()).select_from(Reservation).join(SessionModel, Reservation.session_id == SessionModel.id).filter(
            Reservation.user_id == current_user.id,
            Reservation.status == 'booked',
            func.tstzrange(SessionModel.start_time, SessionModel.end_time).op("&&")(func.tstzrange(sess_row.start_time, sess_row.end_time))
        )
        overlap_count = db.execute(overlap_q).scalar_one()
        if overlap_count > 0:
            raise HTTPException(status_code=400, detail="Tienes otra reserva que se solapa con este horario")
        if booked_count >= sess_row.capacity:
            if payload.auto_waitlist:
                max_pos = db.execute(select(func.coalesce(func.max(WaitlistEntry.position), 0)).filter(WaitlistEntry.session_id == payload.session_id)).scalar_one()
                new_pos = (max_pos or 0) + 1
                entry = WaitlistEntry(session_id=payload.session_id, user_id=current_user.id, position=new_pos)
                db.add(entry)
                db.commit()
                return {"status": "waitlisted", "position": new_pos}
            else:
                raise HTTPException(status_code=400, detail="Session llena")
        res = Reservation(session_id=payload.session_id, user_id=current_user.id, status='booked')
        db.add(res)
        db.commit()
        db.refresh(res)
        return {"reservation_id": str(res.id), "status": "booked"}

@app.patch("/reservations/{reservation_id}/cancel")
def cancel_reservation(reservation_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = db.get(Reservation, reservation_id)
    if not res:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    if str(res.user_id) != str(current_user.id) and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="No autorizado")
    with db.begin():
        res.status = 'cancelled'
        db.add(res)
        db.commit()
        promote_waitlist(res.session_id, db)
        return {"status": "cancelled"}

def promote_waitlist(session_id: UUID, db: Session):
    next_entry = db.execute(
        select(WaitlistEntry).filter_by(session_id=session_id).order_by(WaitlistEntry.position.asc(), WaitlistEntry.created_at.asc()).limit(1)
    ).scalar_one_or_none()
    if not next_entry:
        return None
    try:
        sess_row = db.execute(select(SessionModel).filter_by(id=session_id).with_for_update()).scalar_one()
        booked_count = db.execute(select(func.count()).select_from(Reservation).filter_by(session_id=session_id, status='booked')).scalar_one()
        if booked_count < sess_row.capacity:
            new_res = Reservation(session_id=session_id, user_id=next_entry.user_id, status='booked')
            db.add(new_res)
            db.delete(next_entry)
            db.commit()
            return new_res
    except Exception:
        db.rollback()
    return None

@app.post("/sessions/{session_id}/waitlist")
def add_to_waitlist(session_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sess = db.get(SessionModel, session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session no encontrada")
    existing = db.execute(select(WaitlistEntry).filter_by(session_id=session_id, user_id=current_user.id)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Ya estás en la lista de espera")
    max_pos = db.execute(select(func.coalesce(func.max(WaitlistEntry.position), 0)).filter(WaitlistEntry.session_id == session_id)).scalar_one()
    pos = (max_pos or 0) + 1
    entry = WaitlistEntry(session_id=session_id, user_id=current_user.id, position=pos)
    db.add(entry)
    db.commit()
    return {"status": "waitlisted", "position": pos}

# Obtener mis reservas (para la UI)
@app.get("/me/reservations")
def my_reservations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.execute(select(Reservation).filter_by(user_id=current_user.id)).scalars().all()
    out = []
    for r in rows:
        sess = db.get(SessionModel, r.session_id)
        out.append({
            "id": str(r.id),
            "status": str(r.status),
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "session": {
                "id": str(sess.id),
                "start_time": sess.start_time.isoformat() if sess.start_time else None,
                "end_time": sess.end_time.isoformat() if sess.end_time else None,
                "capacity": sess.capacity,
                "class_type_title": getattr(sess.class_type, "title", None)
            }
        })
    return out

@app.get("/")
def root():
    return {"message": "API del Gym funcionando correctamente"}
