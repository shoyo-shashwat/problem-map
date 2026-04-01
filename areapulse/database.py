import sqlite3, time

def get_db():
    db = sqlite3.connect('areapulse.db')
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area TEXT, description TEXT, tag TEXT,
        timestamp REAL, upvotes INTEGER DEFAULT 0,
        priority REAL DEFAULT 0.0, verified INTEGER DEFAULT 0,
        status TEXT DEFAULT 'open', user TEXT,
        lat REAL, lng REAL
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS users (
        name TEXT PRIMARY KEY, points INTEGER DEFAULT 0
    )''')
    # add lat/lng columns if upgrading old DB
    try: db.execute('ALTER TABLE issues ADD COLUMN lat REAL')
    except: pass
    try: db.execute('ALTER TABLE issues ADD COLUMN lng REAL')
    except: pass
    db.commit(); db.close()

def seed_real_issues():
    """Seeds realistic Delhi civic issues only if DB is empty."""
    db = get_db()
    count = db.execute('SELECT COUNT(*) FROM issues').fetchone()[0]
    if count > 0:
        db.close(); return

    seeds = [
        # (area, description, tag, user, status, upvotes, lat, lng)
        ('Rohini', 'Massive pothole on Rohini Sector 3 main road near D-mall, causing daily accidents especially for two-wheelers', 'pothole', 'Arav Sharma', 'open', 14, 28.7041, 77.1025),
        ('Karol Bagh', 'Sewage overflow on Arya Samaj Road blocking pedestrian path, extremely foul smell since 3 days', 'sewage', 'Priya Mehta', 'verified', 9, 28.6514, 77.1907),
        ('Dwarka', 'Streetlight at Sector 12 bus stop completely dark for 2 weeks, women feel unsafe at night', 'streetlight', 'Rahul Gupta', 'open', 22, 28.5921, 77.0460),
        ('Lajpat Nagar', 'Garbage overflowing from bins near Central Market for 4 days, stray dogs and rats visible', 'garbage', 'Sneha Kapoor', 'open', 18, 28.5677, 77.2378),
        ('Chandni Chowk', 'Water pipe burst near Fatehpuri Masjid flooding entire lane, shops flooded, traffic jam', 'water', 'Vikram Sethi', 'escalated', 31, 28.6506, 77.2303),
        ('Connaught Place', 'Loud construction noise from Palika Bazaar basement at midnight violating noise norms', 'noise', 'Ananya Singh', 'open', 7, 28.6315, 77.2167),
        ('Pitampura', 'Large fallen tree blocking Pitampura Main Road since last night storm, traffic diverted', 'tree', 'Deepak Verma', 'resolved', 11, 28.7007, 77.1311),
        ('Saket', 'Open manhole on Press Enclave Road near Select Citywalk extremely dangerous for cyclists', 'sewage', 'Neha Agarwal', 'open', 25, 28.5244, 77.2090),
        ('Vasant Kunj', 'Broken water pipeline at B9 DDA Flats, residents without water for 2 days in summer heat', 'water', 'Karan Malhotra', 'verified', 16, 28.5200, 77.1590),
        ('Shahdara', 'Illegal garbage dumping site near Shahdara drain, burning waste at night causing toxic smoke', 'garbage', 'Pooja Yadav', 'open', 20, 28.6706, 77.2944),
        ('Mayur Vihar', 'Traffic signal at Mayur Vihar Phase 1 metro not working for 5 days, near-miss accidents daily', 'traffic', 'Amit Joshi', 'open', 13, 28.6090, 77.2944),
        ('Janakpuri', 'Frequent power cuts in Janakpuri Block C, 4-6 hours outage daily despite paying bills', 'electricity', 'Sunita Rawat', 'open', 8, 28.6219, 77.0878),
        ('Laxmi Nagar', 'Pothole filled with rainwater near Laxmi Nagar Metro, motorcyclist fell yesterday', 'pothole', 'Rohit Pandey', 'open', 19, 28.6310, 77.2780),
        ('Hauz Khas', 'Illegal loudspeakers at event near Hauz Khas Village every night till 2am', 'noise', 'Meera Nair', 'open', 6, 28.5494, 77.2001),
        ('Rajouri Garden', 'Street dog menace near Rajouri Garden metro causing fear, 3 bite incidents this week', 'garbage', 'Suresh Kumar', 'open', 29, 28.6447, 77.1220),
        ('Model Town', 'Broken footpath with exposed iron rods near Model Town Park, elderly fell and got injured', 'pothole', 'Kavita Sharma', 'verified', 12, 28.7167, 77.1900),
        ('Geeta Colony', 'Open electrical wires hanging low over road near Geeta Colony flyover after storm damage', 'electricity', 'Rajan Sood', 'open', 34, 28.6590, 77.2780),
        ('Malviya Nagar', 'Waterlogging in Malviya Nagar market after every rain, shopkeepers losing business', 'water', 'Tina Bhatia', 'open', 17, 28.5355, 77.2068),
        ('Burari', 'Garbage truck not coming to Burari Sector 4 for 6 days, residents burning waste themselves', 'garbage', 'Harish Negi', 'open', 23, 28.7470, 77.2100),
        ('Uttam Nagar', 'Deep pothole crater on Uttam Nagar West road, at least 50cm deep, bus got stuck yesterday', 'pothole', 'Sachin Tyagi', 'open', 41, 28.6219, 77.0560),
    ]

    ts = time.time()
    for s in seeds:
        area, desc, tag, user, status, upvotes, lat, lng = s
        db.execute(
            "INSERT INTO issues (area,description,tag,timestamp,upvotes,status,user,lat,lng) VALUES (?,?,?,?,?,?,?,?,?)",
            (area, desc, tag, ts - (len(seeds)*3600), upvotes, status, user, lat, lng)
        )
        db.execute("INSERT OR IGNORE INTO users (name,points) VALUES (?,?)", (user, upvotes*2 + 10))

    # Seed top users
    top_users = [('Delhi Civic Watch', 320), ('NGO Volunteer', 180), ('RWA Rohini', 95)]
    for name, pts in top_users:
        db.execute("INSERT OR IGNORE INTO users (name,points) VALUES (?,?)", (name, pts))

    db.commit(); db.close()

def insert_issue(area, description, tag, user, lat=None, lng=None):
    db = get_db()
    db.execute(
        "INSERT INTO issues (area,description,tag,timestamp,user,status,lat,lng) VALUES (?,?,?,?,?,'open',?,?)",
        (area, description, tag, time.time(), user, lat, lng)
    )
    db.commit(); db.close()

def get_issues():
    db = get_db()
    rows = db.execute('SELECT * FROM issues ORDER BY priority DESC, timestamp DESC').fetchall()
    db.close()
    return [dict(r) for r in rows]

def upvote_issue(issue_id):
    db = get_db()
    db.execute('UPDATE issues SET upvotes=upvotes+1 WHERE id=?', (issue_id,))
    row = db.execute('SELECT upvotes,timestamp FROM issues WHERE id=?', (issue_id,)).fetchone()
    if row:
        age = max((time.time()-row['timestamp'])/3600, 1)
        db.execute('UPDATE issues SET priority=? WHERE id=?', (round(row['upvotes']/age,2), issue_id))
    db.commit(); db.close()

def verify_issue(issue_id):
    db = get_db()
    db.execute("UPDATE issues SET verified=verified+1, status='verified' WHERE id=?", (issue_id,))
    db.commit(); db.close()

def resolve_issue(issue_id):
    db = get_db()
    db.execute("UPDATE issues SET status='resolved' WHERE id=?", (issue_id,))
    db.commit(); db.close()

def add_points(user, pts):
    if not user or not user.strip(): return
    db = get_db()
    if db.execute('SELECT 1 FROM users WHERE name=?', (user,)).fetchone():
        db.execute('UPDATE users SET points=points+? WHERE name=?', (pts, user))
    else:
        db.execute('INSERT INTO users (name,points) VALUES (?,?)', (user, pts))
    db.commit(); db.close()

def get_summary():
    db = get_db()
    rows = db.execute('SELECT area, COUNT(*) FROM issues GROUP BY area').fetchall()
    db.close()
    result = []
    for area, count in rows:
        heat = 'high' if count>=8 else 'medium' if count>=4 else 'low'
        result.append({'area':area,'count':count,'heat':heat})
    return result
