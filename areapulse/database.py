import psycopg2, psycopg2.extras, time, os, math

def get_db():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        database=os.environ.get('DB_NAME', 'areapulse'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'garv@2025'),
        port=os.environ.get('DB_PORT', '5432')
    )
    conn.autocommit = False
    return conn

def _cur(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

def init_db():
    db = get_db()
    cur = db.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        name TEXT PRIMARY KEY,
        points INTEGER DEFAULT 0
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS issues (
        id SERIAL PRIMARY KEY,
        area TEXT, description TEXT, tag TEXT,
        timestamp REAL, upvotes INTEGER DEFAULT 0,
        priority REAL DEFAULT 0.0, verified INTEGER DEFAULT 0,
        status TEXT DEFAULT 'open', "user" TEXT,
        lat REAL, lng REAL, image TEXT,
        severity TEXT DEFAULT 'medium', landmark TEXT, contact TEXT,
        assigned_to TEXT DEFAULT NULL
    )''')
    # Add assigned_to column if it doesn't exist (for existing databases)
    try:
        cur.execute("ALTER TABLE issues ADD COLUMN IF NOT EXISTS assigned_to TEXT DEFAULT NULL")
    except Exception:
        pass
    cur.execute('''CREATE TABLE IF NOT EXISTS ngos (
        id SERIAL PRIMARY KEY,
        name TEXT, tag TEXT, phone TEXT, email TEXT,
        address TEXT, area TEXT, lat REAL, lng REAL,
        icon TEXT DEFAULT '🏛️', focus TEXT,
        issues_resolved INTEGER DEFAULT 0,
        issues_escalated INTEGER DEFAULT 0,
        rating REAL DEFAULT 4.0,
        org_type TEXT DEFAULT 'ngo'
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS gov_agencies (
        id SERIAL PRIMARY KEY,
        name TEXT, tag TEXT, phone TEXT, email TEXT,
        address TEXT, area TEXT, lat REAL, lng REAL,
        icon TEXT DEFAULT '🏛️', focus TEXT,
        department TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS community_posts (
        id SERIAL PRIMARY KEY,
        "user" TEXT, message TEXT, area TEXT,
        timestamp REAL, likes INTEGER DEFAULT 0,
        post_type TEXT DEFAULT 'update'
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS community_likes (
        user_name TEXT, post_id INTEGER,
        PRIMARY KEY (user_name, post_id)
    )''')
    db.commit()
    db.close()
    _seed_ngos()
    _seed_gov()

def _seed_ngos():
    db = get_db()
    cur = _cur(db)
    cur.execute('SELECT COUNT(*) as cnt FROM ngos')
    if cur.fetchone()['cnt'] > 0:
        db.close(); return
    ngos = [
        ('WaterAid India','water','+91-11-4052-4444','info@wateraid.org','Hauz Khas, South Delhi','Hauz Khas',28.5494,77.2001,'💧','Clean water & sanitation infrastructure',42,18,4.6),
        ('Delhi Jal Board (Citizens)','sewage','1916','citizen@djb.delhi.gov.in','Jhandewalan, New Delhi','Karol Bagh',28.6514,77.1907,'🚰','Sewage, drainage & water supply complaints',67,34,4.2),
        ('Road Safety Network India','pothole','+91-98100-00001','roads@rsni.org','Connaught Place, New Delhi','Connaught Place',28.6315,77.2167,'🛣️','Road safety & pothole repair advocacy',38,22,4.5),
        ('SaveLIFE Foundation','traffic','+91-22-4900-2220','info@savelifefoundation.org','Lajpat Nagar, South Delhi','Lajpat Nagar',28.5677,77.2378,'🚦','Traffic safety, road accidents & signals',55,29,4.7),
        ('Chintan Environmental','garbage','+91-11-2753-2346','info@chintan-india.org','Shahdara, East Delhi','Shahdara',28.6706,77.2944,'♻️','Waste management, recycling & clean-up',89,41,4.8),
        ('Delhi Power Citizens Forum','streetlight','+91-11-2345-6789','help@dpcf.in','Karol Bagh, West Delhi','Karol Bagh',28.6514,77.1907,'💡','Streetlights & BSES electricity complaints',31,15,4.1),
        ('Awaaz Foundation','noise','+91-22-2369-7571','awaaz@awaazfoundation.org','Rohini, North Delhi','Rohini',28.7041,77.1025,'🔇','Noise pollution & air quality advocacy',28,12,4.3),
        ('Delhi Tree Society','tree','+91-11-2300-0001','dts@delhitrees.org','Mehrauli, South Delhi','Mehrauli',28.5244,77.1855,'🌳','Tree plantation & fallen tree removal',19,9,4.4),
        ('BSES Rajdhani Consumer Cell','electricity','19123','consumer@bsesrajdhani.com','Nehru Place, South Delhi','Greater Kailash',28.5494,77.2378,'⚡','Power cuts, meter & electrical safety',74,33,4.0),
        ('Paryavaran Mitra Delhi','garbage','+91-11-4100-2200','contact@paryavaranmitra.org','Pitampura, North Delhi','Pitampura',28.7007,77.1311,'🌿','Environmental cleanliness & waste mgmt',45,20,4.5),
        ('Delhi Road Repair Forum','pothole','+91-98111-55566','info@delhiroads.org','Dwarka, South West Delhi','Dwarka',28.5921,77.0460,'🚧','Pothole complaints & road repair follow-up',33,16,4.2),
        ('Safai Sena','garbage','+91-11-2950-1234','safaisena@gmail.com','Okhla Industrial Area','Okhla',28.5355,77.2780,'🧹','Garbage collection & street cleaning drives',62,28,4.6),
        ('Vatavaran Foundation','water','+91-11-4150-9900','info@vatavaran.org','Vasant Kunj, South Delhi','Vasant Kunj',28.5200,77.1590,'💦','Rainwater harvesting & water conservation',22,11,4.4),
        ('Green Delhi Foundation','tree','+91-98102-33445','greendelhi@gdf.org','Model Town, North Delhi','Model Town',28.7167,77.1900,'🌱','Urban greening & park maintenance',17,8,4.3),
        ('Delhi Pollution Control Cmt','noise','+91-11-2233-0400','dpcc@nic.in','Pragati Vihar, Central','Daryaganj',28.6417,77.2353,'📊','Pollution & industrial violation complaints',34,18,4.1),
        ('East Delhi RWA Federation','garbage','+91-11-2210-3344','edrawafed@gmail.com','Laxmi Nagar, East Delhi','Laxmi Nagar',28.6310,77.2780,'🏘️','East Delhi resident welfare & garbage issues',28,13,4.0),
        ('West Delhi Civic Forum','pothole','+91-98181-77890','wdcf@gmail.com','Janakpuri, West Delhi','Janakpuri',28.6219,77.0878,'🛠️','West Delhi road & infrastructure issues',21,10,4.2),
        ('North Delhi Green Mission','tree','+91-98112-44556','ndgm@gmail.com','Rohini, North Delhi','Rohini',28.7041,77.1025,'🍃','North Delhi tree cover & park maintenance',14,6,4.1),
        ('South Delhi Residents Forum','water','+91-98101-22334','sdrf@gmail.com','Saket, South Delhi','Saket',28.5244,77.2090,'🏙️','South Delhi water & civic issue advocacy',19,9,4.3),
        ('Delhi Citizen Helpline','other','1031','pgrams@delhi.gov.in','Connaught Place, New Delhi','Connaught Place',28.6315,77.2167,'🏛️','General civic issues & govt complaints',120,67,3.9),
    ]
    cur2 = db.cursor()
    for n in ngos:
        cur2.execute('INSERT INTO ngos (name,tag,phone,email,address,area,lat,lng,icon,focus,issues_resolved,issues_escalated,rating) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', n)
    db.commit(); db.close()

def _seed_gov():
    db = get_db()
    cur = _cur(db)
    cur.execute('SELECT COUNT(*) as cnt FROM gov_agencies')
    if cur.fetchone()['cnt'] > 0:
        db.close(); return
    agencies = [
        ('MCD North Delhi','garbage','155305','northdelhi@mcd.gov.in','Civic Centre, New Delhi','Connaught Place',28.6315,77.2167,'🏛️','North Delhi garbage & civic complaints','Municipal Corporation of Delhi'),
        ('MCD South Delhi','garbage','155303','southdelhi@mcd.gov.in','Green Park Extension','Hauz Khas',28.5494,77.2001,'🏛️','South Delhi garbage & civic complaints','Municipal Corporation of Delhi'),
        ('MCD East Delhi','garbage','155304','eastdelhi@mcd.gov.in','Laxmi Nagar, East Delhi','Laxmi Nagar',28.6310,77.2780,'🏛️','East Delhi garbage & civic complaints','Municipal Corporation of Delhi'),
        ('PWD Delhi (Roads)','pothole','011-23490175','secy.pwd@delhi.gov.in','Indraprastha Estate','Daryaganj',28.6417,77.2353,'🛣️','Delhi public works — road repair & pothole','Public Works Department'),
        ('Delhi Traffic Police','traffic','011-23490162','trafficdelhi@nic.in','ITO, Central Delhi','Daryaganj',28.6417,77.2353,'👮','Traffic violations, signals & road accidents','Delhi Police'),
        ('Delhi Jal Board (Helpline)','water','1916','md@djb.delhi.gov.in','Varunalaya Phase II','Civil Lines',28.6800,77.2250,'💧','Water supply, pipeline & sewage issues','Delhi Jal Board'),
        ('BSES Yamuna','electricity','19122','consumer@bsesyamuna.com','Karkardooma, East Delhi','Preet Vihar',28.6355,77.2944,'⚡','East Delhi power cuts & electricity issues','BSES Yamuna Power Ltd'),
        ('BSES Rajdhani','electricity','19123','consumer@bsesrajdhani.com','Nehru Place, South Delhi','Greater Kailash',28.5494,77.2378,'⚡','South/West Delhi electricity complaints','BSES Rajdhani Power Ltd'),
        ('NDMC (New Delhi)','streetlight','1533','grievance@ndmc.gov.in','Palika Bhawan, New Delhi','Connaught Place',28.6315,77.2167,'🏙️','NDMC area: lights, roads & drains','New Delhi Municipal Council'),
        ('Delhi Fire Service','other','101','dfs@delhi.gov.in','Connaught Place, New Delhi','Connaught Place',28.6315,77.2167,'🚒','Fire hazards & emergency response','Delhi Fire Service'),
        ('Delhi Police PCR','other','100','pcr@delhipolice.nic.in','ITO, New Delhi','Daryaganj',28.6417,77.2353,'🚓','Crime, safety & emergency PCR calls','Delhi Police'),
        ('Environment Dept Delhi','noise','+91-11-2336-1800','envt@delhi.gov.in','Paryavaran Bhawan','Daryaganj',28.6417,77.2353,'🌍','Air, noise & environmental violations','Delhi Govt Environment Dept'),
        ('Forest Dept Delhi','tree','+91-11-2306-4911','forest@delhi.gov.in','Aruna Asaf Ali Marg','Daryaganj',28.6417,77.2353,'🌳','Tree cutting permissions & fallen trees','Delhi Forest Department'),
        ('DDA (Parks & Roads)','pothole','011-24690173','pr@dda.org.in','INA, South Delhi','Lajpat Nagar',28.5677,77.2378,'🏗️','DDA roads, parks & housing complaints','Delhi Development Authority'),
        ('Doorstep Delivery Delhi','other','1076','doorstep@delhi.gov.in','Delhi Secretariat','Daryaganj',28.6417,77.2353,'📦','Govt services at doorstep & civic grievances','Delhi Government'),
    ]
    cur2 = db.cursor()
    for a in agencies:
        cur2.execute('INSERT INTO gov_agencies (name,tag,phone,email,address,area,lat,lng,icon,focus,department) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', a)
    db.commit(); db.close()

def seed_real_issues():
    db = get_db()
    cur = _cur(db)
    cur.execute('SELECT COUNT(*) as cnt FROM issues')
    if cur.fetchone()['cnt'] > 0:
        db.close(); return
    seeds = [
        ('Rohini','Massive pothole on Sector 3 road near D-Mall causing daily accidents','pothole','system_seed','open',14,28.7041,77.1025,'high',None),
        ('Rohini','Sewage overflowing near Sector 7 market for 4 days, unbearable stench','sewage','system_seed','open',11,28.7055,77.1040,'high',None),
        ('Rohini','Streetlight dead in Sector 11 for 3 weeks, women feel unsafe walking','streetlight','system_seed','open',18,28.7080,77.1060,'medium',None),
        ('Rohini','Garbage bins overflowing Sector 16, not collected for 5 days, rats visible','garbage','system_seed','open',9,28.7020,77.1010,'medium',None),
        ('Dwarka','Deep crater on Main Road Sector 12 near petrol pump, 2 accidents already','pothole','system_seed','open',21,28.5921,77.0460,'high',None),
        ('Dwarka','Water pipeline burst near Sector 6 park, road waterlogged for 2 days','water','system_seed','open',15,28.5900,77.0500,'high',None),
        ('Dwarka','Multiple streetlights out on Dwarka Mor flyover approach, very dark at night','streetlight','system_seed','open',12,28.6120,77.0590,'medium',None),
        ('Lajpat Nagar','Garbage dumped behind Central Market not cleared for a week, stray dogs','garbage','system_seed','open',8,28.5677,77.2378,'medium',None),
        ('Lajpat Nagar','Open drain near Ring Road overflowing, mosquito breeding ground forming','sewage','system_seed','open',16,28.5690,77.2350,'high',None),
        ('Connaught Place','Broken footpath tiles causing elderly pedestrians to trip and fall near N Block','pothole','system_seed','open',19,28.6315,77.2167,'medium',None),
        ('Connaught Place','Traffic signal malfunction at Barakhamba Road crossing since Tuesday evening','traffic','system_seed','open',24,28.6330,77.2200,'high',None),
        ('Karol Bagh','Power cut lasting 8+ hours daily in Arya Samaj Road area, transformer issue','electricity','system_seed','open',13,28.6514,77.1907,'high',None),
        ('Saket','Fallen tree blocking half of Press Enclave Road near Select Citywalk entrance','tree','system_seed','open',7,28.5244,77.2090,'high',None),
        ('Mayur Vihar','Loud construction noise past midnight near Phase 1 extension, residents awake','noise','system_seed','open',6,28.6090,77.2944,'medium',None),
        ('Shahdara','Overflowing sewer near Vivek Vihar bus stop, smell unbearable','sewage','system_seed','open',22,28.6706,77.2944,'high',None),
    ]
    cur2 = db.cursor()
    t = time.time()
    for i, s in enumerate(seeds):
        area, desc, tag, user, status, upvotes, lat, lng, severity, assigned_to = s
        cur2.execute(
            'INSERT INTO issues (area,description,tag,"user",status,upvotes,lat,lng,timestamp,severity,assigned_to) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
            (area, desc, tag, user, status, upvotes, lat, lng, t - i * 3600, severity, assigned_to)
        )
    db.commit(); db.close()

def insert_issue(area, description, tag, user, lat=None, lng=None, image=None,
                 severity='medium', landmark=None, contact=None, assigned_to=None):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        'INSERT INTO issues (area,description,tag,timestamp,"user",status,lat,lng,image,severity,landmark,contact,assigned_to) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
        (area, description, tag, time.time(), user, 'open', lat, lng, image, severity, landmark, contact, assigned_to)
    )
    db.commit(); db.close()

def get_issues():
    db = get_db()
    cur = _cur(db)
    cur.execute('SELECT * FROM issues ORDER BY priority DESC, timestamp DESC')
    rows = cur.fetchall()
    db.close()
    return [dict(r) for r in rows]

def get_issues_by_user(username):
    db = get_db()
    cur = _cur(db)
    cur.execute('SELECT * FROM issues WHERE "user"=%s ORDER BY timestamp DESC', (username,))
    rows = cur.fetchall()
    db.close()
    return [dict(r) for r in rows]

def upvote_issue(issue_id):
    db = get_db()
    cur = db.cursor()
    cur.execute('UPDATE issues SET upvotes=upvotes+1 WHERE id=%s', (issue_id,))
    cur2 = _cur(db)
    cur2.execute('SELECT upvotes, timestamp FROM issues WHERE id=%s', (issue_id,))
    row = cur2.fetchone()
    if row:
        age = max((time.time() - row['timestamp']) / 3600, 1)
        cur.execute('UPDATE issues SET priority=%s WHERE id=%s', (round(row['upvotes'] / age, 2), issue_id))
    db.commit(); db.close()

def verify_issue(issue_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE issues SET verified=verified+1, status='verified' WHERE id=%s", (issue_id,))
    db.commit(); db.close()

def resolve_issue(issue_id, assigned_to=None):
    db = get_db()
    cur = db.cursor()
    if assigned_to:
        cur.execute("UPDATE issues SET status='resolved', assigned_to=%s WHERE id=%s", (assigned_to, issue_id))
    else:
        cur.execute("UPDATE issues SET status='resolved' WHERE id=%s", (issue_id,))
    db.commit(); db.close()

def escalate_issue(issue_id, assigned_to=None):
    db = get_db()
    cur = db.cursor()
    if assigned_to:
        cur.execute("UPDATE issues SET status='escalated', assigned_to=%s WHERE id=%s", (assigned_to, issue_id))
    else:
        cur.execute("UPDATE issues SET status='escalated' WHERE id=%s", (issue_id,))
    db.commit(); db.close()

def add_points(user, pts):
    if not user or not user.strip(): return
    db = get_db()
    cur = db.cursor()
    cur.execute(
        'INSERT INTO users (name,points) VALUES (%s,%s) ON CONFLICT (name) DO UPDATE SET points=users.points+%s',
        (user, pts, pts)
    )
    db.commit(); db.close()

def get_user_stats(username):
    db = get_db()
    cur = _cur(db)
    cur.execute('SELECT points FROM users WHERE name=%s', (username,))
    row = cur.fetchone()
    points = row['points'] if row else 0
    cur.execute('SELECT COUNT(*) as cnt FROM issues WHERE "user"=%s', (username,))
    total = cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(*) as cnt FROM issues WHERE \"user\"=%s AND status='resolved'", (username,))
    resolved = cur.fetchone()['cnt']
    db.close()
    return {'points': points, 'total_reported': total, 'total_resolved': resolved}

def get_ngos(tag_filter=None, area_filter=None, sort_by='resolved'):
    db = get_db()
    cur = _cur(db)
    q = 'SELECT * FROM ngos WHERE 1=1'
    params = []
    if tag_filter: q += ' AND tag=%s'; params.append(tag_filter)
    if area_filter: q += ' AND area=%s'; params.append(area_filter)
    order = 'issues_resolved DESC' if sort_by == 'resolved' else 'rating DESC'
    q += f' ORDER BY {order}'
    cur.execute(q, params)
    rows = cur.fetchall()
    db.close()
    return [dict(r) for r in rows]

def get_gov_agencies(tag_filter=None, area_filter=None):
    db = get_db()
    cur = _cur(db)
    q = 'SELECT * FROM gov_agencies WHERE 1=1'
    params = []
    if tag_filter: q += ' AND tag=%s'; params.append(tag_filter)
    if area_filter: q += ' AND area=%s'; params.append(area_filter)
    q += ' ORDER BY name'
    cur.execute(q, params)
    rows = cur.fetchall()
    db.close()
    return [dict(r) for r in rows]

def get_nearby_ngos(lat, lng, tag=None, limit=5):
    db = get_db()
    cur = _cur(db)
    q = 'SELECT * FROM ngos WHERE 1=1'
    params = []
    if tag and tag != 'other':
        q += " AND (tag=%s OR tag='other')"; params.append(tag)
    cur.execute(q, params)
    rows = cur.fetchall()
    db.close()
    ngos = []
    for r in rows:
        n = dict(r)
        d = math.sqrt((lat - n['lat']) ** 2 + (lng - n['lng']) ** 2)
        n['distance_km'] = round(d * 111, 1)
        ngos.append(n)
    ngos.sort(key=lambda x: x['distance_km'])
    return ngos[:limit]

def get_community_posts(area=None, limit=30):
    db = get_db()
    cur = _cur(db)
    if area:
        cur.execute('SELECT * FROM community_posts WHERE area=%s ORDER BY timestamp DESC LIMIT %s', (area, limit))
    else:
        cur.execute('SELECT * FROM community_posts ORDER BY timestamp DESC LIMIT %s', (limit,))
    rows = cur.fetchall()
    db.close()
    return [dict(r) for r in rows]

def add_community_post(user, message, area, post_type='update'):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        'INSERT INTO community_posts ("user",message,area,timestamp,post_type) VALUES (%s,%s,%s,%s,%s)',
        (user, message, area, time.time(), post_type)
    )
    db.commit(); db.close()

def like_post(post_id, user):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute('INSERT INTO community_likes (user_name,post_id) VALUES (%s,%s)', (user, post_id))
        cur.execute('UPDATE community_posts SET likes=likes+1 WHERE id=%s', (post_id,))
        db.commit(); result = True
    except Exception:
        db.rollback(); result = False
    db.close()
    return result