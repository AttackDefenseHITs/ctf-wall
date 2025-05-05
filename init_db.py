from app import create_app, db
from app.models.models import User, Post, SecretNote
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password_hash=generate_password_hash('super_secret_password'),
            is_admin=True
        )
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
