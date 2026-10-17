"""Lightweight NLP: text normalisation, entity extraction and a TF-IDF /
cosine-similarity intent model (scikit-learn). Runs fully offline."""
import re
import difflib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_PUNCT = re.compile(r"[^a-z0-9₹\s]")
_SPACE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Lower-case, strip punctuation and collapse whitespace."""
    text = (text or "").lower().replace("₹", " rs ")
    text = _PUNCT.sub(" ", text)
    return _SPACE.sub(" ", text).strip()


class TfidfIntentModel:
    """Two TF-IDF views (character n-grams for typo tolerance + word n-grams
    for semantics) are compared to every training example with cosine
    similarity. The score of an intent is its best-matching example."""

    def __init__(self, examples):
        self.labels = [label for label, _ in examples]
        self.texts = [normalize(t) for _, t in examples]
        self.char_vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True)
        self.word_vec = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), sublinear_tf=True)
        self.char_x = self.char_vec.fit_transform(self.texts)
        self.word_x = self.word_vec.fit_transform(self.texts)

    def rank(self, text: str):
        q = normalize(text)
        if not q:
            return []
        sims = 0.5 * cosine_similarity(self.char_vec.transform([q]), self.char_x)[0] \
            + 0.5 * cosine_similarity(self.word_vec.transform([q]), self.word_x)[0]
        best = {}
        for label, s in zip(self.labels, sims):
            if s > best.get(label, 0.0):
                best[label] = float(s)
        return sorted(best.items(), key=lambda kv: kv[1], reverse=True)


class EntityExtractor:
    """Finds menu items (and menu categories) mentioned in a message.
    Longest phrases are matched first and consumed, so "veg cheese burger" never also matches "burger"."""

    def __init__(self, items, category_keywords=None):
        self.phrases = []  # (phrase, kind, id)   kind = 'item' | 'cat'
        for it in items:
            for kw in it.get("keywords", []) + [it["name"]]:
                self.phrases.append((normalize(kw), "item", it["id"]))
        for cat, kws in (category_keywords or {}).items():
            for kw in kws:
                self.phrases.append((normalize(kw), "cat", cat))
        self.phrases.sort(key=lambda p: -len(p[0]))
        self.single = [(p, k, i) for p, k, i in self.phrases if " " not in p and len(p) >= 5]

    def find_entities(self, text: str):
        """Returns (item_ids, category_names) in order of appearance."""
        orig = " " + normalize(text) + " "
        q, hits = orig, []
        for phrase, kind, ident in self.phrases:
            token = f" {phrase} "
            pos = q.find(token)
            if pos >= 0:
                hits.append((orig.find(token), kind, ident))
                q = q.replace(token, " " + "_" * len(phrase) + " ")
        if not hits:  # typo tolerance, e.g. "burgur", "pizzza", "mojto"
            for tok in orig.split():
                if len(tok) < 4:
                    continue
                m = difflib.get_close_matches(tok, [p for p, _, _ in self.single], n=1, cutoff=0.8)
                if m:
                    _, kind, ident = next(x for x in self.single if x[0] == m[0])
                    hits.append((orig.find(tok), kind, ident))
        hits.sort(key=lambda h: h[0])
        items, cats = [], []
        for _, kind, ident in hits:
            tgt = items if kind == "item" else cats
            if ident not in tgt:
                tgt.append(ident)
        return items, cats

    def find_items(self, text: str):
        return self.find_entities(text)[0]


PRICE_WORDS = ("price", "prices", "cost", "how much", "rate", "rates", "rs", "rupees", "kitna", "charges")
ORDER_WORDS = ("order", "buy", "deliver", "delivery", "purchase", "takeaway", "book")
DETAIL_WORDS = ("detail", "details", "about", "describe", "tell me")


def has_any(text: str, words) -> bool:
    q = " " + normalize(text) + " "
    return any(f" {w} " in q for w in words)
