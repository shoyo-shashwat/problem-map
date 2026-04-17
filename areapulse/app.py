from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from database import (
    init_db, insert_issue, get_issues, get_issues_by_user, upvote_issue, get_db,
    verify_issue, resolve_issue, escalate_issue, add_points, seed_real_issues,
    get_ngos, get_gov_agencies, get_nearby_ngos, get_user_stats,
    get_community_posts, add_community_post, like_post
)
from classifier import auto_tag
import math, time, base64, os
import psycopg2.extras

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'problemmap-secret-2025')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

init_db()
seed_real_issues()

AREA_COORDS = {
    'Connaught Place':[28.6315,77.2167],'Paharganj':[28.6448,77.2167],'Daryaganj':[28.6417,77.2353],
    'Chandni Chowk':[28.6506,77.2303],'Karol Bagh':[28.6514,77.1907],'Patel Nagar':[28.6500,77.1700],
    'Rajendra Place':[28.6436,77.1834],'Sadar Bazar':[28.6600,77.2100],'Civil Lines':[28.6800,77.2250],
    'Kamla Nagar':[28.6850,77.2050],'Rohini':[28.7041,77.1025],'Pitampura':[28.7007,77.1311],
    'Model Town':[28.7167,77.1900],'Shalimar Bagh':[28.7167,77.1667],'Burari':[28.7470,77.2100],
    'Narela':[28.8530,77.0920],'Bawana':[28.7980,77.0410],'Alipur':[28.7970,77.1390],
    'Mukherjee Nagar':[28.7050,77.2100],'GTB Nagar':[28.6970,77.2050],'Adarsh Nagar':[28.7130,77.1780],
    'Ashok Vihar':[28.6970,77.1720],'Wazirabad':[28.7400,77.2550],'Bhalswa':[28.7540,77.1700],
    'Saket':[28.5244,77.2090],'Vasant Kunj':[28.5200,77.1590],'Mehrauli':[28.5244,77.1855],
    'Malviya Nagar':[28.5355,77.2068],'Hauz Khas':[28.5494,77.2001],'Greater Kailash':[28.5494,77.2378],
    'Lajpat Nagar':[28.5677,77.2378],'Kalkaji':[28.5494,77.2590],'Tughlakabad':[28.4808,77.2590],
    'Okhla':[28.5355,77.2780],'Badarpur':[28.5022,77.2944],'Sangam Vihar':[28.5022,77.2590],
    'Govindpuri':[28.5355,77.2590],'Sarita Vihar':[28.5300,77.2900],'Jasola':[28.5430,77.2960],
    'Madangir':[28.5180,77.2060],'Munirka':[28.5580,77.1760],'RK Puram':[28.5650,77.1800],
    'Vasant Vihar':[28.5670,77.1600],'Chirag Delhi':[28.5270,77.2160],'Pushp Vihar':[28.5190,77.2130],
    'Deoli':[28.4980,77.2160],'Dwarka':[28.5921,77.0460],'Janakpuri':[28.6219,77.0878],
    'Uttam Nagar':[28.6219,77.0560],'Vikaspuri':[28.6355,77.0720],'Najafgarh':[28.6090,76.9800],
    'Palam':[28.5930,77.0730],'Dabri':[28.6150,77.0870],'Kakrola':[28.6200,77.0370],
    'Bindapur':[28.6280,77.0600],'Nawada':[28.6340,77.0720],'Uttam Nagar East':[28.6190,77.0720],
    'Dwarka Mor':[28.6120,77.0590],'Rajouri Garden':[28.6447,77.1220],'Punjabi Bagh':[28.6590,77.1311],
    'Tilak Nagar':[28.6355,77.0990],'Subhash Nagar':[28.6355,77.1167],'Peeragarhi':[28.6770,77.0780],
    'Nangloi':[28.6706,77.0590],'Mundka':[28.6840,77.0340],'Paschim Vihar':[28.6670,77.1050],
    'Madipur':[28.6600,77.1380],'Tagore Garden':[28.6390,77.1170],'Ramesh Nagar':[28.6420,77.1390],
    'Moti Nagar':[28.6480,77.1530],'Kirti Nagar':[28.6540,77.1530],'Hari Nagar':[28.6290,77.1150],
    'Laxmi Nagar':[28.6310,77.2780],'Preet Vihar':[28.6355,77.2944],'Shahdara':[28.6706,77.2944],
    'Geeta Colony':[28.6590,77.2780],'Mayur Vihar':[28.6090,77.2944],'Patparganj':[28.6219,77.3012],
    'Seelampur':[28.6706,77.3012],'Welcome':[28.6840,77.2944],'Mustafabad':[28.7167,77.3012],
    'Bhajanpura':[28.7041,77.2780],'Vishwas Nagar':[28.6430,77.2950],'Pandav Nagar':[28.6370,77.2880],
    'Mandawali':[28.6250,77.3100],'Anand Vihar':[28.6470,77.3150],'Karkardooma':[28.6530,77.3050],
    'Dilshad Garden':[28.6810,77.3220],'Jhilmil':[28.6630,77.3100],'Vivek Vihar':[28.6710,77.3150],
    'Yamuna Vihar':[28.7090,77.2840],'Karawal Nagar':[28.7440,77.3020],'Nand Nagri':[28.7050,77.3100],
    'Brahmpuri':[28.6980,77.3000],'Gokulpuri':[28.6960,77.3050],'Jaffrabad':[28.6880,77.2990],
    'Maujpur':[28.6930,77.2960],'Khajuri Khas':[28.7200,77.2900],
}

