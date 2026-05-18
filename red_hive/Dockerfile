FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY red_hive/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY core ./core
COPY red_hive/app.py ./app.py

CMD ["python", "app.py"]
