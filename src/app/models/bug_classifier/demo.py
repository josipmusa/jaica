from src.app.models.bug_classifier.bug_classifier import BugClassifier
from src.app.configuration import config

model = BugClassifier(config.BUG_CLASSIFIER_MODEL_URL, config.BUG_CLASSIFIER_LABEL_URL)
example = """public int sumArray(int[] arr) {
    int total = 0;
    // Off-by-one error: should be i < arr.length, not i < arr.length - 1
    for (int i = 0; i < arr.length - 1; i++) {
        total += arr[i];
    }
    return total;
}"""
print("Predicted label: ", model.predict(example))