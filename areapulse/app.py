from flask import Flask, request, jsonify, render_template
from database import (
    init_db, insert_issue, get_issues, get_summary,
    upvote_issue, get_db, verify_issue, resolve_issue, add_points
)
from classifier import auto_tag
from datetime import datetime

app = Flask(__name__)
init_db()

# ─────────────────────────────────────────
#  NGO REGISTRY
# ─────────────────────────────────────────
NGO_REGISTRY = {
    "water": {
        "name": "WaterAid India",
        "contact": "wateraid@example.org",
        "phone": "+91-11-4052-4444",
        "focus": "Water & sanitation issues",
        "icon": "💧"
    },
    "garbage": {
        "name": "Chintan Environmental Research",
        "contact": "info@chintan-india.org",
        "phone": "+91-11-2753-2346",
        "focus": "Waste management & recycling",
        "icon": "♻️"
    },
    "pothole": {
        "name": "Road Safety Network India",
        "contact": "roads@rsni.org",
        "phone": "+91-98100-00001",
        "focus": "Road safety & infrastructure",
        "icon": "🛣️"
    },
    "streetlight": {
        "name": "Delhi Power Citizens Forum",
        "contact": "help@dpcf.in",
        "phone": "+91-11-2345-6789",
        "focus": "Electricity & public lighting",
        "icon": "💡"
    },
    "electricity": {
        "name": "Delhi Power Citizens Forum",
        "contact": "help@dpcf.in",
        "phone": "+91-11-2345-6789",
        "focus": "Electricity & power issues",
        "icon": "⚡"
    },
    "traffic": {
        "name": "SaveLIFE Foundation",
        "contact": "info@savelifefoundation.org",
        "phone": "+91-22-4900-2220",
        "focus": "Road safety & traffic management",
        "icon": "🚦"
    },
    "noise": {
        "name": "Awaaz Foundation",
        "contact": "awaaz@awaazfoundation.org",
        "phone": "+91-22-2369-7571",
        "focus": "Noise & air pollution",
        "icon": "🔇"
    },
    "sewage": {
        "name": "Delhi Jal Board Citizens Help",
        "contact": "citizen@djb.delhi.gov.in",
        "phone": "1916",
        "focus": "Drainage & sewage issues",
        "icon": "🚰"
    },
    "tree": {
        "name": "Delhi Tree Society",
        "contact": "dts@delhitrees.org",
        "phone": "+91-11-2300-0001",
        "focus": "Tree & green cover issues",
        "icon": "🌳"
    },
    "default": {
        "name": "Delhi Citizen Helpline",
        "contact": "pgrams@delhi.gov.in",
        "phone": "1031",
        "focus": "General civic issues",
        "icon": "🏛️"
    }
}

AREA_COORDS = {
    'Rohini':       [28.7041, 77.1025],
    'Dwarka':       [28.5921, 77.0460],
    'Janakpuri':    [28.6219, 77.0878],
    'Lajpat Nagar': [28.5677, 77.2378],
    'Saket':        [28.5244, 77.2090],
    'Karol Bagh':   [28.6514, 77.1907],
    'Pitampura':    [28.7007, 77.1311],
    'Vasant Kunj':  [28.5200, 77.1590],
}

# ─────────────────────────────────────────
#  PAGES
# ─────────────────────────────────────────

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/issues-page')
def issues_page():
    return render_template('issues.html')

@app.route('/leaderboard-page')
def leaderboard_page():
    return render_template('leaderboard.html')

# ─────────────────────────────────────────
#  REPORT AN ISSUE
# ─────────────────────────────────────────

