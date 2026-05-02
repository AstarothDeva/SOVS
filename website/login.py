from flask import Blueprint, render_template, request, flash, session, redirect, url_for

from website.database import get_db_connection
import time
from flask_mail import Message
from website.mail import mail
import random

login = Blueprint('login', __name__)

@login.route('/', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        password = request.form.get('password')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE student_id=? AND password=?', (student_id, password)
        ).fetchone()
        conn.close()

        if user:
            if user['role'] == 'student':
                session['user_id'] = user['student_id']
                session['role'] = user['role']
                session['email'] = user['email']
                flash(f"Welcome Student {student_id}!", category="success")
                return redirect(url_for("home.home_page"))
            elif user['role'] == 'admin':
                session['user_id'] = user['student_id']
                session['role'] = user['role']
                session['email'] = user['email']
                return redirect(url_for("admin.admin_login"))
            else:
                flash("Invalid user role.", category="error")
                return redirect(url_for("login.login_page"))
        else:
            flash(f"Wrong id number and password. Please try again.", category="error")
            return redirect(url_for("login.login_page"))

    return render_template("login_page.html")

@login.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        email = request.form.get('email')

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE student_id=? AND email=?", (student_id, email)
                            ).fetchone()
        conn.close()

        if user:
            otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            print("Generated OTP: ", otp)

            session['otp'] = otp
            session['email'] = email
            session['otp_expire'] = time.time() + 300

            email = user['email']
            msg = Message("Test Email", recipients=[email], sender="sovs.company@gmail.com")
            msg.body = (f"""Dear Student We received a request to reset the password for your account associated with this email address.
            To proceed, please use the One-Time Password (OTP) provided below:)

            🔐 Your OTP Code: {otp} 

            This code is valid for the next 5 minutes.
            Do not share this code with anyone for security reasons. 
            If you did not request a password reset, please ignore this message or contact support immediately.

            Thank you,
            Opol Community College and SOVS Company IT Support""")

            try:
                mail.send(msg)
                print("Test email sent successfully!")
            except Exception as error:
                print(f"An error occurred: {str(error)}")

    return render_template('forgot_pass_page.html')

@login.route('/otp', methods=['GET', 'POST'])
def enter_otp():
    student_id = session.get('student_id')
    if request.method == 'POST':
        entered_otp = request.form.get('otp')

        if entered_otp == session.get('otp'):
            flash("OTP verified. You can now reset your password.", category="success")
            return render_template('change_pass_page.html', student_id=student_id)
        else:
            flash("Invalid OTP. Please try again.", category="error")
            return redirect(url_for('login.enter_otp'))

    return render_template('otp_page.html')

@login.route('/logout', methods=['GET', 'POST'])
def logout():
    print("Before logout", dict(session))
    session.clear()
    print("After logout", dict(session))

    return redirect(url_for('login.login_page'))

