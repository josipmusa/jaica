from src.app.configuration import config
from src.app.configuration.db import VectorDB
from src.app.models.code_classifier.code_classifier import CodeClassifier
from src.app.models.bug_classifier.bug_classifier import BugClassifier
from src.app.services.code_analysis_service import CodeAnalyzer
from src.app.services.rag_service import RagService

code_classifier_instance = CodeClassifier(config.CODE_CLASSIFIER_MODEL_URL, config.CODE_CLASSIFIER_LABEL_URL)
bug_classifier_instance = BugClassifier(config.BUG_CLASSIFIER_MODEL_URL, config.BUG_CLASSIFIER_LABEL_URL)
db_instance = VectorDB(persist_dir=str(config.VECTORSTORE_PATH))
rag_service_instance = RagService(db=db_instance)
code_analyzer_instance = CodeAnalyzer(bug_classifier=bug_classifier_instance, code_classifier=code_classifier_instance)


def get_code_classifier() -> CodeClassifier:
    return code_classifier_instance

def get_bug_classifier() -> BugClassifier:
    return bug_classifier_instance

def get_db() -> VectorDB:
    return db_instance

def get_rag_service() -> RagService:
    return rag_service_instance

def get_code_analyzer() -> CodeAnalyzer:
    return code_analyzer_instance