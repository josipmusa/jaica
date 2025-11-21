import torch
from model import CodeClassifier
import config

model = CodeClassifier().to(config.DEVICE)
model.load_state_dict(torch.load(config.MODEL_PATH, map_location=config.DEVICE))
model.eval()

# Dummy input for tracing
dummy_input_ids = torch.randint(0, 1000, (1, 128)).to(config.DEVICE)
dummy_attention_mask = torch.ones((1, 128), dtype=torch.long).to(config.DEVICE)

traced_model = torch.jit.trace(model, (dummy_input_ids, dummy_attention_mask))
traced_model.save("code_classifier_traced.pt")
print("Model exported as TorchScript!")
