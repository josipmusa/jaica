import json

import torch
from sklearn.preprocessing import LabelEncoder
from torch.utils.data import TensorDataset, random_split, DataLoader
from transformers import AutoTokenizer

import model.config as config
import pandas as pd

from src.app.models.bug_classifier.training.build_dataset import build_dataset_if_missing
from src.app.models.bug_classifier.training.model import BugClassifier


def _load_training_data(tokenizer):
    data = pd.read_csv(config.DATASET_PATH)
    x = data["code"]
    labels = data["label"].values

    label_encoder = LabelEncoder()
    labels_int = label_encoder.fit_transform(labels)
    with open("labels.json", "w") as f:
        json.dump(label_encoder.classes_.tolist(), f)

    encoded_inputs = tokenizer(x.tolist(),
                               padding=True,
                               truncation=True,
                               max_length=config.MAX_TOKEN_LENGTH,
                               return_tensors="pt")
    input_ids = encoded_inputs["input_ids"]
    attention_mask = encoded_inputs["attention_mask"]

    labels_tensor = torch.tensor(labels_int, dtype=torch.long)

    dataset = TensorDataset(input_ids, attention_mask, labels_tensor)
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(dataset=train_dataset, batch_size=16, shuffle=True)
    val_loader = DataLoader(dataset=val_dataset, batch_size=16, shuffle=False)
    return train_loader, val_loader

def train():
    tokenizer = AutoTokenizer.from_pretrained(config.BACKBONE_MODEL_NAME)
    build_dataset_if_missing()
    train_loader, val_loader = _load_training_data(tokenizer)

    model = BugClassifier(config.NUM_LABELS).to(config.DEVICE)
    model.fit(train_loader, val_loader, config.EPOCHS)

if __name__ == "__main__":
    train()