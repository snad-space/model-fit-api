FROM python:3.11

WORKDIR /app

COPY pyproject.toml LICENSE README.md ./

COPY src ./src

RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --only main --no-interaction

RUN ls -la /app/src/model_fit_api/app.py

CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "src.model_fit_api.app:app"]

