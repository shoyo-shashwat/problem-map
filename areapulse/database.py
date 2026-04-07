import sqlite3, time, os, math

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'areapulse.db')

def get_db():
    db = sqlite3.connect(DB_PATH)
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
        lat REAL, lng REAL, image TEXT,
        severity TEXT DEFAULT 'medium', landmark TEXT, contact TEXT
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS users (
        name TEXT PRIMARY KEY, points INTEGER DEFAULT 0
    )''')
    # NGOs - civil society organisations
    db.execute('''CREATE TABLE IF NOT EXISTS ngos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, tag TEXT, phone TEXT, email TEXT,
        address TEXT, area TEXT, lat REAL, lng REAL,
        icon TEXT DEFAULT '🏛️', focus TEXT,
        issues_resolved INTEGER DEFAULT 0,
        issues_escalated INTEGER DEFAULT 0,
        rating REAL DEFAULT 4.0,
        org_type TEXT DEFAULT 'ngo'
    )''')
    # Government agencies - separate table
    db.execute('''CREATE TABLE IF NOT EXISTS gov_agencies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, tag TEXT, phone TEXT, email TEXT,
        address TEXT, area TEXT, lat REAL, lng REAL,
        icon TEXT DEFAULT '🏛️', focus TEXT,
        department TEXT
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS community_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT, message TEXT, area TEXT,
        timestamp REAL, likes INTEGER DEFAULT 0,
        post_type TEXT DEFAULT 'update'
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS community_likes (
        user_name TEXT, post_id INTEGER,
        PRIMARY KEY (user_name, post_id)
    )''')
    # safe column migrations
    for col, typ in [('lat','REAL'),('lng','REAL'),('image','TEXT'),
                     ('severity','TEXT'),('landmark','TEXT'),('contact','TEXT')]:
        try: db.execute(f'ALTER TABLE issues ADD COLUMN {col} {typ}')
        except: pass
    db.commit()
    db.close()
    _seed_ngos()
    _seed_gov()

def _seed_ngos():
    db = get_db()
    if db.execute('SELECT COUNT(*) FROM ngos').fetchone()[0] > 0:
        db.close(); return
    ngos = [
        # (name, tag, phone, email, address, area, lat, lng, icon, focus, resolved, escalated, rating)
        ('WaterAid India',               'water',       '+91-11-4052-4444',  'info@wateraid.org',              'Hauz Khas, South Delhi',     'Hauz Khas',       28.5494, 77.2001, '💧', 'Clean water & sanitation infrastructure',      42, 18, 4.6),
        ('Delhi Jal Board (Citizens)',   'sewage',      '1916',              'citizen@djb.delhi.gov.in',       'Jhandewalan, New Delhi',     'Karol Bagh',      28.6514, 77.1907, '🚰', 'Sewage, drainage & water supply complaints',   67, 34, 4.2),
        ('Road Safety Network India',    'pothole',     '+91-98100-00001',   'roads@rsni.org',                 'Connaught Place, New Delhi', 'Connaught Place', 28.6315, 77.2167, '🛣️', 'Road safety & pothole repair advocacy',        38, 22, 4.5),
        ('SaveLIFE Foundation',          'traffic',     '+91-22-4900-2220',  'info@savelifefoundation.org',    'Lajpat Nagar, South Delhi',  'Lajpat Nagar',    28.5677, 77.2378, '🚦', 'Traffic safety, road accidents & signals',     55, 29, 4.7),
        ('Chintan Environmental',        'garbage',     '+91-11-2753-2346',  'info@chintan-india.org',         'Shahdara, East Delhi',       'Shahdara',        28.6706, 77.2944, '♻️', 'Waste management, recycling & clean-up',       89, 41, 4.8),
        ('Delhi Power Citizens Forum',   'streetlight', '+91-11-2345-6789',  'help@dpcf.in',                   'Karol Bagh, West Delhi',     'Karol Bagh',      28.6514, 77.1907, '💡', 'Streetlights & BSES electricity complaints',   31, 15, 4.1),
        ('Awaaz Foundation',             'noise',       '+91-22-2369-7571',  'awaaz@awaazfoundation.org',      'Rohini, North Delhi',        'Rohini',          28.7041, 77.1025, '🔇', 'Noise pollution & air quality advocacy',       28, 12, 4.3),
        ('Delhi Tree Society',           'tree',        '+91-11-2300-0001',  'dts@delhitrees.org',             'Mehrauli, South Delhi',      'Mehrauli',        28.5244, 77.1855, '🌳', 'Tree plantation & fallen tree removal',        19,  9, 4.4),
        ('BSES Rajdhani Consumer Cell',  'electricity', '19123',             'consumer@bsesrajdhani.com',      'Nehru Place, South Delhi',   'Greater Kailash', 28.5494, 77.2378, '⚡', 'Power cuts, meter & electrical safety',        74, 33, 4.0),
        ('Paryavaran Mitra Delhi',       'garbage',     '+91-11-4100-2200',  'contact@paryavaranmitra.org',    'Pitampura, North Delhi',     'Pitampura',       28.7007, 77.1311, '🌿', 'Environmental cleanliness & waste mgmt',       45, 20, 4.5),
        ('Delhi Road Repair Forum',      'pothole',     '+91-98111-55566',   'info@delhiroads.org',            'Dwarka, South West Delhi',   'Dwarka',          28.5921, 77.0460, '🚧', 'Pothole complaints & road repair follow-up',   33, 16, 4.2),
        ('Safai Sena',                   'garbage',     '+91-11-2950-1234',  'safaisena@gmail.com',            'Okhla Industrial Area',      'Okhla',           28.5355, 77.2780, '🧹', 'Garbage collection & street cleaning drives',  62, 28, 4.6),
        ('Vatavaran Foundation',         'water',       '+91-11-4150-9900',  'info@vatavaran.org',             'Vasant Kunj, South Delhi',   'Vasant Kunj',     28.5200, 77.1590, '💦', 'Rainwater harvesting & water conservation',    22, 11, 4.4),
        ('Green Delhi Foundation',       'tree',        '+91-98102-33445',   'greendelhi@gdf.org',             'Model Town, North Delhi',    'Model Town',      28.7167, 77.1900, '🌱', 'Urban greening & park maintenance',            17,  8, 4.3),
        ('Delhi Pollution Control Cmt',  'noise',       '+91-11-2233-0400',  'dpcc@nic.in',                    'Pragati Vihar, Central',     'Daryaganj',       28.6417, 77.2353, '📊', 'Pollution & industrial violation complaints',  34, 18, 4.1),
        ('East Delhi RWA Federation',    'garbage',     '+91-11-2210-3344',  'edrawafed@gmail.com',            'Laxmi Nagar, East Delhi',    'Laxmi Nagar',     28.6310, 77.2780, '🏘️', 'East Delhi resident welfare & garbage issues', 28, 13, 4.0),
        ('West Delhi Civic Forum',       'pothole',     '+91-98181-77890',   'wdcf@gmail.com',                 'Janakpuri, West Delhi',      'Janakpuri',       28.6219, 77.0878, '🛠️', 'West Delhi road & infrastructure issues',      21, 10, 4.2),
        ('North Delhi Green Mission',    'tree',        '+91-98112-44556',   'ndgm@gmail.com',                 'Rohini, North Delhi',        'Rohini',          28.7041, 77.1025, '🍃', 'North Delhi tree cover & park maintenance',    14,  6, 4.1),
        ('South Delhi Residents Forum',  'water',       '+91-98101-22334',   'sdrf@gmail.com',                 'Saket, South Delhi',         'Saket',           28.5244, 77.2090, '🏙️', 'South Delhi water & civic issue advocacy',     19,  9, 4.3),
        ('Delhi Citizen Helpline',       'other',       '1031',              'pgrams@delhi.gov.in',            'Connaught Place, New Delhi', 'Connaught Place', 28.6315, 77.2167, '🏛️', 'General civic issues & govt complaints',      120, 67, 3.9),
    ]
    for n in ngos:
        db.execute('''INSERT INTO ngos (name,tag,phone,email,address,area,lat,lng,icon,focus,issues_resolved,issues_escalated,rating)
                      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', n)
    db.commit(); db.close()

