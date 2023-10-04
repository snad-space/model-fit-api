FROM python:3.11

RUN pip install gunicorn uvicorn[standard]

RUN mkdir /app
COPY pyproject.toml LICENSE README.md /app/
COPY src /app/src/

RUN pip install /app

CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "model_fit_api.app:app"]