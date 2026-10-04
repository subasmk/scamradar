"""Combines rules, text model and behaviour into one score and a tier."""
from .behaviour import score_behaviour
from .classifier import TextClassifier
from .rules import score_rules

W_RULES, W_MODEL, W_BEHAVE = 0.40, 0.45, 0.15
T_HIGH, T_CAUTION = 0.60, 0.35

TIER_COPY = {
    "high": ("Likely scam", "Stop. Do not approve, enter a PIN, or share a code. If you are unsure, call your bank on the number on your card."),
    "caution": ("Be careful", "Something looks off. Check with the sender in another way before you pay or reply."),
    "ok": ("Looks fine", "Nothing suspicious found."),
}


class Scorer:
    def __init__(self, model: TextClassifier):
        self.model = model

    def score(self, text, ctx=None):
        ctx = ctx or {}
        r, hits, safe = score_rules(text)
        m = self.model.predict_proba(text)
        b, b_why = score_behaviour(ctx)
        final = W_RULES * r + W_MODEL * m + W_BEHAVE * b
        if r >= 0.7 and m >= 0.5:  # two independent detectors agree strongly
            final = max(final, 0.75)
        tier = "high" if final >= T_HIGH else "caution" if final >= T_CAUTION else "ok"
        reasons = [h["reason"] for h in sorted(hits, key=lambda h: -h["weight"])][:3]
        if tier != "ok":
            for w in b_why[:2]:
                if len(reasons) < 4:
                    reasons.append(w)
        if tier != "ok" and not reasons:
            reasons.append("The wording is close to scams that were reported before.")
        title, advice = TIER_COPY[tier]
        return {
            "score": round(final, 3), "tier": tier, "title": title, "advice": advice, "reasons": reasons,
            "parts": {"rules": round(r, 3), "model": round(m, 3), "behaviour": round(b, 3)},
            "safe_signals": safe,
            "model_words": self.model.top_features(text) if tier != "ok" else [],
        }
