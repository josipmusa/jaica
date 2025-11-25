from src.app.models.code_classifier.code_classifier import CodeClassifier
from src.app.configuration import config

clf = CodeClassifier(config.CODE_CLASSIFIER_MODEL_URL, config.CODE_CLASSIFIER_LABEL_URL)
example = "private final MyService myService;"
print("Predicted language: ", clf.predict(example))