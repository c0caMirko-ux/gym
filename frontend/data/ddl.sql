-- frontend/static/data/ddl.sql
-- 1) DDL para Postgres (ejecutar en tu BD)
-- Recomendación: crear un schema, p.ej. "gym"
CREATE SCHEMA IF NOT EXISTS gym;

-- ENUM types
CREATE TYPE gym.user_role AS ENUM ('member','trainer','admin');
CREATE TYPE gym.reservation_status AS ENUM ('booked','cancelled','attended','no_show');
CREATE TYPE gym.session_status AS ENUM ('scheduled','cancelled','completed');

-- Plans
CREATE TABLE gym.plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT,
  max_monthly_bookings INT NULL, -- null = unlimited
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Users
CREATE TABLE gym.users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  phone TEXT,
  password_hash TEXT NOT NULL,
  role gym.user_role NOT NULL DEFAULT 'member',
  plan_id UUID REFERENCES gym.plans(id),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Locations / Rooms / Resources
CREATE TABLE gym.locations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  address TEXT,
  capacity INT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Class / Service types (zumba, spinning, crossfit...)
CREATE TABLE gym.class_types (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  description TEXT,
  duration_minutes INT NOT NULL,
  is_group BOOLEAN NOT NULL DEFAULT TRUE,
  level TEXT,
  price_cents INT DEFAULT 0,
  currency TEXT DEFAULT 'USD',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Trainers extra metadata (optional: links to users with role=trainer)
CREATE TABLE gym.trainers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES gym.users(id) ON DELETE CASCADE,
  bio TEXT,
  specialties TEXT[],
  certifications TEXT[],
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Sessions (instances of a class/service)
CREATE TABLE gym.sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  class_type_id UUID NOT NULL REFERENCES gym.class_types(id) ON DELETE CASCADE,
  trainer_id UUID REFERENCES gym.trainers(id),
  location_id UUID REFERENCES gym.locations(id),
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ NOT NULL,
  capacity INT NOT NULL DEFAULT 20, -- relevant for group classes
  status gym.session_status NOT NULL DEFAULT 'scheduled',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  CHECK (end_time > start_time)
);

-- Index to speed up queries by date range
CREATE INDEX idx_sessions_time ON gym.sessions USING BRIN (start_time);

-- Payments
CREATE TABLE gym.payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES gym.users(id),
  reservation_id UUID REFERENCES gym.reservations(id), -- created below as FK; circular ref avoided by nullable here
  amount_cents INT NOT NULL,
  currency TEXT NOT NULL DEFAULT 'USD',
  provider TEXT,
  provider_payment_id TEXT,
  status TEXT, -- pending, succeeded, failed
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Reservations (a booking by a user for a session)
CREATE TABLE gym.reservations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES gym.sessions(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES gym.users(id) ON DELETE CASCADE,
  status gym.reservation_status NOT NULL DEFAULT 'booked',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (session_id, user_id) -- prevents duplicate booking same session
);

-- Now that reservations exist, add foreign key from payments
ALTER TABLE gym.payments
  ADD COLUMN IF NOT EXISTS reservation_id UUID,
  ADD CONSTRAINT fk_payments_reservation FOREIGN KEY (reservation_id) REFERENCES gym.reservations(id);

-- Waitlist entries
CREATE TABLE gym.waitlist_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES gym.sessions(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES gym.users(id) ON DELETE CASCADE,
  position INT NOT NULL, -- smaller = higher priority
  notified_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (session_id, user_id)
);

CREATE INDEX idx_waitlist_session_pos ON gym.waitlist_entries (session_id, position);

-- Availability for trainers (for 1:1 sessions)
CREATE TABLE gym.trainer_availability (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trainer_id UUID NOT NULL REFERENCES gym.trainers(id) ON DELETE CASCADE,
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ NOT NULL,
  recurring_rule TEXT, -- optional RRULE string (iCal) if needed
  created_at TIMESTAMPTZ DEFAULT now(),
  CHECK (end_time > start_time)
);

-- Audit logs
CREATE TABLE gym.audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_type TEXT,
  entity_id UUID,
  action TEXT,
  payload JSONB,
  performed_by UUID REFERENCES gym.users(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- FUNCTIONS / TRIGGERS for integrity & overbooking prevention
-- 1) Before insert reservation: check capacity and overlapping bookings for user
CREATE OR REPLACE FUNCTION gym.check_reservation_constraints() RETURNS TRIGGER AS $$
DECLARE
  current_bookings INT;
  sess_capacity INT;
  overlap_count INT;
  sess_start TIMESTAMPTZ;
  sess_end TIMESTAMPTZ;
BEGIN
  -- get session times & capacity
  SELECT start_time, end_time, capacity INTO sess_start, sess_end, sess_capacity
    FROM gym.sessions WHERE id = NEW.session_id FOR SHARE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Session % not found', NEW.session_id;
  END IF;

  -- count active bookings for that session
  SELECT COUNT(*) INTO current_bookings
    FROM gym.reservations
    WHERE session_id = NEW.session_id AND status = 'booked';

  IF current_bookings >= sess_capacity THEN
    RAISE EXCEPTION 'Session is full';
  END IF;

  -- prevent a user from booking overlapping sessions
  SELECT COUNT(*) INTO overlap_count
    FROM gym.reservations r
    JOIN gym.sessions s ON r.session_id = s.id
    WHERE r.user_id = NEW.user_id
      AND r.status = 'booked'
      AND tstzrange(s.start_time, s.end_time) && tstzrange(sess_start, sess_end);

  IF overlap_count > 0 THEN
    RAISE EXCEPTION 'User has another booking that overlaps this session';
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_reservation_constraints
  BEFORE INSERT ON gym.reservations
  FOR EACH ROW EXECUTE FUNCTION gym.check_reservation_constraints();

-- 2) On reservation cancellation: auto-promote waitlist (simplified)
CREATE OR REPLACE FUNCTION gym.on_reservation_cancel_promote_waitlist() RETURNS TRIGGER AS $$
DECLARE
  next_waitlist RECORD;
BEGIN
  IF (TG_OP = 'UPDATE' AND NEW.status = 'cancelled' AND OLD.status <> 'cancelled') THEN
    -- find first waitlist entry for this session by position
    SELECT * INTO next_waitlist FROM gym.waitlist_entries
      WHERE session_id = OLD.session_id
      ORDER BY position ASC, created_at ASC LIMIT 1;

    IF FOUND THEN
      -- create reservation for that user (can raise if constraints fail; consider wrapping in transaction in app)
      INSERT INTO gym.reservations (session_id, user_id, status, created_at)
        VALUES (OLD.session_id, next_waitlist.user_id, 'booked', now());
      -- remove promoted waitlist entry
      DELETE FROM gym.waitlist_entries WHERE id = next_waitlist.id;
      -- Note: Ideally notify the user via app-level job
    END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_on_cancel_promote_waitlist
  AFTER UPDATE ON gym.reservations
  FOR EACH ROW EXECUTE FUNCTION gym.on_reservation_cancel_promote_waitlist();

-- Helpful indexes
CREATE INDEX idx_reservations_user ON gym.reservations (user_id);
CREATE INDEX idx_reservations_session ON gym.reservations (session_id);
