FROM debian:bookworm-slim

WORKDIR /app

# create a non-root user variable
ARG USERNAME=whatapp-webhook

RUN adduser --disabled-password --gecos "" ${USERNAME} && \
    chown -R ${USERNAME}:${USERNAME} /app


RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

USER ${USERNAME}

COPY whatsapp_webhook/ whatsapp_webhook
COPY main.py .
COPY pyproject.toml .

RUN curl -Ls https://astral.sh/uv/install.sh -o /tmp/install.sh

RUN sh /tmp/install.sh
# Usar la ruta completa de uv
RUN ~/.local/bin/uv sync

USER ${USERNAME}

ENV PATH="/home/${USERNAME}/.local/bin:$PATH"

CMD ["uv", "run","uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]