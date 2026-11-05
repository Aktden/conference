from fastapi import APIRouter, Depends, HTTPException

from database import audit, get_db
from security import staff

router = APIRouter(prefix="/api/badges", tags=["Бейджи"])


@router.post("/{participant_id}/print")
def print_badge(participant_id: int, user=Depends(staff), conn=Depends(get_db)):
    if not conn.execute(
        "UPDATE participants SET badgePrinted=1 WHERE id=?", (participant_id,)
    ).rowcount:
        raise HTTPException(404, "Участник не найден")
    audit(conn, user, "badge_mark", "participant", participant_id)
    return {"ok": True}


@router.post("/print-all")
def print_all_badges(user=Depends(staff), conn=Depends(get_db)):
    count = conn.execute("UPDATE participants SET badgePrinted=1 WHERE badgePrinted=0").rowcount
    audit(conn, user, "badges_mark_all", "participant")
    return {"count": count}
