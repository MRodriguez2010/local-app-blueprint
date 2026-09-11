FROM python:3.12-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app \
    && mkdir -p /app/data && chown app:app /app/data
WORKDIR /app
COPY --chown=app:app app.py /app/app.py
USER 10001:10001
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_BIND=0.0.0.0 APP_DATA_DIR=/app/data
CMD ["python", "/app/app.py"]
