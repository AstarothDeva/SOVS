from flask import Flask, redirect, url_for

from .login import logout
from .mail import mail

def create_web_app():
    web_app = Flask(__name__)
    web_app.config['SECRET_KEY'] = 'Student Online Voting System'

    from .login import login
    from .home import home
    from .forgot_pass import forgot_pass
    from .change_pass import change_pass
    from .voting import voting
    from .history import history
    from .auth import admin

    web_app.register_blueprint(login, url_prefix="/login")
    web_app.register_blueprint(home, url_prefix="/home")
    web_app.register_blueprint(voting, url_prefix="/voting")
    web_app.register_blueprint(history, url_prefix="/history")
    web_app.register_blueprint(forgot_pass, url_prefix="/forgot_pass")
    web_app.register_blueprint(change_pass, url_prefix="/change_pass")
    web_app.register_blueprint(admin, url_prefix="/admin")

    web_app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    web_app.config['MAIL_PORT'] = 587
    web_app.config['MAIL_USE_TLS'] = True
    web_app.config['MAIL_USERNAME'] = 'sovs.company@gmail.com'
    web_app.config['MAIL_PASSWORD'] = 'ygbs zlvp akoh rkdn'

    @web_app.route('/')
    def home():
        return redirect(url_for('home.home_page'))

    mail.init_app(web_app)

    return web_app