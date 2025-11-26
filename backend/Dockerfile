FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
# Install CPU-only torch to save space
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Pre-load model
RUN python -c "from transformers import pipeline; pipeline('sentiment-analysis', model='yiyanghkust/finbert-tone')"

# Copy the 'app' folder
COPY ./app ./app

RUN adduser --disabled-password --gecos '' appuser
USER appuser

EXPOSE 8000
# Note the change: we run "app.main:app" assuming the code is inside an "app" folder
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]