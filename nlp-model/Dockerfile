FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir transformers

COPY scamshield_bert_model ./scamshield_bert_model
COPY app.py ./

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
