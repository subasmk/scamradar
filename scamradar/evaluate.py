"""Train on synthetic data, measure on a held-out synthetic set, write metrics.json.

The held-out set uses message templates the model never saw in training.
These numbers describe synthetic data only, not real-world accuracy.
"""
import json
import os
import sys

from .classifier import TextClassifier
from .datagen import generate
from .scorer import Scorer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return round(p, 3), round(r, 3), round(2 * p * r / (p + r), 3) if p + r else 0.0


def evaluate(train_n=4000, test_n=1500, seed_train=11, seed_test=2026):
    train = generate(train_n, seed_train, "train")
    held = generate(test_n, seed_test, "heldout")
    model = TextClassifier().fit(train)
    sc = Scorer(model)
    out = {"data": "synthetic only", "train_messages": train_n, "heldout_messages": test_n,
           "heldout_note": "held-out messages use sentence templates never seen in training",
           "heldout_scam_share": round(sum(r["label"] for r in held) / test_n, 3)}
    def counts(pred):
        tp = sum(1 for r, p in zip(held, pred) if p and r["label"])
        fp = sum(1 for r, p in zip(held, pred) if p and not r["label"])
        fn = sum(1 for r, p in zip(held, pred) if not p and r["label"])
        tn = len(held) - tp - fp - fn
        return tp, fp, fn, tn
    results = [sc.score(r["text"], r["context"]) for r in held]
    variants = {
        "full_system_flagged": [x["tier"] != "ok" for x in results],
        "full_system_high_only": [x["tier"] == "high" for x in results],
        "text_model_only": [x["parts"]["model"] >= 0.5 for x in results],
        "rules_only": [x["parts"]["rules"] >= 0.4 for x in results],
    }
    out["variants"] = {}
    for name, pred in variants.items():
        tp, fp, fn, tn = counts(pred)
        p, r, f = prf(tp, fp, fn)
        out["variants"][name] = {"precision": p, "recall": r, "f1": f, "tp": tp, "fp": fp, "fn": fn, "tn": tn}
    fam = {}
    for row, x in zip(held, results):
        if row["label"]:
            d = fam.setdefault(row["family"], [0, 0])
            d[0] += 1
            d[1] += x["tier"] != "ok"
    out["scam_recall_by_family"] = {k: round(v[1] / v[0], 3) for k, v in sorted(fam.items())}
    return model, out


def main():
    os.makedirs(DATA, exist_ok=True)
    model, out = evaluate()
    model.save(os.path.join(DATA, "model.json"))
    with open(os.path.join(DATA, "metrics.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
