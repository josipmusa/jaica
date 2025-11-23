import json
import os
import requests
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer


class CodeClassifier:
    def __init__(self, model_url, labels_url, model_name="code_classifier.onnx",
                 backbone_model="microsoft/codebert-base"):

        model_path = os.path.join(os.path.dirname(__file__), model_name)
        label_path = os.path.join(os.path.dirname(__file__), "labels.json")

        # Download ONNX model if missing
        if model_url and not os.path.exists(model_path):
            print("Downloading ONNX code classifier model...")
            r = requests.get(model_url)
            with open(model_path, "wb") as f:
                f.write(r.content)
            print("Download complete.")

        # Download labels if missing
        if labels_url and not os.path.exists(label_path):
            print("Downloading labels...")
            r = requests.get(labels_url)
            with open(label_path, "wb") as f:
                f.write(r.content)
            print("Download complete.")

        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        self.session = ort.InferenceSession(model_path, providers=providers)

        self.tokenizer = AutoTokenizer.from_pretrained(backbone_model)

        with open(label_path) as f:
            self.classes = json.load(f)

    def predict(self, code_snippet: str) -> str:
        encoded = self.tokenizer(
            code_snippet,
            padding="max_length",
            truncation=True,
            max_length=512,
            return_tensors="np"   # IMPORTANT: NumPy for ONNX
        )

        # ONNXRuntime requires int64 (int64 = numpy.int64)
        input_ids = encoded["input_ids"].astype("int64")
        attention_mask = encoded["attention_mask"].astype("int64")

        outputs = self.session.run(
            None,
            {
                "input_ids": input_ids,
                "attention_mask": attention_mask
            }
        )

        logits = outputs[0]
        pred_idx = int(np.argmax(logits, axis=-1)[0])

        return self.classes[pred_idx]
