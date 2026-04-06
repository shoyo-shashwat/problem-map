from flask import Flask, request, jsonify, render_template
from database import init_db, insert_issue, get_issues, upvote_issue, get_db, verify_issue, resolve_issue, add_points, seed_real_issues
from classifier import auto_tag
import math, time, base64, os

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

init_db()
seed_real_issues()

# ── ADMIN PASSWORD ────────────────────────────────────────────────────────────
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# ── ALL DELHI AREAS ───────────────────────────────────────────────────────────
AREA_COORDS = {
    # Central Delhi
    'Connaught Place':   [28.6315, 77.2167], 'Paharganj':         [28.6448, 77.2167],
    'Daryaganj':         [28.6417, 77.2353], 'Chandni Chowk':     [28.6506, 77.2303],
    'Karol Bagh':        [28.6514, 77.1907], 'Patel Nagar':       [28.6500, 77.1700],
    'Rajendra Place':    [28.6436, 77.1834], 'Sadar Bazar':       [28.6600, 77.2100],
    'Civil Lines':       [28.6800, 77.2250], 'Kamla Nagar':       [28.6850, 77.2050],
    # North Delhi
    'Rohini':            [28.7041, 77.1025], 'Pitampura':         [28.7007, 77.1311],
    'Model Town':        [28.7167, 77.1900], 'Shalimar Bagh':     [28.7167, 77.1667],
    'Burari':            [28.7470, 77.2100], 'Narela':            [28.8530, 77.0920],
    'Bawana':            [28.7980, 77.0410], 'Alipur':            [28.7970, 77.1390],
    'Mukherjee Nagar':   [28.7050, 77.2100], 'GTB Nagar':         [28.6970, 77.2050],
    'Adarsh Nagar':      [28.7130, 77.1780], 'Ashok Vihar':       [28.6970, 77.1720],
    'Wazirabad':         [28.7400, 77.2550], 'Bhalswa':           [28.7540, 77.1700],
    # South Delhi
    'Saket':             [28.5244, 77.2090], 'Vasant Kunj':       [28.5200, 77.1590],
    'Mehrauli':          [28.5244, 77.1855], 'Malviya Nagar':     [28.5355, 77.2068],
    'Hauz Khas':         [28.5494, 77.2001], 'Greater Kailash':   [28.5494, 77.2378],
    'Lajpat Nagar':      [28.5677, 77.2378], 'Kalkaji':           [28.5494, 77.2590],
    'Tughlakabad':       [28.4808, 77.2590], 'Okhla':             [28.5355, 77.2780],
    'Badarpur':          [28.5022, 77.2944], 'Sangam Vihar':      [28.5022, 77.2590],
    'Govindpuri':        [28.5355, 77.2590], 'Sarita Vihar':      [28.5300, 77.2900],
    'Jasola':            [28.5430, 77.2960], 'Madangir':          [28.5180, 77.2060],
    'Munirka':           [28.5580, 77.1760], 'RK Puram':          [28.5650, 77.1800],
    'Vasant Vihar':      [28.5670, 77.1600], 'Chirag Delhi':      [28.5270, 77.2160],
    'Sheikh Sarai':      [28.5280, 77.2150], 'Pushp Vihar':       [28.5190, 77.2130],
    'Neb Sarai':         [28.5040, 77.2010], 'Deoli':             [28.4980, 77.2160],
    # South West Delhi
    'Dwarka':            [28.5921, 77.0460], 'Janakpuri':         [28.6219, 77.0878],
    'Uttam Nagar':       [28.6219, 77.0560], 'Vikaspuri':         [28.6355, 77.0720],
    'Najafgarh':         [28.6090, 76.9800], 'Palam':             [28.5930, 77.0730],
    'Dabri':             [28.6150, 77.0870], 'Kakrola':           [28.6200, 77.0370],
    'Bindapur':          [28.6280, 77.0600], 'Nawada':            [28.6340, 77.0720],
    'Uttam Nagar East':  [28.6190, 77.0720], 'Dwarka Mor':        [28.6120, 77.0590],
    # West Delhi
    'Rajouri Garden':    [28.6447, 77.1220], 'Punjabi Bagh':      [28.6590, 77.1311],
    'Tilak Nagar':       [28.6355, 77.0990], 'Subhash Nagar':     [28.6355, 77.1167],
    'Peeragarhi':        [28.6770, 77.0780], 'Nangloi':           [28.6706, 77.0590],
    'Mundka':            [28.6840, 77.0340], 'Paschim Vihar':     [28.6670, 77.1050],
    'Madipur':           [28.6600, 77.1380], 'Tagore Garden':     [28.6390, 77.1170],
    'Ramesh Nagar':      [28.6420, 77.1390], 'Moti Nagar':        [28.6480, 77.1530],
    'Kirti Nagar':       [28.6540, 77.1530], 'Hari Nagar':        [28.6290, 77.1150],
    # East Delhi
    'Laxmi Nagar':       [28.6310, 77.2780], 'Preet Vihar':       [28.6355, 77.2944],
    'Shahdara':          [28.6706, 77.2944], 'Geeta Colony':      [28.6590, 77.2780],
    'Mayur Vihar':       [28.6090, 77.2944], 'Patparganj':        [28.6219, 77.3012],
    'Seelampur':         [28.6706, 77.3012], 'Welcome':           [28.6840, 77.2944],
    'Mustafabad':        [28.7167, 77.3012], 'Bhajanpura':        [28.7041, 77.2780],
    'Vishwas Nagar':     [28.6430, 77.2950], 'Pandav Nagar':      [28.6370, 77.2880],
    'Mandawali':         [28.6250, 77.3100], 'Anand Vihar':       [28.6470, 77.3150],
    'Karkardooma':       [28.6530, 77.3050], 'Dilshad Garden':    [28.6810, 77.3220],
    'Jhilmil':           [28.6630, 77.3100], 'Vivek Vihar':       [28.6710, 77.3150],
    # North East Delhi
    'Yamuna Vihar':      [28.7090, 77.2840], 'Karawal Nagar':     [28.7440, 77.3020],
    'Nand Nagri':        [28.7050, 77.3100], 'Brahmpuri':         [28.6980, 77.3000],
    'Gokulpuri':         [28.6960, 77.3050], 'Jaffrabad':         [28.6880, 77.2990],
    'Maujpur':           [28.6930, 77.2960], 'Khajuri Khas':      [28.7200, 77.2900],
}

