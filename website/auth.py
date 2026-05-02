from flask import Blueprint, render_template, request, flash, url_for, redirect
from website.database import get_db_connection
import os
from werkzeug.utils import secure_filename

admin = Blueprint('admin', __name__)

from collections import defaultdict

from datetime import datetime

@admin.route('/', methods=['GET', 'POST'])
def admin_login():
    conn = get_db_connection()

    # Total number of events (active + closed)
    total_event_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    # Total votes (based on selections table or votes table)
    total_votes = conn.execute("SELECT SUM(vote_count) FROM selections").fetchone()[0]
    total_votes = total_votes if total_votes else 0

    # Total number of voters
    num_voters = conn.execute("SELECT COUNT(*) FROM users WHERE role=?", ('student',)).fetchone()[0]

    # Get all events
    events = get_all_events(conn, only_active=True)

    # Ongoing events: status = 'active' AND today between start_date and end_date
    today = datetime.today().date()
    ongoing_count = conn.execute("SELECT COUNT(*) FROM events WHERE status = 'active'").fetchone()[0]

    # For dropdown-selected event
    event_id = get_event_id(request)
    selected_event = get_event_by_id(conn, event_id) if event_id else None
    selections = get_candidates(conn, event_id)

    grouped_roles = defaultdict(list)
    for s in selections:
        s = dict(s)
        s['votes'] = s['vote_count']
        grouped_roles[s['role']].append(s)
    grouped_roles = dict(grouped_roles)

    conn.close()
    return render_template("dashboard.html",
                           events=events,
                           count=total_event_count,
                           total_votes=total_votes,
                           ongoing_count=ongoing_count,
                           num_voters=num_voters,
                           selected_event=selected_event,
                           grouped_roles=grouped_roles)



@admin.route('/create', methods=['GET', 'POST'])
def create_event():
    conn = get_db_connection()
    events = conn.execute("SELECT * FROM events").fetchall()
    conn.close()

    if request.method == "POST":
        title = request.form.get('event-title')
        start_date = request.form.get('start-date')
        end_date = request.form.get('end-date')

        conn = get_db_connection()
        conn.execute("INSERT INTO events (title,start_date,end_date) VALUES (?,?,?)",
                    (title,start_date,end_date))
        conn.commit()
        conn.close()

        flash("Event created successfully.", category="success")

    return render_template('create_event.html', events=events)

@admin.route('/delete', methods=['POST'])
def delete_event():
    event_id = request.form.get('event-id')

    if not event_id:
        flash("No event selected.", category="error")
        return redirect(url_for('admin.create_event'))

    conn = get_db_connection()
    conn.execute("DELETE FROM selections WHERE event_id = ?", (event_id,))
    conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()

    flash("Event and its selections deleted successfully.", category="success")
    return redirect(url_for('admin.create_event'))

UPLOAD_FOLDER = os.path.join('website', 'static', 'uploads', 'pfps')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@admin.route('/candidates', methods=['GET', 'POST'])
def manage_candidates():
    conn = get_db_connection()
    events = get_all_events(conn)

    event_id = get_event_id(request)
    selected_event = get_event_by_id(conn, event_id) if event_id else None
    selected_role = get_selected_role(request)

    if request.method == 'POST':
        if 'candidate-name' in request.form:
            add_candidate(request, conn, event_id)
        elif 'edit-selection-id' in request.form:
            edit_candidate(request, conn)
        elif 'delete-selection-id' in request.form:
            delete_candidate(request, conn)
        elif 'photo-selection-id' in request.form and 'new-photo' in request.files:
            update_candidate_photo(request, conn)

        return redirect(url_for('admin.manage_candidates', event_id=event_id, role=selected_role))

    selections = get_candidates(conn, event_id, selected_role)
    roles = get_roles(conn, event_id)

    conn.close()
    return render_template("candidate_page.html",
        events=events,
        selected_event=selected_event,
        selections=selections,
        roles=roles,
        selected_role=selected_role
    )

