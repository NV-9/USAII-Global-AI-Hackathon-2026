# ScamShield AI - NLP Model

Full model documentation (performance, architecture, development journey, training data, API contract, model-update history) now lives in the [repository root README](../README.md#nlp-model).

## Files

| File | Description |
|---|---|
| `scamshield_nlp.ipynb` | Main Jupyter notebook — full BERT training pipeline |
| `scamshield_bert_model/` | Deployed three-tier BERT model folder (`model.safetensors` downloaded separately, see root README) |
| `scamshield_bert_model_v2/`, `_v3/`, `_v4/` | Local GPU retrain checkpoints kept for reference only — not used by the deployed service |
| `train_bert.py` | GPU training script used for the `v2`-`v4` retrain experiments |
| `app.py` | FastAPI wrapper that serves the model on port 8001 |
| `scamshield_model.pkl`, `tfidf_vectorizer.pkl` | TF-IDF baseline model (kept for reference) |
| `synthetic_scam_data*.csv`, `synthetic_medium_extra*.csv` | Synthetic training datasets |
| `test_set_50.csv` | 50-message held-out evaluation set |
| `requirements.txt` | Notebook/training dependencies |
| `requirements-serve.txt` | Pinned dependencies for the `app.py` FastAPI service |

## Running the notebook

```bash
pip install -r requirements.txt
jupyter notebook scamshield_nlp.ipynb
```

Requires `scamshield_bert_model/model.safetensors` to be downloaded first — see the root README's [Download the Model](../README.md#download-the-model) section.
