FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home appuser
COPY main.py config.py database.py models.py security.py ./
COPY routers ./routers
COPY frontend ./frontend
COPY scripts ./scripts
RUN mkdir -p data logs backups && chown -R appuser:appuser /app
USER appuser
ENV APP_HOST=0.0.0.0 APP_PORT=8000
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD python scripts/manage.py health || exit 1
CMD ["python", "main.py"]
