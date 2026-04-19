import os, re, json, math, time
from difflib import get_close_matches
from database import get_db
import psycopg2.extras

try:
    import anthropic
    _client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY', ''))
    ANTHROPIC_AVAILABLE = bool(os.environ.get('ANTHROPIC_API_KEY'))
except ImportError:
    ANTHROPIC_AVAILABLE = False
    _client = None

MODEL = 'claude-sonnet-4-20250514'

KNOWN_TAGS = ['pothole', 'water', 'garbage', 'streetlight', 'traffic',
              'sewage', 'electricity', 'noise', 'tree', 'other']

KNOWN_WORDS = KNOWN_TAGS + [
    'road', 'drain', 'pipe', 'flood', 'leak', 'waste', 'trash',
    'broken', 'damaged', 'blocked', 'overflow', 'smell', 'stench', 'accident',
    'signal', 'junction', 'crossing', 'park', 'colony', 'sector', 'market',
    'metro', 'bus', 'stop', 'light', 'pole', 'wire', 'transformer', 'branch',
    'fallen', 'construction', 'drilling', 'loud', 'speaker', 'mosquito',
    'rat', 'rodent', 'filth', 'litter', 'footpath', 'pavement', 'crater',
    'puddle', 'waterlog', 'batti', 'nali', 'kachra', 'bijli', 'pani',
]

SPAM_PATTERNS = [
    r'\b(test|testing|asdf|qwerty|hello world|dummy|fake|abc123)\b',
    r'^.{0,5}$',
    r'(.)\1{5,}',
    r'\b(xxx|lol|haha|blah)\b',
    r'^\s*(na|n/a|none|nil|no issue)\s*$',
]

FRAUD_KEYWORDS = [
    'money', 'cash', 'bribe', 'pay me', 'send money', 'reward', 'prize',
    'click here', 'whatsapp', 'telegram', 'instagram', 'follow', 'subscribe',
    'loan', 'insurance', 'investment', 'crypto', 'bitcoin',
]


def correct_spelling(text: str) -> tuple:
    words   = re.findall(r'\b[a-zA-Z]+\b', text)
    result  = text
    changes = []
    for w in words:
        if len(w) < 4:
            continue
        lower = w.lower()
        if lower in KNOWN_WORDS:
            continue
        matches = get_close_matches(lower, KNOWN_WORDS, n=1, cutoff=0.75)
        if matches and matches[0] != lower:
            corrected = matches[0]
            result    = re.sub(r'\b' + re.escape(w) + r'\b', corrected, result,
                               count=1, flags=re.IGNORECASE)
            changes.append(f"'{w}' → '{corrected}'")
    return result, changes


def _rule_based_spam(text: str) -> tuple:
    t = text.lower().strip()
    for pat in SPAM_PATTERNS:
        if re.search(pat, t, re.IGNORECASE):
            return True, 'Pattern match: generic/empty content'
    for kw in FRAUD_KEYWORDS:
        if kw in t:
            return True, f"Fraud keyword detected: '{kw}'"
    non_alpha = sum(1 for c in t if not c.isalpha() and not c.isspace())
    if len(t) > 0 and non_alpha / len(t) > 0.5:
        return True, 'Excessive special characters'
    return False, ''


def analyze_report(area: str, description: str, user: str) -> dict:
    corrected, corrections = correct_spelling(description)

    rule_spam, rule_reason = _rule_based_spam(description)
    if rule_spam:
        return {
            'is_spam':               True,
            'spam_reason':           rule_reason,
            'confidence':            0.95,
            'corrected_description': corrected,
            'spelling_corrections':  corrections,
            'suggested_tag':         'spam',
            'llm_verdict':           f'Auto-flagged by rule engine: {rule_reason}',
        }

    if not ANTHROPIC_AVAILABLE or not _client:
        return {
            'is_spam':               False,
            'spam_reason':           '',
            'confidence':            0.7,
            'corrected_description': corrected,
            'spelling_corrections':  corrections,
            'suggested_tag':         _fallback_tag(corrected),
            'llm_verdict':           'Rule engine passed (LLM unavailable)',
        }

    prompt = f"""You are a civic issue fraud detection system for Delhi.

Analyse this submitted report:
Area: {area}
User: {user}
Description: "{description}"

Respond ONLY in this exact JSON format (no markdown, no preamble):
{{
  "is_spam": true/false,
  "spam_reason": "short reason or empty string",
  "confidence": 0.0-1.0,
  "suggested_tag": "one of: pothole/water/garbage/streetlight/traffic/sewage/electricity/noise/tree/other/spam",
  "verdict": "1-sentence explanation"
}}

Flag as spam if:
- Content is gibberish, test data, or meaningless
- Contains commercial/promotional content
- Describes something that is not a civic issue
- Appears to be a duplicate attempt or abuse
- Is clearly fictional or impossible"""

    try:
        resp = _client.messages.create(
            model=MODEL,
            max_tokens=300,
            messages=[{'role': 'user', 'content': prompt}]
        )
        raw  = resp.content[0].text.strip()
        data = json.loads(raw)
        return {
            'is_spam':               bool(data.get('is_spam', False)),
            'spam_reason':           data.get('spam_reason', ''),
            'confidence':            float(data.get('confidence', 0.8)),
            'corrected_description': corrected,
            'spelling_corrections':  corrections,
            'suggested_tag':         data.get('suggested_tag', 'other'),
            'llm_verdict':           data.get('verdict', ''),
        }
    except Exception as e:
        return {
            'is_spam':               False,
            'spam_reason':           '',
            'confidence':            0.6,
            'corrected_description': corrected,
            'spelling_corrections':  corrections,
            'suggested_tag':         _fallback_tag(corrected),
            'llm_verdict':           f'LLM error ({e}); rule engine passed',
        }


