import os
import base64
from app.config.config import Config


def allowed_file(filename):
    return '.' in filename and filename.lower().endswith(tuple(Config.ALLOWED_EXTENSIONS))


def save_file(file, filename):
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    save_path = os.path.join(Config.UPLOAD_FOLDER, filename)

    image_path = os.path.join('uploads', filename).replace('\\', '/')
    
    file.save(save_path)
    return image_path, save_path


def inject_data_into_image(file_path, data):
    with open(file_path, 'ab') as f:
        f.write(base64.b64encode(data.encode()))
