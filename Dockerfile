FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY docker/train-requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY params.yaml ./
COPY data/processed/ ./data/processed/

CMD ["python", "src/train.py"]
