from pathlib import Path

import torch

BACKBONE_MODEL_NAME = "Salesforce/codet5-small"
NUM_LABELS = 5
LABEL_MAP = {
    0: "CLEAN",
    1: "NULL_POINTER",
    2: "OFF_BY_ONE",
    3: "INCORRECT_RETURN",
    4: "LOGIC_ERROR"
}
EPOCHS = 20
LEARNING_RATE = 1e-4
WEIGHT_DECAY=0.01
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
SCRIPT_DIR = Path(__file__).resolve().parent
LOSS_CURVE_PATH = SCRIPT_DIR / "loss_curve.png"
MODEL_PATH = SCRIPT_DIR / "model.pth"
DATASET_PATH = SCRIPT_DIR / "data/dataset.csv"
BATCH_SIZE = 16
MAX_TOKEN_LENGTH = 512
