from flask import Flask, request, jsonify, render_template
from database import (
    init_db, insert_issue, get_issues, get_summary,
    upvote_issue, get_db, verify_issue, resolve_issue, add_points
)
from classifier import auto_tag

app = Flask(__name__)
init_db()

@app.route('/')
def home():
    return render_template('index.html')

# ---------------- REPORT ----------------
@app.route('/report', methods=['POST'])
def report():
    data = request.json
    tag = auto_tag(data['description'])

    insert_issue(data['area'], data['description'], tag, data['user'])
    add_points(data['user'], 10)

    return jsonify({'status': 'ok', 'tag': tag})

# ---------------- GET ----------------
@app.route('/issues')
def issues():
    return jsonify(get_issues())

@app.route('/summary')
def summary():
    return jsonify(get_summary())

# ---------------- ACTIONS ----------------
@app.route('/upvote/<int:issue_id>', methods=['POST'])
def upvote(issue_id):
    upvote_issue(issue_id)
    add_points("anonymous", 2)
    return jsonify({'status': 'ok'})

@app.route('/verify/<int:issue_id>', methods=['POST'])
def verify(issue_id):
    verify_issue(issue_id)
    add_points("anonymous", 5)
    return jsonify({'status': 'verified'})

@app.route('/resolve/<int:issue_id>', methods=['POST'])
def resolve(issue_id):
    resolve_issue(issue_id)
    add_points("anonymous", 20)
    return jsonify({'status': 'resolved'})

# ---------------- MAP ----------------
@app.route('/map-data')
def map_data():
    db = get_db()
    rows = db.execute('SELECT area, COUNT(*) FROM issues GROUP BY area').fetchall()
    db.close()

    AREA_COORDS = {
        'Rohini': [28.7041, 77.1025],
        'Dwarka': [28.5921, 77.0460],
        'Janakpuri': [28.6219, 77.0878],
        'Lajpat Nagar': [28.5677, 77.2378],
        'Saket': [28.5244, 77.2090],
        'Karol Bagh': [28.6514, 77.1907],
        'Pitampura': [28.7007, 77.1311],
        'Vasant Kunj': [28.5200, 77.1590],
    }

    result = []
    for area, count in rows:
        if area in AREA_COORDS:
            heat = 'low'
            if count >= 8:
                heat = 'high'
            elif count >= 4:
                heat = 'medium'

            result.append({
                'area': area,
                'count': count,
                'heat': heat,
                'lat': AREA_COORDS[area][0],
                'lng': AREA_COORDS[area][1]
            })

    return jsonify(result)

# ---------------- LEADERBOARD ----------------
@app.route('/leaderboard')
def leaderboard():
    db = get_db()
    rows = db.execute('SELECT name, points FROM users ORDER BY points DESC LIMIT 10').fetchall()
    db.close()

    return jsonify([{'name': r[0], 'points': r[1]} for r in rows])

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)