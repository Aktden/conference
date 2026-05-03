"""
Маршруты: секции
"""

from fastapi import APIRouter, HTTPException, status

from database import db, row_to_dict
from models import Section

router = APIRouter(prefix="/api/sections", tags=["Секции"])


@router.get("")
def get_sections():
    with db() as conn:
        rows = conn.execute("SELECT * FROM sections ORDER BY id").fetchall()
    return [row_to_dict(r) for r in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_section(data: Section):
    with db() as conn:
        cursor = conn.execute(
            "INSERT INTO sections (title, room, startTime, capacity) VALUES (?, ?, ?, ?)",
            (data.title, data.room, data.startTime, data.capacity)
        )
        row = conn.execute("SELECT * FROM sections WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return row_to_dict(row)


@router.delete("/{section_id}")
def delete_section(section_id: int):
    with db() as conn:
        row = conn.execute("SELECT id FROM sections WHERE id = ?", (section_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Секция не найдена")
        conn.execute("DELETE FROM sections WHERE id = ?", (section_id,))
    return {"ok": True}