def _seed_gov():
    db = get_db()
    if db.execute('SELECT COUNT(*) FROM gov_agencies').fetchone()[0] > 0:
        db.close(); return
    agencies = [
        # (name, tag, phone, email, address, area, lat, lng, icon, focus, department)
        ('MCD North Delhi',            'garbage',     '155305',        'northdelhi@mcd.gov.in',        'Civic Centre, New Delhi',    'Connaught Place', 28.6315, 77.2167, '🏛️', 'North Delhi garbage & civic complaints',       'Municipal Corporation of Delhi'),
        ('MCD South Delhi',            'garbage',     '155303',        'southdelhi@mcd.gov.in',        'Green Park Extension',       'Hauz Khas',       28.5494, 77.2001, '🏛️', 'South Delhi garbage & civic complaints',       'Municipal Corporation of Delhi'),
        ('MCD East Delhi',             'garbage',     '155304',        'eastdelhi@mcd.gov.in',         'Laxmi Nagar, East Delhi',    'Laxmi Nagar',     28.6310, 77.2780, '🏛️', 'East Delhi garbage & civic complaints',        'Municipal Corporation of Delhi'),
        ('PWD Delhi (Roads)',          'pothole',     '011-23490175',  'secy.pwd@delhi.gov.in',        'Indraprastha Estate',        'Daryaganj',       28.6417, 77.2353, '🛣️', 'Delhi public works — road repair & pothole',   'Public Works Department'),
        ('Delhi Traffic Police',       'traffic',     '011-23490162',  'trafficdelhi@nic.in',          'ITO, Central Delhi',         'Daryaganj',       28.6417, 77.2353, '👮', 'Traffic violations, signals & road accidents', 'Delhi Police'),
        ('Delhi Jal Board (Helpline)', 'water',       '1916',          'md@djb.delhi.gov.in',          'Varunalaya Phase II',        'Civil Lines',     28.6800, 77.2250, '💧', 'Water supply, pipeline & sewage issues',       'Delhi Jal Board'),
        ('BSES Yamuna',                'electricity', '19122',         'consumer@bsesyamuna.com',      'Karkardooma, East Delhi',    'Preet Vihar',     28.6355, 77.2944, '⚡', 'East Delhi power cuts & electricity issues',   'BSES Yamuna Power Ltd'),
        ('BSES Rajdhani',              'electricity', '19123',         'consumer@bsesrajdhani.com',    'Nehru Place, South Delhi',   'Greater Kailash', 28.5494, 77.2378, '⚡', 'South/West Delhi electricity complaints',      'BSES Rajdhani Power Ltd'),
        ('NDMC (New Delhi)',           'streetlight', '1533',          'grievance@ndmc.gov.in',        'Palika Bhawan, New Delhi',   'Connaught Place', 28.6315, 77.2167, '🏙️', 'NDMC area: lights, roads & drains',            'New Delhi Municipal Council'),
        ('Delhi Fire Service',         'other',       '101',           'dfs@delhi.gov.in',             'Connaught Place, New Delhi', 'Connaught Place', 28.6315, 77.2167, '🚒', 'Fire hazards & emergency response',            'Delhi Fire Service'),
        ('Delhi Police PCR',           'other',       '100',           'pcr@delhipolice.nic.in',       'ITO, New Delhi',             'Daryaganj',       28.6417, 77.2353, '🚓', 'Crime, safety & emergency PCR calls',          'Delhi Police'),
        ('Environment Dept Delhi',     'noise',       '+91-11-2336-1800','envt@delhi.gov.in',           'Paryavaran Bhawan',          'Daryaganj',       28.6417, 77.2353, '🌍', 'Air, noise & environmental violations',        'Delhi Govt Environment Dept'),
        ('Forest Dept Delhi',          'tree',        '+91-11-2306-4911','forest@delhi.gov.in',         'Aruna Asaf Ali Marg',        'Daryaganj',       28.6417, 77.2353, '🌳', 'Tree cutting permissions & fallen trees',      'Delhi Forest Department'),
        ('DDA (Parks & Roads)',        'pothole',     '011-24690173',  'pr@dda.org.in',                'INA, South Delhi',           'Lajpat Nagar',    28.5677, 77.2378, '🏗️', 'DDA roads, parks & housing complaints',        'Delhi Development Authority'),
        ('Doorstep Delivery Delhi',    'other',       '1076',          'doorstep@delhi.gov.in',        'Delhi Secretariat',          'Daryaganj',       28.6417, 77.2353, '📦', 'Govt services at doorstep & civic grievances', 'Delhi Government'),
    ]
    for a in agencies:
        db.execute('''INSERT INTO gov_agencies (name,tag,phone,email,address,area,lat,lng,icon,focus,department)
                      VALUES (?,?,?,?,?,?,?,?,?,?,?)''', a)
    db.commit(); db.close()

