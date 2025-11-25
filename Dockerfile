# 1. Use a slim Python image (Debian-based) - much smaller than full python:3.9
FROM python:3.9-slim

# 2. Set environment variables to prevent Python from buffering stdout (logs)
# and to prevent writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3. Set work directory
WORKDIR /app

# 4. Install System Dependencies (if needed for some python libs)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# 5. Copy requirements first! (Docker Cache Optimization)
COPY requirements.txt .

# 6. Install Dependencies
# CRITICAL: We use --extra-index-url to download the CPU-only version of PyTorch.
# This reduces image size from ~3GB to ~700MB.
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# 7. "Bake" the model into the image (The Advanced Trick)
# This downloads the model during 'docker build' so the container starts instantly.
# If you don't do this, it will download the model every time the container restarts (slow & bad).
RUN python -c "from transformers import pipeline; pipeline('sentiment-analysis', model='yiyanghkust/finbert-tone')"

# 8. Copy the rest of the code
COPY . .

# 9. Create a non-root user for security (Best Practice)
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# 10. Run the app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]