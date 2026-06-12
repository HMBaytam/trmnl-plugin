# ---- builder ----
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    UV_PYTHON_DOWNLOADS=0
WORKDIR /app
# Install deps first (cached layer) without the project itself.
# Copy only the lock + manifest so this layer is reused unless deps change.
COPY uv.lock pyproject.toml ./
RUN uv sync --frozen --no-install-project
COPY . /app
RUN uv sync --frozen

# ---- runtime ----
FROM python:3.13-slim-bookworm
# Non-root user
RUN groupadd --system --gid 999 nonroot \
 && useradd  --system --gid 999 --uid 999 --create-home nonroot
COPY --from=builder --chown=nonroot:nonroot /app /app
ENV PATH="/app/.venv/bin:$PATH"
USER nonroot
WORKDIR /app
EXPOSE 8000
CMD ["fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]
