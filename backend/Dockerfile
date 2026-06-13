# SecOps backend — FastAPI + LangGraph. Lean python:3.12-slim + uv, non-root.
# No secrets baked in: DEMO_PASSWORD / POSTGRES_DSN / OPENROUTER_API_KEY are runtime env.
# The HF embedding model + RAG knowledge index are prebuilt into the image so the
# container runs fully offline (mock mode) with a fast cold start.
FROM python:3.12-slim

# uv from the official distroless image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app \
    HF_HOME=/app/.cache/huggingface

# 1) Dependencies only (cached layer — re-used unless the lockfile changes).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 2) App source + fixtures, then install the project.
COPY secops ./secops
COPY fixtures ./fixtures
RUN uv sync --frozen --no-dev

# 3) Prebuild the RAG knowledge index + cache the embedding model into the image.
RUN uv run python -m secops.app index

# Non-root runtime user owns the app dir (incl. the baked model + LanceDB index).
RUN useradd -m -u 10001 app && chown -R app:app /app
USER app

EXPOSE 8000
CMD ["uvicorn", "secops.server:app", "--host", "0.0.0.0", "--port", "8000"]
