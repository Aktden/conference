import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query

from database import audit, get_db, record
from models import BadgeUpdate, Participant
from security import admin, staff

router = APIRouter(prefix="/api/participants", tags=["Участники"])


def existing(conn, pid):
    row = conn.execute("SELECT * FROM participants WHERE id=?", (pid,)).fetchone()
    if not row:
        raise HTTPException(404, "Участник не найден")
    return row


@router.get("")
def get_participants(
    search: str = Query("", max_length=200), user=Depends(staff), conn=Depends(get_db)
):
    # CASEFOLD handles Cyrillic; SQLite LOWER only handles ASCII by default.
    rows = conn.execute(
        "SELECT * FROM participants WHERE instr(CASEFOLD(lastName || ' ' || firstName || ' ' || email || ' ' || organization), CASEFOLD(?))>0 ORDER BY id DESC",
        (search.strip(),),
    ).fetchall()
    return [record(r) for r in rows]


@router.get("/{participant_id}")
def get_participant(participant_id: int, user=Depends(staff), conn=Depends(get_db)):
    return record(existing(conn, participant_id))


@router.post("", status_code=201)
def create_participant(data: Participant, user=Depends(staff), conn=Depends(get_db)):
    try:
        # Also protects case-insensitive uniqueness when opening a legacy schema.
        conn.execute("BEGIN IMMEDIATE")
        if conn.execute(
            "SELECT 1 FROM participants WHERE lower(email)=?", (str(data.email),)
        ).fetchone():
            raise HTTPException(409, "Этот email уже зарегистрирован")
        pid = conn.execute(
            "INSERT INTO participants(lastName,firstName,organization,email,role) VALUES (?,?,?,?,?)",
            tuple(data.model_dump().values()),
        ).lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Этот email уже зарегистрирован") from None
    audit(conn, user, "create", "participant", pid)
    return record(existing(conn, pid))


@router.put("/{participant_id}")
def update_participant(
    participant_id: int, data: Participant | BadgeUpdate, user=Depends(staff), conn=Depends(get_db)
):
    existing(conn, participant_id)
    if isinstance(data, BadgeUpdate):
        conn.execute(
            "UPDATE participants SET badgePrinted=? WHERE id=?",
            (int(data.badgePrinted), participant_id),
        )
    else:
        conn.execute("BEGIN IMMEDIATE")
        if conn.execute(
            "SELECT 1 FROM participants WHERE lower(email)=? AND id!=?",
            (str(data.email), participant_id),
        ).fetchone():
            raise HTTPException(409, "Этот email уже зарегистрирован")
        conn.execute(
            "UPDATE participants SET lastName=?,firstName=?,organization=?,email=?,role=? WHERE id=?",
            (*data.model_dump().values(), participant_id),
        )
    audit(conn, user, "update", "participant", participant_id)
    return record(existing(conn, participant_id))


@router.delete("/{participant_id}")
def delete_participant(participant_id: int, user=Depends(admin), conn=Depends(get_db)):
    existing(conn, participant_id)
    conn.execute("DELETE FROM participants WHERE id=?", (participant_id,))
    audit(conn, user, "delete", "participant", participant_id)
    return {"ok": True}
