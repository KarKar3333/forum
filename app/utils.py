import os
import secrets
from flask import current_app, url_for
from PIL import Image

def save_avatar(image_file):
    if not image_file or not image_file.filename:
        return None
    
    try:
        # Генерируем случайное имя файла
        random_hex = secrets.token_hex(8)
        _, file_extension = os.path.splitext(image_file.filename)
        picture_filename = random_hex + file_extension.lower()
        
        # Получаем путь для сохранения из конфига (корневая папка)
        upload_folder = current_app.config['UPLOAD_FOLDER']
        
        # Убеждаемся, что папка существует
        os.makedirs(upload_folder, exist_ok=True)
        
        picture_path = os.path.join(upload_folder, picture_filename)
        
        # Обрабатываем изображение
        output_size = (150, 150)
        i = Image.open(image_file)
        
        if i.mode in ('RGBA', 'LA', 'P'):
            i = i.convert('RGB')
        
        i.thumbnail(output_size, Image.Resampling.LANCZOS)
        i.save(picture_path, quality=85)
        
        print(f"✅ Аватар сохранен в: {picture_path}")
        return picture_filename
    
    except Exception as e:
        print(f"❌ Ошибка при сохранении аватарки: {e}")
        return None

def delete_old_avatar(old_avatar):
    if old_avatar and old_avatar != 'default.png':
        try:
            upload_folder = current_app.config['UPLOAD_FOLDER']
            old_avatar_path = os.path.join(upload_folder, old_avatar)
            if os.path.exists(old_avatar_path):
                os.remove(old_avatar_path)
                print(f"✅ Старая аватарка удалена: {old_avatar_path}")
        except Exception as e:
            print(f"❌ Ошибка при удалении старой аватарки: {e}")

def get_avatar_url(filename):
    """Получить URL для отображения аватарки из КОРНЕВОЙ папки"""
    if not filename or filename == 'default.png':
        filename = 'default.png'
    
    # Всегда используем путь к корневой папке static/avatars/
    return url_for('static', filename=f'avatars/{filename}')

def allowed_file(filename):
    if not filename:
        return False
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS