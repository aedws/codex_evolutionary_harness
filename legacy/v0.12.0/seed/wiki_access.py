"""Local account/session store for a read-only wiki adapter. No shared/default credentials."""
import hashlib
import hmac
import json
from pathlib import Path
import re
import secrets
import sqlite3
import time
from contextlib import closing


class Accounts:
    def __init__(self, path, roles, policy_digest, clock=time.time):
        self.path = Path(path).absolute()
        self.roles = set(roles); self.policy_digest = policy_digest; self.clock = clock

    def connect(self):
        for p in [self.path, *self.path.parents]:
            if p.exists() and (p.is_symlink() or getattr(p.lstat(), 'st_file_attributes', 0) & 0x400):
                raise ValueError('Reparse account store forbidden')
        if not self.path.is_file():
            raise ValueError('Accounts unconfigured')
        db = sqlite3.connect(self.path, timeout=5)
        if db.execute('PRAGMA user_version').fetchone()[0] != 1:
            db.close(); raise ValueError('Unsupported account store; preserve before migration')
        return db

    def provision(self, username, role, password):
        if role not in self.roles or not re.fullmatch(r'[a-z][a-z0-9_-]{0,31}', username) or not 16 <= len(password) <= 256:
            raise ValueError('Approved role, safe username and 16+ character password required')
        # Explicit one-time local provisioning. Never change an existing credential.
        for p in [self.path, *self.path.parents]:
            if p.exists() and (p.is_symlink() or getattr(p.lstat(), 'st_file_attributes', 0) & 0x400):
                raise ValueError('Reparse account store forbidden')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open('xb'):
            pass
        db = sqlite3.connect(self.path)
        try:
            db.executescript('''CREATE TABLE users(name TEXT PRIMARY KEY, role TEXT NOT NULL, salt BLOB NOT NULL, hash BLOB NOT NULL);
            CREATE TABLE sessions(token_hash TEXT PRIMARY KEY, username TEXT NOT NULL, expires REAL NOT NULL, policy TEXT NOT NULL);
            CREATE TABLE attempts(name TEXT PRIMARY KEY, failures INTEGER NOT NULL, blocked_until REAL NOT NULL);
            PRAGMA user_version=1;''')
            salt = secrets.token_bytes(16)
            hashed = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
            db.execute('INSERT INTO users VALUES(?,?,?,?)', (username, role, salt, hashed)); db.commit()
        finally:
            db.close()

    def login(self, username, password):
        if type(username) is not str or type(password) is not str or len(username) > 32 or len(password) > 256:
            return None
        now = self.clock()
        with closing(self.connect()) as db, db:
            db.execute('BEGIN IMMEDIATE')
            user = db.execute('SELECT role,salt,hash FROM users WHERE name=?', (username,)).fetchone()
            key = username if user else '<unknown>'
            attempts = db.execute('SELECT failures,blocked_until FROM attempts WHERE name=?', (key,)).fetchone()
            if attempts and attempts[1] > now:
                return None
            candidate = hashlib.scrypt(password.encode(), salt=user[1] if user else b'0'*16, n=16384, r=8, p=1)
            if not user or user[0] not in self.roles or not hmac.compare_digest(candidate, user[2]):
                # Bound unknown-user storage; all unknown names share one throttle key.
                key = username if user else '<unknown>'
                previous = db.execute('SELECT failures,blocked_until FROM attempts WHERE name=?', (key,)).fetchone()
                failures = (previous[0] if previous and previous[1] == 0 else 0) + 1
                db.execute('INSERT OR REPLACE INTO attempts VALUES(?,?,?)', (key, failures, now+900 if failures >= 5 else 0)); return None
            db.execute('DELETE FROM attempts WHERE name=?', (username,))
            token = secrets.token_urlsafe(32)
            db.execute('DELETE FROM sessions WHERE expires<=?', (now,))
            db.execute('INSERT INTO sessions VALUES(?,?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), username, now+8*3600, self.policy_digest))
            return token

    def role(self, token):
        if type(token) is not str or len(token) > 128:
            return None
        with closing(self.connect()) as db:
            row = db.execute('SELECT u.role,s.expires,s.policy FROM sessions s JOIN users u ON u.name=s.username WHERE token_hash=?', (hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
        if row and row[0] in self.roles and row[1] > self.clock() and row[2] == self.policy_digest:
            return row[0]
        return None

    def logout(self, token):
        with closing(self.connect()) as db, db:
            db.execute('DELETE FROM sessions WHERE token_hash=?', (hashlib.sha256(token.encode()).hexdigest(),))

    def add_account(self, username, role, password):
        if role not in self.roles or not re.fullmatch(r'[a-z][a-z0-9_-]{0,31}', username) or not 16 <= len(password) <= 256:
            raise ValueError('Approved role, username and strong password required')
        salt = secrets.token_bytes(16)
        hashed = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
        with closing(self.connect()) as db, db:
            db.execute('INSERT INTO users VALUES(?,?,?,?)', (username, role, salt, hashed))
