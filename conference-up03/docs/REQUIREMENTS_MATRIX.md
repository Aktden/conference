# Соответствие методическим указаниям

| Этап | Требуемые материалы | Реализация в комплекте | Ограничения подтверждения |
|---|---|---|---|
| 1 Входной аудит | Паспорт, состав, настройки, журнал, запуск | Отчёт и отдельные конфигурация/журнал в submission/Этап1; INSTALL; .env.example; evidence | Реальную ссылку GitHub и ФИО вписать после публикации |
| 2 Инсталляция | BAT, Make, Docker, линтер, форматтер | scripts, Makefile, Dockerfile, Compose, Ruff, отчёт этапа 2 | Linux проверен; BAT и Docker нужно подтвердить на Windows/CI |
| 3 Развёртывание | Demo/release, env, адрес, проверка рестарта | ZIP релиза, DEPLOYMENT, DEMO_GUIDE, SHA256, release-verification.json | Это Python release/demo без публичного хостинга; Docker дополнительно |
| 4 Качество | План, API/UI, метрики, дефекты, риски, отчёт | TEST_PLAN, API_TEST_REPORT, PERFORMANCE_REPORT, DEFECT_LOG, UI PNG, QUALITY_REPORT | Вместо Lighthouse — Navigation Timing и HTTP-замеры; нет теста большой нагрузки |
| 5 Безопасность | Секреты, зависимости, роли, backup/restore, порты | SECURITY_CHECKLIST, SECURITY_REPORT, RISK_REGISTER, BACKUP_RESTORE_REPORT, логи | ss ограничен правами netlink; полный аудит ОС и внешнего TLS не выполнен |
| 6 Сопровождение | Issue, ветка, дефект, commit, CI, PR, релиз | Ветка support/conference-up03; исходный и исправляющий commits; CI; конкретные Issue/PR тексты; SUPPORT_REPORT | Реальные Issue/PR/Actions/Release создаются на GitHub после push |

Документы Word заполнены по содержанию. Пустыми оставлены только неизвестные персональные реквизиты. Не созданы фиктивные подтверждения Windows, Docker или GitHub. В evidence/screenshots — реальные снимки работающего приложения, в evidence/logs — фактические машиночитаемые и текстовые результаты.
