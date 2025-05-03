from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
from app.models.models import User
from app import db

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует')
            return redirect(url_for('auth.register'))
        
        if "'" in username or '"' in username:
            flash('Недопустимые символы в имени пользователя')
            return redirect(url_for('auth.register'))
        
        user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна!')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        result = db.session.execute(text(f"SELECT * FROM user WHERE username='{username}'"))
        user = result.fetchone()
        
        if user and check_password_hash(user.password_hash, password):
            user_obj = User.query.get(user.id)
            login_user(user_obj)
            return redirect(url_for('main.home'))
        flash('Неверное имя пользователя или пароль')
    
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home')) 