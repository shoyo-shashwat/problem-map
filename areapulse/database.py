import sqlite3
import time


def get_db():
    db = sqlite3.connect('areapulse.db')
    db.row_factory = sqlite3.Row
    return db


def init_db():
    db = get_db()

    db.execute('''CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area TEXT,
        description TEXT,
        tag TEXT,
        timestamp REAL,
        upvotes INTEGER DEFAULT 0,
        priority REAL DEFAULT 0.0,
        verified INTEGER DEFAULT 0,
        status TEXT DEFAULT 'open',
        user TEXT
    )''')

    db.execute('''CREATE TABLE IF NOT EXISTS users (
        name TEXT PRIMARY KEY,
        points INTEGER DEFAULT 0
    )''')

    db.commit()
    db.close()


def insert_issue(area, description, tag, user):
    db = get_db()
    ts = time.time()
    db.execute(
        "INSERT INTO issues (area, description, tag, timestamp, user, status) VALUES (?, ?, ?, ?, ?, 'open')",
        (area, description, tag, ts, user)
    )
    db.commit()
    db.close()


def get_issues():
    db = get_db()
    rows = db.execute('SELECT * FROM issues ORDER BY priority DESC, timestamp DESC').fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_summary():
    db = get_db()
    rows = db.execute('SELECT area, COUNT(*) FROM issues GROUP BY area').fetchall()
    db.close()
    result = []
    for area, count in rows:
        heat = 'low'
        if count >= 8:
            heat = 'high'
        elif count >= 4:
            heat = 'medium'
        result.append({'area': area, 'count': count, 'heat': heat})
    return result


def upvote_issue(issue_id):
    db = get_db()
    db.execute('UPDATE issues SET upvotes = upvotes + 1 WHERE id=?', (issue_id,))
    row = db.execute('SELECT upvotes, timestamp FROM issues WHERE id=?', (issue_id,)).fetchone()
    if row:
        age = max((time.time() - row['timestamp']) / 3600, 1)
        priority = round(row['upvotes'] / age, 2)
        db.execute('UPDATE issues SET priority=? WHERE id=?', (priority, issue_id))
    db.commit()
    db.close()


def verify_issue(issue_id):
    db = get_db()
    db.execute(
        "UPDATE issues SET verified = verified + 1, status='verified' WHERE id=?",
        (issue_id,)
    )
    db.commit()
    db.close()


def resolve_issue(issue_id):
    db = get_db()
    db.execute("UPDATE issues SET status='resolved' WHERE id=?", (issue_id,))
    db.commit()
    db.close()


def add_points(user, pts):
    if not user or user.strip() == '':
        return
    db = get_db()
    row = db.execute('SELECT points FROM users WHERE name=?', (user,)).fetchone()
    if row:
        db.execute('UPDATE users SET points = points + ? WHERE name=?', (pts, user))
    else:
        db.execute('INSERT INTO users (name, points) VALUES (?, ?)', (user, pts))
    db.commit()
    db.close()