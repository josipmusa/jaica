from pathlib import Path
import torch

SCRIPT_DIR = Path(__file__).resolve().parent
LOSS_CURVE_PATH = SCRIPT_DIR / "loss_curve.png"
MODEL_PATH = SCRIPT_DIR / "model.pth"
BATCH_SIZE = 16
EPOCHS = 20
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
NUM_CLASSES = 6
MAX_TOKEN_LENGTH = 512
BACKBONE_MODEL_NAME = "microsoft/codebert-base"
OUTPUT_CSV = "dataset.csv"
LABELS = {0: "Python", 1: "Java", 2: "SQL", 3: "HTML", 4: "JavaScript", 5: "PHP"}

TARGET_SAMPLES = 2000
# Supported languages
LANGUAGES = {
    "python": {
        "extensions": [".py"],
        "repos": [
            "https://github.com/pallets/flask.git",
            "https://github.com/psf/requests.git",
            "https://github.com/pandas-dev/pandas.git"
        ]
    },
    "javascript": {
        "extensions": [".js", ".jsx", ".ts", ".tsx"],
        "repos": [
            "https://github.com/axios/axios.git",
            "https://github.com/facebook/react.git",
            "https://github.com/expressjs/express.git"
        ]
    },
    "java": {
        "extensions": [".java"],
        "repos": [
            "https://github.com/spring-projects/spring-framework.git",
            "https://github.com/google/guava.git"
        ]
    },
    "php": {
        "extensions": [".php"],
        "repos": [
            "https://github.com/laravel/laravel.git"
        ]
    }
}