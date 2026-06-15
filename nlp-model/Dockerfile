FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn "scikit-learn==1.2.2" scipy "numpy<2.0"

COPY scamshield_model.pkl tfidf_vectorizer.pkl app.py ./

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
