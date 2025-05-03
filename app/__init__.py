import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.config.config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Создаем директорию для загрузок
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Инициализируем расширения
    db.init_app(app)
    login_manager.init_app(app)

    from app.routes.auth import auth
    from app.routes.main import main
    
    # Регистрируем блюпринты
    app.register_blueprint(auth)
    app.register_blueprint(main)

    # Загружаем пользователя
    from app.models.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app 