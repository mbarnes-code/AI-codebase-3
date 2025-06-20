FROM python:3.10-slim

# Security: Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Security: Install security updates only
RUN apt-get update && apt-get upgrade -y && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Security: Copy and install dependencies first (better caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY llm_server.py ./

# Security: Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Security: Switch to non-root user
USER appuser

EXPOSE 8000

# Security: Use exec form and specific user
CMD ["python", "-m", "uvicorn", "llm_server:app", "--host", "0.0.0.0", "--port", "8000"]
