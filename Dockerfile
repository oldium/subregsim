ARG PYTHON_IMAGE=python:3.14-alpine
ARG UV_IMAGE=ghcr.io/astral-sh/uv:latest

FROM ${UV_IMAGE} AS uv
FROM ${PYTHON_IMAGE} AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

COPY --from=uv /uv /uvx /bin/

COPY pyproject.toml uv.lock README.md LICENSE.txt ./
RUN uv sync --locked --no-install-project --no-dev --no-editable

COPY subregsim ./subregsim
RUN uv sync --locked --no-dev --no-editable

FROM ${PYTHON_IMAGE} AS runtime

WORKDIR /app

EXPOSE 80 443

COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

RUN mkdir -p /config

WORKDIR /config

ENTRYPOINT ["subregsim"]
CMD ["--help"]
