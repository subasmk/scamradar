import os
import tempfile
import unittest

from scamradar.classifier import TextClassifier
from scamradar.datagen import generate
from scamradar.scorer import Scorer
from scamradar.server import App, samples
from scamradar.store import DAILY_CAP, Store

SCAM = samples()[0]
REAL = samples()[3]


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = TextClassifier().fit(generate(1500, 1, "train"))

    def test_scam_flagged_real_not(self):
        sc = Scorer(self.model)
        self.assertEqual(sc.score(SCAM["text"], SCAM["context"])["tier"], "high")
        self.assertEqual(sc.score(REAL["text"], REAL["context"])["tier"], "ok")

    def test_reasons_are_plain_language(self):
        r = Scorer(self.model).score(SCAM["text"], SCAM["context"])
        self.assertTrue(r["reasons"])
        self.assertTrue(any("PIN" in x for x in r["reasons"]))

    def test_daily_cap_and_review_queue(self):
        d = tempfile.mkdtemp()
        st = Store(os.path.join(d, "t.db"))
        sc = Scorer(self.model)
        res = sc.score(SCAM["text"], SCAM["context"])
        outs = [st.record(SCAM["text"], SCAM["context"], res, "2026-10-04T10:00:00") for _ in range(5)]
        self.assertEqual(sum(o["alert_shown"] for o in outs), DAILY_CAP)
        self.assertTrue(all(o["queued_for_review"] for o in outs))  # high risk always gets a human look
        self.assertEqual(len(st.queue()), 5)
        # a new day resets the cap
        o = st.record(SCAM["text"], SCAM["context"], res, "2026-10-05T10:00:00")
        self.assertTrue(o["alert_shown"])

    def test_no_auto_block(self):
        d = tempfile.mkdtemp()
        app = App(os.path.join(d, "t.db"))
        out = app.analyze({"text": SCAM["text"], "context": SCAM["context"]})
        self.assertFalse(out["auto_blocked"])

    def test_audit_chain_detects_tampering(self):
        d = tempfile.mkdtemp()
        st = Store(os.path.join(d, "t.db"))
        res = Scorer(self.model).score(SCAM["text"], SCAM["context"])
        st.record(SCAM["text"], SCAM["context"], res)
        st.decide(1, "scam", "confirmed")
        self.assertTrue(st.verify_chain())
        st.db.execute("UPDATE audit SET detail='{}' WHERE id=1")
        self.assertFalse(st.verify_chain())

    def test_review_decision_validated(self):
        d = tempfile.mkdtemp()
        st = Store(os.path.join(d, "t.db"))
        with self.assertRaises(ValueError):
            st.decide(1, "maybe")


if __name__ == "__main__":
    unittest.main()
