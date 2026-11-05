# Развёртывание и перезапуск

Основной проверенный результат — релизный ZIP с приложением и локальными ресурсами, запускаемый вне IDE. Это не exe: нужен Python и первоначальная установка зависимостей. Публичный хостинг не создавался.

## Релиз

`make build` или scripts\build.bat создаёт release/conference-v3.0.0.zip. Сборщик использует явный список исходных файлов; не включает рабочую БД, .env, сессии, логи, резервные копии и .git. Внутри MANIFEST.sha256.json, рядом SHA256SUMS.txt. Распакуйте в новую папку, выполните setup и run, проверьте /api/health. Остановите сервер и запустите снова; записи должны сохраниться. Фактические проверки отдельной распаковки — evidence/logs/release-verification.json.

## Docker демо

```sh
docker compose up --build -d
docker compose ps
docker compose logs --tail=100
docker compose restart app
curl --fail http://127.0.0.1:8000/api/health
docker compose down
```

BAT-эквиваленты: deploy, restart, check_deploy, docker-down. Данные сохраняются в именованном томе; `down -v` удаляет том, не применяйте его для сохранённых данных. Docker в среде подготовки отсутствовал; реальная сборка контейнера проверяется на компьютере пользователя или job container в CI.

## Production

Скопируйте .env.production.example в .env.production, задайте собственные ADMIN_PASSWORD и ALLOWED_HOSTS. Настройте HTTPS reverse proxy перед 127.0.0.1:8000. Передавайте Host и X-Forwarded-Proto; доверие прокси ограничьте его адресом. Затем выполните `docker compose -f docker-compose.prod.yml up --build -d`. Войдите через HTTPS, проверьте Secure cookie и отсутствие /docs.

Рабочий режим использует отдельный том и отклоняет БД с меткой demo. Изменение ADMIN_PASSWORD после создания аккаунта не меняет сохранённый пароль; задайте его до первого запуска. Управление аккаунтами через интерфейс не реализовано.

## Откат

До обновления сделайте backup. Остановите сервер, замените исходники на новый релиз, сохраните конфигурацию и данные, запустите health и основной сценарий. При сбое верните предыдущую версию; восстановите backup в новый файл и укажите его в DATABASE_PATH. Подробности — docs/BACKUP_RESTORE_REPORT.md.
