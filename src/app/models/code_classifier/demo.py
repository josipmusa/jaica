from src.app.models.code_classifier.code_classifier import CodeClassifier

model_url = "https://huggingface.co/josipmusa/code-classifier/resolve/main/code_classifier.onnx"
label_url = "https://huggingface.co/josipmusa/code-classifier/resolve/main/labels.json"
clf = CodeClassifier(model_url, label_url)
example = "private final MyService myService;"
print("Predicted language: ", clf.predict(example))