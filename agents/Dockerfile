FROM python:3.12-slim
WORKDIR /app

# create a non-root user variable
ARG USERNAME=agent-app-user

COPY agent_pp_app/ agent_pp_app
COPY agent_aa_app/ agent_aa_app
COPY main.py .
COPY pyproject.toml .
COPY uv.lock .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv

RUN uv sync

RUN adduser --disabled-password --gecos "" ${USERNAME} && \
    chown -R ${USERNAME}:${USERNAME} /app


USER ${USERNAME}

ENV PATH="/home/${USERNAME}/.local/bin:$PATH"

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]