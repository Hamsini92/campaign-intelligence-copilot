FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY app/ app/

# Copy lambda handlers and model/data (mounted as volumes in docker-compose)
# These are added via volume mounts

ENV PYTHONPATH="/app:/lambdas"
ENV LOCAL_MODE=true

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