@app.route('/report', methods=['POST'])
def report():
    try:
        data = request.json
        user = (data.get('user') or 'anonymous').strip() or 'anonymous'
        area = (data.get('area') or '').strip()
        desc = (data.get('description') or '').strip()

        if not area or not desc:
            return jsonify({'error': 'Area and description are required'}), 400
        if len(desc) < 10:
            return jsonify({'error': 'Description too short — please be more specific'}), 400

        tag = auto_tag(desc)
        insert_issue(area, desc, tag, user)
        add_points(user, 10)

        ngo = _get_ngo_for_tag(tag)

        return jsonify({
            'status': 'ok',
            'tag': tag,
            'points_earned': 10,
            'ngo': ngo,
            'message': f'Issue reported! Tagged as "{tag}". +10 points added.'
        })

    except Exception as e:
        print("ERROR in /report:", e)
        return jsonify({'error': 'Server error. Please try again.'}), 500


# ─────────────────────────────────────────
#  GET ISSUES
# ─────────────────────────────────────────

@app.route('/issues')
def issues():
    tag_filter    = request.args.get('tag', '').strip().lower()
    area_filter   = request.args.get('area', '').strip()
    status_filter = request.args.get('status', '').strip().lower()
    query         = request.args.get('q', '').strip().lower()

    all_issues = get_issues()

    if tag_filter:
        all_issues = [i for i in all_issues if i.get('tag', '').lower() == tag_filter]
    if area_filter:
        all_issues = [i for i in all_issues if i.get('area', '') == area_filter]
    if status_filter:
        all_issues = [i for i in all_issues if (i.get('status') or 'open') == status_filter]
    if query:
        all_issues = [i for i in all_issues
                      if query in i.get('description', '').lower()
                      or query in i.get('area', '').lower()
                      or query in i.get('tag', '').lower()]

    return jsonify(all_issues)


# ─────────────────────────────────────────
#  SUMMARY / ANALYTICS
# ─────────────────────────────────────────

@app.route('/summary')
def summary():
    return jsonify(get_summary())


@app.route('/analytics')
def analytics():
    db = get_db()
    total    = db.execute('SELECT COUNT(*) FROM issues').fetchone()[0]
    open_c   = db.execute("SELECT COUNT(*) FROM issues WHERE status='open'").fetchone()[0]
    verified = db.execute("SELECT COUNT(*) FROM issues WHERE status='verified'").fetchone()[0]
    resolved = db.execute("SELECT COUNT(*) FROM issues WHERE status='resolved'").fetchone()[0]

    by_tag  = db.execute('SELECT tag, COUNT(*) as cnt FROM issues GROUP BY tag ORDER BY cnt DESC').fetchall()
    by_area = db.execute('SELECT area, COUNT(*) as cnt FROM issues GROUP BY area ORDER BY cnt DESC').fetchall()
    top_reporters = db.execute('SELECT name, points FROM users ORDER BY points DESC LIMIT 5').fetchall()
    db.close()

    return jsonify({
        'totals': {'total': total, 'open': open_c, 'verified': verified, 'resolved': resolved},
        'by_tag':  [{'tag': r[0], 'count': r[1]} for r in by_tag],
        'by_area': [{'area': r[0], 'count': r[1]} for r in by_area],
        'top_reporters': [{'name': r[0], 'points': r[1]} for r in top_reporters]
    })


# ─────────────────────────────────────────
#  ACTIONS
# ─────────────────────────────────────────

@app.route('/upvote/<int:issue_id>', methods=['POST'])
def upvote(issue_id):
    data = request.json or {}
    user = data.get('user', 'anonymous')
    upvote_issue(issue_id)
    add_points(user, 2)
    return jsonify({'status': 'ok', 'points_earned': 2})


@app.route('/verify/<int:issue_id>', methods=['POST'])
def verify(issue_id):
    data = request.json or {}
    user = data.get('user', 'anonymous')
    verify_issue(issue_id)
    add_points(user, 5)
    return jsonify({'status': 'verified', 'points_earned': 5})


@app.route('/resolve/<int:issue_id>', methods=['POST'])
def resolve(issue_id):
    data = request.json or {}
    user = data.get('user', 'anonymous')
    resolve_issue(issue_id)
    add_points(user, 20)
    return jsonify({'status': 'resolved', 'points_earned': 20})


# ─────────────────────────────────────────
#  MAP DATA
# ─────────────────────────────────────────

