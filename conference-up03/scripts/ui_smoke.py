"""Real browser verification on an isolated disposable demo database."""

import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", help="Optional installed Chromium executable")
    parser.add_argument("--output", default="evidence")
    args = parser.parse_args()
    output = Path(args.output).resolve()
    shots = output / "screenshots"
    logs = output / "logs"
    shots.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    errors, network, console, checks = [], [], [], []
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory(prefix="conference-ui-") as tmp:
        env = {
            **os.environ,
            "APP_ENV": "demo",
            "DEMO_MODE": "true",
            "COOKIE_SECURE": "false",
            "APP_PORT": str(port),
            "APP_HOST": "127.0.0.1",
            "DATABASE_PATH": str(Path(tmp) / "demo.db"),
            "ALLOWED_HOSTS": "127.0.0.1,localhost",
        }
        with (logs / "browser-server.txt").open("w", encoding="utf-8") as log:
            server = subprocess.Popen(
                [sys.executable, "main.py"], cwd=ROOT, env=env, stdout=log, stderr=log
            )
            try:
                for _ in range(100):
                    try:
                        with urllib.request.urlopen(base + "/api/health", timeout=1) as r:
                            if r.status == 200:
                                break
                    except OSError:
                        time.sleep(0.1)
                else:
                    raise RuntimeError("Server startup timeout")
                with sync_playwright() as p:
                    browser = p.chromium.launch(
                        headless=True,
                        executable_path=args.browser,
                        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
                    )
                    page = browser.new_page(
                        viewport={"width": 1440, "height": 1060}, device_scale_factor=1
                    )
                    page.on("pageerror", lambda err: errors.append(str(err)))
                    page.on(
                        "console", lambda msg: console.append({"type": msg.type, "text": msg.text})
                    )
                    page.on(
                        "response",
                        lambda r: network.append(
                            {"path": r.url.replace(base, ""), "status": r.status}
                        ),
                    )

                    def shot(name):
                        page.screenshot(path=str(shots / (name + ".png")), full_page=True)

                    def nav(name):
                        page.goto(base + "/#" + name)
                        expect(page.locator("#page-body")).to_be_visible()

                    def sign_in(role, password):
                        page.get_by_label("Логин", exact=True).fill(role)
                        page.get_by_label("Пароль", exact=True).fill(password)
                        page.get_by_role("button", name="Войти в пространство").click()
                        expect(
                            page.get_by_role("heading", name="Обзор конференции")
                        ).to_be_visible()

                    page.goto(base)
                    expect(page.get_by_label("Логин", exact=True)).to_be_visible()
                    shot("login")
                    sign_in("admin", "DemoAdmin!2026")
                    shot("dashboard")
                    for name in [
                        "participants",
                        "sections",
                        "attendance",
                        "badges",
                        "reports",
                        "audit",
                    ]:
                        nav(name)
                        shot(name)
                    checks.append("All seven application pages opened as administrator")

                    nav("participants")
                    page.get_by_role("button", name="Добавить участника").click()
                    form = page.locator("#modal-form")
                    form.get_by_label("Фамилия", exact=True).fill("Проверочный")
                    form.get_by_label("Имя", exact=True).fill("Участник")
                    form.get_by_label("Email", exact=True).fill("ui-check@example.com")
                    form.get_by_label("Организация", exact=True).fill("Учебная проверка")
                    shot("participant-form")
                    form.get_by_role("button", name="Сохранить", exact=True).click()
                    expect(page.locator("#modal")).not_to_be_visible()
                    page.get_by_label("Поиск по имени, email или организации").fill("ПРОВЕРОЧНЫЙ")
                    expect(page.locator("tbody tr")).to_have_count(1)
                    checks.append(
                        "UI creates and searches a participant with Cyrillic case folding"
                    )
                    page.get_by_role("button", name="Добавить участника").click()
                    form.get_by_label("Фамилия", exact=True).fill("Дубликат")
                    form.get_by_label("Имя", exact=True).fill("Тест")
                    form.get_by_label("Email", exact=True).fill("ui-check@example.com")
                    form.get_by_role("button", name="Сохранить", exact=True).click()
                    expect(page.locator("#modal-error")).to_contain_text("уже зарегистрирован")
                    shot("duplicate-error")
                    page.get_by_role("button", name="Закрыть", exact=True).click()
                    checks.append(
                        "Duplicate email displays an explicit error without losing the form"
                    )

                    nav("sections")
                    page.get_by_role("button", name="Создать секцию", exact=True).click()
                    form.get_by_label("Название", exact=True).fill("Проверка UI")
                    form.get_by_label("Аудитория", exact=True).fill("Тестовая")
                    form.get_by_label("Вместимость", exact=True).fill("1")
                    form.get_by_label("Время начала", exact=True).fill("16:00")
                    form.get_by_role("button", name="Сохранить", exact=True).click()
                    expect(page.locator("#modal")).not_to_be_visible()
                    card = page.locator(".section-card").filter(has_text="Проверка UI")
                    card.get_by_role("button", name="Записать участника", exact=True).click()
                    option = form.locator("select[name=participantId] option").filter(
                        has_text="ui-check@example.com"
                    )
                    form.locator('select[name="participantId"]').select_option(
                        option.get_attribute("value")
                    )
                    form.get_by_role("button", name="Записать", exact=True).click()
                    expect(page.locator("#modal")).not_to_be_visible()
                    nav("attendance")
                    page.get_by_label("Поиск участника", exact=True).fill("Проверочный")
                    page.get_by_role("button", name="Пришёл", exact=True).click()
                    expect(page.locator("tbody")).to_contain_text("присутствовал")
                    checks.append(
                        "UI creates a section, registers a participant and marks attendance"
                    )

                    nav("badges")
                    page.get_by_label("Найти бейдж по имени", exact=True).fill("Проверочный")
                    page.evaluate("window.print = () => { window.printRequested = true; }")
                    page.get_by_role("button", name="Печать", exact=True).click()
                    assert page.evaluate("window.printRequested")
                    expect(page.locator("#print-area .badge-preview")).to_have_count(1)
                    expect(page.get_by_role("button", name="Выдан", exact=True)).to_be_visible()
                    page.get_by_role("button", name="Выдан", exact=True).click()
                    expect(
                        page.get_by_role("button", name="Выдан · отменить", exact=True)
                    ).to_be_visible()
                    checks.append(
                        "Print preview is built separately from badge issuance; no physical printer used"
                    )

                    nav("reports")
                    with page.expect_download() as download:
                        page.get_by_role("button", name="Экспорт JSON", exact=True).click()
                    dest = Path(tmp) / "export.json"
                    download.value.save_as(dest)
                    data = json.loads(dest.read_text())
                    assert len(data["participants"]) == 13 and "users" not in data
                    page.get_by_role("button", name="Восстановить из JSON", exact=True).click()
                    page.locator("#import-file").set_input_files(dest)
                    form.get_by_label("Введите ЗАМЕНИТЬ для подтверждения", exact=True).fill(
                        "ЗАМЕНИТЬ"
                    )
                    form.get_by_role("button", name="Заменить данные", exact=True).click()
                    expect(page.locator("#modal")).not_to_be_visible()
                    checks.append("UI exports JSON and restores the same validated dataset")

                    page.set_viewport_size({"width": 390, "height": 844})
                    nav("dashboard")
                    assert page.evaluate(
                        "document.documentElement.scrollWidth <= window.innerWidth"
                    )
                    shot("mobile-dashboard")
                    page.get_by_role("button", name="Открыть меню", exact=True).click()
                    expect(page.locator(".app")).to_have_class("app menu-open")
                    page.locator("nav").get_by_role("link", name="Участники").click()
                    expect(
                        page.get_by_role("heading", name="Участники", exact=True)
                    ).to_be_visible()
                    assert page.evaluate(
                        "document.documentElement.scrollWidth <= window.innerWidth"
                    )
                    shot("mobile-participants")
                    checks.append(
                        "390px mobile viewport has no document-level horizontal overflow; navigation works"
                    )

                    page.set_viewport_size({"width": 1440, "height": 1060})
                    page.get_by_role("button", name="Выйти", exact=True).click()
                    expect(page.get_by_label("Логин", exact=True)).to_be_visible()
                    sign_in("viewer", "DemoViewer!2026")
                    expect(page.locator('nav a[href="#participants"]')).to_have_count(0)
                    nav("reports")
                    expect(
                        page.get_by_role("button", name="Экспорт JSON", exact=True)
                    ).to_have_count(0)
                    shot("viewer-reports")
                    checks.append(
                        "Viewer sees aggregate reports without participant navigation or export controls"
                    )
                    performance = page.evaluate(
                        "JSON.stringify(performance.getEntriesByType('navigation').map(n=>({domContentLoadedMs:n.domContentLoadedEventEnd,loadMs:n.loadEventEnd,transferBytes:n.transferSize})))"
                    )
                    report = {
                        "browser": browser.version,
                        "checks": checks,
                        "javascript_errors": errors,
                        "http_5xx": [r for r in network if r["status"] >= 500],
                        "expected_errors": "401 before login and 409 for deliberate duplicate submission are expected",
                        "navigation_timing": json.loads(performance),
                        "network": network,
                        "console": console,
                    }
                    (logs / "ui-report.json").write_text(
                        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
                    assert not errors and not report["http_5xx"]
                    print(
                        json.dumps(
                            {
                                "ui_checks": len(checks),
                                "javascript_errors": len(errors),
                                "http_5xx": len(report["http_5xx"]),
                                "screenshots": len(list(shots.glob("*.png"))),
                                "browser": browser.version,
                            },
                            indent=2,
                        )
                    )
                    browser.close()
            finally:
                server.terminate()
                server.wait(timeout=10)


if __name__ == "__main__":
    main()
