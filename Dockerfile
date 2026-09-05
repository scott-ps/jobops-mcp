FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run via stdio (for agent containers)
ENTRYPOINT ["python", "server.py"]