NGO_REGISTRY = {
    "water":       {"name":"WaterAid India",                  "contact":"wateraid@example.org",            "phone":"+91-11-4052-4444", "focus":"Water & sanitation",      "icon":"💧","address":"Hauz Khas, New Delhi",       "lat":28.5494,"lng":77.2001},
    "garbage":     {"name":"Chintan Environmental Research",  "contact":"info@chintan-india.org",          "phone":"+91-11-2753-2346", "focus":"Waste management",         "icon":"♻️","address":"Shahdara, Delhi",           "lat":28.6706,"lng":77.2944},
    "pothole":     {"name":"Road Safety Network India",       "contact":"roads@rsni.org",                  "phone":"+91-98100-00001",  "focus":"Road safety",              "icon":"🛣️","address":"Connaught Place, Delhi",    "lat":28.6315,"lng":77.2167},
    "streetlight": {"name":"Delhi Power Citizens Forum",      "contact":"help@dpcf.in",                    "phone":"+91-11-2345-6789", "focus":"Electricity & lighting",   "icon":"💡","address":"Karol Bagh, Delhi",          "lat":28.6514,"lng":77.1907},
    "electricity": {"name":"Delhi Power Citizens Forum",      "contact":"help@dpcf.in",                    "phone":"+91-11-2345-6789", "focus":"Power issues",             "icon":"⚡","address":"Karol Bagh, Delhi",          "lat":28.6514,"lng":77.1907},
    "traffic":     {"name":"SaveLIFE Foundation",             "contact":"info@savelifefoundation.org",     "phone":"+91-22-4900-2220", "focus":"Road safety & traffic",    "icon":"🚦","address":"Lajpat Nagar, Delhi",       "lat":28.5677,"lng":77.2378},
    "noise":       {"name":"Awaaz Foundation",                "contact":"awaaz@awaazfoundation.org",       "phone":"+91-22-2369-7571", "focus":"Noise & air pollution",    "icon":"🔇","address":"Rohini, Delhi",              "lat":28.7041,"lng":77.1025},
    "sewage":      {"name":"Delhi Jal Board Citizens Help",   "contact":"citizen@djb.delhi.gov.in",        "phone":"1916",             "focus":"Drainage & sewage",        "icon":"🚰","address":"Dwarka, Delhi",              "lat":28.5921,"lng":77.0460},
    "tree":        {"name":"Delhi Tree Society",              "contact":"dts@delhitrees.org",              "phone":"+91-11-2300-0001", "focus":"Tree & green cover",       "icon":"🌳","address":"Mehrauli, Delhi",            "lat":28.5244,"lng":77.1855},
    "default":     {"name":"Delhi Citizen Helpline",          "contact":"pgrams@delhi.gov.in",             "phone":"1031",             "focus":"General civic issues",     "icon":"🏛️","address":"Connaught Place, Delhi",    "lat":28.6315,"lng":77.2167},
}

