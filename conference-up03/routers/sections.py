from fastapi import APIRouter, Depends, HTTPException

from database import audit, get_db, record
from models import Section
from security import admin, current_user

router = APIRouter(prefix="/api/sections", tags=["Секции"])


def existing(conn, sid):
    row = conn.execute("SELECT * FROM sections WHERE id=?", (sid,)).fetchone()
    if not row:
        raise HTTPException(404, "Секция не найдена")
    return row


@router.get("")
def get_sections(user=Depends(current_user), conn=Depends(get_db)):
    return [
        record(r)
        for r in conn.execute(
            "SELECT s.*, COUNT(a.id) registered, COALESCE(SUM(a.status='присутствовал'),0) attended FROM sections s LEFT JOIN attendance a ON s.id=a.sectionId GROUP BY s.id ORDER BY s.startTime,s.id"
        )
    ]


@router.post("", status_code=201)
def create_section(data: Section, user=Depends(admin), conn=Depends(get_db)):
    sid = conn.execute(
        "INSERT INTO sections(title,room,startTime,capacity) VALUES (?,?,?,?)",
        tuple(data.model_dump().values()),
    ).lastrowid
    audit(conn, user, "create", "section", sid)
    return record(existing(conn, sid))


@router.put("/{section_id}")
def update_section(section_id: int, data: Section, user=Depends(admin), conn=Depends(get_db)):
    conn.execute("BEGIN IMMEDIATE")
    existing(conn, section_id)
    count = conn.execute(
        "SELECT COUNT(*) FROM attendance WHERE sectionId=?", (section_id,)
    ).fetchone()[0]
    if data.capacity < count:
        raise HTTPException(409, "Вместимость не может быть меньше числа записанных участников")
    conn.execute(
        "UPDATE sections SET title=?,room=?,startTime=?,capacity=? WHERE id=?",
        (*data.model_dump().values(), section_id),
    )
    audit(conn, user, "update", "section", section_id)
    return record(existing(conn, section_id))


@router.delete("/{section_id}")
def delete_section(section_id: int, user=Depends(admin), conn=Depends(get_db)):
    existing(conn, section_id)
    conn.execute("DELETE FROM sections WHERE id=?", (section_id,))
    audit(conn, user, "delete", "section", section_id)
    return {"ok": True}
