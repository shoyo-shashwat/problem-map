from flask import Flask, request, jsonify, render_template
from database import init_db, insert_issue, get_issues, get_summary, upvote_issue, get_db
from classifier import auto_tag, priority_score

app = Flask(__name__)
init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/report', methods=['POST'])
def report():
    data = request.json
    tag = auto_tag(data['description'])
    insert_issue(data['area'], data['description'], tag)
    return jsonify({'status': 'ok', 'tag': tag})

@app.route('/issues', methods=['GET'])
def issues():
    tag = request.args.get('tag', 'All')
    area = request.args.get('area', None)
    return jsonify(get_issues(tag, area))

@app.route('/summary', methods=['GET'])
def summary():
    return jsonify(get_summary())

@app.route('/upvote/<int:issue_id>', methods=['POST'])
def upvote(issue_id):
    upvote_issue(issue_id)
    return jsonify({'status': 'ok'})

@app.route('/map-data', methods=['GET'])
def map_data():
    db = get_db()
    rows = db.execute('''
        SELECT area, COUNT(*) as count
        FROM issues
        GROUP BY area
    ''').fetchall()
    db.close()

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

    result = []
    for area, count in rows:
        if area in AREA_COORDS:
            if count >= 8:   heat = 'high'
            elif count >= 4: heat = 'medium'
            else:            heat = 'low'
            result.append({
                'area': area,
                'count': count,
                'heat': heat,
                'lat': AREA_COORDS[area][0],
                'lng': AREA_COORDS[area][1],
            })
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)