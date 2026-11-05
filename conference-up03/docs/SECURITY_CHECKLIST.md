# Проверки безопасности

| Проверка | Итог | Доказательство |
|---|---|---|
| .env, базы, ключи, backups исключены из Git | Проверка скриптом и просмотр состава | secret-scan.json, .gitignore |
| Примеры настроек не содержат реальных секретов | Пустой ADMIN_PASSWORD; демо-пароли намеренно открытые | .env*.example, README |
| Зависимости | Проверены 17 runtime-дистрибутивов, известных advisories не найдено | dependency-audit.json |
| Доступ без входа | 401 | test_authentication_cookie_and_logout |
| viewer к персональным объектам | 403, в UI нет именных разделов | test_viewer_cannot_read_personal_records, viewer-reports.png |
| operator к admin-функциям | 403 | test_operator_permissions |
| CSRF и чужой Origin | 403 | test_login_origin_and_csrf |
| CORS, hosts и заголовки | Wildcard CORS отсутствует, чужой Host отклоняется | test_headers_and_hosts |
| Backup/restore | Количества сохранены, integrity ok, сессии очищены | backup-restore.json |
| Порты | Частичная проверка: виден loopback; netlink ограничен средой, полный аудит ОС не выполнен | ports.txt |
| Логи | В успешных UI сценариях нет 500 | ui-report.json, browser-server.txt |
| Production HTTPS | Конфигурация подготовлена, внешний TLS не проверен | DEPLOYMENT.md |

Отсутствие известных advisories на дату проверки не равно полной безопасности. Файлы с демонстрационными паролями не являются утечкой реальных учётных данных. Владение отдельными участниками не применяется: общий реестр оргкомитета, защита по роли.
