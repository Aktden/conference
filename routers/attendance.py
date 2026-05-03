"""
Маршруты: посещение секций
"""

import sqlite3
from fastapi import APIRouter, HTTPException, status

from database import db, row_to_dict, now
from models import AttendanceCreate, AttendanceUpdate

router = APIRouter(prefix="/api/attendance", tags=["Посещение"])


@router.get("")
def get_attendance():
    with db() as conn:
        rows = conn.execute("SELECT * FROM attendance ORDER BY id").fetchall()
    return [row_to_dict(r) for r in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def register_attendance(data: AttendanceCreate):
    with db() as conn:
        # Проверяем существование участника и секции
        p = conn.execute("SELECT id FROM participants WHERE id = ?", (data.participantId,)).fetchone()
        if not p:
            raise HTTPException(status_code=404, detail="Участник не найден")

        s = conn.execute("SELECT id, capacity FROM sections WHERE id = ?", (data.sectionId,)).fetchone()
        if not s:
            raise HTTPException(status_code=404, detail="Секция не найдена")

        # Проверяем вместимость
        count = conn.execute(
            "SELECT COUNT(*) FROM attendance WHERE sectionId = ?", (data.sectionId,)
        ).fetchone()[0]
        if count >= s["capacity"]:
            raise HTTPException(status_code=400, detail="Секция заполнена")

        try:
            cursor = conn.execute(
                "INSERT INTO attendance (participantId, sectionId) VALUES (?, ?)",
                (data.participantId, data.sectionId)
            )
            row = conn.execute("SELECT * FROM attendance WHERE id = ?", (cursor.lastrowid,)).fetchone()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="Участник уже записан на эту секцию")

    return row_to_dict(row)


@router.put("/{participant_id}/{section_id}")
def update_attendance(participant_id: int, section_id: int, data: AttendanceUpdate):
    new_status = "присутствовал" if data.attended else "отсутствовал"
    with db() as conn:
        row = conn.execute(
            "SELECT id FROM attendance WHERE participantId = ? AND sectionId = ?",
            (participant_id, section_id)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Запись о посещении не найдена")

        conn.execute(
            "UPDATE attendance SET status = ?, updatedAt = ? WHERE participantId = ? AND sectionId = ?",
            (new_status, now(), participant_id, section_id)
        )
        updated = conn.execute(
            "SELECT * FROM attendance WHERE participantId = ? AND sectionId = ?",
            (participant_id, section_id)
        ).fetchone()
    return row_to_dict(updated)
