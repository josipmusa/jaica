import json
import os

import requests
import torch
from transformers import AutoTokenizer


class CodeClassifier:
    def __init__(self, model_url, labels_url, model_name="code_classifier_traced.pt", backbone_model="microsoft/codebert-base"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model_path = os.path.join(os.path.dirname(__file__), model_name)
        label_path = os.path.join(os.path.dirname(__file__), "labels.json")

        #Download model if missing
        if model_url and not os.path.exists(model_path):
            print("Downloading code classifier model...")
            r = requests.get(model_url)
            with open (model_path, "wb") as f:
                f.write(r.content)
            print("Code classifier model download complete.")
        #Download labels if missing:
        if labels_url and not os.path.exists(label_path):
            print("Downloading labels...")
            r = requests.get(labels_url)
            with open (label_path, "wb") as f:
                f.write(r.content)
            print("Labels download complete.")

        self.model = torch.jit.load(model_path, map_location=self.device)
        self.model.eval()
        self.tokenizer = AutoTokenizer.from_pretrained(backbone_model)
        with open(label_path) as f:
            self.classes = json.load(f)

    #Predics the language of a full file, splitting trained-size chunks (128)
    def predict_file(self, file_content: str) -> str:
        lines = file_content.splitlines()

    def predict(self, code_snippet: str) -> str:
        encoded = self.tokenizer(
            code_snippet,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt"
        )
        input_ids = encoded["input_ids"].to(self.device)
        attention_mask = encoded["attention_mask"].to(self.device)

        with torch.no_grad():
            logits = self.model(input_ids, attention_mask)
            pred_idx = logits.argmax(dim=-1).item()

        return self.classes[pred_idx]