"""
Маршруты: участники
"""

import sqlite3
from fastapi import APIRouter, HTTPException, status

from database import db, row_to_dict
from models import Participant, ParticipantUpdate

router = APIRouter(prefix="/api/participants", tags=["Участники"])


@router.get("")
def get_participants(search: str = ""):
    with db() as conn:
        if search:
            like = f"%{search.lower()}%"
            rows = conn.execute(
                """SELECT * FROM participants
                   WHERE lower(lastName || ' ' || firstName || ' ' || email || ' ' || organization) LIKE ?
                   ORDER BY id""",
                (like,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM participants ORDER BY id").fetchall()
    return [row_to_dict(r) for r in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_participant(data: Participant):
    try:
        with db() as conn:
            cursor = conn.execute(
                """INSERT INTO participants (lastName, firstName, organization, email, role)
                   VALUES (?, ?, ?, ?, ?)""",
                (data.lastName, data.firstName, data.organization, data.email, data.role)
            )
            row = conn.execute("SELECT * FROM participants WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return row_to_dict(row)
    except sqlite3.IntegrityError as e:
        if "UNIQUE" in str(e):
            raise HTTPException(status_code=409, detail="Email уже зарегистрирован")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{participant_id}")
def update_participant(participant_id: int, data: ParticipantUpdate):
    with db() as conn:
        row = conn.execute("SELECT id FROM participants WHERE id = ?", (participant_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Участник не найден")

        if data.badgePrinted is not None:
            conn.execute(
                "UPDATE participants SET badgePrinted = ? WHERE id = ?",
                (int(data.badgePrinted), participant_id)
            )

        updated = conn.execute("SELECT * FROM participants WHERE id = ?", (participant_id,)).fetchone()
    return row_to_dict(updated)


@router.delete("/{participant_id}")
def delete_participant(participant_id: int):
    with db() as conn:
        row = conn.execute("SELECT id FROM participants WHERE id = ?", (participant_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Участник не найден")
        # Записи посещения удалятся каскадно (ON DELETE CASCADE)
        conn.execute("DELETE FROM participants WHERE id = ?", (participant_id,))
    return {"ok": True}
