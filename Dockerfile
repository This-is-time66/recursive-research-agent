# ── Hugging Face Spaces — Docker SDK ────────────────────────────────────────
# Base image: slim Python 3.11
FROM python:3.11-slim

# HF Spaces requires the app to listen on port 7860
ENV PORT=7860

# Set working directory
WORKDIR /app

# Install system dependencies needed by psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Expose the port Hugging Face expects
EXPOSE 7860

# Start the FastAPI app with uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
