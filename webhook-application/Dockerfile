FROM python:3.12-slim
WORKDIR /app

# create a non-root user variable
ARG USERNAME=whatapp-webhook

COPY whatsapp_webhook/ whatsapp_webhook
COPY main.py .
COPY pyproject.toml .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv

RUN uv sync

RUN adduser --disabled-password --gecos "" ${USERNAME} && \
    chown -R ${USERNAME}:${USERNAME} /app


USER ${USERNAME}

ENV PATH="/home/${USERNAME}/.local/bin:$PATH"

CMD ["uv", "run","uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]