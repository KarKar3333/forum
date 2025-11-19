from flask import render_template, flash, redirect, url_for, request, abort
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime
from app import db
from app.models import User, Category, Section, Thread, Post
from app.forms import RegistrationForm, LoginForm, ThreadForm, PostForm, ProfileForm, ChangePasswordForm, SortForm
from app.utils import save_avatar, delete_old_avatar, allowed_file
from sqlalchemy import desc, func, asc, text
from app.utils import get_avatar_url
from app.forms import CategoryForm, SectionForm

def init_routes(app):
    
    @app.context_processor
    def utility_processor():
        def get_thread_post_count(thread):
            return thread.posts.count()
        
        def get_section_post_count(section_id):
            """Подсчет сообщений в разделе"""
            from app.models import Post, Thread
            return db.session.query(Post).join(Thread).filter(Thread.section_id == section_id).count()
        
        def get_section_stats(section):
            thread_count = section.threads.count()
            post_count = get_section_post_count(section.id)
            latest_thread = section.threads.order_by(desc(Thread.updated_at)).first()
            return {
                'thread_count': thread_count,
                'post_count': post_count,
                'latest_thread': latest_thread
            }
        
        return dict(
            get_thread_post_count=get_thread_post_count,
            get_section_post_count=get_section_post_count,  # ← ДОБАВЛЯЕМ
            get_section_stats=get_section_stats,
            get_avatar_url=get_avatar_url
        )

    @app.route('/')
    def index():
        categories = Category.query.order_by(Category.order).all()
        
        # Предварительно загружаем данные для статистики
        for category in categories:
            for section in category.sections:
                # Получаем последнюю тему для каждого раздела
                section.latest_thread = section.threads.order_by(desc(Thread.updated_at)).first()
        
        return render_template('forum/index.html', categories=categories)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Регистрация успешна! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))
        
        return render_template('auth/register.html', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                flash('Неверное имя пользователя или пароль.', 'danger')
        
        return render_template('auth/login.html', form=form)

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('index'))

    # Профиль пользователя
    @app.route('/profile')
    @login_required
    def profile():
        # Используем desc() для сортировки вместо строки
        recent_threads = current_user.threads.order_by(desc(Thread.created_at)).limit(3).all()
        recent_posts = current_user.posts.order_by(desc(Post.created_at)).limit(3).all()
        
        return render_template('user/profile.html', 
                             recent_threads=recent_threads, 
                             recent_posts=recent_posts)

    @app.route('/profile/edit', methods=['GET', 'POST'])
    @login_required
    def edit_profile():
        form = ProfileForm(original_username=current_user.username, original_email=current_user.email)
        
        if form.validate_on_submit():
            if form.avatar.data:
                # Сохраняем новую аватарку
                avatar_filename = save_avatar(form.avatar.data)
                if avatar_filename:
                    # Удаляем старую аватарку если она не дефолтная
                    delete_old_avatar(current_user.avatar)
                    current_user.avatar = avatar_filename
            
            current_user.username = form.username.data
            current_user.email = form.email.data
            current_user.about = form.about.data
            
            db.session.commit()
            flash('Профиль успешно обновлен!', 'success')
            return redirect(url_for('profile'))
        
        elif request.method == 'GET':
            form.username.data = current_user.username
            form.email.data = current_user.email
            form.about.data = current_user.about
        
        return render_template('user/edit_profile.html', form=form)

    @app.route('/profile/change_password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        form = ChangePasswordForm()
        
        if form.validate_on_submit():
            if current_user.check_password(form.current_password.data):
                current_user.set_password(form.new_password.data)
                db.session.commit()
                flash('Пароль успешно изменен!', 'success')
                return redirect(url_for('profile'))
            else:
                flash('Текущий пароль неверен.', 'danger')
        
        return render_template('user/change_password.html', form=form)

    # Публичный профиль
    @app.route('/user/<username>')
    def user_profile(username):
        user = User.query.filter_by(username=username).first_or_404()
        
        # Получаем последние темы и сообщения пользователя
        recent_threads = user.threads.order_by(desc(Thread.created_at)).limit(5).all()
        recent_posts = user.posts.order_by(desc(Post.created_at)).limit(5).all()
        
        return render_template('user/user_profile.html', 
                             user=user, 
                             recent_threads=recent_threads, 
                             recent_posts=recent_posts)



    @app.route('/section/<int:section_id>')
    def section(section_id):
        section = Section.query.get_or_404(section_id)
        form = SortForm()
        
        # Получаем параметры сортировки
        sort_by = request.args.get('sort_by', 'updated_at_desc')
        
        # Базовый запрос
        query = section.threads
        
        # Применяем сортировку
        if sort_by == 'updated_at_desc':
            threads = query.order_by(desc(Thread.updated_at)).all()
        elif sort_by == 'updated_at_asc':
            threads = query.order_by(asc(Thread.updated_at)).all()
        elif sort_by == 'title_asc':
            threads = query.order_by(asc(Thread.title)).all()
        elif sort_by == 'title_desc':
            threads = query.order_by(desc(Thread.title)).all()
        elif sort_by == 'post_count_desc':
            # Сортировка по количеству сообщений
            threads = query.outerjoin(Post).group_by(Thread.id).order_by(
                desc(func.count(Post.id))
            ).all()
        else:
            threads = query.order_by(desc(Thread.updated_at)).all()
        
        return render_template('forum/category.html', 
                            section=section, 
                            threads=threads, 
                            form=form,
                            current_sort=sort_by)

    @app.route('/section/<int:section_id>/new', methods=['GET', 'POST'])
    @login_required
    def new_thread(section_id):
        section = Section.query.get_or_404(section_id)
        form = ThreadForm()
        
        if form.validate_on_submit():
            thread = Thread(
                title=form.title.data,
                content=form.content.data,
                user_id=current_user.id,
                section_id=section_id
            )
            db.session.add(thread)
            db.session.commit()
            flash('Тема создана успешно!', 'success')
            return redirect(url_for('thread', thread_id=thread.id))
        
        return render_template('forum/new_thread.html', form=form, section=section)

    @app.route('/thread/<int:thread_id>')
    def thread(thread_id):
        thread = Thread.query.get_or_404(thread_id)
        posts = thread.posts.order_by(Post.created_at.asc()).all()
        form = PostForm()
        return render_template('forum/thread.html', thread=thread, posts=posts, form=form)

    @app.route('/thread/<int:thread_id>/reply', methods=['POST'])
    @login_required
    def reply(thread_id):
        thread = Thread.query.get_or_404(thread_id)
        
        if thread.is_locked:
            flash('Эта тема закрыта для новых сообщений.', 'warning')
            return redirect(url_for('thread', thread_id=thread_id))
        
        form = PostForm()
        if form.validate_on_submit():
            post = Post(
                content=form.content.data,
                user_id=current_user.id,
                thread_id=thread_id
            )
            thread.updated_at = datetime.utcnow()
            db.session.add(post)
            db.session.commit()
            flash('Сообщение добавлено!', 'success')
        else:
            flash('Ошибка при отправке сообщения.', 'danger')
        
        return redirect(url_for('thread', thread_id=thread_id))

    @app.route('/delete_thread/<int:thread_id>')
    @login_required
    def delete_thread(thread_id):
        thread = Thread.query.get_or_404(thread_id)
        
        if not current_user.is_moderator and thread.user_id != current_user.id:
            abort(403)
        
        section_id = thread.section_id
        db.session.delete(thread)
        db.session.commit()
        flash('Тема удалена!', 'success')
        return redirect(url_for('section', section_id=section_id))

    @app.route('/delete_post/<int:post_id>')
    @login_required
    def delete_post(post_id):
        post = Post.query.get_or_404(post_id)
        
        if not current_user.is_moderator and post.user_id != current_user.id:
            abort(403)
        
        thread_id = post.thread_id
        db.session.delete(post)
        db.session.commit()
        flash('Сообщение удалено!', 'success')
        return redirect(url_for('thread', thread_id=thread_id))
    
    @app.route('/admin')
    @login_required
    def admin_panel():
        if not current_user.is_moderator:
            abort(403)
        
        categories = Category.query.order_by(Category.order).all()
        return render_template('admin/admin_panel.html', categories=categories)
    
    # Создание категории
    @app.route('/admin/category/new', methods=['GET', 'POST'])
    @login_required
    def new_category():
        if not current_user.is_moderator:
            abort(403)
        
        form = CategoryForm()
        if form.validate_on_submit():
            category = Category(
                name=form.name.data,
                description=form.description.data,
                order=form.order.data
            )
            db.session.add(category)
            db.session.commit()
            flash('Категория успешно создана!', 'success')
            return redirect(url_for('admin_panel'))
        
        return render_template('admin/new_category.html', form=form)
    
    # Создание раздела
    @app.route('/admin/section/new', methods=['GET', 'POST'])
    @login_required
    def new_section():
        if not current_user.is_moderator:
            abort(403)
        
        form = SectionForm()
        if form.validate_on_submit():
            section = Section(
                name=form.name.data,
                description=form.description.data,
                category_id=form.category_id.data
            )
            db.session.add(section)
            db.session.commit()
            flash('Раздел успешно создан!', 'success')
            return redirect(url_for('admin_panel'))
        
        return render_template('admin/new_section.html', form=form)
    
    # Редактирование категории
    @app.route('/admin/category/<int:category_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_category(category_id):
        if not current_user.is_moderator:
            abort(403)
        
        category = Category.query.get_or_404(category_id)
        form = CategoryForm()
        
        if form.validate_on_submit():
            category.name = form.name.data
            category.description = form.description.data
            category.order = form.order.data
            db.session.commit()
            flash('Категория успешно обновлена!', 'success')
            return redirect(url_for('admin_panel'))
        
        elif request.method == 'GET':
            form.name.data = category.name
            form.description.data = category.description
            form.order.data = category.order
        
        return render_template('admin/edit_category.html', form=form, category=category)
    
    # Удаление категории (только если нет разделов)
    @app.route('/admin/category/<int:category_id>/delete')
    @login_required
    def delete_category(category_id):
        if not current_user.is_moderator:
            abort(403)
        
        category = Category.query.get_or_404(category_id)
        
        if category.sections.count() > 0:
            flash('Нельзя удалить категорию, в которой есть разделы!', 'danger')
            return redirect(url_for('admin_panel'))
        
        db.session.delete(category)
        db.session.commit()
        flash('Категория успешно удалена!', 'success')
        return redirect(url_for('admin_panel'))
    
    # Удаление раздела (только если нет тем)
    @app.route('/admin/section/<int:section_id>/delete')
    @login_required
    def delete_section(section_id):
        if not current_user.is_moderator:
            abort(403)
        
        section = Section.query.get_or_404(section_id)
        
        if section.threads.count() > 0:
            flash('Нельзя удалить раздел, в котором есть темы!', 'danger')
            return redirect(url_for('admin_panel'))
        
        db.session.delete(section)
        db.session.commit()
        flash('Раздел успешно удален!', 'success')
        return redirect(url_for('admin_panel'))
    
    @app.route('/admin/category/<int:category_id>/force_delete')
    @login_required
    def force_delete_category(category_id):
        """Принудительное удаление категории со всеми разделами"""
        if not current_user.is_moderator:
            abort(403)
        
        category = Category.query.get_or_404(category_id)
        
        try:
            # Удаляем все разделы в категории (и их темы/сообщения через каскад)
            for section in category.sections.all():
                db.session.delete(section)
            
            # Удаляем саму категорию
            db.session.delete(category)
            db.session.commit()
            
            flash(f'Категория "{category.name}" и все её разделы успешно удалены!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при удалении категории: {str(e)}', 'danger')
            print(f"Ошибка принудительного удаления: {e}")
        
        return redirect(url_for('admin_panel'))

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403