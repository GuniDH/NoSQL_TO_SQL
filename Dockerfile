# Use a Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire source code
COPY . .

# Create a non-root user
RUN useradd -m appuser
USER appuser

# Ensure Python can find local modules
ENV PYTHONPATH=/app

# Entry point using your poetry-style script path
ENTRYPOINT ["python", "-m", "json2csv.cli"]
