FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Streamlit runs on 8501 by default
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]