# SecOps backend — FastAPI + LangGraph. Lean python:3.12-slim + uv, non-root.
# No secrets baked in: DEMO_PASSWORD / POSTGRES_DSN / OPENROUTER_API_KEY are runtime env.
# The HF embedding model + RAG knowledge index are prebuilt into the image so the
# container runs fully offline (mock mode) with a fast cold start.
FROM python:3.12-slim

# uv from the official distroless image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Trivy — the vuln_scanner agent shells out to the `trivy` binary; without it the cloud
# run hits FileNotFoundError. ca-certificates/curl are needed to fetch the install script.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
       | sh -s -- -b /usr/local/bin \
    && apt-get purge -y curl \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_CACHE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app \
    HF_HOME=/app/.cache/huggingface \
    TRIVY_CACHE_DIR=/opt/trivy-cache

# Bake the Trivy vulnerability DB into the image (network is only available at build time —
# the running container can't reach ghcr.io). Lives outside /app so the fs scan never walks
# it; scanner.py runs with --skip-db-update so vuln_scanner works fully offline. chown to the
# runtime uid (the 'app' user is created later) since trivy needs to lock the cache dir.
RUN trivy fs --download-db-only && chown -R 10001:10001 /opt/trivy-cache

# 1) Dependencies only (cached layer — re-used unless the lockfile changes).
# torch is pinned to the CPU wheel index in pyproject.toml/uv.lock, so this pulls the
# lean CPU build (not the ~6GB CUDA one) — bge-small embeddings run on CPU. UV_NO_CACHE
# (set above, the uv equivalent of pip --no-cache-dir) keeps the layer slim.
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
