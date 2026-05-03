"""
Маршруты: бейджи
"""

from fastapi import APIRouter, HTTPException

from database import db

router = APIRouter(prefix="/api/badges", tags=["Бейджи"])


@router.post("/{participant_id}/print")
def print_badge(participant_id: int):
    with db() as conn:
        row = conn.execute("SELECT id FROM participants WHERE id = ?", (participant_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Участник не найден")
        conn.execute("UPDATE participants SET badgePrinted = 1 WHERE id = ?", (participant_id,))
    return {"ok": True}


@router.post("/print-all")
def print_all_badges():
    with db() as conn:
        result = conn.execute("UPDATE participants SET badgePrinted = 1 WHERE badgePrinted = 0")
        count = result.rowcount
    return {"count": count}
