"""
Маршруты: статистика, экспорт, импорт
"""

from typing import Any, Dict
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from database import db, row_to_dict, now

router = APIRouter(tags=["Статистика и данные"])


@router.get("/api/stats")
def get_stats():
    with db() as conn:
        total_participants = conn.execute("SELECT COUNT(*) FROM participants").fetchone()[0]
        total_sections     = conn.execute("SELECT COUNT(*) FROM sections").fetchone()[0]
        badges_printed     = conn.execute("SELECT COUNT(*) FROM participants WHERE badgePrinted = 1").fetchone()[0]
        total_att          = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
        attended           = conn.execute("SELECT COUNT(*) FROM attendance WHERE status = 'присутствовал'").fetchone()[0]

    rate = int(attended * 100 / total_att) if total_att > 0 else 0
    return {
        "participants":       total_participants,
        "sections":           total_sections,
        "attendance_records": total_att,
        "attended":           attended,
        "badges_printed":     badges_printed,
        "attendance_rate":    rate,
    }


@router.get("/api/export")
def export_data():
    with db() as conn:
        participants = [row_to_dict(r) for r in conn.execute("SELECT * FROM participants ORDER BY id").fetchall()]
        sections     = [row_to_dict(r) for r in conn.execute("SELECT * FROM sections ORDER BY id").fetchall()]
        attendance   = [row_to_dict(r) for r in conn.execute("SELECT * FROM attendance ORDER BY id").fetchall()]

    return JSONResponse(
        content={
            "participants": participants,
            "sections":     sections,
            "attendance":   attendance,
            "exportedAt":   now(),
        },
        headers={"Content-Disposition": "attachment; filename=conference-export.json"}
    )


@router.post("/api/import")
def import_data(data: Dict[str, Any]):
    """Полная замена данных (используется для сброса)"""
    with db() as conn:
        conn.execute("DELETE FROM attendance")
        conn.execute("DELETE FROM sections")
        conn.execute("DELETE FROM participants")

        for p in data.get("participants", []):
            conn.execute(
                """INSERT OR IGNORE INTO participants
                   (id, lastName, firstName, organization, email, role, badgePrinted, createdAt)
                   VALUES (:id,:lastName,:firstName,:organization,:email,:role,:badgePrinted,:createdAt)""",
                {
                    "id":           p.get("id"),
                    "lastName":     p.get("lastName", ""),
                    "firstName":    p.get("firstName", ""),
                    "organization": p.get("organization", ""),
                    "email":        p.get("email", ""),
                    "role":         p.get("role", "слушатель"),
                    "badgePrinted": int(p.get("badgePrinted", False)),
                    "createdAt":    p.get("createdAt", now()),
                }
            )

        for s in data.get("sections", []):
            conn.execute(
                """INSERT OR IGNORE INTO sections
                   (id, title, room, startTime, capacity, createdAt)
                   VALUES (:id,:title,:room,:startTime,:capacity,:createdAt)""",
                {
                    "id":        s.get("id"),
                    "title":     s.get("title", ""),
                    "room":      s.get("room", ""),
                    "startTime": s.get("startTime", ""),
                    "capacity":  s.get("capacity", 1),
                    "createdAt": s.get("createdAt", now()),
                }
            )

        for a in data.get("attendance", []):
            conn.execute(
                """INSERT OR IGNORE INTO attendance
                   (id, participantId, sectionId, status, registeredAt, updatedAt)
                   VALUES (:id,:participantId,:sectionId,:status,:registeredAt,:updatedAt)""",
                {
                    "id":            a.get("id"),
                    "participantId": a.get("participantId"),
                    "sectionId":     a.get("sectionId"),
                    "status":        a.get("status", "зарегистрирован"),
                    "registeredAt":  a.get("registeredAt", now()),
                    "updatedAt":     a.get("updatedAt"),
                }
            )

    return {"ok": True}
