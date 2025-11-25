FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Streamlit runs on 8501 by default
EXPOSE 8501

CMD ["python3", "-m", "streamlit", "run", "app.py", "--server.port", "8501", "--server.enableCORS", "true", "--server.address", "0.0.0.0"]