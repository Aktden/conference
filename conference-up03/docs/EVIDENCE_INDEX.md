# Доказательства выполнения

Все файлы logs перечислены относительно evidence. Скриншоты сделаны Chromium 133 через Playwright с работающего временного демо-приложения. Синтетические участники используют example.com. Содержимое не изображает реальные действия в GitHub или Windows.

| Файл | Что подтверждает |
|---|---|
| logs/check.txt | Чистая копия: Ruff, форматирование, 40 тестов, покрытие 95,94% |
| logs/clean-clone.txt, clean-install.txt | Клонирование и установка зависимостей с нуля |
| logs/check-primary.txt | Предыдущий полный прогон: 40 тестов, покрытие 96,35% |
| logs/ui-report.json, ui-check.txt | 8 браузерных проверок, сеть, отсутствие ошибок JavaScript |
| logs/original-startup-error.txt | Воспроизведение исходной ошибки чистого запуска |
| logs/concurrency-before.xml | Реальный упавший тест до исправления SQLite |
| logs/dependency-audit.json | Проверка всех 17 зафиксированных runtime-дистрибутивов |
| logs/pip-check.txt | Совместимость установленных зависимостей |
| logs/release-verification.json | Распаковка, манифест, запуск вне cwd, рестарт |
| logs/api-cases.json, performance.json | Реальные HTTP-результаты и время 300 запросов |
| logs/backup-restore.json | Копирование, восстановление, целостность и числа записей |
| logs/ports.txt | Частичный ss с явным ограничением netlink |
| screenshots/dashboard.png | Работающий обзор конференции |
| screenshots/participant-form.png, duplicate-error.png | Форма и обработка дубликата |
| screenshots/sections.png, attendance.png, badges.png | Основные модули приложения |
| screenshots/mobile-dashboard.png, mobile-participants.png | Мобильный интерфейс 390 px |
| screenshots/viewer-reports.png | Ограниченная роль наблюдателя |

Негативные 401 до входа и 409 при намеренном дубликате ожидаемы. Ошибки в файлах «before» — доказательства устранённого дефекта, а не результат финального прогона.