def seed_real_issues():
    init_db()
    db = get_db()
    if db.execute('SELECT COUNT(*) FROM issues').fetchone()[0] > 0:
        db.close(); return
    seeds = [
        # RED areas (8+ issues) — Rohini, Uttam Nagar, Shahdara
        ('Rohini','Massive pothole on Sector 3 road near D-Mall causing daily accidents for two-wheelers','pothole','Arav Sharma','open',14,28.7041,77.1025,'high'),
        ('Rohini','Sewage overflowing near Sector 7 market for 4 days, unbearable stench','sewage','Meena Devi','open',11,28.7055,77.1040,'high'),
        ('Rohini','Streetlight dead in Sector 11 for 3 weeks, women feel unsafe walking','streetlight','Rahul Gupta','open',18,28.7080,77.1060,'medium'),
        ('Rohini','Garbage bins overflowing Sector 16, not collected for 5 days, rats visible','garbage','Sneha Kapoor','open',9,28.7020,77.1010,'medium'),
        ('Rohini','Water pipe burst near Sector 2 flooding 3 lanes since morning','water','Dhruv Rathi','verified',22,28.7045,77.1015,'high'),
        ('Rohini','Traffic signal broken at Sector 9 chowk, causing peak hour jams','traffic','Ananya Singh','open',7,28.7055,77.1035,'medium'),
        ('Rohini','Open electrical wires hanging dangerously near Sector 6 park','electricity','Neha Agarwal','open',31,28.7035,77.1045,'high'),
        ('Rohini','Construction noise from illegal building site past midnight daily','noise','Pooja Singh','open',6,28.7090,77.1055,'medium'),
        ('Rohini','Fallen tree blocking Rohini West road since storm, bus diverted','tree','Karan Malhotra','resolved',11,28.7065,77.1065,'medium'),
        ('Uttam Nagar','Deep pothole 60cm on Uttam Nagar West road, bus got stuck','pothole','Sachin Tyagi','open',41,28.6219,77.0560,'high'),
        ('Uttam Nagar','Blocked drain near metro causing severe waterlogging for 3 days','sewage','Pooja Yadav','open',19,28.6230,77.0570,'high'),
        ('Uttam Nagar','No streetlights in C-block sector, residents use torch to walk','streetlight','Amit Joshi','open',14,28.6210,77.0550,'high'),
        ('Uttam Nagar','Water supply cut for 48 hours in B block, buying expensive tankers','water','Sunita Rawat','verified',26,28.6215,77.0555,'high'),
        ('Uttam Nagar','Power outage 3-4 hours daily, inverters draining, equipment damaged','electricity','Rohit Pandey','open',17,28.6220,77.0565,'medium'),
        ('Uttam Nagar','Traffic signal broken at main chowk, accident happened yesterday','traffic','Meera Nair','escalated',22,28.6235,77.0575,'high'),
        ('Uttam Nagar','Illegal construction waste dumped on main road blocking lane','garbage','Suresh Kumar','open',8,28.6225,77.0545,'medium'),
        ('Uttam Nagar','Aggressive stray dogs near school, 2 children bitten this week','garbage','Kavita Sharma','open',35,28.6205,77.0535,'high'),
        ('Shahdara','Illegal burning of garbage near drain, toxic fumes at night','garbage','Harish Negi','open',28,28.6706,77.2944,'high'),
        ('Shahdara','Open manhole near metro exit — cyclist fell in last week','sewage','Tina Bhatia','open',33,28.6715,77.2955,'high'),
        ('Shahdara','Pothole filled with water near flyover, motorcyclist fell','pothole','Rajan Sood','open',21,28.6695,77.2935,'high'),
        ('Shahdara','Water pipeline leaking at market road for 1 week','water','Geeta Sharma','open',16,28.6725,77.2965,'medium'),
        ('Shahdara','Loud DJ music from venue past 1am every weekend','noise','Anil Kapoor','open',9,28.6700,77.2950,'medium'),
        # YELLOW areas (4-7 issues)
        ('Dwarka','Streetlight at Sector 12 bus stop dark 2 weeks, women unsafe','streetlight','Mohan Das','open',22,28.5921,77.0460,'medium'),
        ('Dwarka','Sewage overflow near Sector 6 market causing diseases','sewage','Lalita Rani','verified',18,28.5930,77.0480,'high'),
        ('Dwarka','Pothole near school Sector 10, student fell from cycle','pothole','Vinod Kumar','open',12,28.5910,77.0450,'medium'),
        ('Dwarka','Power fluctuation in Sector 23 damaging electronics','electricity','Suman Bose','open',8,28.5940,77.0490,'medium'),
        ('Dwarka','Garbage collection not happening Sector 18 pocket B for 4 days','garbage','Ramesh Garg','open',6,28.5915,77.0470,'medium'),
        ('Lajpat Nagar','Garbage overflowing near Central Market 4 days, rodents visible','garbage','Sneha Kapoor','open',18,28.5677,77.2378,'medium'),
        ('Lajpat Nagar','Waterlogging at Ring Road junction after every rain','water','Pankaj Gupta','verified',20,28.5665,77.2365,'medium'),
        ('Lajpat Nagar','Broken footpath with exposed iron rods near park, elderly fell','pothole','Renu Sharma','open',14,28.5685,77.2390,'medium'),
        ('Chandni Chowk','Water pipe burst near Fatehpuri Masjid, flooding lanes and shops','water','Vikram Sethi','escalated',31,28.6506,77.2303,'high'),
        ('Chandni Chowk','Electric wire sparking near metro station gate','electricity','Manish Goyal','verified',39,28.6500,77.2295,'high'),
        ('Chandni Chowk','Garbage dump near Kinari Bazar for 3 days, foul smell','garbage','Sunil Jain','open',13,28.6515,77.2315,'medium'),
        # GREEN areas (1-3 issues each)
        ('Karol Bagh','Sewage overflow on Arya Samaj Road, foul smell 3 days','sewage','Priya Mehta','verified',9,28.6514,77.1907,'high'),
        ('Saket','Open manhole Press Enclave Road near Select Citywalk','sewage','Neha Agarwal','open',25,28.5244,77.2090,'high'),
        ('Vasant Kunj','Broken water pipeline B9 DDA Flats, no water for 2 days','water','Karan Malhotra','verified',16,28.5200,77.1590,'medium'),
        ('Mayur Vihar','Traffic signal Phase 1 metro broken 5 days, near-miss accidents','traffic','Amit Joshi','open',13,28.6090,77.2944,'medium'),
        ('Janakpuri','Power cuts Block C, 4-6 hours daily','electricity','Sunita Rawat','open',8,28.6219,77.0878,'medium'),
        ('Laxmi Nagar','Pothole with rainwater near metro, motorcyclist fell','pothole','Rohit Pandey','open',19,28.6310,77.2780,'high'),
        ('Hauz Khas','Loudspeakers at Hauz Khas Village events till 2am nightly','noise','Meera Nair','open',6,28.5494,77.2001,'medium'),
        ('Model Town','Broken footpath exposed iron rods near park, wrist fracture','pothole','Kavita Sharma','verified',12,28.7167,77.1900,'medium'),
        ('Geeta Colony','Open electrical wires over road near flyover','electricity','Rajan Sood','open',34,28.6590,77.2780,'high'),
        ('Malviya Nagar','Waterlogging in market after every rain, drain blocked','water','Tina Bhatia','open',17,28.5355,77.2068,'medium'),
        ('Burari','Garbage truck not coming 6 days, residents burning waste','garbage','Harish Negi','open',23,28.7470,77.2100,'medium'),
        ('Okhla','Toxic smoke from burning garbage near Okhla Bird Sanctuary','garbage','Geeta Sharma','escalated',45,28.5355,77.2780,'high'),
        ('Nangloi','No water supply Sector 5 for 72 hours','water','Anil Kapoor','open',38,28.6706,77.0590,'high'),
        ('Seelampur','Broken road near metro, 4 accidents in 1 week','pothole','Mohan Das','open',27,28.6706,77.3012,'high'),
        ('Mustafabad','Drain overflow near crossing, sewage entering homes','sewage','Lalita Rani','open',16,28.7167,77.3012,'medium'),
        ('Sangam Vihar','No electricity Block J 18 hours, elderly suffering in heat','electricity','Vinod Kumar','open',22,28.5022,77.2590,'high'),
        ('Rajouri Garden','Stray dogs near metro, 3 bite incidents this week','garbage','Suresh Kumar','open',29,28.6447,77.1220,'high'),
        ('Pitampura','Fallen tree blocking Pitampura Main Road after storm','tree','Deepak Verma','resolved',11,28.7007,77.1311,'medium'),
        ('Connaught Place','Construction noise Palika Bazaar basement at midnight','noise','Ananya Singh','open',7,28.6315,77.2167,'medium'),
    ]
    ts = time.time()
    for i, s in enumerate(seeds):
        area,desc,tag,user,status,upvotes,lat,lng,severity = s
        db.execute(
            "INSERT INTO issues (area,description,tag,timestamp,upvotes,status,user,lat,lng,severity) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (area,desc,tag,ts-(len(seeds)-i)*1800,upvotes,status,user,lat,lng,severity)
        )
        db.execute("INSERT OR IGNORE INTO users (name,points) VALUES (?,?)",(user,upvotes*2+10))
    for name,pts in [('Delhi Civic Watch',520),('NGO Volunteer',240),('RWA Delhi',185),('SafeStreets India',310)]:
        db.execute("INSERT OR IGNORE INTO users (name,points) VALUES (?,?)",(name,pts))
    # Community posts seed
    posts = [
        ('Arav Sharma','Rohini Sector 3 pothole finally fixed after 2 weeks! Thanks to Road Safety Network 🎉','Rohini',time.time()-3600,12,'success'),
        ('Priya Mehta','Sewage on Arya Samaj Road getting worse. Please upvote so authorities notice!','Karol Bagh',time.time()-7200,8,'alert'),
        ('Delhi Civic Watch','Monsoon = potholes everywhere. Report early so MCD fixes before they get dangerous.','Connaught Place',time.time()-18000,23,'tip'),
        ('Neha Agarwal','Just reported open manhole near Saket metro. Please be careful in that area!','Saket',time.time()-28800,15,'alert'),
        ('RWA Delhi','Community clean-up drive in Rohini Sector 9 this Sunday 8AM. Join us! 🌿','Rohini',time.time()-43200,31,'event'),
        ('Vikram Sethi','Chandni Chowk water pipe burst escalated to Delhi Jal Board. Resolution expected 24hrs.','Chandni Chowk',time.time()-54000,19,'update'),
        ('Kavita Sharma','Pro tip: always add a landmark — helps NGO find exact location faster!','Model Town',time.time()-86400,27,'tip'),
        ('Harish Negi','Burari garbage truck came after escalating to Safai Sena! The system works.','Burari',time.time()-108000,14,'success'),
    ]
    for p in posts:
        db.execute('INSERT INTO community_posts (user,message,area,timestamp,likes,post_type) VALUES (?,?,?,?,?,?)',p)
    db.commit(); db.close()

