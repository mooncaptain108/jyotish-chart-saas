# Stage 1: Builder
FROM python:3.11-slim AS builder
ENV PATH="/opt/venv/bin:$PATH"
RUN python -m venv /opt/venv
WORKDIR /build
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY 

# Stage 2: Production
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"  # Must re-declare!
COPY 
EXPOSE 8000
CMD ["python", "app.py"]   