REWARDS = [
    {"id":1,  "title":"Metro Card Top-up ₹50",   "points":100, "icon":"🚇", "category":"Transport"},
    {"id":2,  "title":"Metro Card Top-up ₹100",  "points":180, "icon":"🚇", "category":"Transport"},
    {"id":3,  "title":"DTC Bus Pass (1 Day)",     "points":60,  "icon":"🚌", "category":"Transport"},
    {"id":4,  "title":"Paytm Cashback ₹25",       "points":80,  "icon":"💸", "category":"Cash"},
    {"id":5,  "title":"Paytm Cashback ₹50",       "points":140, "icon":"💸", "category":"Cash"},
    {"id":6,  "title":"Amazon Voucher ₹100",       "points":200, "icon":"🛒", "category":"Shopping"},
    {"id":7,  "title":"Swiggy Voucher ₹75",        "points":150, "icon":"🍔", "category":"Food"},
    {"id":8,  "title":"Plant a Tree (on behalf)",  "points":50,  "icon":"🌱", "category":"Green"},
    {"id":9,  "title":"Civic Hero Certificate",    "points":30,  "icon":"🏅", "category":"Recognition"},
]

# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/issues-page')
def issues_page():
    return render_template('issues.html')

@app.route('/leaderboard-page')
def leaderboard_page():
    return render_template('leaderboard.html')

@app.route('/redeem-page')
def redeem_page():
    return render_template('redeem.html')

@app.route('/areas')
def areas():
    return jsonify(sorted(AREA_COORDS.keys()))

