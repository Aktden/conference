from fastapi import APIRouter, Depends, HTTPException

from database import audit, get_db, record
from models import AttendanceCreate, AttendanceUpdate
from security import staff

router = APIRouter(prefix="/api/attendance", tags=["Посещаемость"])


@router.get("")
def get_attendance(user=Depends(staff), conn=Depends(get_db)):
    return [
        record(r)
        for r in conn.execute(
            "SELECT a.*,p.lastName,p.firstName,p.organization,s.title sectionTitle FROM attendance a JOIN participants p ON p.id=a.participantId JOIN sections s ON s.id=a.sectionId ORDER BY a.id DESC"
        )
    ]


@router.post("", status_code=201)
def register_attendance(data: AttendanceCreate, user=Depends(staff), conn=Depends(get_db)):
    # Serialize capacity check and insert so parallel requests cannot overbook.
    conn.execute("BEGIN IMMEDIATE")
    if not conn.execute("SELECT 1 FROM participants WHERE id=?", (data.participantId,)).fetchone():
        raise HTTPException(404, "Участник не найден")
    section = conn.execute("SELECT * FROM sections WHERE id=?", (data.sectionId,)).fetchone()
    if not section:
        raise HTTPException(404, "Секция не найдена")
    if conn.execute(
        "SELECT 1 FROM attendance WHERE participantId=? AND sectionId=?",
        (data.participantId, data.sectionId),
    ).fetchone():
        raise HTTPException(409, "Участник уже записан на эту секцию")
    if (
        conn.execute(
            "SELECT COUNT(*) FROM attendance WHERE sectionId=?", (data.sectionId,)
        ).fetchone()[0]
        >= section["capacity"]
    ):
        raise HTTPException(409, "Свободных мест в секции нет")
    aid = conn.execute(
        "INSERT INTO attendance(participantId,sectionId) VALUES (?,?)",
        (data.participantId, data.sectionId),
    ).lastrowid
    audit(conn, user, "register", "attendance", aid)
    return record(conn.execute("SELECT * FROM attendance WHERE id=?", (aid,)).fetchone())


@router.put("/{participant_id}/{section_id}")
def update_attendance(
    participant_id: int,
    section_id: int,
    data: AttendanceUpdate,
    user=Depends(staff),
    conn=Depends(get_db),
):
    row = conn.execute(
        "SELECT id FROM attendance WHERE participantId=? AND sectionId=?",
        (participant_id, section_id),
    ).fetchone()
    if not row:
        raise HTTPException(404, "Регистрация не найдена")
    status = "присутствовал" if data.attended else "отсутствовал"
    conn.execute(
        "UPDATE attendance SET status=?, updatedAt=datetime('now') WHERE id=?", (status, row["id"])
    )
    audit(conn, user, "attendance_update", "attendance", row["id"])
    return record(conn.execute("SELECT * FROM attendance WHERE id=?", (row["id"],)).fetchone())


@router.delete("/{participant_id}/{section_id}")
def delete_attendance(
    participant_id: int, section_id: int, user=Depends(staff), conn=Depends(get_db)
):
    result = conn.execute(
        "DELETE FROM attendance WHERE participantId=? AND sectionId=?", (participant_id, section_id)
    )
    if not result.rowcount:
        raise HTTPException(404, "Регистрация не найдена")
    audit(conn, user, "unregister", "participant", participant_id)
    return {"ok": True}
