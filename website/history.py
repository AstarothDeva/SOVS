from flask import Blueprint, render_template, session, flash, redirect, url_for
from .database import get_db_connection

history = Blueprint("history", __name__)

@history.route('/', methods=['GET'])
def history_page():
    if 'user_id' not in session:
        flash("Please login first to proceed.")
        return redirect(url_for('login.login_page'))

    conn = get_db_connection()

    closed_events = conn.execute("SELECT * FROM events WHERE status = 'closed'").fetchall()
    user_id = session['user_id']
    history_data = []

    for event in closed_events:
        # Get all roles for the event
        roles_data = conn.execute(
            "SELECT DISTINCT role FROM selections WHERE event_id = ?", (event['id'],)
        ).fetchall()
        roles = [r['role'] if r['role'] else 'None' for r in roles_data]

        role_entries = []

        for role in roles:
            # Get user's vote
            vote = conn.execute("""
                SELECT s.name FROM votes v
                JOIN selections s ON v.selection_id = s.id
                WHERE v.user_id = ? AND v.event_id = ? AND s.role = ?
            """, (user_id, event['id'], role)).fetchone()

            # Get winner(s)
            top_votes = conn.execute("""
                SELECT MAX(vote_count) FROM selections 
                WHERE event_id = ? AND role = ?
            """, (event['id'], role)).fetchone()[0]

            winners = conn.execute("""
                SELECT name FROM selections 
                WHERE event_id = ? AND role = ? AND vote_count = ?
            """, (event['id'], role, top_votes)).fetchall()

            role_entries.append({
                'role': role,
                'user_vote': vote['name'] if vote else "N/A",
                'winners': [w['name'] for w in winners] if winners else ["N/A"]
            })

        history_data.append({
            'event_title': event['title'],
            'roles': role_entries
        })

    conn.close()
    return render_template('history_page.html', history_data=history_data)
