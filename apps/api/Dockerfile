ARG DOCKER_PYTHON_IMAGE=docker.io/library/python:3.12-slim
FROM ${DOCKER_PYTHON_IMAGE}

WORKDIR /app

ARG PYPI_INDEX_URL=https://pypi.org/simple/
ARG PIP_TRUSTED_HOST=

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt .

RUN if [ -n "$PIP_TRUSTED_HOST" ]; then \
      pip install --no-cache-dir \
        --index-url "${PYPI_INDEX_URL}" \
        --trusted-host "${PIP_TRUSTED_HOST}" \
        -r requirements.txt; \
    else \
      pip install --no-cache-dir \
        --index-url "${PYPI_INDEX_URL}" \
        -r requirements.txt; \
    fi

COPY apps/api/app ./app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