def insert_issue(area,description,tag,user,lat=None,lng=None,image=None,severity='medium',landmark=None,contact=None):
    db = get_db()
    db.execute(
        "INSERT INTO issues (area,description,tag,timestamp,user,status,lat,lng,image,severity,landmark,contact) VALUES (?,?,?,?,?,'open',?,?,?,?,?,?)",
        (area,description,tag,time.time(),user,lat,lng,image,severity,landmark,contact)
    )
    db.commit(); db.close()

def get_issues():
    db = get_db()
    rows = db.execute('SELECT * FROM issues ORDER BY priority DESC, timestamp DESC').fetchall()
    db.close()
    return [dict(r) for r in rows]

def get_ngos(tag_filter=None, area_filter=None, sort_by='resolved'):
    db = get_db()
    q = 'SELECT * FROM ngos WHERE 1=1'
    params = []
    if tag_filter: q += ' AND tag=?'; params.append(tag_filter)
    if area_filter: q += ' AND area=?'; params.append(area_filter)
    order = 'issues_resolved DESC' if sort_by == 'resolved' else 'rating DESC'
    q += f' ORDER BY {order}'
    rows = db.execute(q, params).fetchall()
    db.close()
    return [dict(r) for r in rows]

def get_gov_agencies(tag_filter=None, area_filter=None):
    db = get_db()
    q = 'SELECT * FROM gov_agencies WHERE 1=1'
    params = []
    if tag_filter: q += ' AND tag=?'; params.append(tag_filter)
    if area_filter: q += ' AND area=?'; params.append(area_filter)
    q += ' ORDER BY name'
    rows = db.execute(q, params).fetchall()
    db.close()
    return [dict(r) for r in rows]

