import time

import torch
from matplotlib import pyplot as plt
from torch import nn
from transformers import AutoModel
import config


class CodeClassifier(nn.Module):
    def __init__(self, num_classes=config.NUM_CLASSES):
        super(CodeClassifier, self).__init__()
        self.bert = AutoModel.from_pretrained(config.BACKBONE_MODEL_NAME, dtype=torch.float32, use_safetensors=True)

        # Freeze all layers except last 2 and pooler and layer normalization - improves accuracy
        trainable_keywords = ["encoder.layer.10", "encoder.layer.11", "pooler", "LayerNorm"]
        for name, param in self.bert.named_parameters():
            param.requires_grad = any(k in name for k in trainable_keywords)

        self.dropout = nn.Dropout(0.3)
        hidden_size = self.bert.config.hidden_size
        fc1_output_size = 256

        self.classifier = nn.Sequential(
            nn.Linear(in_features=hidden_size, out_features=fc1_output_size),
            nn.ReLU(),
            nn.Linear(in_features=fc1_output_size, out_features=num_classes))
        self.patience = 5

    def forward(self, input_ids, attention_mask):
        bert_outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        embedding_CLS = bert_outputs.pooler_output

        x = self.dropout(embedding_CLS)
        return self.classifier(x)

    def fit(self, train_loader, val_loader, epochs=20):
        loss_fn = nn.CrossEntropyLoss()
        # dont give optimizer frozen parameters
        optimizer = torch.optim.AdamW(filter(lambda p: p.requires_grad, self.parameters()), lr=2e-5)
        trigger_times = 0
        best_val_loss = float('inf')
        start_time = time.time()

        train_losses, val_losses = [], []
        for epoch in range(epochs):
            self.train()
            train_loss = 0
            for batch in train_loader:
                input_ids, attention_mask, labels = batch
                input_ids = input_ids.to(config.DEVICE)
                attention_mask = attention_mask.to(config.DEVICE)
                labels = labels.to(config.DEVICE)

                logits = self(input_ids, attention_mask)
                loss = loss_fn(logits, labels)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                train_loss += loss.item() * input_ids.size(0)

            #validation
            val_loss = self._compute_validation_loss(val_loader, loss_fn)
            if val_loss < best_val_loss:
                trigger_times = 0
                best_val_loss = val_loss
                torch.save(self.state_dict(), config.MODEL_PATH)
            else:
                trigger_times += 1
                if trigger_times >= self.patience:
                    print(f"Early stopping at epoch {epoch}")
                    break

            avg_train_loss = train_loss / len(train_loader.dataset)
            train_losses.append(avg_train_loss)
            val_losses.append(val_loss)
            print(f"Epoch {epoch}, Train loss: {avg_train_loss: .4f}, Val loss: {val_loss: .4f}")

        end_time = time.time()
        print(f"Model finished training in {(end_time - start_time): .4f} seconds")
        self.load_state_dict(torch.load(config.MODEL_PATH, map_location=config.DEVICE))
        _plot_loss_curve(train_losses, val_losses)

    def predict(self, input_ids, attention_mask):
        input_ids = input_ids.to(config.DEVICE)
        attention_mask = attention_mask.to(config.DEVICE)

        self.eval()
        with torch.no_grad():
            logits = self(input_ids, attention_mask)
            prediction = logits.argmax(dim=-1)

        return prediction.item()

    def _compute_validation_loss(self, val_loader, loss_fn):
        val_loss = 0
        self.eval()
        with torch.no_grad():
            for batch in val_loader:
                input_ids, attention_mask, labels = batch
                input_ids = input_ids.to(config.DEVICE)
                attention_mask = attention_mask.to(config.DEVICE)
                labels = labels.to(config.DEVICE)

                logits = self(input_ids, attention_mask)
                loss = loss_fn(logits, labels)

                val_loss += loss.item() * input_ids.size(0)

        val_loss = val_loss / len(val_loader.dataset)
        return val_loss



def _plot_loss_curve(train_losses, val_losses):
    plt.figure(figsize=(8, 5))
    plt.plot(train_losses, label="train_loss")
    plt.plot(val_losses, label="val_loss")
    plt.title("Loss Curve")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(config.LOSS_CURVE_PATH)
    plt.close()
    print(f"Saved loss curve to {config.LOSS_CURVE_PATH}")