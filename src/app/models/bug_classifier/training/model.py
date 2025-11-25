import time

import torch
from matplotlib import pyplot as plt
from torch import nn, optim
from transformers import T5EncoderModel
from src.app.models.bug_classifier.training import config

#TODO would be nice to implement multi-labeling to this model
class BugClassifier(nn.Module):
    def __init__(self, num_labels=config.NUM_LABELS):
        super(BugClassifier, self).__init__()
        self.encoder = T5EncoderModel.from_pretrained(config.BACKBONE_MODEL_NAME)
        for name, param in self.encoder.named_parameters():
            if name.startswith("block.0") or name.startswith("block.1"):
                param.requires_grad = False
        self.dropout = nn.Dropout(0.1)
        hidden_size = self.encoder.config.d_model
        self.classifier = nn.Linear(hidden_size, num_labels)
        self.patience = 5

    def forward(self, input_ids, attention_mask):
        enc_output = self.encoder(input_ids=input_ids, attention_mask=attention_mask)

        # enc_output.last_hidden_state -> (batch, seq_len, 512)
        hidden = enc_output.last_hidden_state
        pooled = _mean_pooling(hidden, attention_mask)

        logits = self.classifier(self.dropout(pooled))
        return logits

    def fit(self, train_loader, val_loader, epochs=config.EPOCHS):
        optimizer = optim.AdamW((p for p in self.parameters() if p.requires_grad), lr=config.LEARNING_RATE, weight_decay=config.WEIGHT_DECAY)
        loss_fn = nn.CrossEntropyLoss()

        trigger_times = 0
        best_val_loss = float('inf')

        train_losses, val_losses = [], []
        start_time = time.time()
        for epoch in range(epochs):
            self.train()
            train_loss = 0
            for batch in train_loader:
                input_ids, attention_mask, labels = batch
                input_ids = input_ids.to(config.DEVICE)
                attention_mask = attention_mask.to(config.DEVICE)
                labels = labels.to(config.DEVICE)

                outputs = self(input_ids, attention_mask)
                loss = loss_fn(outputs, labels)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                train_loss += loss.item() * input_ids.size(0)

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

            train_loss = train_loss / len(train_loader.dataset)
            train_losses.append(train_loss)
            val_losses.append(val_loss)
            print(f"Epoch {epoch}, Train loss: {train_loss: .4f}, Val loss: {val_loss: .4f}")

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

                outputs = self(input_ids, attention_mask)
                loss = loss_fn(outputs, labels)

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

def _mean_pooling(hidden_state, attention_mask):
    # Expand mask to the same shape as embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(hidden_state.size())

    # Sum only unmasked embeddings
    sum_embeddings = torch.sum(hidden_state * input_mask_expanded, dim=1)

    # Divide by number of valid tokens
    sum_mask = input_mask_expanded.sum(dim=1)
    sum_mask = torch.clamp(sum_mask, min=1e-9)  # avoid division by zero

    return sum_embeddings / sum_mask