FROM python:3.12-slim
ARG GIT_COMMIT=unknown
ENV GIT_COMMIT=${GIT_COMMIT}
WORKDIR /app
COPY docker/train-requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ src/
COPY params.yaml .
COPY data/processed/ data/processed/
CMD ["python", "src/train_hpo.py"]