@app.route('/report', methods=['POST'])
def report():
    try:
        if request.content_type and 'multipart' in request.content_type:
            user  = (request.form.get('user') or 'anonymous').strip() or 'anonymous'
            area  = (request.form.get('area') or '').strip()
            desc  = (request.form.get('description') or '').strip()
            lat   = request.form.get('lat')
            lng   = request.form.get('lng')
            severity = (request.form.get('severity') or 'medium').strip()
            landmark = (request.form.get('landmark') or '').strip()
            contact  = (request.form.get('contact') or '').strip()
            image_data = None
            if 'image' in request.files:
                f = request.files['image']
                if f and f.filename:
                    img_bytes = f.read()
                    mime = f.content_type or 'image/jpeg'
                    image_data = f'data:{mime};base64,{base64.b64encode(img_bytes).decode()}'
        else:
            data     = request.json or {}
            user     = (data.get('user') or 'anonymous').strip() or 'anonymous'
            area     = (data.get('area') or '').strip()
            desc     = (data.get('description') or '').strip()
            lat      = data.get('lat')
            lng      = data.get('lng')
            image_data = data.get('image')        # base64 data URI from JS FileReader
            severity = (data.get('severity') or 'medium').strip()
            landmark = (data.get('landmark') or '').strip()
            contact  = (data.get('contact') or '').strip()

        if not area or not desc:
            return jsonify({'error': 'Area and description required'}), 400
        if len(desc) < 10:
            return jsonify({'error': 'Description too short'}), 400

        try:    lat = float(lat) if lat else None
        except: lat = None
        try:    lng = float(lng) if lng else None
        except: lng = None

        tag = auto_tag(desc)
        insert_issue(area, desc, tag, user, lat, lng, image_data, severity, landmark, contact)
        add_points(user, 10)
        ngo = _get_ngo_for_tag(tag)
        return jsonify({'status': 'ok', 'tag': tag, 'points_earned': 10, 'ngo': ngo})

    except Exception as e:
        print("ERROR /report:", e)
        import traceback; traceback.print_exc()
        return jsonify({'error': 'Server error'}), 500

@app.route('/issues')
def issues():
    tf = request.args.get('tag',   '').strip().lower()
    af = request.args.get('area',  '').strip()
    sf = request.args.get('status','').strip().lower()
    q  = request.args.get('q',     '').strip().lower()
    all_i = get_issues()
    if tf: all_i = [i for i in all_i if i.get('tag','').lower() == tf]
    if af: all_i = [i for i in all_i if i.get('area','') == af]
    if sf: all_i = [i for i in all_i if (i.get('status') or 'open') == sf]
    if q:  all_i = [i for i in all_i if q in i.get('description','').lower()
                                      or q in i.get('area','').lower()
                                      or q in (i.get('tag') or '').lower()]
    return jsonify(all_i)

@app.route('/map-data')
def map_data():
    db = get_db()
    rows = db.execute('SELECT area, COUNT(*) as cnt FROM issues GROUP BY area').fetchall()
    db.close()
    result = []
    for row in rows:
        area, count = row['area'], row['cnt']
        coords = AREA_COORDS.get(area)
        if coords:
            heat = 'high' if count >= 8 else 'medium' if count >= 4 else 'low'
            result.append({'area': area, 'count': count, 'heat': heat,
                           'lat': coords[0], 'lng': coords[1]})
    return jsonify(result)

@app.route('/leaderboard')
def leaderboard():
    db = get_db()
    rows = db.execute('SELECT name, points FROM users ORDER BY points DESC LIMIT 10').fetchall()
    db.close()
    result = []
    for i, r in enumerate(rows):
        pts = r['points']
        lvl = 'Champion' if pts >= 500 else 'Active' if pts >= 200 else 'Rising' if pts >= 50 else 'Newcomer'
        result.append({'rank': i + 1, 'name': r['name'], 'points': pts, 'level': lvl})
    return jsonify(result)

@app.route('/upvote/<int:id>', methods=['POST'])
def upvote(id):
    d = request.json or {}
    upvote_issue(id)
    add_points(d.get('user', 'anonymous'), 2)
    return jsonify({'status': 'ok', 'points_earned': 2})

@app.route('/verify/<int:id>', methods=['POST'])
def verify(id):
    d = request.json or {}
    password = d.get('admin_password', '')
    if password != ADMIN_PASSWORD:
        return jsonify({'error': 'Incorrect admin password'}), 403
    verify_issue(id)
    add_points(d.get('user', 'anonymous'), 5)
    return jsonify({'status': 'verified', 'points_earned': 5})

