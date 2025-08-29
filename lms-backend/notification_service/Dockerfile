FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
ENV PYTHONUNBUFFERED=1
EXPOSE 5002
CMD ["gunicorn", "-b", "0.0.0.0:5002", "app:app"]