# ── AUTH ──────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        if not name or len(name) < 2:
            return render_template('login.html', error='Please enter a valid name (at least 2 characters).')
        if len(name) > 50:
            return render_template('login.html', error='Name too long (max 50 characters).')
        session['user'] = name
        add_points(name, 0)  # ensure user row exists
        return redirect(url_for('home'))
    if 'user' in session:
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# ── PAGES ─────────────────────────────────────────────
@app.route('/')
def home():
    return render_template('index.html', current_user=session.get('user'))

@app.route('/issues-page')
def issues_page():
    return render_template('issues.html', current_user=session.get('user'))

@app.route('/my-issues')
def my_issues():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('my_issues.html', current_user=session['user'])

@app.route('/reputation')
def reputation():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('reputation.html', current_user=session['user'])

@app.route('/ngo-page')
def ngo_page():
    return render_template('ngos.html', current_user=session.get('user'))

@app.route('/community-page')
def community_page():
    return render_template('community.html', current_user=session.get('user'))

# ── API ────────────────────────────────────────────────
@app.route('/areas')
def areas():
    return jsonify(sorted(AREA_COORDS.keys()))

@app.route('/report', methods=['POST'])
def report():
    try:
        if request.content_type and 'multipart' in request.content_type:
            user = (request.form.get('user') or session.get('user') or 'anonymous').strip() or 'anonymous'
            area = (request.form.get('area') or '').strip()
            desc = (request.form.get('description') or '').strip()
            lat  = request.form.get('lat', type=float)
            lng  = request.form.get('lng', type=float)
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
            data = request.json or {}
            user = (data.get('user') or session.get('user') or 'anonymous').strip() or 'anonymous'
            area = (data.get('area') or '').strip()
            desc = (data.get('description') or '').strip()
            lat  = data.get('lat'); lng = data.get('lng')
            image_data = data.get('image')
            severity = (data.get('severity') or 'medium').strip()
            landmark = (data.get('landmark') or '').strip()
            contact  = (data.get('contact') or '').strip()

        if not area or not desc:
            return jsonify({'error': 'Area and description required'}), 400
        if len(desc) < 10:
            return jsonify({'error': 'Description too short'}), 400
        try: lat = float(lat) if lat else None
        except: lat = None
        try: lng = float(lng) if lng else None
        except: lng = None
        if lat is None or lng is None:
            coords = AREA_COORDS.get(area)
            if coords: lat, lng = coords[0], coords[1]

        tag = auto_tag(desc)
        insert_issue(area, desc, tag, user, lat, lng, image_data, severity, landmark, contact)
        add_points(user, 10)
        nearby = get_nearby_ngos(lat or 28.6139, lng or 77.2090, tag=tag, limit=5) if lat else []
        return jsonify({'status': 'ok', 'tag': tag, 'points_earned': 10, 'nearby_ngos': nearby})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': 'Server error'}), 500

@app.route('/issues')
def issues():
    tf = request.args.get('tag', '').strip().lower()
    af = request.args.get('area', '').strip()
    sf = request.args.get('status', '').strip().lower()
    q  = request.args.get('q', '').strip().lower()
    all_i = get_issues()
    if tf: all_i = [i for i in all_i if i.get('tag', '').lower() == tf]
    if af: all_i = [i for i in all_i if i.get('area', '') == af]
    if sf: all_i = [i for i in all_i if (i.get('status') or 'open') == sf]
    if q:  all_i = [i for i in all_i if q in i.get('description', '').lower() or q in i.get('area', '').lower() or q in (i.get('tag') or '').lower()]
    return jsonify(all_i)

@app.route('/my-issues-data')
def my_issues_data():
    user = request.args.get('user', '').strip() or session.get('user', '')
    if not user:
        return jsonify([])
    return jsonify(get_issues_by_user(user))

@app.route('/map-data')
def map_data():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT area, COUNT(*) as cnt FROM issues GROUP BY area')
    rows = cur.fetchall()
    db.close()
    result = []
    for row in rows:
        area, count = row['area'], row['cnt']
        coords = AREA_COORDS.get(area)
        if coords:
            heat = 'high' if count >= 8 else 'medium' if count >= 4 else 'low'
            result.append({'area': area, 'count': count, 'heat': heat, 'lat': coords[0], 'lng': coords[1]})
    return jsonify(result)

