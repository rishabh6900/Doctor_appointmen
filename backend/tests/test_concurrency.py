"""Concurrency tests verifying atomic double booking prevention under parallel load."""

import os
import tempfile
import concurrent.futures
from datetime import date, time
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.database.session import Base
from app.models.doctor import Doctor
from app.models.availability import Availability
from app.services.appointment_service import AppointmentService, BookingError


def test_concurrent_parallel_booking_same_slot():
    """
    Critical Concurrency Test:
    Spawn 10 concurrent threads all attempting to book the EXACT same doctor, date, and time.
    Uses SQLite WAL mode with independent connection handles per thread.
    Assert that exactly 1 booking succeeds and the other 9 receive a typed SlotTaken conflict!
    """
    # Create a unique temporary SQLite database file for true multi-connection concurrency
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_concurrency.db")

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )

    @event.listens_for(engine, "connect")
    def set_pragmas(dbapi_conn, record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    init_db = Session()
    doctor = Doctor(name="Dr. Concurrency Specialist", speciality="Cardiology")
    init_db.add(doctor)
    init_db.commit()
    doc_id = doctor.id

    target_date = date(2026, 12, 10)
    target_time = time(10, 0)

    avail = Availability(
        doctor_id=doc_id,
        appointment_date=target_date,
        start_time=time(9, 0),
        end_time=time(17, 0),
        slot_duration_min=30,
    )
    init_db.add(avail)
    init_db.commit()
    init_db.close()

    successes = []
    conflicts = []

    def attempt_booking(patient_num: int):
        db = Session()
        try:
            service = AppointmentService(db)
            res = service.book_appointment(
                patient_phone=f"+1555123{patient_num:04d}",
                doctor_id=doc_id,
                appointment_date=target_date,
                appointment_time=target_time,
                phone_readback_confirmed=True,
                action_confirmed=True,
            )
            successes.append(res)
        except BookingError as exc:
            conflicts.append(exc)
        finally:
            db.close()

    # Launch 10 parallel threads simultaneously
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(attempt_booking, i) for i in range(10)]
        concurrent.futures.wait(futures)

    engine.dispose()
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

    # Exactly 1 success, exactly 9 conflicts!
    assert len(successes) == 1, f"Expected 1 success, got {len(successes)}"
    assert len(conflicts) == 9, f"Expected 9 conflicts, got {len(conflicts)}"
    for c in conflicts:
        assert c.code == "SLOT_TAKEN"
