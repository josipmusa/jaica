import time
import torch
from torch import nn
from matplotlib import pyplot as plt
from transformers import AutoModel
import config

class CodeClassifier(nn.Module):
    def __init__(self, num_classes=config.NUM_CLASSES):
        super(CodeClassifier, self).__init__()

        # Load BERT backbone
        self.bert = AutoModel.from_pretrained(
            config.BACKBONE_MODEL_NAME, dtype=torch.float32, use_safetensors=True
        )

        # Freeze all layers except last 2 and pooler
        trainable_keywords = ["encoder.layer.10", "encoder.layer.11", "pooler", "LayerNorm"]
        for name, param in self.bert.named_parameters():
            param.requires_grad = any(k in name for k in trainable_keywords)

        self.dropout = nn.Dropout(0.3)
        hidden_size = self.bert.config.hidden_size
        fc1_output_size = 256

        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, fc1_output_size),
            nn.ReLU(),
            nn.Linear(fc1_output_size, num_classes)
        )
        self.patience = 5

    def forward(self, input_ids, attention_mask):
        bert_outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        x = bert_outputs.pooler_output
        x = self.dropout(x)
        return self.classifier(x)

    def fit(self, train_loader, val_loader, epochs=20, accum_steps=2):
        loss_fn = nn.CrossEntropyLoss()
        optimizer = torch.optim.AdamW(filter(lambda p: p.requires_grad, self.parameters()), lr=2e-5)
        scaler = torch.cuda.amp.GradScaler()

        trigger_times = 0
        best_val_loss = float('inf')

        train_losses, val_losses = [], []
        start_time = time.time()

        for epoch in range(epochs):
            self.train()
            train_loss = 0
            optimizer.zero_grad()

            for step, batch in enumerate(train_loader):
                input_ids, attention_mask, labels = [b.to(config.DEVICE) for b in batch]

                with torch.cuda.amp.autocast():
                    logits = self(input_ids, attention_mask)
                    loss = loss_fn(logits, labels) / accum_steps

                scaler.scale(loss).backward()
                train_loss += loss.item() * accum_steps * input_ids.size(0)

                if (step + 1) % accum_steps == 0:
                    scaler.step(optimizer)
                    scaler.update()
                    optimizer.zero_grad()

            # Validation
            val_loss = self._compute_validation_loss(val_loader, loss_fn)
            train_losses.append(train_loss / len(train_loader.dataset))
            val_losses.append(val_loss)
            print(f"Epoch {epoch}, Train Loss: {train_losses[-1]:.4f}, Val Loss: {val_loss:.4f}")

            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                trigger_times = 0
                torch.save(self.state_dict(), config.MODEL_PATH)
            else:
                trigger_times += 1
                if trigger_times >= self.patience:
                    print(f"Early stopping at epoch {epoch}")
                    break

        self.load_state_dict(torch.load(config.MODEL_PATH, map_location=config.DEVICE))
        end_time = time.time()
        print(f"Training finished in {end_time - start_time:.2f} seconds")

        _plot_loss_curve(train_losses, val_losses)

    def _compute_validation_loss(self, val_loader, loss_fn):
        self.eval()
        val_loss = 0
        with torch.no_grad():
            for batch in val_loader:
                input_ids, attention_mask, labels = [b.to(config.DEVICE) for b in batch]
                logits = self(input_ids, attention_mask)
                loss = loss_fn(logits, labels)
                val_loss += loss.item() * input_ids.size(0)
        return val_loss / len(val_loader.dataset)

    def predict(self, input_ids, attention_mask):
        self.eval()
        input_ids, attention_mask = input_ids.to(config.DEVICE), attention_mask.to(config.DEVICE)
        with torch.no_grad():
            logits = self(input_ids, attention_mask)
            return logits.argmax(dim=-1).item()


def _plot_loss_curve(train_losses, val_losses):
    plt.figure(figsize=(8,5))
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
