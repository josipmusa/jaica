import torch
from model import CodeClassifier
import config

model = CodeClassifier().to(config.DEVICE)
model.load_state_dict(torch.load(config.MODEL_PATH, map_location=config.DEVICE))
model.eval()

dummy_input_ids = torch.randint(0, 1000, (1, config.MAX_TOKEN_LENGTH)).to(config.DEVICE)
dummy_attention_mask = torch.ones((1, config.MAX_TOKEN_LENGTH), dtype=torch.long).to(config.DEVICE)

torch.onnx.export(
    model,
    (dummy_input_ids, dummy_attention_mask),
    "code_classifier.onnx",
    input_names=["input_ids", "attention_mask"],
    output_names=["logits"],
    dynamic_axes={
        "input_ids": {0: "batch"},
        "attention_mask": {0: "batch"},
        "logits": {0: "batch"}
    },
    opset_version=17
)

print("ONNX export complete!")
