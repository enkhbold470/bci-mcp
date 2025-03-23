FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for recordings
RUN mkdir -p /app/recordings && chmod 777 /app/recordings

# Create a non-root user to run the application
RUN useradd -m bciuser && chown -R bciuser:bciuser /app
USER bciuser

# Default command - start the MCP server
CMD ["python", "src/main.py", "--server"]

# Expose the WebSocket port
EXPOSE 8765