import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response

from database import audit, get_db, record
from models import ImportBundle
from security import admin, current_user

router = APIRouter(tags=["Отчёты и данные"])


@router.get("/api/stats")
def get_stats(user=Depends(current_user), conn=Depends(get_db)):
    def scalar(query):
        return conn.execute(query).fetchone()[0]

    total = scalar("SELECT COUNT(*) FROM attendance")
    attended = scalar("SELECT COUNT(*) FROM attendance WHERE status='присутствовал'")
    return {
        "participants": scalar("SELECT COUNT(*) FROM participants"),
        "sections": scalar("SELECT COUNT(*) FROM sections"),
        "attendance_records": total,
        "attended": attended,
        "badges_printed": scalar("SELECT COUNT(*) FROM participants WHERE badgePrinted=1"),
        "attendance_rate": round(attended * 100 / total) if total else 0,
        "roles": [
            dict(r)
            for r in conn.execute("SELECT role,COUNT(*) count FROM participants GROUP BY role")
        ],
    }


@router.get("/api/audit")
def audit_log(user=Depends(admin), conn=Depends(get_db)):
    return [dict(r) for r in conn.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 100")]


@router.get("/api/export")
def export_data(user=Depends(admin), conn=Depends(get_db)):
    data = {
        name: [record(r) for r in conn.execute(f"SELECT * FROM {name} ORDER BY id")]
        for name in ("participants", "sections", "attendance")
    }
    data.update(exportedAt=datetime.now(timezone.utc).isoformat(), version="3.0.0")
    audit(conn, user, "export", "data")
    return JSONResponse(
        data, headers={"Content-Disposition": "attachment; filename=conference-export.json"}
    )


@router.get("/api/export/csv")
def export_csv(user=Depends(admin), conn=Depends(get_db)):
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["ID", "Фамилия", "Имя", "Организация", "Email", "Роль"])
    for row in conn.execute(
        "SELECT id,lastName,firstName,organization,email,role FROM participants ORDER BY id"
    ):
        # Prevent formula execution if opened in Excel.
        writer.writerow(
            [("'" + str(v)) if str(v).lstrip().startswith(("=", "+", "-", "@")) else v for v in row]
        )
    audit(conn, user, "export_csv", "data")
    return Response(
        "\ufeff" + output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=participants.csv"},
    )


@router.post("/api/import")
def import_data(data: ImportBundle, user=Depends(admin), conn=Depends(get_db)):
    # Entire payload was validated before touching any persistent record.
    conn.execute("BEGIN IMMEDIATE")
    for name in ("attendance", "sections", "participants"):
        conn.execute(f"DELETE FROM {name}")
    for name in ("participants", "sections", "attendance"):
        for item in getattr(data, name):
            values = item.model_dump()
            columns = ",".join(values)
            marks = ",".join("?" for _ in values)
            conn.execute(f"INSERT INTO {name} ({columns}) VALUES ({marks})", tuple(values.values()))
    audit(conn, user, "import_replace", "data")
    return {
        "ok": True,
        "participants": len(data.participants),
        "sections": len(data.sections),
        "attendance": len(data.attendance),
    }
