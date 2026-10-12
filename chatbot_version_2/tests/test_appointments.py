"""Appointment business rules (services/appointment_service.py) with a fake DB.

MySQL TIME columns arrive from PyMySQL as datetime.timedelta - the tests use
timedelta on purpose, exactly like production.
"""
from datetime import date, datetime, time, timedelta

import pytest

import services.appointment_service as svc
from tests.fakes import ScriptedDB

TOMORROW = date.today() + timedelta(days=1)
NEXT_WEEK = date.today() + timedelta(days=7)

SCHEDULE = [{"start_time": timedelta(hours=9), "end_time": timedelta(hours=11), "slot_duration": 30}]


def use(monkeypatch, *results, **kw):
    db = ScriptedDB(list(results), **kw)
    monkeypatch.setattr(svc, "get_db", db)
    return db


# ---------------------------------------------------------------- slots

def test_slots_with_timedelta_columns_and_booked_slot_removed(monkeypatch):
    booked = [{"start_time": timedelta(hours=9, minutes=30), "end_time": timedelta(hours=10)}]
    use(monkeypatch, {"id": 2}, SCHEDULE, booked)
    slots = svc.get_available_slots(2, NEXT_WEEK)
    assert [s["start_time"] for s in slots] == ["09:00:00", "10:00:00", "10:30:00"]
    assert slots[-1]["end_time"] == "11:00:00"


def test_slots_empty_for_inactive_doctor_no_schedule_past_date(monkeypatch):
    use(monkeypatch, None)
    assert svc.get_available_slots(2, NEXT_WEEK) == []
    use(monkeypatch, {"id": 2}, [])
    assert svc.get_available_slots(2, NEXT_WEEK) == []
    db = use(monkeypatch)
    assert svc.get_available_slots(2, date.today() - timedelta(days=1)) == []
    assert db.queries == []                       # no DB work for past dates


def test_slots_invalid_input(monkeypatch):
    assert svc.get_available_slots(0, NEXT_WEEK) == []
    assert svc.get_available_slots(2, None) == []


def test_zero_slot_duration_does_not_loop_forever(monkeypatch):
    bad = [{"start_time": timedelta(hours=9), "end_time": timedelta(hours=11), "slot_duration": 0}]
    use(monkeypatch, {"id": 2}, bad, [])
    assert svc.get_available_slots(2, NEXT_WEEK) == []


# --------------------------------------------------------------- booking

def _book(monkeypatch, d=NEXT_WEEK, start=time(10, 0), end=time(10, 30), *rows):
    rows = rows or (
        {"id": 2, "status": "active", "department_id": 1},   # doctor
        {"id": 1},                                            # department
        {"id": 7},                                            # patient
        SCHEDULE,                                             # schedules
        None,                                                 # no conflict
    )
    db = use(monkeypatch, *rows)
    res = svc.book_appointment(patient_id=7, doctor_id=2, department_id=1,
                               appointment_date=d, start_time=start, end_time=end, reason="fever")
    return res, db


def test_booking_success_inserts_row(monkeypatch):
    res, db = _book(monkeypatch)
    assert res["success"] and res["appointment_id"] == 55
    sql, params = db.queries[-1]
    assert sql.startswith("INSERT INTO appointments") and params[0] == 7


def test_booking_locks_doctor_row_against_double_booking(monkeypatch):
    _, db = _book(monkeypatch)
    assert any("FOR UPDATE" in q for q, _ in db.queries)


def test_booking_in_the_past_refused(monkeypatch):
    res, db = _book(monkeypatch, d=date.today() - timedelta(days=1))
    assert not res["success"] and "past" in res["message"]
    assert db.queries == []


def test_booking_earlier_today_refused(monkeypatch):
    res, _ = _book(monkeypatch, d=date.today(), start=time(0, 0, 1), end=time(0, 30))
    if datetime.now().time() > time(0, 0, 1):
        assert not res["success"] and "past" in res["message"]