def get_all_events(conn, only_active=False):
    if only_active:
        return conn.execute("SELECT * FROM events WHERE status = 'active'").fetchall()
    return conn.execute("SELECT * FROM events").fetchall()


def get_event_id(req):
    return req.form.get('event-title') if req.method == 'POST' else req.args.get('event_id')

def get_selected_role(req):
    return req.form.get('candidate-role') if req.method == 'POST' else req.args.get('role')

def get_event_by_id(conn, event_id):
    return conn.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()

def get_roles(conn, event_id):
    return conn.execute("SELECT DISTINCT role FROM selections WHERE event_id=?", (event_id,)).fetchall()

def get_candidates(conn, event_id, role=None):
    if role:
        return conn.execute("SELECT * FROM selections WHERE event_id=? AND role=?", (event_id, role)).fetchall()
    return conn.execute("SELECT * FROM selections WHERE event_id=?", (event_id,)).fetchall()

def add_candidate(req, conn, event_id):
    name = req.form.get('candidate-name')
    role = req.form.get('candidate-role')
    file = req.files.get('candidate-photo')

    photo_path = None

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        photo_path = f"uploads/pfps/{filename}"  # For storing in DB (web-accessible path)
        save_path = os.path.join('website', 'static', photo_path)

        os.makedirs(os.path.dirname(save_path), exist_ok=True)  # Make sure upload folders exist
        file.save(save_path)
        print("Saved file to:", save_path)

    if name and role:
        conn.execute("INSERT INTO selections (name, role, event_id, pfp) VALUES (?, ?, ?, ?)",
                     (name, role, event_id, photo_path))
        conn.commit()
        flash("Candidate added!", category="success")


def edit_candidate(req, conn):
    selection_id = req.form.get('edit-selection-id')
    new_name = req.form.get('new-name')
    if new_name:
        conn.execute("UPDATE selections SET name=? WHERE id=?", (new_name, selection_id))
        conn.commit()
        flash("Candidate updated!", category="success")

def delete_candidate(req, conn):
    selection_id = req.form.get('delete-selection-id')
    conn.execute("DELETE FROM selections WHERE id=?", (selection_id,))
    conn.commit()
    flash("Candidate deleted!", category="success")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def update_candidate_photo(req, conn):
    selection_id = req.form.get('photo-selection-id')
    file = req.files.get('new-photo')

    if not file or not allowed_file(file.filename):
        flash("Invalid photo selected.", category="error")
        return

    filename = secure_filename(file.filename)
    photo_path = f"uploads/pfps/{filename}"
    save_path = os.path.join('website', 'static', photo_path)

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    file.save(save_path)

    conn.execute("UPDATE selections SET pfp=? WHERE id=?", (photo_path, selection_id))
    conn.commit()
    flash("Profile photo updated!", category="success")


@admin.route('/close_event/<int:event_id>', methods=['POST'])
def close_event(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Mark event as closed
    cursor.execute("UPDATE events SET status = 'closed' WHERE id = ?", (event_id,))

    # Get unique roles in this event
    cursor.execute("SELECT DISTINCT role FROM selections WHERE event_id = ?", (event_id,))
    roles = cursor.fetchall()

    for role in roles:
        role_name = role[0]
        # Find highest vote_count for this role in this event
        cursor.execute("""
            SELECT id FROM selections 
            WHERE event_id = ? AND role = ? AND vote_count = (
                SELECT MAX(vote_count) FROM selections WHERE event_id = ? AND role = ?
            )
        """, (event_id, role_name, event_id, role_name))

        winners = cursor.fetchall()
        for winner in winners:
            selection_id = winner[0]
            cursor.execute("""
                INSERT INTO winners (event_id, selection_id, role) 
                VALUES (?, ?, ?)
            """, (event_id, selection_id, role_name))

    conn.commit()
    flash("Event successfully closed and winners stored.", "success")
    return redirect(url_for('admin.create_event'))
