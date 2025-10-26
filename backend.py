import sqlite3
import os
import hashlib
import base64

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def _hash_password(password: str, salt: bytes = None, iterations: int = 150000) -> str:
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return f'{iterations}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}'

def _verify_password(password: str, stored: str) -> bool:
    try:
        iterations, salt_b64, dk_b64 = stored.split('$')
        iterations = int(iterations)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(dk_b64)
        dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
        return hashlib.compare_digest(dk, expected)
    except Exception:
        return False

def create_user(username: str, email: str, password: str) -> bool:
    pwd_hash = _hash_password(password)
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                    (username, email, pwd_hash))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def get_user_by_username(username: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT id, username, email, password_hash, created_at FROM users WHERE username = ?', (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        'id': row[0],
        'username': row[1],
        'email': row[2],
        'password_hash': row[3],
        'created_at': row[4]
    }

def authenticate_user(username: str, password: str):
    user = get_user_by_username(username)
    if not user:
        return False
    return _verify_password(password, user['password_hash'])
