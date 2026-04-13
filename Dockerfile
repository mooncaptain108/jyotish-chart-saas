# Stage 1: Builder
FROM python:3.11-slim AS builder
ENV PATH="/opt/venv/bin:$PATH"
RUN python -m venv /opt/venv
WORKDIR /build
COPY requirements.txt .
RUN pip install -r requirements.txt

# depending on .dockerignore
COPY . .

# Stage 2: Production
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /build/calculations ./calculations
COPY --from=builder /build/constants ./constants
COPY --from=builder /build/ephemeris ./ephemeris
COPY --from=builder /build/include ./include
COPY --from=builder /build/models   ./models
COPY --from=builder /build/routers ./routers
COPY --from=builder /build/services ./services
COPY --from=builder /build/static ./static
COPY --from=builder /build/config.py .
COPY --from=builder /build/main.py .

ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000
# Use a JSON array to ensure correct execution
CMD  ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
