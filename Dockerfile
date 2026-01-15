FROM python:3.13

WORKDIR /app

COPY pyproject.toml LICENSE README.md ./

COPY src ./src

RUN pip install uv
RUN uv pip install --system --compile-bytecode .

RUN ls -la /app/src/model_fit_api/app.py

CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "model_fit_api.app:app"]

