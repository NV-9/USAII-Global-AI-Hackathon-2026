FROM python:3.11-slim

WORKDIR /app

COPY requirements-serve.txt .
RUN pip install --no-cache-dir -r requirements-serve.txt --extra-index-url https://download.pytorch.org/whl/cpu

COPY scamshield_bert_model ./scamshield_bert_model
COPY app.py ./

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
