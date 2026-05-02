from flask import Blueprint, render_template, session, flash, redirect, url_for, request
from .database import get_db_connection

voting = Blueprint("voting", __name__)

@voting.route('/', methods=['GET', 'POST'])
def voting_page():
    if 'user_id' not in session:
        flash("Please login first to proceed.")
        return redirect(url_for('login.login_page'))

    event_id = request.args.get('event_id')
    conn = get_db_connection()
    all_events = conn.execute("SELECT * FROM events").fetchall()

    all_event_data = []
    current_event = None

    for event in all_events:
        roles_data = conn.execute(
            "SELECT DISTINCT role FROM selections WHERE event_id=?", (event['id'],)
        ).fetchall()

        roles = []
        valid_roles = [r['role'] for r in roles_data if r['role'] and r['role'].strip() != '']

        if valid_roles:
            for role_name in valid_roles:
                candidates = conn.execute(
                    "SELECT * FROM selections WHERE event_id=? AND role=?", (event['id'], role_name)
                ).fetchall()
                roles.append({
                    'role': role_name,
                    'selections': candidates
                })

        candidates_without_role = conn.execute(
            "SELECT * FROM selections WHERE event_id=? AND (role IS NULL OR TRIM(role) = '')",
            (event['id'],)
        ).fetchall()

        if candidates_without_role:
            roles.append({
                'role': 'None',
                'selections': candidates_without_role
            })

        event_data = {
            'id': event['id'],
            'title': event['title'],
            'status': event['status'],
            'roles': roles,
            'is_active': event['status'] == 'active'
        }

        all_event_data.append(event_data)

        if str(event['id']) == str(event_id) and event_data['is_active']:
            current_event = event_data

    # Default to first active event if none selected or selected is closed
    if not current_event:
        for e in all_event_data:
            if e['is_active']:
                current_event = e
                break

    if request.method == 'POST':
        # User already voted?
        voted_check = conn.execute(
            "SELECT 1 FROM votes WHERE user_id = ? AND event_id = ?",
            (session['user_id'], current_event['id'])
        ).fetchone()
        if voted_check:
            flash("You have already voted in this event.", "danger")
            return redirect(url_for('voting.voting_page', event_id=current_event['id']))

        # Ensure all roles are selected
        missing_roles = []
        for role in current_event['roles']:
            field_name = f"vote_{role['role'].replace(' ', '_')}"
            if not request.form.get(field_name):
                missing_roles.append(role['role'])

        if missing_roles:
            flash(f"Missing votes for: {', '.join(missing_roles)}", "warning")
            return redirect(url_for('voting.voting_page', event_id=current_event['id']))

        # Cast votes
        for role in current_event['roles']:
            field_name = f"vote_{role['role'].replace(' ', '_')}"
            selection_id = request.form.get(field_name)
            if selection_id:
                conn.execute("UPDATE selections SET vote_count = vote_count + 1 WHERE id=?", (selection_id,))
                conn.execute(
                    "INSERT INTO votes (user_id, selection_id, event_id) VALUES (?, ?, ?)",
                    (session['user_id'], selection_id, current_event['id'])
                )

        conn.execute("UPDATE users SET has_voted = 1 WHERE id = ?", (session['user_id'],))
        conn.commit()
        flash("Your votes have been submitted successfully!", "success")
        return redirect(url_for('voting.voting_page', event_id=current_event['id']))

    conn.close()
    return render_template('voting_page.html', all_event_data=all_event_data, current_event=current_event)