@pytest.mark.parametrize("start,end,expected", [
    (time(8, 0), time(8, 30), "outside"),          # before the schedule
    (time(10, 10), time(10, 40), "slot timing"),   # not on the 30-min grid
    (time(10, 0), time(10, 45), "outside"),        # wrong length
    (time(10, 30), time(10, 0), "after start"),    # end before start
])
def test_booking_rules(monkeypatch, start, end, expected):
    res, _ = _book(monkeypatch, start=start, end=end)
    assert not res["success"] and expected in res["message"]


def test_booking_conflict(monkeypatch):
    rows = ({"id": 2, "status": "active", "department_id": 1}, {"id": 1}, {"id": 7},
            SCHEDULE, {"id": 99})
    db = use(monkeypatch, *rows)
    res = svc.book_appointment(patient_id=7, doctor_id=2, department_id=1,
                               appointment_date=NEXT_WEEK, start_time=time(10, 0), end_time=time(10, 30))
    assert not res["success"] and "already booked" in res["message"]
    assert not any(q.startswith("INSERT") for q, _ in db.queries)


def test_booking_wrong_department_or_inactive_doctor(monkeypatch):
    rows = ({"id": 2, "status": "active", "department_id": 5},)
    res, _ = _book(monkeypatch, NEXT_WEEK, time(10, 0), time(10, 30), *rows)
    assert not res["success"] and "department" in res["message"].lower()
    rows = ({"id": 2, "status": "inactive", "department_id": 1},)
    res, _ = _book(monkeypatch, NEXT_WEEK, time(10, 0), time(10, 30), *rows)
    assert not res["success"] and "not available" in res["message"]


def test_booking_invalid_ids():
    for kw in ({"patient_id": 0}, {"doctor_id": 0}, {"department_id": 0}):
        args = dict(patient_id=1, doctor_id=1, department_id=1, appointment_date=NEXT_WEEK,
                    start_time=time(10), end_time=time(10, 30))
        args.update(kw)
        assert not svc.book_appointment(**args)["success"]


# ---------------------------------------------------------------- cancel

FUTURE = {"id": 5, "patient_id": 7, "status": "booked",
          "appointment_date": NEXT_WEEK, "start_time": timedelta(hours=10)}


def test_cancel_own_future_appointment(monkeypatch):
    db = use(monkeypatch, dict(FUTURE))
    res = svc.cancel_appointment(7, 5)
    assert res["success"]
    assert any(q.startswith("UPDATE appointments SET status = 'cancelled'") for q, _ in db.queries)


def test_cancel_someone_elses_appointment_is_refused_and_looks_like_not_found(monkeypatch):
    db = use(monkeypatch, dict(FUTURE))
    res = svc.cancel_appointment(8, 5)                 # patient 8 != owner 7
    assert not res["success"] and res["message"] == "Appointment not found."
    assert not any(q.startswith("UPDATE") for q, _ in db.queries)


def test_cancel_missing_already_cancelled_and_past(monkeypatch):
    use(monkeypatch, None)
    assert svc.cancel_appointment(7, 5)["message"] == "Appointment not found."
    use(monkeypatch, {**FUTURE, "status": "cancelled"})
    assert "cannot be cancelled" in svc.cancel_appointment(7, 5)["message"]
    past = {**FUTURE, "appointment_date": date.today() - timedelta(days=2)}
    db = use(monkeypatch, past)
    assert "Past" in svc.cancel_appointment(7, 5)["message"]
    assert not any(q.startswith("UPDATE") for q, _ in db.queries)


def test_to_time_handles_all_types():
    assert svc._to_time(timedelta(hours=9, minutes=5, seconds=3)) == time(9, 5, 3)
    assert svc._to_time(timedelta(hours=25)) == time(1, 0)
    assert svc._to_time(datetime(2026, 1, 1, 8, 30)) == time(8, 30)
    assert svc._to_time(time(7, 0)) == time(7, 0)
    assert svc._to_time(None) is None
