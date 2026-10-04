"""SQLite storage: alerts (with a daily cap), human review queue, hash-chained audit trail."""
import hashlib
import json
import sqlite3
import threading
from datetime import datetime

DAILY_CAP = 3


class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, ts TEXT, day TEXT, text TEXT, ctx TEXT,
            score REAL, tier TEXT, reasons TEXT, shown INTEGER, status TEXT);
        CREATE TABLE IF NOT EXISTS review(id INTEGER PRIMARY KEY, event_id INTEGER, why TEXT, decision TEXT, note TEXT, decided_ts TEXT);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, ts TEXT, event_id INTEGER, action TEXT, detail TEXT, prev TEXT, hash TEXT);
        """)

    def _audit(self, event_id, action, detail):
        prev = self.db.execute("SELECT hash FROM audit ORDER BY id DESC LIMIT 1").fetchone()
        prev = prev["hash"] if prev else "genesis"
        ts = datetime.now().isoformat(timespec="seconds")
        body = json.dumps(detail, sort_keys=True)
        h = hashlib.sha256(f"{prev}|{ts}|{event_id}|{action}|{body}".encode()).hexdigest()
        self.db.execute("INSERT INTO audit(ts,event_id,action,detail,prev,hash) VALUES(?,?,?,?,?,?)",
                        (ts, event_id, action, body, prev, h))

    def record(self, text, ctx, result, ts=None):
        """Store a scored event. Applies the daily alert cap. Never blocks anything."""
        ts = ts or datetime.now().isoformat(timespec="seconds")
        day = ts[:10]
        with self.lock:
            used = self.db.execute("SELECT COUNT(*) c FROM events WHERE day=? AND shown=1", (day,)).fetchone()["c"]
            tier = result["tier"]
            shown, status, why = 0, "no_alert", None
            if tier != "ok":
                if used < DAILY_CAP:
                    shown, status = 1, "alert_shown"
                else:
                    status = "capped"
                    why = "Daily alert cap reached, kept out of the user's face"
                if tier == "high" or status == "capped":
                    why = why or "High risk, a human should double check"
            cur = self.db.execute(
                "INSERT INTO events(ts,day,text,ctx,score,tier,reasons,shown,status) VALUES(?,?,?,?,?,?,?,?,?)",
                (ts, day, text, json.dumps(ctx), result["score"], tier, json.dumps(result["reasons"]), shown, status))
            eid = cur.lastrowid
            self._audit(eid, "scored", {"tier": tier, "score": result["score"], "parts": result["parts"], "status": status})
            if why:
                self.db.execute("INSERT INTO review(event_id,why) VALUES(?,?)", (eid, why))
                self._audit(eid, "queued_for_review", {"why": why})
            self.db.commit()
            return {"event_id": eid, "alert_shown": bool(shown), "status": status,
                    "alerts_used_today": used + shown, "daily_cap": DAILY_CAP, "queued_for_review": bool(why)}

    def alerts(self, day=None):
        q = "SELECT * FROM events WHERE shown=1 " + ("AND day=? " if day else "") + "ORDER BY id DESC LIMIT 50"
        return [dict(r) for r in self.db.execute(q, (day,) if day else ())]

    def used_today(self, day):
        return self.db.execute("SELECT COUNT(*) c FROM events WHERE day=? AND shown=1", (day,)).fetchone()["c"]

    def queue(self, pending_only=True):
        q = """SELECT r.id rid, r.why, r.decision, r.note, e.* FROM review r JOIN events e ON e.id=r.event_id
               {} ORDER BY r.id DESC LIMIT 100""".format("WHERE r.decision IS NULL" if pending_only else "")
        return [dict(r) for r in self.db.execute(q)]

    def decide(self, rid, decision, note=""):
        if decision not in ("scam", "safe"):
            raise ValueError("decision must be 'scam' or 'safe'")
        with self.lock:
            row = self.db.execute("SELECT event_id FROM review WHERE id=?", (rid,)).fetchone()
            if not row:
                raise KeyError(rid)
            self.db.execute("UPDATE review SET decision=?, note=?, decided_ts=? WHERE id=?",
                            (decision, note, datetime.now().isoformat(timespec="seconds"), rid))
            self._audit(row["event_id"], "human_decision", {"decision": decision, "note": note})
            self.db.commit()

    def user_action(self, event_id, action):
        """The user's own choice (ignored / continued / reported). Logged, never enforced."""
        with self.lock:
            self._audit(event_id, "user_" + action, {})
            self.db.commit()

    def audit(self, limit=100):
        return [dict(r) for r in self.db.execute("SELECT * FROM audit ORDER BY id DESC LIMIT ?", (limit,))]

    def verify_chain(self):
        prev = "genesis"
        for r in self.db.execute("SELECT * FROM audit ORDER BY id"):
            h = hashlib.sha256(f"{prev}|{r['ts']}|{r['event_id']}|{r['action']}|{r['detail']}".encode()).hexdigest()
            if r["prev"] != prev or r["hash"] != h:
                return False
            prev = r["hash"]
        return True
