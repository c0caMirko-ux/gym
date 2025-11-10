
# tests/test_concurrent_reservations.py
import threading
import time
import pytest
import httpx
from uuid import UUID

BASE_URL = "http://localhost:8000"

@pytest.mark.integration
def test_concurrent_reservations_simulation():
    # Este test asume que ya levantaste el servidor y que existe una session con capacity=1
    # Paso 1: crear dos usuarios y loguearlos
    client = httpx.Client()
    u1 = {"full_name":"User One","email":"u1@example.com","password":"pass123"}
    u2 = {"full_name":"User Two","email":"u2@example.com","password":"pass123"}
    r = client.post(f"{BASE_URL}/auth/register", json=u1)
    assert r.status_code == 200
    token1 = r.json()["access_token"]
    r = client.post(f"{BASE_URL}/auth/register", json=u2)
    assert r.status_code == 200
    token2 = r.json()["access_token"]
    # Ajusta session_id aquí a una session creada manualmente con capacity=1
    session_id = "00000000-0000-0000-0000-000000000000"  # <-- reemplaza
    results = []
    def try_reserve(token, out):
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(f"{BASE_URL}/reservations", json={"session_id": session_id, "auto_waitlist": False}, headers=headers)
        out.append(resp)
    t1_out = []
    t2_out = []
    t1 = threading.Thread(target=try_reserve, args=(token1, t1_out))
    t2 = threading.Thread(target=try_reserve, args=(token2, t2_out))
    t1.start(); t2.start()
    t1.join(); t2.join()
    # Uno debería tener éxito y el otro fallar por capacidad llena
    statuses = [o[0].status_code for o in (t1_out, t2_out) if len(o)>0]
    assert 200 in statuses
    assert 400 in statuses or 409 in statuses
