#!/usr/bin/env python3
"""Maintenance queue schema + core primitives for the Atlas brand-hygiene lane.

Idle-gated, propose-only, resumable background maintenance. One row = one small
idempotent file-decision. Worker claims a row (lease), acts, verifies, then marks
staged -> (approved externally) -> archived. Never deletes anything itself.
"""
import json, os, sqlite3, time, hashlib, uuid
from dataclasses import dataclass, field, asdict

QUEUE_DIR = os.path.expanduser("~/.openclaw/workspace/SYSTEM/maintenance-queue")
DB_PATH = os.path.join(QUEUE_DIR, "queue.sqlite")
AUDIT_PATH = os.path.join(QUEUE_DIR, "audit.jsonl")

# Row lifecycle. Reserved = intent lease (never evidence). staged = verbed artifact
# exists + verified. approved = human signed off. archived = moved + verified.
STATES = {"pending", "reserved", "staged", "approved", "archived", "rejected", "dead"}
# ordered for progression sanity
_ORDER = ["pending", "reserved", "staged", "approved", "archived"]


def _conn():
    os.makedirs(QUEUE_DIR, exist_ok=True)
    c = sqlite3.connect(DB_PATH, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")   # WAL: crash-safe, concurrent readers
    c.execute("PRAGMA busy_timeout=5000")
    return c


def init_db():
    c = _conn()
    c.execute("""CREATE TABLE IF NOT EXISTS rows (
        id TEXT PRIMARY KEY,
        lane TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        path TEXT NOT NULL,
        canonical_path TEXT,
        file_type TEXT,
        file_size INTEGER,
        sha256 TEXT,
        mtime REAL,
        birth_time REAL,
        kind TEXT,               -- plan/spec|built-artifact|superseded|working-doc|media|reference|unknown
        status_probe TEXT,       -- active|paused|complete|shipped|superseded|dup|cache|generated|unknown
        dependency TEXT,         -- 'load-bearing' | 'none' | 'unknown'
        confidence REAL,
        evidence TEXT,           -- structured JSON text
        proposed_action TEXT,    -- archive|consolidate|flag|leave|unknown
        lease_owner TEXT,
        lease_expires REAL,
        retries INTEGER DEFAULT 0,
        created_at REAL,
        updated_at REAL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS transitions (
        row_id TEXT, from_state TEXT, to_state TEXT, at REAL, owner TEXT, note TEXT
    )""")
    c.commit()
    c.close()


def _audit(owner, note):
    os.makedirs(QUEUE_DIR, exist_ok=True)
    with open(AUDIT_PATH, "a") as f:
        f.write(json.dumps({"at": time.time(), "owner": owner, "note": note}) + "\n")


def add_row(lane, path):
    """Add a new candidate row. Idempotent on canonical path."""
    c = _conn()
    cp = os.path.normpath(path)
    cur = c.execute("SELECT id,status FROM rows WHERE canonical_path=?", (cp,))
    if cur.fetchone():
        c.close(); return None
    rid = uuid.uuid4().hex[:12]
    st = os.stat(cp)
    # sha256 only for small files (default below); big media recorded separately
    sha = None
    if st.st_size < 5_000_000:
        try:
            sha = hashlib.sha256(open(cp,'rb').read()).hexdigest()
        except Exception:
            sha = None
    c.execute("""INSERT INTO rows (id,lane,status,path,canonical_path,file_type,file_size,
                 sha256,mtime,birth_time,created_at,updated_at)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
              (rid, lane, "pending", cp, cp, os.path.splitext(cp)[1].lower(),
               st.st_size, sha, st.st_mtime,
               getattr(st, 'st_birthtime', st.st_mtime),
               time.time(), time.time()))
    c.commit(); c.close()
    return rid


def claim_next(owner, lane="maintenance"):
    """Atomically reserve the oldest pending row (lease). Returns row or None.
    Sets status pending->reserved with lease_owner/expires. Expires stale leases."""
    c = _conn()
    now = time.time()
    # expire abandoned leases
    c.execute("""UPDATE rows SET status='pending', lease_owner=NULL, lease_expires=NULL,
                 retries=retries+1
                 WHERE status='reserved' AND lease_expires < ?""", (now,))
    c.execute("""SELECT * FROM rows WHERE status='pending' AND lane=?
                 ORDER BY created_at LIMIT 1""", (lane,))
    r = c.fetchone()
    if not r:
        c.close()
        return None
    rid = r["id"]
    c.execute("""UPDATE rows SET status='reserved', lease_owner=?, lease_expires=?
                 WHERE id=?""", (owner, now+300, rid))
    _transition(c, rid, "pending", "reserved", owner)
    c.commit(); c.close()
    return dict(r)


def transition(row_id, to_state, owner="worker", note=""):
    c = _conn()
    _transition(c, row_id, None, to_state, owner, note)
    c.execute("UPDATE rows SET status=?, updated_at=? WHERE id=?",
              (to_state, time.time(), row_id))
    c.commit(); c.close()


def _transition(c, row_id, frm, to, owner, note=""):
    from_state = frm if frm else (c.execute("SELECT status FROM rows WHERE id=?", (row_id,)).fetchone() or ["?"])[0]
    c.execute("INSERT INTO transitions (row_id,from_state,to_state,at,owner,note) VALUES (?,?,?,?,?,?)",
              (row_id, from_state, to, time.time(), owner, note))
    _audit(owner, f"{row_id}:{from_state}->{to} {note}")


if __name__ == "__main__":
    init_db()
    print("queue initialized:", DB_PATH)