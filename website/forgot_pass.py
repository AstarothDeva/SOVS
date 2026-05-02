import time

from flask import Blueprint, request, session, render_template, flash, url_for
from werkzeug.utils import redirect

from website.database import get_db_connection
from flask_mail import Message
from website.mail import mail
import random

forgot_pass = Blueprint("forgot_pass", __name__)

@forgot_pass.route('/', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        email = request.form.get('email')

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE student_id=? AND email=?", (student_id, email)
        ).fetchone()
        conn.close()

        if user:
            otp = ''.join([str(random.randint(0,9)) for _ in range(6)])
            print("Generated OTP: ", otp)

            session['student_id'] = student_id
            session['otp'] = otp
            session['email'] = email
            session['otp_expire'] = time.time() + 300

            marks = ["✅", "📧", "📌","📎", "🛠️", "🧾", "🗂️", "✅✅", "✅✅✅", "✅📧"]
            outro = random.choice(marks)

            email = user['email']
            msg = Message("SOVS OTP", recipients=[email], sender="sovs.company@gmail.com")
            msg.html = (f"""
<p>Dear Student,</p>
<p>We received a request to reset the password for your account associated with this email address.</p>
<p>To proceed, please use the One-Time Password (OTP) provided below:</p>

<h2 style="color: #2e6c80;">🔐 Your OTP Code: <strong>{otp}</strong></h2>

<p>This code is valid for the next <strong>5 minutes</strong>.</p>
<p><strong>Do not share this code</strong> with anyone for security reasons.</p>

<p>If you did not request a password reset, please ignore this message or contact support immediately.</p>

<p>Thank you,<br>
Opol Community College and SOVS Company IT Support {outro}</p>
""")

            try:
                mail.send(msg)
                print("Test email sent successfully!")
                return render_template('otp_page.html')
            except Exception as error:
                print(f"An error occurred: {str(error)}")

        else:
            flash("Student ID and email account does not match. Please try again.")
            return redirect(url_for("forgot_pass.forgot_password"))
    return render_template('forgot_pass_page.html')