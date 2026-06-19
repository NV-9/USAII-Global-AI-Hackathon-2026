import os
import random

import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, BertForSequenceClassification, get_linear_schedule_with_warmup

SEED = 42
MODEL_NAME = "bert-base-uncased"
MAX_LENGTH = 256
BATCH_SIZE = 32
EPOCHS = 3
LR = 2e-5
OUT_DIR = "scamshield_bert_model_v4"

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")


def load_combined_dataset() -> pd.DataFrame:
    df1 = pd.read_csv("spam.csv", encoding="latin-1")[["v1", "v2"]]
    df1.columns = ["label", "message"]
    df1["label"] = df1["label"].map({"ham": 0, "spam": 1})
    df1["source"] = "sms_spam"

    df2 = pd.read_csv("SMS Spam Dataset.csv")
    df2 = df2.rename(columns={"sms": "message"})[["message", "label"]]
    df2["source"] = "sms_spam"

    df3 = pd.read_csv("synthetic_scam_data.csv")[["message", "label"]]
    df3["source"] = "synthetic_conversational"

    combined = pd.concat([df1, df2, df3], ignore_index=True)
    combined["message"] = combined["message"].astype(str).str.strip()
    combined = combined.drop_duplicates(subset="message").dropna()
    combined["label"] = combined["label"].astype(int)
    return combined.reset_index(drop=True)


class ScamDataset(Dataset):
    def __init__(self, messages, labels, tokenizer):
        self.encodings = tokenizer(
            list(messages),
            truncation=True,
            max_length=MAX_LENGTH,
            padding="max_length",
            return_tensors="pt",
        )
        self.labels = torch.tensor(list(labels), dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {k: v[idx] for k, v in self.encodings.items()}
        item["labels"] = self.labels[idx]
        return item


def evaluate(model, loader):
    model.eval()
    all_preds, all_labels, all_probs = [], [], []
    with torch.no_grad():
        for batch in loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            logits = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"]).logits
            probs = torch.softmax(logits, dim=-1)[:, 1]
            preds = torch.argmax(logits, dim=-1)
            all_preds.extend(preds.cpu().tolist())
            all_labels.extend(batch["labels"].cpu().tolist())
            all_probs.extend(probs.cpu().tolist())
    acc = accuracy_score(all_labels, all_preds)
    f1 = f1_score(all_labels, all_preds)
    return acc, f1, all_labels, all_preds, all_probs


def main():
    df = load_combined_dataset()
    print(f"Combined dataset: {len(df)} rows, label distribution: {df['label'].value_counts().to_dict()}")

    train_df, val_df = train_test_split(
        df, test_size=0.1, stratify=df["label"], random_state=SEED
    )

    OVERSAMPLE_FACTOR = 2
    conversational = train_df[train_df["source"] == "synthetic_conversational"]
    train_df = pd.concat(
        [train_df] + [conversational] * (OVERSAMPLE_FACTOR - 1), ignore_index=True
    ).sample(frac=1.0, random_state=SEED).reset_index(drop=True)

    print(f"Train: {len(train_df)}  Val: {len(val_df)}")
    print(f"Train source distribution: {train_df['source'].value_counts().to_dict()}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    train_ds = ScamDataset(train_df["message"], train_df["label"], tokenizer)
    val_ds = ScamDataset(val_df["message"], val_df["label"], tokenizer)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE * 2)

    model = BertForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=2, problem_type="single_label_classification"
    ).to(device)

    class_counts = train_df["label"].value_counts().sort_index()
    class_weights = torch.tensor(
        [len(train_df) / (2 * class_counts[0]), len(train_df) / (2 * class_counts[1])],
        dtype=torch.float,
    ).to(device)
    print(f"Class weights (0=legit, 1=scam): {class_weights.tolist()}")

    loss_fn = torch.nn.CrossEntropyLoss(weight=class_weights, label_smoothing=0.2)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
    total_steps = len(train_loader) * EPOCHS
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=int(0.1 * total_steps), num_training_steps=total_steps)

    best_f1 = -1.0
    for epoch in range(1, EPOCHS + 1):
        model.train()
        running_loss = 0.0
        for step, batch in enumerate(train_loader, 1):
            batch = {k: v.to(device) for k, v in batch.items()}
            optimizer.zero_grad()
            logits = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"]).logits
            loss = loss_fn(logits, batch["labels"])
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            running_loss += loss.item()
            if step % 50 == 0:
                print(f"  epoch {epoch} step {step}/{len(train_loader)} loss {running_loss / step:.4f}")

        acc, f1, labels, preds, probs = evaluate(model, val_loader)
        print(f"Epoch {epoch}: val_acc={acc:.4f} val_f1={f1:.4f}")

        if f1 > best_f1:
            best_f1 = f1
            os.makedirs(OUT_DIR, exist_ok=True)
            model.save_pretrained(OUT_DIR)
            tokenizer.save_pretrained(OUT_DIR)
            print(f"  -> saved new best checkpoint (f1={f1:.4f}) to {OUT_DIR}/")

    print("\nFinal validation report (best checkpoint):")
    best_model = BertForSequenceClassification.from_pretrained(OUT_DIR).to(device)
    acc, f1, labels, preds, probs = evaluate(best_model, val_loader)
    print(classification_report(labels, preds, target_names=["legit", "scam"]))

    probs_arr = np.array(probs)
    mid_band = ((probs_arr > 0.1) & (probs_arr < 0.9)).mean()
    print(f"Fraction of val predictions landing strictly between 10%-90% confidence: {mid_band:.3f}")
    print("(this should be well above 0 if the model is calibrated rather than bimodal)")

    if os.path.exists("test_set_50.csv"):
        held_out = pd.read_csv("test_set_50.csv")
        ds = ScamDataset(held_out["message"], held_out["expected_label"], tokenizer)
        loader = DataLoader(ds, batch_size=32)
        acc, f1, labels, preds, probs = evaluate(best_model, loader)
        print(f"\nHeld-out test_set_50.csv (never trained on): acc={acc:.4f} f1={f1:.4f}")
        print(classification_report(labels, preds, target_names=["legit", "scam"]))


if __name__ == "__main__":
    main()
