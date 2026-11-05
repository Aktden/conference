"""Cross-platform maintenance commands. Run from any working directory."""

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import statistics
import subprocess
import sys
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import settings_from_env  # noqa: E402


def run(*args):
    print("$", " ".join(str(a) for a in args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def verified_connection(path):
    if not path.is_file():
        raise ValueError(f"Database does not exist: {path}")
    conn = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("SQLite integrity check failed")
        if conn.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("SQLite foreign key check failed")
        required = {"participants", "sections", "attendance", "users", "sessions", "audit"}
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not required <= tables:
            raise ValueError("This is not a complete conference database")
    except Exception:
        conn.close()
        raise
    return conn


def backup_database(source, destination):
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve() or destination.exists():
        raise ValueError("Choose a new backup path; existing files are never overwritten")
    destination.parent.mkdir(parents=True, exist_ok=True)
    src = verified_connection(source)
    try:
        with sqlite3.connect(destination) as dst:
            src.backup(dst)
    finally:
        src.close()
    check = verified_connection(destination)
    check.close()
    try:
        destination.chmod(0o600)
    except OSError:
        pass
    return {
        "file": str(destination),
        "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        "bytes": destination.stat().st_size,
    }


def restore_database(source, destination):
    # Restore into a NEW path; never replace a live SQLite/WAL file.
    info = backup_database(source, destination)
    with sqlite3.connect(destination) as conn:
        conn.execute("DELETE FROM sessions")
        conn.execute("DELETE FROM login_attempts")
        counts = {
            t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for t in ("participants", "sections", "attendance")
        }
    return {
        "file": info["file"],
        "sha256": hashlib.sha256(Path(destination).read_bytes()).hexdigest(),
        "counts": counts,
        "sessions": "invalidated",
    }


def build_release():
    release = ROOT / "release"
    release.mkdir(exist_ok=True)
    target = release / "conference-v3.0.0.zip"
    root_files = [
        "main.py",
        "database.py",
        "models.py",
        "security.py",
        "config.py",
        "requirements.txt",
        "requirements-dev.txt",
        "pyproject.toml",
        "README.md",
        "INSTALL.md",
        "DEPLOYMENT.md",
        "DEMO_GUIDE.md",
        "CHANGELOG.md",
        "RELEASE_NOTES.md",
        "SECURITY.md",
        "Makefile",
        "Dockerfile",
        "docker-compose.yml",
        "docker-compose.prod.yml",
        ".dockerignore",
        ".gitignore",
        ".editorconfig",
        ".env.example",
        ".env.demo.example",
        ".env.production.example",
    ]
    files = [ROOT / name for name in root_files if (ROOT / name).is_file()]
    for folder in ["frontend", "routers", "scripts", "tests", ".github", "docs"]:
        files.extend(
            p
            for p in (ROOT / folder).rglob("*")
            if p.is_file()
            and "__pycache__" not in p.parts
            and p.suffix not in (".pyc", ".db", ".log")
        )
    preview = ROOT / "evidence" / "screenshots" / "dashboard.png"
    if preview.is_file():
        files.append(preview)
    manifest = {}
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(files):
            rel = path.relative_to(ROOT).as_posix()
            z.write(path, "conference/" + rel)
            manifest[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
        z.writestr("conference/MANIFEST.sha256.json", json.dumps(manifest, indent=2))
    checksum = hashlib.sha256(target.read_bytes()).hexdigest()
    (release / "SHA256SUMS.txt").write_text(f"{checksum}  {target.name}\n", encoding="utf-8")
    print(json.dumps({"archive": str(target), "files": len(files), "sha256": checksum}, indent=2))
    return target


def security_scan():
    proc = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc.returncode:
        raise ValueError("Run security scan inside a Git checkout")
    bad, suspicious = [], []
    for name in sorted(set(proc.stdout.splitlines())):
        path = ROOT / name
        if not path.is_file():
            continue
        if path.name == ".env" or path.suffix in (".db", ".sqlite", ".pem", ".key"):
            bad.append(name)
        if path.suffix in (".py", ".js", ".yml", ".md", ".txt"):
            source = path.read_text(encoding="utf-8", errors="replace")
            if re.search(
                r"(?:gh[pousr]_[A-Za-z0-9]{30,}|AKIA[A-Z0-9]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)",
                source,
            ):
                suspicious.append(name)
    print(
        json.dumps(
            {
                "forbidden_tracked_files": bad,
                "credential_patterns": suspicious,
                "note": "Demo credentials are intentional synthetic examples; review generic password/token matches manually.",
            },
            indent=2,
        )
    )
    if bad or suspicious:
        raise ValueError("Review findings before publishing")


def health(base):
    with urllib.request.urlopen(base.rstrip("/") + "/api/health", timeout=10) as r:
        data = json.load(r)
    if data.get("status") != "ok":
        raise ValueError("Healthcheck failed")
    print(json.dumps(data, ensure_ascii=False))


def performance(base, count=100):
    durations = []
    for _ in range(count):
        start = time.perf_counter()
        with urllib.request.urlopen(base.rstrip("/") + "/api/health", timeout=10) as r:
            if r.status != 200:
                raise ValueError("Non-200 response")
            r.read()
        durations.append((time.perf_counter() - start) * 1000)
    result = {
        "endpoint": "/api/health",
        "requests": count,
        "concurrency": 1,
        "median_ms": round(statistics.median(durations), 2),
        "p95_ms": round(sorted(durations)[int(count * 0.95) - 1], 2),
        "max_ms": round(max(durations), 2),
        "errors": 0,
        "scope": "Local sequential healthcheck only; not a production capacity estimate",
    }
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=[
            "check",
            "test",
            "format",
            "build",
            "health",
            "backup",
            "restore",
            "security",
            "deps",
            "performance",
            "ports",
            "logs",
        ],
    )
    parser.add_argument("file", nargs="?")
    parser.add_argument("--target")
    parser.add_argument("--confirm")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    py = sys.executable
    if args.command == "check":
        run(py, "-m", "ruff", "check", ".")
        run(py, "-m", "ruff", "format", "--check", ".")
        run(
            py,
            "-m",
            "pytest",
            "--cov",
            "--cov-report=term-missing",
            "--cov-fail-under=80",
            "--junitxml=reports/junit.xml",
        )
    elif args.command == "test":
        run(py, "-m", "pytest", "-q")
    elif args.command == "format":
        run(py, "-m", "ruff", "check", "--fix", ".")
        run(py, "-m", "ruff", "format", ".")
    elif args.command == "build":
        build_release()
    elif args.command == "health":
        health(args.url)
    elif args.command == "backup":
        destination = (
            Path(args.file)
            if args.file
            else ROOT
            / "backups"
            / ("conference-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f") + ".db")
        )
        print(json.dumps(backup_database(settings_from_env().db_path, destination), indent=2))
    elif args.command == "restore":
        if not args.file or not args.target or args.confirm != "RESTORE":
            parser.error("restore requires FILE --target NEW_DB_PATH --confirm RESTORE")
        print(json.dumps(restore_database(Path(args.file), Path(args.target)), indent=2))
    elif args.command == "security":
        security_scan()
    elif args.command == "deps":
        run(py, "-m", "pip_audit", "-r", "requirements.txt", "--timeout", "20")
    elif args.command == "performance":
        performance(args.url)
    elif args.command == "ports":
        run(*(["netstat", "-ano"] if os.name == "nt" else ["ss", "-ltnp"]))
    elif args.command == "logs":
        path = ROOT / "logs" / "app.log"
        if path.exists():
            print("\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-100:]))
        elif shutil.which("docker"):
            run("docker", "compose", "logs", "--tail=100")
        else:
            raise ValueError("No logs/app.log yet. Start the application first.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
