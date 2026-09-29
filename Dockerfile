FROM python:3.12-slim

WORKDIR /app

# Keep the database and generated documents in /data, separate from the code in /app,
# so a volume mounted there (docker run -v jobops-data:/data ...) survives rebuilds
ENV JOBOPS_DATA_DIR=/data

# Install dependencies before copying the code, so Docker can reuse this cached
# layer when only the code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run via stdio (for agent containers); set MCP_TRANSPORT=http to serve over the network instead
ENTRYPOINT ["python", "server.py"]
