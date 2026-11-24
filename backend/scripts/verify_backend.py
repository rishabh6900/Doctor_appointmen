"""End-to-end verification script for all backend services and REST APIs."""

import sys
import subprocess
import time
import urllib.request
import json
import os

env = os.environ.copy()
env["PYTHONPATH"] = "backend"

proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
    env=env,
)
time.sleep(3)


def get(url):
    req = urllib.request.Request("http://127.0.0.1:8000" + url)
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())


def post(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8000" + url,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())


try:
    print("=" * 60)
    print("BACKEND VERIFICATION REPORT")
    print("=" * 60)

    # 1. Health Probe
    st, data = get("/health")
    print(f"1. GET /health -> HTTP {st}")
    print(f"   Status: {data['status']}, Database: {data['database']}, Timezone: {data['clinic_timezone']}")
    assert st == 200 and data["status"] == "healthy"

    # 2. Doctors List Probe
    st, data = get("/api/v1/doctors")
    print(f"2. GET /api/v1/doctors -> HTTP {st}")
    print(f"   Total Doctors: {data['total']}, First Doctor: {data['items'][0]['name']} ({data['items'][0]['speciality']})")
    assert st == 200 and data["total"] == 8

    # 3. Specialties Probe
    st, data = get("/api/v1/specialities")
    print(f"3. GET /api/v1/specialities -> HTTP {st}")
    print(f"   Specialties: {', '.join([s['speciality'] for s in data])}")
    assert st == 200 and len(data) >= 5

    # 4. Availability Probe
    st, data = get("/api/v1/availability?speciality=Cardiology")
    print(f"4. GET /api/v1/availability?speciality=Cardiology -> HTTP {st}")
    doc_match = data["results"][0]
    target_date = doc_match["schedules"][0]["date"]
    target_slot = doc_match["schedules"][0]["time_slots"][0]
    doc_id = doc_match["doctor_id"]
    print(f"   Selected: {doc_match['doctor_name']} for {target_date} at {target_slot}")
    assert st == 200 and len(doc_match["schedules"][0]["time_slots"]) > 0

    # 5. Live Booking Probe
    st, book_res = post(
        "/api/v1/appointments",
        {
            "patient_phone_number": "+919876543210",
            "patient_name": "Live Verification Patient",
            "doctor_id": doc_id,
            "appointment_date": target_date,
            "appointment_time": f"{target_slot}:00",
            "phone_readback_confirmed": True,
            "action_confirmed": True,
        },
    )
    booking_id = book_res["booking_id"]
    print(f"5. POST /api/v1/appointments -> HTTP {st}")
    print(f"   Booking ID: {booking_id}, Status: {book_res['status']}")
    print(f"   Message: {book_res['message']}")
    assert st == 201 and book_res["status"] == "confirmed"

    # 6. Live Cancellation Probe
    st, cancel_res = post(
        f"/api/v1/appointments/{booking_id}/cancel",
        {
            "patient_phone_number": "+919876543210",
            "phone_readback_confirmed": True,
            "action_confirmed": True,
        },
    )
    print(f"6. POST /api/v1/appointments/{booking_id}/cancel -> HTTP {st}")
    print(f"   Cancellation Status: {cancel_res['status']}")
    print(f"   Message: {cancel_res['message']}")
    assert st == 200 and cancel_res["status"] == "cancelled"

    # 7. Dashboard Metrics Probe
    st, stats_res = get("/api/v1/dashboard/stats")
    print(f"7. GET /api/v1/dashboard/stats -> HTTP {st}")
    print(f"   Total Appointments: {stats_res['total_appointments']}")
    print(f"   Confirmed: {stats_res['confirmed_appointments']}, Cancelled: {stats_res['cancelled_appointments']}")
    print(f"   Recent Activity Feed Items: {len(stats_res['recent_activity'])}")
    assert st == 200 and stats_res["cancelled_appointments"] >= 1

    print("=" * 60)
    print("ALL LIVE BACKEND ENDPOINTS ARE FULLY OPERATIONAL!")
    print("=" * 60)
finally:
    proc.terminate()
