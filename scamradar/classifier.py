"""Small text classifier: logistic regression on word uni+bigrams, pure Python."""
import json
import math
import random
import re

TOKEN = re.compile(r"[a-z]+|\d+")


def tokenize(text):
    t = text.lower()
    t = re.sub(r"https?://\S+|\b\S+\.(xyz|top|in|com|ly|net)\S*|\bbit\.ly\S*", " urltok ", t)
    t = re.sub(r"[a-z0-9._-]+@[a-z]+", " upitok ", t)
    t = re.sub(r"\b\d{9,}\b", " phonetok ", t)
    t = re.sub(r"\b\d{1,2}[,\d]*\b", " numtok ", t)
    words = TOKEN.findall(t)
    words = [w for w in words if w not in ("rs", "inr")]
    feats = set(words)
    feats.update(a + "_" + b for a, b in zip(words, words[1:]))
    return feats


class TextClassifier:
    def __init__(self):
        self.w = {}
        self.b = 0.0

    def _z(self, feats):
        return self.b + sum(self.w.get(f, 0.0) for f in feats)

    def predict_proba(self, text):
        z = self._z(tokenize(text))
        z = max(-30.0, min(30.0, z))
        return 1.0 / (1.0 + math.exp(-z))

    def top_features(self, text, k=4):
        feats = tokenize(text)
        ranked = sorted(((self.w.get(f, 0.0), f) for f in feats), reverse=True)
        return [f.replace("_", " ") for v, f in ranked[:k] if v > 0.3]

    def fit(self, rows, epochs=30, lr=0.15, l2=1e-4, min_df=2, seed=7):
        data = [(tokenize(r["text"]), r["label"]) for r in rows]
        df = {}
        for feats, _ in data:
            for f in feats:
                df[f] = df.get(f, 0) + 1
        vocab = {f for f, c in df.items() if c >= min_df}
        data = [([f for f in feats if f in vocab], y) for feats, y in data]
        self.w = {f: 0.0 for f in vocab}
        self.b = 0.0
        rng = random.Random(seed)
        for ep in range(epochs):
            rng.shuffle(data)
            step = lr / (1 + 0.1 * ep)
            for feats, y in data:
                z = self._z(feats)
                p = 1 / (1 + math.exp(-max(-30, min(30, z))))
                g = p - y
                for f in feats:
                    self.w[f] -= step * (g + l2 * self.w[f])
                self.b -= step * g
        return self

    def save(self, path):
        with open(path, "w") as fh:
            json.dump({"b": self.b, "w": {k: round(v, 4) for k, v in self.w.items() if abs(v) > 0.02}}, fh)

    @classmethod
    def load(cls, path):
        with open(path) as fh:
            d = json.load(fh)
        m = cls()
        m.b, m.w = d["b"], d["w"]
        return m
