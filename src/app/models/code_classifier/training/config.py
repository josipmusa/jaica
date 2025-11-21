from pathlib import Path
import torch

SCRIPT_DIR = Path(__file__).resolve().parent
LOSS_CURVE_PATH = SCRIPT_DIR / "loss_curve.png"
MODEL_PATH = SCRIPT_DIR / "model.pth"
BATCH_SIZE = 16
EPOCHS = 20
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
NUM_CLASSES = 6
BACKBONE_MODEL_NAME = "microsoft/codebert-base"
LABELS = {0: "Python", 1: "Java", 2: "SQL", 3: "HTML", 4: "JavaScript", 5: "PHP"}