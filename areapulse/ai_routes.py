from flask import Blueprint, request, jsonify, session
from ai_assistant import (
    analyze_report, chat as ai_chat,
    get_most_polluted, compare_areas, get_map_summary
)
from database import get_db, add_points
import psycopg2.extras
import time

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')


def init_ai_tables():
    db  = get_db()
    cur = db.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS spam_reports (
            id                    SERIAL PRIMARY KEY,
            area                  TEXT,
            description           TEXT,
            tag                   TEXT,
            "user"                TEXT,
            timestamp             REAL,
            spam_reason           TEXT,
            confidence            REAL,
            status                TEXT DEFAULT 'pending',
            corrected_description TEXT,
            spelling_corrections  TEXT
        )
    """)
    db.commit()
    db.close()


@ai_bp.route('/analyze-report', methods=['POST'])
def analyze_report_route():
    data = request.json or {}
    area = (data.get('area')        or '').strip()
    desc = (data.get('description') or '').strip()
    user = (data.get('user')        or session.get('user') or 'anonymous').strip()

    if not area or not desc:
        return jsonify({'error': 'area and description required'}), 400

    result = analyze_report(area, desc, user)

    if result['is_spam']:
        db  = get_db()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO spam_reports
              (area, description, tag, "user", timestamp,
               spam_reason, confidence, corrected_description, spelling_corrections)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            area, desc,
            result.get('suggested_tag', 'spam'),
            user, time.time(),
            result['spam_reason'],
            result['confidence'],
            result['corrected_description'],
            ', '.join(result['spelling_corrections'])
        ))
        db.commit()
        db.close()
        return jsonify({
            'status':     'spam',
            'reason':     result['spam_reason'],
            'confidence': result['confidence'],
            'verdict':    result['llm_verdict'],
        }), 200

    return jsonify({
        'status':                'clean',
        'corrected_description': result['corrected_description'],
        'spelling_corrections':  result['spelling_corrections'],
        'suggested_tag':         result['suggested_tag'],
        'verdict':               result['llm_verdict'],
        'confidence':            result['confidence'],
    }), 200


@ai_bp.route('/chat', methods=['POST'])
def chat_route():
    data    = request.json or {}
    message = (data.get('message') or '').strip()
    history = data.get('history', [])

    if not message:
        return jsonify({'error': 'message required'}), 400

    response = ai_chat(message, history=history)
    return jsonify(response)


@ai_bp.route('/hotspots')
def hotspots():
    tag   = request.args.get('tag')   or None
    limit = int(request.args.get('limit', 5))
    return jsonify(get_most_polluted(limit=limit, tag=tag))


@ai_bp.route('/compare', methods=['POST'])
def compare():
    data  = request.json or {}
    areas = data.get('areas', [])
    if not areas or len(areas) < 2:
        return jsonify({'error': 'Provide at least 2 areas'}), 400
    return jsonify(compare_areas(areas))


@ai_bp.route('/map-summary')
def map_summary():
    return jsonify(get_map_summary())


@ai_bp.route('/spam-queue')
def spam_queue():
    db  = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT * FROM spam_reports
        WHERE status = 'pending'
        ORDER BY timestamp DESC
        LIMIT 50
    """)
    rows = cur.fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@ai_bp.route('/spam-action/<int:report_id>', methods=['POST'])
def spam_action(report_id):
    data   = request.json or {}
    action = data.get('action')

    db  = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT * FROM spam_reports WHERE id=%s', (report_id,))
    row = cur.fetchone()

    if not row:
        db.close()
        return jsonify({'error': 'Not found'}), 404

    cur2 = db.cursor()
    if action == 'approve':
        cur2.execute("""
            INSERT INTO issues
              (area, description, tag, "user", timestamp, status)
            VALUES (%s, %s, %s, %s, %s, 'open')
        """, (
            row['area'],
            row['corrected_description'] or row['description'],
            row['tag'], row['user'], row['timestamp']
        ))
        cur2.execute("UPDATE spam_reports SET status='approved' WHERE id=%s", (report_id,))
    elif action == 'delete':
        cur2.execute("UPDATE spam_reports SET status='deleted' WHERE id=%s", (report_id,))
    else:
        db.close()
        return jsonify({'error': "action must be 'approve' or 'delete'"}), 400

    db.commit()
    db.close()
    return jsonify({'status': action + 'd'})