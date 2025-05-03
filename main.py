import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import base64
from sqlalchemy import text

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///forum.db'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Создаем директории, если они не существуют
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    notes = db.relationship('SecretNote', backref='owner', lazy=True)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(200))
    hidden_data = db.Column(db.Text, nullable=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class SecretNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_encrypted = db.Column(db.Boolean, default=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def allowed_file(filename):
    return '.' in filename and filename.lower().endswith(tuple(ALLOWED_EXTENSIONS))


@app.route('/')
def home():
    page = request.args.get('page', 'posts')
    if page == 'posts':
        posts = Post.query.order_by(Post.date_posted.desc()).all()
        return render_template('home.html', posts=posts)
    return send_file(page)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует')
            return redirect(url_for('register'))

        if "'" in username or '"' in username:
            flash('Недопустимые символы в имени пользователя')
            return redirect(url_for('register'))
        
        user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна!')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # SQL инъекция через text()
        result = db.session.execute(text(f"SELECT * FROM user WHERE username='{username}'"))
        user = result.fetchone()
        
        if user and check_password_hash(user.password_hash, password):
            user_obj = User.query.get(user.id)
            login_user(user_obj)
            return redirect(url_for('home'))
        flash('Неверное имя пользователя или пароль')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        image = request.files.get('image')
        secret_note = request.form.get('secret_note', '')
        image_path = None
        
        if image:
            if image.filename == '':
                flash('Файл не выбран')
                return redirect(request.url)
            
            try:
                filename = image.filename
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image_path = os.path.join('uploads', filename).replace('\\', '/')
                image.save(save_path)
                
                if secret_note:
                    with open(save_path, 'ab') as f:
                        f.write(base64.b64encode(secret_note.encode()))
                
            except Exception as e:
                flash('Ошибка при загрузке файла: ' + str(e))
                return redirect(request.url)
        
        post = Post(title=title, content=content, image_path=image_path, author=current_user)
        
        if secret_note:
            note = SecretNote(content=secret_note, owner=current_user)
            db.session.add(note)
            post.hidden_data = str(note.id)
        
        db.session.add(post)
        db.session.commit()
        flash('Пост создан!')
        return redirect(url_for('home'))
    
    return render_template('create_post.html')


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    # Используем os.path.join для корректного формирования пути
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))


@app.route('/post/<int:post_id>/raw')
def raw_post(post_id):
    post = Post.query.get_or_404(post_id)
    return {
        'title': post.title,
        'content': post.content,
        'image_path': post.image_path,
        'hidden_data': post.hidden_data,
        'author_id': post.user_id
    }


@app.route('/admin/notes')
@login_required
def admin_notes():
    if not current_user.is_admin:
        flash('Доступ запрещен')
        return redirect(url_for('home'))
    notes = SecretNote.query.all()
    return render_template('admin_notes.html', notes=notes)


@app.route('/api/notes/<int:note_id>')
@login_required
def get_note(note_id):
    note = SecretNote.query.get_or_404(note_id)
    if not current_user.is_admin and note.user_id != current_user.id:
        return jsonify({'error': 'Доступ запрещен'}), 403
    return jsonify({
        'content': note.content,
        'user_id': note.user_id,
        'is_encrypted': note.is_encrypted
    })


if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()

        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', 
                        password_hash=generate_password_hash('super_secret_password'),
                        is_admin=True)
            db.session.add(admin)

            admin_note = SecretNote(
                content="FLAG{admin_secret_note_1337}",
                owner=admin,
                is_encrypted=True
            )
            db.session.add(admin_note)

            test_post = Post(
                title="Тестовый пост",
                content="Это тестовый пост от администратора",
                hidden_data=str(admin_note.id),
                author=admin
            )
            db.session.add(test_post)
            db.session.commit()
    app.run(debug=True)
