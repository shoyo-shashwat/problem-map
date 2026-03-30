import sqlite3, time

def get_db():
    return sqlite3.connect('areapulse.db')

def init_db():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area TEXT, description TEXT, tag TEXT,
        timestamp REAL, upvotes INTEGER DEFAULT 0,
        priority REAL DEFAULT 0.0
    )''')
    db.commit(); db.close()

def insert_issue(area, description, tag):
    db = get_db()
    ts = time.time()
    db.execute('INSERT INTO issues (area,description,tag,timestamp) VALUES (?,?,?,?)',
               (area, description, tag, ts))
    db.commit(); db.close()

def get_issues(tag='All', area=None):
    db = get_db()
    if tag != 'All' and area:
        rows = db.execute('SELECT * FROM issues WHERE tag=? AND area=? ORDER BY priority DESC',
                          (tag, area)).fetchall()
    elif tag != 'All':
        rows = db.execute('SELECT * FROM issues WHERE tag=? ORDER BY priority DESC',
                          (tag,)).fetchall()
    else:
        rows = db.execute('SELECT * FROM issues ORDER BY priority DESC').fetchall()
    db.close()
    keys = ['id','area','description','tag','timestamp','upvotes','priority']
    return [dict(zip(keys, r)) for r in rows]

def get_summary():
    db = get_db()
    rows = db.execute('SELECT area, COUNT(*) as count FROM issues GROUP BY area').fetchall()
    db.close()
    result = []
    for area, count in rows:
        if count >= 8: heat = 'high'
        elif count >= 4: heat = 'medium'
        else: heat = 'low'
        result.append({'area': area, 'count': count, 'heat': heat})
    return result

def upvote_issue(issue_id):
    db = get_db()
    db.execute('UPDATE issues SET upvotes = upvotes + 1 WHERE id=?', (issue_id,))
    row = db.execute('SELECT upvotes, timestamp FROM issues WHERE id=?',
                     (issue_id,)).fetchone()
    if row:
        import time
        age = max((time.time() - row[1]) / 3600, 1)
        priority = round(row[0] / age, 2)
        db.execute('UPDATE issues SET priority=? WHERE id=?', (priority, issue_id))
    db.commit(); db.close()