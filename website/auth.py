import pandas as pd
import asyncio
import socket
from datetime import datetime
from scipy.stats import entropy
from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)
ips = {'127.0.0.1': {'count': 0, 'time': datetime.now()}}


async def take_login(user, delay=1):
    await asyncio.sleep(delay)
    login_user(user, remember=True)


@auth.route('/login', methods=['GET', 'POST'])
async def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)

        if ip in ips:
            ips[ip] = {'count': ips[ip]['count'] + 1, 'time': datetime.now()}
        else:
            ips[ip] = {'count': 1, 'time': datetime.now()}

        if (ips[ip]['time'] - datetime.now()).total_seconds() > 5:
            ips[ip]['count'] = 1

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                if ip == user.ip and user.new_ip is not None:
                    flash('Logged in successfully. New device accessing your account found: ' + str(user.new_ip),
                          category='success')
                elif ip == user.ip and user.new_ip is None:
                    user.new_ip = '169.254.83.106'
                    db.session.commit()
                    flash('Logged in successfully!', category='success')
                elif ip != user.ip:
                    user.new_ip = ip
                    flash('Logged in successfully!', category='success')
                await take_login(user)
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
                if ips[ip]['count'] > 5:
                    abort(403)
        else:
            flash('Email does not exist.', category='error')
            if ips[ip]['count'] > 5:
                abort(403)

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
async def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        hostname = socket.gethostname()
        ip = str(socket.gethostbyname(hostname))

        pd_series = pd.Series(list(password1))
        e = entropy(pd_series.value_counts())

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 5:
            flash('Email must be greater than 4 characters.', category='error')
        elif '@' not in email:
            flash('Email should contain @ character', category='error')
        elif len(first_name) < 3:
            flash('Nick name must be greater than 2 characters.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 8:
            flash('Password must be at least 8 characters.', category='error')
        elif len(password1) > 24:
            flash('Password must not be longer than 24 characters.', category='error')
        elif 'admin123' in password1:
            flash('Password is too obvious', category='error')
        elif e < 1.1:
            flash('Password is too easy', category='error')
        elif not any(not c.isalnum() for c in password1):
            flash('Password should have at least one special character: !@#$%^&*()-+/', category='error')
        elif not any(c.isdigit() for c in password1):
            flash('Password should have at least one number: 1234567890', category='error')
        else:
            new_user = User(email=email, first_name=first_name, ip=ip, password=generate_password_hash(
                password1, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            await take_login(new_user)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign_up.html", user=current_user)
