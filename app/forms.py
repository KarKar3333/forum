from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, PasswordField, SubmitField, BooleanField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional, NumberRange
from app.models import User, Category

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', 
                          validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', 
                       validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', 
                            validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтвердите пароль', 
                                    validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя пользователя уже занято.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже используется.')

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class ThreadForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Сообщение', validators=[DataRequired()])
    submit = SubmitField('Создать тему')

class PostForm(FlaskForm):
    content = TextAreaField('Сообщение', validators=[DataRequired()])
    submit = SubmitField('Отправить')

class ProfileForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    about = TextAreaField('О себе', validators=[Optional(), Length(max=500)])
    avatar = FileField('Аватарка', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!')])
    submit = SubmitField('Обновить профиль')
    
    def __init__(self, original_username, original_email, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
    
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Это имя пользователя уже занято.')
    
    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Этот email уже используется.')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Текущий пароль', validators=[DataRequired()])
    new_password = PasswordField('Новый пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтвердите новый пароль', 
                                    validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Сменить пароль')

class CategoryForm(FlaskForm):
    name = StringField('Название категории', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Описание категории', validators=[Optional(), Length(max=500)])
    order = IntegerField('Порядок отображения', validators=[Optional(), NumberRange(min=0)], default=0)
    submit = SubmitField('Создать категорию')

class SectionForm(FlaskForm):
    name = StringField('Название раздела', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Описание раздела', validators=[Optional(), Length(max=500)])
    category_id = SelectField('Категория', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Создать раздел')
    
    def __init__(self, *args, **kwargs):
        super(SectionForm, self).__init__(*args, **kwargs)
        # Заполняем выбор категорий
        self.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.order).all()]

class SortForm(FlaskForm):
    sort_by = SelectField('Сортировка', choices=[
        ('updated_at_desc', 'Новые сначала'),
        ('updated_at_asc', 'Старые сначала'),
        ('title_asc', 'По названию (А-Я)'),
        ('title_desc', 'По названию (Я-А)'),
        ('post_count_desc', 'По активности')
    ], default='updated_at_desc')
    submit = SubmitField('Применить')