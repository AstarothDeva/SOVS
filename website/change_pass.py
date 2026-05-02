from flask import Blueprint, request, flash, session, render_template, redirect, url_for

from .database import get_db_connection

change_pass = Blueprint("change_pass", __name__)

@change_pass.route("/", methods=['GET', 'POST'])
def change_password():
    student_id = session.get('student_id')
    if request.method == 'POST':
        new_pass = request.form.get('new_pass')
        confirm_pass = request.form.get('confirm_pass')

        if new_pass != confirm_pass:
            flash("Password does not match!", "error")
        else:
            conn = get_db_connection()
            conn.execute("UPDATE students SET password=? WHERE student_id=?", (new_pass, student_id))
            conn.commit()
            conn.close()
            flash("Password changed successfully!", "success")
            return redirect(url_for('login.login_page'))

    return render_template('change_pass_page.html', student_id=student_id)