@app.route('/upvote/<int:id>', methods=['POST'])
def upvote(id):
    d = request.json or {}
    user = d.get('user') or session.get('user') or 'anonymous'
    upvote_issue(id)
    add_points(user, 2)
    return jsonify({'status': 'ok', 'points_earned': 2})

@app.route('/verify/<int:id>', methods=['POST'])
def verify(id):
    d = request.json or {}
    if d.get('admin_password', '') != ADMIN_PASSWORD:
        return jsonify({'error': 'Incorrect admin password'}), 403
    verify_issue(id)
    add_points(d.get('user', 'anonymous'), 5)
    return jsonify({'status': 'verified', 'points_earned': 5})

@app.route('/resolve/<int:id>', methods=['POST'])
def resolve(id):
    d = request.json or {}
    user = d.get('user') or session.get('user') or 'anonymous'
    assigned_to = d.get('assigned_to') or None
    resolve_issue(id, assigned_to=assigned_to)
    add_points(user, 20)
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT * FROM issues WHERE id=%s', (id,))
    issue = cur.fetchone()
    db.close()
    nearby = []
    if issue:
        lat = issue.get('lat') or AREA_COORDS.get(issue.get('area'), [28.6139, 77.2090])[0]
        lng = issue.get('lng') or AREA_COORDS.get(issue.get('area'), [28.6139, 77.2090])[1]
        nearby = get_nearby_ngos(lat, lng, tag=issue.get('tag'), limit=4)
    return jsonify({'status': 'resolved', 'points_earned': 20, 'nearby_ngos': nearby})

@app.route('/ngo/all')
def ngo_all():
    tag = request.args.get('tag', '').strip() or None
    area = request.args.get('area', '').strip() or None
    sort = request.args.get('sort', 'resolved')
    return jsonify(get_ngos(tag_filter=tag, area_filter=area, sort_by=sort))

@app.route('/ngo/nearby')
def ngo_nearby():
    try: lat, lng = float(request.args.get('lat', 28.6139)), float(request.args.get('lng', 77.2090))
    except: lat, lng = 28.6139, 77.2090
    tag = request.args.get('tag', '').strip() or None
    return jsonify(get_nearby_ngos(lat, lng, tag=tag, limit=8))

@app.route('/ngo/escalate/<int:id>', methods=['POST'])
def ngo_escalate(id):
    d = request.json or {}
    assigned_to = d.get('assigned_to') or None
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT * FROM issues WHERE id=%s', (id,))
    issue = cur.fetchone()
    db.close()
    if not issue:
        return jsonify({'error': 'Not found'}), 404
    escalate_issue(id, assigned_to=assigned_to)
    return jsonify({'status': 'escalated'})

@app.route('/gov/all')
def gov_all():
    tag = request.args.get('tag', '').strip() or None
    area = request.args.get('area', '').strip() or None
    return jsonify(get_gov_agencies(tag_filter=tag, area_filter=area))

@app.route('/user/stats')
def user_stats():
    name = request.args.get('name', '').strip() or session.get('user', '')
    if not name:
        return jsonify({'points': 0, 'total_reported': 0, 'total_resolved': 0})
    stats = get_user_stats(name)
    pts = stats['points']
    if pts >= 500:
        level = 'Civic Hero'
    elif pts >= 200:
        level = 'Contributor'
    elif pts >= 50:
        level = 'Active Member'
    else:
        level = 'Newbie'
    stats['level'] = level
    stats['name'] = name
    return jsonify(stats)

@app.route('/user/points')
def user_points():
    name = request.args.get('name', '').strip() or session.get('user', '')
    if not name:
        return jsonify({'points': 0})
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT points FROM users WHERE name=%s', (name,))
    row = cur.fetchone()
    db.close()
    return jsonify({'points': row['points'] if row else 0})

@app.route('/community/posts')
def community_posts():
    area = request.args.get('area', '').strip() or None
    return jsonify(get_community_posts(area=area, limit=30))

@app.route('/community/post', methods=['POST'])
def community_post():
    d = request.json or {}
    user = (d.get('user') or session.get('user') or '').strip()
    message = (d.get('message') or '').strip()
    area = (d.get('area') or 'Delhi').strip()
    ptype = (d.get('type') or 'update').strip()
    if not user or not message:
        return jsonify({'error': 'Name and message required'}), 400
    if len(message) < 5:
        return jsonify({'error': 'Message too short'}), 400
    add_community_post(user, message, area, ptype)
    add_points(user, 3)
    return jsonify({'status': 'ok', 'points_earned': 3})

@app.route('/community/like/<int:post_id>', methods=['POST'])
def community_like(post_id):
    d = request.json or {}
    user = (d.get('user') or session.get('user') or '').strip()
    if not user:
        return jsonify({'error': 'Login required'}), 400
    ok = like_post(post_id, user)
    if not ok:
        return jsonify({'error': 'Already liked'}), 400
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)