@app.route('/resolve/<int:id>', methods=['POST'])
def resolve(id):
    d = request.json or {}
    user = d.get('user', 'anonymous')
    resolve_issue(id)
    add_points(user, 20)
    db = get_db()
    issue = db.execute('SELECT * FROM issues WHERE id=?', (id,)).fetchone()
    db.close()
    nearby = []
    if issue:
        lat = issue['lat'] or AREA_COORDS.get(issue['area'], [28.6139, 77.2090])[0]
        lng = issue['lng'] or AREA_COORDS.get(issue['area'], [28.6139, 77.2090])[1]
        nearby = _nearby_ngos(lat, lng)
    return jsonify({'status': 'resolved', 'points_earned': 20, 'nearby_ngos': nearby})

@app.route('/ngo/all')
def ngo_all():
    return jsonify(NGO_REGISTRY)

@app.route('/ngo/suggest')
def ngo_suggest():
    return jsonify(_get_ngo_for_tag(request.args.get('tag', '').strip().lower()))

@app.route('/ngo/nearby')
def ngo_nearby():
    try:
        lat = float(request.args.get('lat', 28.6139))
        lng = float(request.args.get('lng', 77.2090))
    except:
        lat, lng = 28.6139, 77.2090
    return jsonify(_nearby_ngos(lat, lng))

@app.route('/ngo/escalate/<int:id>', methods=['POST'])
def ngo_escalate(id):
    db = get_db()
    issue = db.execute('SELECT * FROM issues WHERE id=?', (id,)).fetchone()
    if not issue:
        db.close()
        return jsonify({'error': 'Not found'}), 404
    ngo = _get_ngo_for_tag(issue['tag'] or '')
    db.execute("UPDATE issues SET status='escalated' WHERE id=?", (id,))
    db.commit()
    db.close()
    return jsonify({'status': 'escalated', 'ngo': ngo})

@app.route('/rewards')
def rewards():
    return jsonify(REWARDS)

@app.route('/redeem', methods=['POST'])
def redeem():
    data = request.json or {}
    user = (data.get('user') or '').strip()
    rid  = data.get('reward_id')
    if not user:
        return jsonify({'error': 'Enter your name first'}), 400
    reward = next((r for r in REWARDS if r['id'] == rid), None)
    if not reward:
        return jsonify({'error': 'Reward not found'}), 404
    db = get_db()
    row = db.execute('SELECT points FROM users WHERE name=?', (user,)).fetchone()
    if not row:
        db.close()
        return jsonify({'error': 'User not found. Report some issues first!'}), 404
    if row['points'] < reward['points']:
        db.close()
        return jsonify({'error': f"Need {reward['points']} pts, you have {row['points']}"}), 400
    db.execute('UPDATE users SET points=points-? WHERE name=?', (reward['points'], user))
    db.commit()
    remaining = db.execute('SELECT points FROM users WHERE name=?', (user,)).fetchone()['points']
    db.close()
    return jsonify({'status': 'redeemed', 'reward': reward, 'remaining_points': remaining})

@app.route('/user/points')
def user_points():
    name = request.args.get('name', '').strip()
    if not name:
        return jsonify({'points': 0})
    db = get_db()
    row = db.execute('SELECT points FROM users WHERE name=?', (name,)).fetchone()
    db.close()
    return jsonify({'points': row['points'] if row else 0})

# ── HELPERS ───────────────────────────────────────────────────────────────────

def _get_ngo_for_tag(tag):
    tag = (tag or '').lower()
    for key in NGO_REGISTRY:
        if key != 'default' and key in tag:
            return {**NGO_REGISTRY[key], 'tag': key}
    return {**NGO_REGISTRY['default'], 'tag': 'general'}

def _nearby_ngos(lat, lng):
    ngos = []
    for key, ngo in NGO_REGISTRY.items():
        if key == 'default':
            continue
        d = math.sqrt((lat - ngo.get('lat', 28.6139))**2 + (lng - ngo.get('lng', 77.2090))**2)
        ngos.append({**ngo, 'tag': key, 'distance_km': round(d * 111, 1)})
    ngos.sort(key=lambda x: x['distance_km'])
    return ngos[:4]

if __name__ == '__main__':
    app.run(debug=True, port=5000)