from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_required, current_user
from app.models.models import Post, SecretNote
from app.utils.helpers import allowed_file, save_file, inject_data_into_image
from app import db
import os
from app.config.config import Config

main = Blueprint('main', __name__)


@main.route('/')
def home():
    page = request.args.get('page', 'posts')
    if page == 'posts':
        posts = Post.query.order_by(Post.date_posted.desc()).all()
        return render_template('home.html', posts=posts)
    return send_file(page)


@main.route('/create_post', methods=['GET', 'POST'])
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
                image_path, save_path = save_file(image, image.filename)

                if secret_note:
                    inject_data_into_image(save_path, secret_note)

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
        return redirect(url_for('main.home'))

    return render_template('create_post.html')


@main.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_file(os.path.join(Config.UPLOAD_FOLDER, filename))


@main.route('/post/<int:post_id>/raw')
def raw_post(post_id):
    post = Post.query.get_or_404(post_id)
    return {
        'title': post.title,
        'content': post.content,
        'image_path': post.image_path,
        'hidden_data': post.hidden_data,
        'author_id': post.user_id
    }


@main.route('/admin/notes')
@login_required
def admin_notes():
    if not current_user.is_admin:
        flash('Доступ запрещен')
        return redirect(url_for('main.home'))
    notes = SecretNote.query.all()
    return render_template('admin_notes.html', notes=notes)


@main.route('/api/notes/<int:note_id>')
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


@main.route('/api/notes/', methods=['GET'])
@login_required
def get_all_user_notes():
    notes = SecretNote.query.filter_by(user_id=current_user.id).all()
    return jsonify([
        {
            'id': note.id,
            'content': note.content,
            'user_id': note.user_id,
            'is_encrypted': note.is_encrypted
        }
        for note in notes
    ])
