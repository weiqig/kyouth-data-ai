FROM python:3.14.4-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .
RUN uv sync --frozen --no-dev

EXPOSE 8000

ENTRYPOINT ["uv", "run", "uvicorn"]
CMD ["--app-dir", "src", "--host", "0.0.0.0", "--port", "8000", "app:app"]