def _fallback_tag(text: str) -> str:
    from classifier import auto_tag
    return auto_tag(text)


def get_area_coords() -> dict:
    try:
        from app import AREA_COORDS
        return AREA_COORDS
    except Exception:
        return {}


def get_map_summary() -> dict:
    db  = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT area,
               COUNT(*) as total,
               SUM(CASE WHEN severity='high'   THEN 1 ELSE 0 END) as high_count,
               SUM(CASE WHEN status='resolved' THEN 1 ELSE 0 END) as resolved,
               SUM(upvotes) as total_upvotes
        FROM issues
        GROUP BY area
        ORDER BY total DESC
    """)
    area_rows = cur.fetchall()

    cur.execute('SELECT tag, COUNT(*) as cnt FROM issues GROUP BY tag ORDER BY cnt DESC')
    tag_rows  = cur.fetchall()

    cur.execute('SELECT status, COUNT(*) as cnt FROM issues GROUP BY status')
    status_rows = cur.fetchall()

    db.close()

    coords = get_area_coords()
    areas  = []
    for r in area_rows:
        a = dict(r)
        c = coords.get(a['area'])
        if c:
            a['lat'], a['lng'] = c
            total    = a['total'] or 1
            a['heat'] = 'high' if a['total'] >= 8 else 'medium' if a['total'] >= 4 else 'low'
            a['pollution_score'] = round(
                (a['high_count'] * 3 + (a['total_upvotes'] or 0) * 0.5) / total, 2
            )
            areas.append(a)

    return {
        'areas':          areas,
        'tag_breakdown':  [dict(r) for r in tag_rows],
        'status_summary': [dict(r) for r in status_rows],
        'total_issues':   sum(r['total'] for r in area_rows),
    }


def compare_areas(area_names: list) -> list:
    db  = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    result = []
    for area in area_names:
        cur.execute("""
            SELECT
              COUNT(*) as total,
              SUM(CASE WHEN severity='high' THEN 1 ELSE 0 END) as high_severity,
              SUM(CASE WHEN status='resolved' THEN 1 ELSE 0 END) as resolved,
              SUM(CASE WHEN status='open'     THEN 1 ELSE 0 END) as open_issues,
              SUM(upvotes) as upvotes,
              MAX(timestamp) as last_report,
              MODE() WITHIN GROUP (ORDER BY tag) as most_common_tag
            FROM issues WHERE area=%s
        """, (area,))
        row = cur.fetchone()
        if row:
            d = dict(row)
            d['area']            = area
            d['total']           = d['total'] or 0
            d['resolution_rate'] = (
                round(d['resolved'] / d['total'] * 100, 1) if d['total'] else 0
            )
            result.append(d)
        else:
            result.append({'area': area, 'total': 0, 'high_severity': 0,
                           'resolved': 0, 'open_issues': 0, 'upvotes': 0,
                           'resolution_rate': 0, 'most_common_tag': '—'})
    db.close()
    return result


def get_most_polluted(limit: int = 5, tag: str = None) -> list:
    db  = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    q   = """
        SELECT area,
               COUNT(*) as total,
               SUM(CASE WHEN severity='high'   THEN 3
                        WHEN severity='medium' THEN 1 ELSE 0 END) as severity_score,
               SUM(upvotes) as upvotes,
               SUM(CASE WHEN status='open' THEN 1 ELSE 0 END) as unresolved
        FROM issues
        {where}
        GROUP BY area
        ORDER BY severity_score DESC, total DESC
        LIMIT %s
    """
    if tag:
        cur.execute(q.format(where='WHERE tag=%s'), (tag, limit))
    else:
        cur.execute(q.format(where=''), (limit,))
    rows = cur.fetchall()
    db.close()
    coords = get_area_coords()
    result = []
    for i, r in enumerate(rows):
        d         = dict(r)
        c         = coords.get(d['area'])
        d['rank'] = i + 1
        d['lat']  = c[0] if c else None
        d['lng']  = c[1] if c else None
        result.append(d)
    return result


SYSTEM_PROMPT = """You are AreaPulse AI — a smart civic intelligence assistant for Delhi.

