from app import create_app, db
from app.models import User, Category, Section, Thread, Post
from datetime import datetime, timedelta

def create_sample_data():
    app = create_app()
    
    with app.app_context():
        # Очистка существующих данных
        db.drop_all()
        db.create_all()
        
        print("Создание тестовых данных...")
        
        # Создание тестовых пользователей
        admin = User(username='admin', email='admin@forum.com')
        admin.set_password('admin123')
        admin.is_moderator = True
        
        user1 = User(username='user1', email='user1@forum.com')
        user1.set_password('user123')
        
        user2 = User(username='user2', email='user2@forum.com')
        user2.set_password('user123')
        
        # Создание категорий и разделов
        main_category = Category(name="Основные разделы", description="Основные обсуждения форума", order=1)
        other_category = Category(name="Дополнительные", description="Дополнительные темы для обсуждения", order=2)
        
        general_section = Section(name="Обсуждения", description="Общие обсуждения и беседы", category=main_category)
        help_section = Section(name="Помощь и поддержка", description="Помощь новичкам и ответы на вопросы", category=main_category)
        offtop_section = Section(name="Оффтоп", description="Свободные темы для общения", category=other_category)
        
        # Добавление пользователей и разделов
        db.session.add_all([admin, user1, user2, main_category, other_category, general_section, help_section, offtop_section])
        db.session.commit()
        
        print("✓ Пользователи и разделы созданы")
        
        # Создание тестовых тем
        thread1 = Thread(
            title="Добро пожаловать на форум!",
            content="Приветствуем всех новых пользователей! Расскажите немного о себе.",
            user_id=admin.id,
            section_id=general_section.id,
            created_at=datetime.utcnow() - timedelta(days=2),
            updated_at=datetime.utcnow() - timedelta(hours=3)
        )
        
        thread2 = Thread(
            title="Как пользоваться форумом?",
            content="Здесь вы можете найти ответы на часто задаваемые вопросы о работе форума.",
            user_id=admin.id,
            section_id=help_section.id,
            created_at=datetime.utcnow() - timedelta(days=1),
            updated_at=datetime.utcnow() - timedelta(hours=1)
        )
        
        thread3 = Thread(
            title="Обсуждение фильмов и сериалов",
            content="Какие фильмы или сериалы вы посмотрели недавно? Поделитесь впечатлениями!",
            user_id=user1.id,
            section_id=offtop_section.id,
            created_at=datetime.utcnow() - timedelta(hours=5),
            updated_at=datetime.utcnow() - timedelta(minutes=30)
        )
        
        # Добавление тем
        db.session.add_all([thread1, thread2, thread3])
        db.session.commit()
        
        print("🔐 Администратор:")
        print("   Логин: admin")
        print("   Пароль: admin123")
        print("\n👤 Обычные пользователи:")
        print("   Логин: user1 / Пароль: user123")
        print("   Логин: user2 / Пароль: user123")
if __name__ == '__main__':
    create_sample_data()