"""Intent classification on top of the TF-IDF model."""
import json
import os
from config import DATA_DIR, NLP_THRESHOLD
from .nlp_engine import TfidfIntentModel

INTENTS = ["greeting", "menu", "main_attractions", "coffee", "burger", "fries", "pizza", "price",
           "location", "timings", "order", "zomato", "swiggy", "toing", "recommendation",
           "enquiry", "feedback", "thanks", "goodbye", "fallback"]


class IntentClassifier:
    def __init__(self, path=None, threshold=NLP_THRESHOLD):
        path = path or os.path.join(DATA_DIR, "intents.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)["intents"]
        examples = [(label, t) for label, texts in data.items() for t in texts]
        self.model = TfidfIntentModel(examples)
        self.threshold = threshold

    def classify(self, text: str):
        """Returns (intent, confidence, top3). Below threshold -> 'fallback'."""
        ranking = self.model.rank(text)
        if not ranking:
            return "fallback", 0.0, []
        label, score = ranking[0]
        if score < self.threshold or label == "fallback":
            return "fallback", round(score, 3), ranking[:3]
        return label, round(score, 3), ranking[:3]
