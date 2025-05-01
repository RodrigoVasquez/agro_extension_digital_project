FROM python:3.12-slim
WORKDIR /app

COPY pyproject.toml .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv && \
    uv pip install

RUN adduser --disabled-password --gecos "" myuser && \
    chown -R myuser:myuser /app

COPY . .

USER agent-app-user

ENV PATH="/home/agent-app-user/.local/bin:$PATH"

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8080"]