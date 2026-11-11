FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir mlflow-skinny scikit-learn pandas skops fastapi uvicorn
COPY src/serve.py .
CMD ["uvicorn", "serve:app", "--host", "0.0.0.0", "--port", "8000"]