@app.route('/map-data')
def map_data():
    db = get_db()
    rows = db.execute('SELECT area, COUNT(*) FROM issues GROUP BY area').fetchall()
    db.close()

    result = []
    for row in rows:
        area, count = row[0], row[1]
        if area in AREA_COORDS:
            heat = 'low'
            if count >= 8:   heat = 'high'
            elif count >= 4: heat = 'medium'
            result.append({
                'area': area, 'count': count, 'heat': heat,
                'lat': AREA_COORDS[area][0], 'lng': AREA_COORDS[area][1]
            })
    return jsonify(result)


# ─────────────────────────────────────────
#  LEADERBOARD
# ─────────────────────────────────────────

@app.route('/leaderboard')
def leaderboard():
    db = get_db()
    rows = db.execute('SELECT name, points FROM users ORDER BY points DESC LIMIT 10').fetchall()
    db.close()

    result = []
    for i, r in enumerate(rows):
        points = r[1]
        if points >= 500:   level = 'Champion'
        elif points >= 200: level = 'Active'
        elif points >= 50:  level = 'Rising'
        else:               level = 'Newcomer'
        result.append({'rank': i + 1, 'name': r[0], 'points': points, 'level': level})

    return jsonify(result)


# ─────────────────────────────────────────
#  NGO ENDPOINTS
# ─────────────────────────────────────────

@app.route('/ngo/suggest')
def ngo_suggest():
    tag = request.args.get('tag', '').strip().lower()
    ngo = _get_ngo_for_tag(tag)
    return jsonify(ngo)


@app.route('/ngo/all')
def ngo_all():
    return jsonify(NGO_REGISTRY)


@app.route('/ngo/escalate/<int:issue_id>', methods=['POST'])
def ngo_escalate(issue_id):
    db = get_db()
    issue = db.execute('SELECT * FROM issues WHERE id=?', (issue_id,)).fetchone()

    if not issue:
        db.close()
        return jsonify({'error': 'Issue not found'}), 404

    tag = issue['tag'] if issue['tag'] else ''
    ngo = _get_ngo_for_tag(tag)

    try:
        db.execute("UPDATE issues SET status='escalated' WHERE id=?", (issue_id,))
        db.commit()
    except Exception as e:
        print("Escalate DB error:", e)
    db.close()

    print(f"[NGO ESCALATE] Issue #{issue_id} → {ngo['name']} at {ngo['contact']}")
    return jsonify({
        'status': 'escalated',
        'issue_id': issue_id,
        'ngo': ngo,
        'message': f"Issue escalated to {ngo['name']}. They will be notified."
    })


# ─────────────────────────────────────────
#  SEARCH
# ─────────────────────────────────────────

@app.route('/search')
def search():
    q = request.args.get('q', '').strip().lower()
    if not q:
        return jsonify({'error': 'Query required'}), 400

    all_issues = get_issues()
    matched = [i for i in all_issues
               if q in i.get('description', '').lower()
               or q in i.get('tag', '').lower()
               or q in i.get('area', '').lower()]

    area_counts = {}
    for issue in matched:
        a = issue.get('area', 'Unknown')
        area_counts[a] = area_counts.get(a, 0) + 1

    ngo = _get_ngo_for_tag(q)
    return jsonify({
        'query': q, 'total': len(matched), 'issues': matched,
        'areas': [{'area': k, 'count': v} for k, v in sorted(area_counts.items(), key=lambda x: -x[1])],
        'ngo': ngo
    })


# ─────────────────────────────────────────
#  HELPER
# ─────────────────────────────────────────

def _get_ngo_for_tag(tag: str) -> dict:
    tag = (tag or '').lower()
    for key in NGO_REGISTRY:
        if key != 'default' and key in tag:
            return {**NGO_REGISTRY[key], 'tag': key}
    return {**NGO_REGISTRY['default'], 'tag': 'general'}


if __name__ == '__main__':
    app.run(debug=True, port=5000)