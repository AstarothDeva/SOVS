from flask import Blueprint, render_template

home = Blueprint("home", __name__)

@home.route("/")
def home_page():
    """if 'student_id' not in session:
        flash("Please Login first to proceed.")
        return redirect(url_for('login.login_page'))"""
    return render_template("homepage.html")