def get_nearby_ngos(lat, lng, tag=None, limit=5):
    db = get_db()
    q = 'SELECT * FROM ngos WHERE 1=1'
    params = []
    if tag and tag != 'other':
        q += ' AND (tag=? OR tag="other")'; params.append(tag)
    rows = db.execute(q, params).fetchall()
    db.close()
    ngos = []
    for r in rows:
        n = dict(r)
        d = math.sqrt((lat-n['lat'])**2+(lng-n['lng'])**2)
        n['distance_km'] = round(d*111, 1)
        ngos.append(n)
    ngos.sort(key=lambda x: x['distance_km'])
    return ngos[:limit]

def upvote_issue(issue_id):
    db = get_db()
    db.execute('UPDATE issues SET upvotes=upvotes+1 WHERE id=?',(issue_id,))
    row = db.execute('SELECT upvotes,timestamp FROM issues WHERE id=?',(issue_id,)).fetchone()
    if row:
        age = max((time.time()-row['timestamp'])/3600,1)
        db.execute('UPDATE issues SET priority=? WHERE id=?',(round(row['upvotes']/age,2),issue_id))
    db.commit(); db.close()

def verify_issue(issue_id):
    db = get_db()
    db.execute("UPDATE issues SET verified=verified+1, status='verified' WHERE id=?",(issue_id,))
    db.commit(); db.close()

