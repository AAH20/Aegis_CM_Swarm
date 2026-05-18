FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY blue_hive/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY core ./core
COPY blue_hive/app.py ./app.py

CMD ["python", "app.py"]
