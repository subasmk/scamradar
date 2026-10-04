"""Tiny dependency-free web server and JSON API. Run: python -m scamradar"""
import json
import os
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .classifier import TextClassifier
from .datagen import SCAM, LEGIT, generate
from .evaluate import DATA, ROOT, evaluate
from .scorer import Scorer
from .store import DAILY_CAP, Store

WEB = os.path.join(ROOT, "web")


def load_model():
    path = os.path.join(DATA, "model.json")
    if not os.path.exists(path):
        os.makedirs(DATA, exist_ok=True)
        model, out = evaluate()
        model.save(path)
        with open(os.path.join(DATA, "metrics.json"), "w") as fh:
            json.dump(out, fh, indent=2)
    return TextClassifier.load(path)


def samples():
    """A few ready-made messages for the demo (fixed, hand-picked)."""
    return [
        {"name": "Fake refund", "text": "Your Swiggy refund of Rs 499 is ready. Approve the collect request from meera42@ybl and enter your UPI PIN to receive it.",
         "context": {"kind": "collect", "sender_known": False, "payee_new": True, "amount": 499, "typical_amount": 600, "hour": 14, "account_age_days": 20}},
        {"name": "KYC link", "text": "Dear customer your SBI account will be blocked in 6 hours. Complete KYC now: bit.ly/k9x2ab",
         "context": {"kind": "info", "sender_known": False, "payee_new": False, "amount": 0, "typical_amount": 600, "hour": 3, "account_age_days": 400}},
        {"name": "Prize fee", "text": "Congratulations! You won Rs 49,999 in the lucky draw. Pay Rs 99 processing fee to ravi31@okaxis to claim your prize.",
         "context": {"kind": "pay", "sender_known": False, "payee_new": True, "amount": 99, "typical_amount": 600, "hour": 21, "account_age_days": 400}},
        {"name": "Bank debit (real)", "text": "Rs 250 debited from A/c XX4821 to swiggy@icici on UPI Ref 482913. If not you, call your bank helpline. - HDFC",
         "context": {"kind": "info", "sender_known": True, "payee_new": False, "amount": 250, "typical_amount": 600, "hour": 13, "account_age_days": 900}},
        {"name": "Friend asks for money", "text": "Hey it's Kavya, can you send me Rs 480 for dinner yesterday? I'll pay you back on Friday.",
         "context": {"kind": "collect", "sender_known": True, "payee_new": False, "amount": 480, "typical_amount": 600, "hour": 20, "account_age_days": 900}},
        {"name": "Genuine refund", "text": "Refund of Rs 799 for order #482911 has been credited to your account. It may take 2 days to show.",
         "context": {"kind": "info", "sender_known": True, "payee_new": False, "amount": 799, "typical_amount": 600, "hour": 11, "account_age_days": 900}},
    ]


class App:
    def __init__(self, db_path):
        self.model = load_model()
        self.scorer = Scorer(self.model)
        self.store = Store(db_path)

    def analyze(self, body):
        text = str(body.get("text", "")).strip()
        if not text:
            raise ValueError("text is required")
        ctx = body.get("context") or {}
        result = self.scorer.score(text, ctx)
        rec = self.store.record(text, ctx, result, body.get("timestamp"))
        # No auto-block anywhere: the result only advises. The user always decides.
        result.update(rec)
        result["auto_blocked"] = False
        return result


def make_handler(app):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, obj, ctype="application/json"):
            data = obj if isinstance(obj, bytes) else json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _body(self):
            n = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(n) or b"{}")

        def do_GET(self):
            p = urlparse(self.path).path
            try:
                if p in ("/", "/index.html"):
                    with open(os.path.join(WEB, "index.html"), "rb") as fh:
                        return self._send(200, fh.read(), "text/html; charset=utf-8")
                if p == "/api/samples":
                    return self._send(200, samples())
                if p == "/api/alerts":
                    day = datetime.now().strftime("%Y-%m-%d")
                    return self._send(200, {"cap": DAILY_CAP, "used_today": app.store.used_today(day), "alerts": app.store.alerts()})
                if p == "/api/review":
                    return self._send(200, {"pending": app.store.queue(), "all": app.store.queue(False)})
                if p == "/api/audit":
                    return self._send(200, {"chain_ok": app.store.verify_chain(), "entries": app.store.audit()})
                if p == "/api/metrics":
                    with open(os.path.join(DATA, "metrics.json")) as fh:
                        return self._send(200, json.load(fh))
                if p == "/api/health":
                    return self._send(200, {"ok": True})
                self._send(404, {"error": "not found"})
            except Exception as e:  # keep the demo alive
                self._send(500, {"error": str(e)})

        def do_POST(self):
            p = urlparse(self.path).path
            try:
                b = self._body()
                if p == "/api/analyze":
                    return self._send(200, app.analyze(b))
                if p == "/api/review":
                    app.store.decide(int(b["id"]), b["decision"], b.get("note", ""))
                    return self._send(200, {"ok": True})
                if p == "/api/user-action":
                    app.store.user_action(int(b["event_id"]), b["action"])
                    return self._send(200, {"ok": True})
                self._send(404, {"error": "not found"})
            except (ValueError, KeyError) as e:
                self._send(400, {"error": str(e)})
            except Exception as e:
                self._send(500, {"error": str(e)})
    return H


def main(argv=None):
    port = int(os.environ.get("PORT", "8000"))
    db = os.environ.get("SCAMRADAR_DB", os.path.join(DATA, "scamradar.db"))
    os.makedirs(os.path.dirname(db), exist_ok=True)
    app = App(db)
    srv = ThreadingHTTPServer(("127.0.0.1", port), make_handler(app))
    print(f"ScamRadar running at http://127.0.0.1:{port}  (synthetic data only)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