def resolve_issue(issue_id):
    db = get_db()
    db.execute("UPDATE issues SET status='resolved' WHERE id=?",(issue_id,))
    db.commit(); db.close()

def add_points(user, pts):
    if not user or not user.strip(): return
    db = get_db()
    if db.execute('SELECT 1 FROM users WHERE name=?',(user,)).fetchone():
        db.execute('UPDATE users SET points=points+? WHERE name=?',(pts,user))
    else:
        db.execute('INSERT INTO users (name,points) VALUES (?,?)',(user,pts))
    db.commit(); db.close()

def get_community_posts(area=None, limit=30):
    db = get_db()
    if area:
        rows = db.execute('SELECT * FROM community_posts WHERE area=? ORDER BY timestamp DESC LIMIT ?',(area,limit)).fetchall()
    else:
        rows = db.execute('SELECT * FROM community_posts ORDER BY timestamp DESC LIMIT ?',(limit,)).fetchall()
    db.close()
    return [dict(r) for r in rows]

def add_community_post(user, message, area, post_type='update'):
    db = get_db()
    db.execute('INSERT INTO community_posts (user,message,area,timestamp,post_type) VALUES (?,?,?,?,?)',
               (user,message,area,time.time(),post_type))
    db.commit(); db.close()

def like_post(post_id, user):
    db = get_db()
    try:
        db.execute('INSERT INTO community_likes (user_name,post_id) VALUES (?,?)',(user,post_id))
        db.execute('UPDATE community_posts SET likes=likes+1 WHERE id=?',(post_id,))
        db.commit(); result = True
    except: result = False
    db.close()
    return result