You have access to live map and issue data for 100+ Delhi areas. Your role:
1. Answer questions about civic issues, problem areas, NGOs, and government agencies
2. Pinpoint areas on the map by returning structured JSON actions
3. Compare areas using data tables
4. Provide insights on pollution hotspots, resolution rates, trending issues

IMPORTANT RULES:
- Always respond with a JSON object (no markdown wrapper) in this exact format:
{
  "message": "your conversational response here",
  "action": null OR one of the action objects below,
  "table": null OR array of row objects for comparison tables,
  "pinpoints": null OR array of {area, lat, lng, label, heat} for map pins
}

Available actions:
- {"type": "zoom_to", "lat": X, "lng": Y, "zoom": 13, "label": "..."}
- {"type": "highlight_areas", "areas": ["Area1","Area2",...]}
- {"type": "show_heatmap"}
- {"type": "filter_issues", "tag": "pothole", "area": "Rohini"}

When asked to pinpoint something, include pinpoints array with coordinates.
When asked to compare, include table array with clean column data.
Be concise, specific, and data-driven. Mention actual area names and numbers."""


def chat(user_message: str, history: list = None, context_data: dict = None) -> dict:
    if not ANTHROPIC_AVAILABLE or not _client:
        return _offline_chat(user_message, context_data)

    map_data  = get_map_summary()
    top5      = get_most_polluted(5)
    top5_text = '\n'.join(
        f"  {r['rank']}. {r['area']} — {r['total']} issues, severity score {r['severity_score']}"
        for r in top5
    )
    tag_text = ', '.join(
        f"{r['tag']}({r['cnt']})" for r in map_data['tag_breakdown'][:6]
    )

    data_context = f"""
=== LIVE MAP DATA ===
Total issues in database: {map_data['total_issues']}
Top issue categories: {tag_text}
Top 5 most problematic areas right now:
{top5_text}

Status breakdown: {json.dumps({r['status']: r['cnt'] for r in map_data['status_summary']})}
"""

    messages = []
    if history:
        for h in (history or [])[-6:]:
            messages.append({'role': h['role'], 'content': h['content']})
    messages.append({'role': 'user', 'content': user_message})

    try:
        resp = _client.messages.create(
            model=MODEL,
            max_tokens=1200,
            system=SYSTEM_PROMPT + '\n\n' + data_context,
            messages=messages
        )
        raw  = resp.content[0].text.strip()
        raw  = re.sub(r'^```json\s*', '', raw, flags=re.MULTILINE)
        raw  = re.sub(r'^```\s*$',   '', raw, flags=re.MULTILINE)
        data = json.loads(raw)
        if data.get('pinpoints'):
            coords = get_area_coords()
            for p in data['pinpoints']:
                if not p.get('lat') and p.get('area'):
                    c = coords.get(p['area'])
                    if c:
                        p['lat'], p['lng'] = c
        return data
    except json.JSONDecodeError:
        return {'message': raw, 'action': None, 'table': None, 'pinpoints': None}
    except Exception as e:
        return _offline_chat(user_message, context_data, error=str(e))


def _offline_chat(message: str, context_data=None, error: str = '') -> dict:
    msg_l  = message.lower()
    coords = get_area_coords()

    if any(w in msg_l for w in ['most polluted', 'worst', 'top', 'hotspot']):
        top = get_most_polluted(5)
        return {
            'message':   'Based on live data, here are Delhi\'s top 5 problem areas:\n' +
                         '\n'.join(f"{r['rank']}. **{r['area']}** — {r['total']} issues"
                                   for r in top),
            'action':    {'type': 'highlight_areas', 'areas': [r['area'] for r in top]},
            'table':     top,
            'pinpoints': [{'area': r['area'], 'lat': r['lat'], 'lng': r['lng'],
                           'label': f"#{r['rank']} {r['area']}", 'heat': 'high'}
                          for r in top if r['lat']],
        }

    if 'compare' in msg_l:
        known = [a for a in coords if a.lower() in msg_l]
        if known:
            data = compare_areas(known)
            return {'message': f"Comparison for {', '.join(known)}:",
                    'action': None, 'table': data, 'pinpoints': None}

    for area in coords:
        if area.lower() in msg_l:
            c = coords[area]
            return {
                'message':   f'Showing **{area}** on the map.',
                'action':    {'type': 'zoom_to', 'lat': c[0], 'lng': c[1], 'zoom': 14, 'label': area},
                'table':     None,
                'pinpoints': [{'area': area, 'lat': c[0], 'lng': c[1], 'label': area, 'heat': 'medium'}],
            }

    suffix = f' (LLM error: {error})' if error else ''
    return {
        'message':   f"I'm your AreaPulse AI assistant. Ask me about Delhi's civic issues, compare areas, or find hotspots!{suffix}",
        'action':    None,
        'table':     None,
        'pinpoints': None,
    }