from datetime import datetime
from random import randint
from flask import Flask, render_template, request, redirect, url_for, flash, g
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from transliterate import translit
from werkzeug.security import generate_password_hash, check_password_hash
from peewee import *
from flask_login import UserMixin
from forms import LoginForm, MessageForm, RegisterForm
from flask_bootstrap import Bootstrap
from config import DATABASE_NAME, DATABASE_USER, DATABASE_PWD, DATABASE_HOST

# Описание необходимых переменных

ENV = 'dev'
Messages = ''
app = Flask(__name__)
bootstrap = Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app)
app.secret_key = 'some secret key'
# Создание базы данных и описание моделей

if ENV == 'dev':
    app.debug = True
    db = PostgresqlDatabase(database=DATABASE_NAME, user=DATABASE_USER,
                            password=DATABASE_PWD,
                            host=DATABASE_HOST)


class Users(Model, UserMixin):
    class Meta:
        database = db
        table_name = "users"

    name = CharField()
    surname = CharField()
    middle_name = CharField()
    nickname = CharField()
    status = CharField()
    email = CharField(unique=True)
    password = CharField()
    phone_number = CharField()


class Posts(Model):
    class Meta:
        database = db
        table_name = "posts"

    title = CharField()
    category = CharField()
    content = TextField()
    author = ForeignKeyField(Users, backref='posts_author')
    create_date = DateTimeField()
    is_published = BooleanField(default=True)


class Notification(Model):
    class Meta:
        database = db
        table_name = "notification"

    title = CharField()
    message = TextField()
    sender = ForeignKeyField(Users, backref='notify_sender')
    recipient = ForeignKeyField(Users, backref='notify_recipient')
    date = DateTimeField()
    status_view = BooleanField(default=False)


class CommentsH(Model):
    class Meta:
        database = db
        table_name = "comments_h"

    k1h_grade = IntegerField()
    k1h = CharField()
    k2h_grade = IntegerField()
    k2h = CharField()
    k3h_grade = IntegerField()
    k3h = CharField()
    k4h_grade = IntegerField()
    k4h = CharField()
    k5h_grade = IntegerField()
    k5h = CharField()
    k6h_grade = IntegerField()
    k6h = CharField()
    k7h_grade = IntegerField()
    k7h = CharField()
    total = IntegerField()
    date = DateTimeField()
    author = ForeignKeyField(Users, backref='history_comments')
    category = CharField(default='История')
    post_id = ForeignKeyField(Posts, backref='post_id_h')


class CommentsS(Model):
    class Meta:
        database = db
        table_name = "comments_s"

    k1s_grade = IntegerField()
    k1s = CharField()
    k2s_grade = IntegerField()
    k2s = CharField()
    k3s_grade = IntegerField()
    k3s = CharField()
    k4s_grade = IntegerField()
    k4s = CharField()
    total = IntegerField()
    date = DateTimeField()
    author = ForeignKeyField(Users, backref='social_comments')
    category = CharField(default='Обществознание')
    post_id = ForeignKeyField(Posts, backref='post_id_s')


class Messages(Model):
    class Meta:
        database = db
        table_name = "messages"

    sender = ForeignKeyField(Users, backref='message_sender')
    recipient = ForeignKeyField(Users, backref='message_recipient')
    theme = CharField()
    message = TextField()
    date = DateTimeField()
    is_read = BooleanField(default=False)


# Контекст-процессоры и иные декораторы

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))


@login_manager.user_loader
def load_user(user_id):
    return Users.get(Users.id == user_id)


@app.context_processor
def sidebar():
    # Вывод бокового сайдбара. Новые материалы на сайте - Начало секции
    last_posts = Posts.select().order_by(Posts.create_date.desc()).limit(5)
    # Вывод бокового сайдбара. Новые материалы на сайте - Конец секции
    # Вывод бокового сайдбара. Имеющие максимальный балл - Начало секции
    max_total_h = CommentsH.select().join(Posts).where(CommentsH.post_id == Posts.id).order_by(
        CommentsH.total.desc()).limit(5)
    max_total_s = CommentsS.select().join(Posts).order_by(CommentsS.total.desc()).limit(5)
    # Вывод бокового сайдбара. Имеющие максимальный балл - Конец секции
    return dict(last_posts=last_posts, max_total_h=max_total_h, max_total_s=max_total_s)


@app.context_processor
def need_info():
    rand_id = randint(0, 10)
    # Определение статуса пользователя, система доступа - Начало секции
    u_status = ''
    u_id = 0
    u_name = ''
    u_surname = ''
    u_middle_name = ''
    u_nickname = ''
    u_phone = ''
    u_email = ''
    cu_name = ''
    cu_surname = ''
    cu_middle_name = ''
    cu_nickname = ''
    cu_email = ''
    cu_phone = ''
    g.user = current_user.get_id()
    user_info = Users.select().where(Users.id == g.user)
    for now_user in user_info:
        u_status = now_user.status
        u_id = now_user.id
        cu_name = now_user.name
        cu_surname = now_user.surname
        cu_middle_name = now_user.middle_name
        cu_nickname = now_user.nickname
        cu_email = now_user.email
        cu_phone = now_user.phone_number
    # Определение статуса пользователя, система доступа - Конец секции
    # Формирование ссылок на пользователей - Начало секции
    all_users = Users.select()
    for i in all_users:
        u_name = i.name
        u_surname = i.surname
        u_middle_name = i.middle_name
        u_nickname = i.nickname
        u_email = i.email
        u_phone = i.phone_number
    # Формирование ссылок на пользователей - Конец секции
    return dict(u_status=u_status, u_id=u_id, all_users=all_users, u_name=u_name, u_surname=u_surname,
                u_middle_name=u_middle_name, u_nickname=u_nickname, u_phone=u_phone, u_email=u_email,
                cu_name=cu_name, cu_surname=cu_surname, cu_email=cu_email, cu_nickname=cu_nickname, cu_phone=cu_phone,
                cu_middle_name=cu_middle_name)


# Маршруты

@app.route('/', methods=['GET', 'POST'])
def index():
    # Вывод всех постов - Начало секции
    public_posts = Posts.select().join(Users).where(Users.id == Posts.author).order_by(Posts.create_date.desc())
    # Вывод всех постов - Конец секции
    return render_template('index.html', public_posts=public_posts)


@app.route('/users')
def users():
    return render_template('users.html')


@app.route('/add', methods=['GET', 'POST'])
def add():
    return render_template('add.html')


@app.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    # Добавление и вывод комментариев - Начало секции
    post_id = Posts.get(Posts.id == id)
    if request.method == 'POST':
        current_category = Posts.select(Posts.category).where(Posts.id == post_id)
        for cat in current_category:
            if cat.category == 'История':
                k1h = request.form.get('k1h')
                k1h_grade = request.form.get('k1h_grade')
                k2h = request.form.get('k2h')
                k2h_grade = request.form.get('k2h_grade')
                k3h = request.form.get('k3h')
                k3h_grade = request.form.get('k3h_grade')
                k4h = request.form.get('k4h')
                k4h_grade = request.form.get('k4h_grade')
                k5h = request.form.get('k5h')
                k5h_grade = request.form.get('k5h_grade')
                k6h = request.form.get('k6h')
                k6h_grade = request.form.get('k6h_grade')
                k7h = request.form.get('k7h')
                k7h_grade = request.form.get('k7h_grade')
                total_h = int(k1h_grade) + int(k2h_grade) + int(k3h_grade) + int(k4h_grade) + int(k5h_grade) + int(
                    k6h_grade) + int(k7h_grade)
                g.user = current_user.get_id()
                create_date = datetime.today()
                post_id_h = post_id
                CommentsH.create(k1h=k1h, k2h=k2h, k3h=k3h, k4h=k4h, k5h=k5h, k6h=k6h, k7h=k7h,
                                 k1h_grade=k1h_grade, k2h_grade=k2h_grade, k3h_grade=k3h_grade,
                                 k4h_grade=k4h_grade, k5h_grade=k5h_grade, k6h_grade=k6h_grade,
                                 k7h_grade=k7h_grade, total=total_h, author=g.user, post_id=post_id_h,
                                 date=create_date)
                current_author_post = Posts.select(Posts).join(Users).where(Posts.id == post_id,
                                                                            Users.id == Posts.author)
                title = 'Ваше сочинение получило новую оценку'
                for j in current_author_post:
                    sender = Users.select().where(Users.id == g.user)
                    for i in sender:
                        message = i.surname + ' ' + i.name + ' оценил ваше историческое сочинение по периоду ' + j.title
                        recipient = j.author.id
                ntf_date = datetime.today()
                Notification.create(title=title, message=message, sender=sender, recipient=recipient, date=ntf_date)
                return redirect(request.url)
            elif cat.category == 'Обществознание':
                k1s = request.form.get('k1s')
                k1s_grade = request.form.get('k1s_grade')
                k2s = request.form.get('k2s')
                k2s_grade = request.form.get('k2s_grade')
                k3s = request.form.get('k3s')
                k3s_grade = request.form.get('k3s_grade')
                k4s = request.form.get('k4s')
                k4s_grade = request.form.get('k4s_grade')
                total_s = int(k1s_grade) + int(k2s_grade) + int(k3s_grade) + int(k4s_grade)
                g.user = current_user.get_id()
                create_date = datetime.today()
                post_id_s = post_id
                CommentsS.create(k1s=k1s, k2s=k2s, k3s=k3s, k4s=k4s, k1s_grade=k1s_grade, k2s_grade=k2s_grade,
                                 k3s_grade=k3s_grade,
                                 k4s_grade=k4s_grade, total=total_s, author=g.user, post_id=post_id_s, date=create_date)
                current_author_post = Posts.select(Posts).join(Users).where(Posts.id == post_id,
                                                                            Users.id == Posts.author)
                title = 'Ваше эссе получило новую оценку'
                for j in current_author_post:
                    sender = Users.select().where(Users.id == g.user)
                    for i in sender:
                        message = i.surname + ' ' + i.name + ' оценил ваше эссе на тему ' + j.title
                    recipient = j.author.id
                ntf_date = datetime.today()
                Notification.create(title=title, message=message, sender=sender, recipient=recipient, date=ntf_date)
                return redirect(request.url)
    comments_h = CommentsH.select().join(Users).where(CommentsH.post_id == post_id,
                                                      Users.id == CommentsH.author).order_by(CommentsH.date.desc())
    comments_s = CommentsS.select().join(Users).where(CommentsS.post_id == post_id,
                                                      Users.id == CommentsS.author).order_by(CommentsS.date.desc())
    # Добавление и вывод комментариев - Конец секции
    return render_template("post.html", post=post_id, comments_h=comments_h, comments_s=comments_s)


@app.route('/add_post', methods=['GET', 'POST'])
def add_post():
    title = request.form.get('title')
    category = request.form.get('category')
    content = request.form.get('content')
    g.user = current_user.get_id()
    create_date = datetime.today()
    Posts.create(title=title, content=content, category=category, author=g.user, create_date=create_date)

    return redirect(url_for('index'))


@app.route('/about', methods=['GET', 'POST'])
def about():
    return render_template('about.html')


@app.route('/contacts')
def contacts():
    return render_template('contacts.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    rand_id = randint(0, 10)
    # Форма регистрации - Начало секции
    if request.method == "POST" and form.validate_on_submit():
        name = form.name.data
        surname = form.surname.data
        middle_name = form.middle_name.data
        status = form.status.data
        email = form.email.data
        password = form.password.data
        repeat_password = form.repeat_pass.data
        phone_number = form.phone.data
        if not (name or surname or status or email or password or repeat_password):
            flash('Пожалуйста, заполните обязательные для регистрации поля')
        elif password != repeat_password:
            flash('Пароли не совпадают! Попробуйте ввести выбранный пароль ещё раз!')
        else:
            hash_pwd = generate_password_hash(password)
            Users.create(name=name, surname=surname, middle_name=middle_name, status=status, email=email,
                         password=hash_pwd, phone_number=phone_number, nickname=translit(str(name).lower()
                                                                                         + str(surname).lower()
                                                                                         + str(rand_id), 'ru',
                                                                                         reversed=True))
            return redirect(url_for('index'))
    # Форма регистрации - Конец секции
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Форма входа на сайт - Начало секции
    form = LoginForm()
    if form.validate_on_submit():
        if form.email.data and form.password.data:
            user_email = Users.get(Users.email == form.email.data)
            if form.email.data and check_password_hash(user_email.password, form.password.data):
                login_user(user_email)
                return redirect(url_for('index'))
            else:
                flash('Адрес электронной почты или пароль введены неверно. Попробуйте ещё раз.')
        else:
            flash('Вы не ввели адрес электронной почты или пароль')
    # Форма входа на сайт - Конец секции
    return render_template('login.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/profile/<nickname>', methods=['GET', 'POST'])
@login_required
def profile(nickname):
    # Используемые переменные
    user_surname = ''
    user_id = 0
    student_post_count = 0
    all_count = 0
    notification_count_new = 0
    notification_count_old = 0
    user_middle_name = ''
    user_name = ''
    user_nickname = ''
    user_status = ''
    user_email = ''
    user_phone = ''
    student_post_list = ''
    expert_comments_h = ''
    expert_comments_s = ''
    expert_comments_h_last = ''
    expert_comments_s_last = ''
    g.user = current_user.get_id()
    all_users = Users.select().where(Users.nickname == nickname)
    form = MessageForm()
    # Используемые переменные
    # Создание профилей пользователя - Начало секции
    for p_user in all_users:
        user_id = p_user.id
        user_name = p_user.name
        user_surname = p_user.surname
        user_middle_name = p_user.middle_name
        user_nickname = p_user.nickname
        user_status = p_user.status
        user_email = p_user.email
        user_phone = p_user.phone_number
        # Создание профилей пользователя - Конец секции
        # Работа с уведомлениями - Начало секции
    notification_list = Notification.select().join(Users, on=Notification.recipient).where(
        Notification.recipient == g.user).order_by(Notification.date.desc())
    notification_count_new = Notification.select().join(Users, on=Notification.recipient).where(
        Notification.recipient == g.user, Notification.status_view == False).count()
    notification_count_old = Notification.select().join(Users, on=Notification.recipient).where(
        Notification.recipient == g.user, Notification.status_view == True).count()
    # Работа с уведомлениями - Конец секции
    # Работа с личными сообщениями - Начало секции
    message_list = Messages.select().join(Users, on=Messages.recipient).where(
        Messages.recipient == g.user).order_by(Messages.date.desc())
    message_count_new = Messages.select().join(Users, on=Messages.recipient).where(
        Messages.recipient == g.user, Messages.is_read == False).count()
    message_count_old = Messages.select().join(Users, on=Messages.recipient).where(
        Messages.recipient == g.user, Messages.is_read == True).count()
    # Работа с личными сообщениями - Начало секции
    # Вывод опубликованных учеником постов - Начало секции
    # for student in all_users:
    # if student.status == 'Учащийся':
    student_post_list = Posts.select().join(Users).where(Users.nickname == nickname)
    student_post_count = Posts.select().join(Users).where(Users.nickname == nickname).count()
    # Вывод опубликованных учеником постов - Конец секции
    # Вывод оценок, выставленных экспертом - Начало секции
    # for expert in all_users:
    #     if expert.status == 'Педагог' or expert.status == 'Эксперт' or expert.status == 'Репетитор':
    expert_comments_h = CommentsH.select().join(Posts).where(CommentsH.post_id == Posts.id,
                                                             CommentsH.author == g.user)
    expert_comments_s = CommentsS.select().join(Posts).where(CommentsS.post_id == Posts.id,
                                                             CommentsS.author == g.user)
    expert_comments_h_last = CommentsH.select().join(Users).where(Users.nickname == nickname)
    expert_comments_s_last = CommentsS.select().join(Users).where(Users.nickname == nickname)
    expert_comments_h_count = CommentsH.select().join(Posts).where(CommentsH.post_id == Posts.id,
                                                                   CommentsH.author == g.user).count()
    expert_comments_s_count = CommentsS.select().join(Posts).where(CommentsS.post_id == Posts.id,
                                                                   CommentsS.author == g.user).count()
    all_count = expert_comments_h_count + expert_comments_s_count
    # Вывод оценок, выставленных экспертом - Конец секции
    # Форма отправки сообщения - Начало секции
    if request.method == "POST" and form.validate_on_submit():
        theme = form.theme.data
        message = form.message.data
        Messages.create(theme=theme, message=message, sender=g.user, recipient=user_id,
                        date=datetime.today())
        return redirect(request.url)
        # Форма отправки сообщения - Конец секции
    if user_id == g.user:
        return render_template('my_profile.html', user_surname=user_surname,
                               user_middle_name=user_middle_name, user_name=user_name, user_nickname=user_nickname,
                               user_status=user_status, user_email=user_email, user_phone=user_phone,
                               notification_list=notification_list, student_post_list=student_post_list,
                               expert_comments_h=expert_comments_h, expert_comments_s=expert_comments_s,
                               message_list=message_list, message_count_new=message_count_new,
                               message_count_old=message_count_old,
                               notification_count_new=notification_count_new,
                               notification_count_old=notification_count_old, student_post_count=student_post_count,
                               all_count=all_count)
    else:
        return render_template('user.html', user_surname=user_surname,
                               user_middle_name=user_middle_name, user_name=user_name, user_nickname=user_nickname,
                               user_status=user_status, user_email=user_email, user_phone=user_phone,
                               notification_list=notification_list, student_post_list=student_post_list,
                               expert_comments_h=expert_comments_h, expert_comments_s=expert_comments_s,
                               expert_comments_h_last=expert_comments_h_last,
                               expert_comments_s_last=expert_comments_s_last, form=form)


@app.route('/update_ntf/<int:ntf_id>')
def update_ntf(ntf_id):
    nickname = ''
    g.user = current_user.get_id()
    current_nickname = Users.select().where(Users.id == g.user)
    for j in current_nickname:
        nickname = j.nickname
    Notification.update(status_view=True).where(Notification.id == ntf_id).execute()
    return redirect(url_for('profile', nickname=nickname))


@app.route('/update_msg/<int:msg_id>')
def update_msg(msg_id):
    nickname = ''
    g.user = current_user.get_id()
    current_nickname = Users.select().where(Users.id == g.user)
    for j in current_nickname:
        nickname = j.nickname
    Messages.update(is_read=True).where(Messages.id == msg_id).execute()
    return redirect(url_for('profile', nickname=nickname))


@app.route('/delete_ntf/<int:ntf_id>')
def delete_ntf(ntf_id):
    nickname = ''
    g.user = current_user.get_id()
    current_nickname = Users.select().where(Users.id == g.user)
    for j in current_nickname:
        nickname = j.nickname
    Notification.delete().where(Notification.id == ntf_id).execute()
    return redirect(url_for('profile', nickname=nickname) + '#ntf')


@app.route('/delete_msg/<int:msg_id>')
def delete_msg(msg_id):
    nickname = ''
    g.user = current_user.get_id()
    current_nickname = Users.select().where(Users.id == g.user)
    for j in current_nickname:
        nickname = j.nickname
    Messages.delete().where(Messages.id == msg_id).execute()
    return redirect(url_for('profile', nickname=nickname))


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    my_nickname = ''
    g.user = current_user.get_id()
    current_nickname = Users.select().where(Users.id == g.user)
    for j in current_nickname:
        my_nickname = j.nickname
    rand_id = randint(0, 10)
    if request.method == "POST":
        name = request.form.get('name')
        # surname = request.form.get('surname')
        # middle_name = request.form.get('middle_name')
        # status = request.form.get('status')
        # nickname = translit(str(name).lower()
        #                     + str(surname).lower()
        #                     + str(rand_id), 'ru',
        #                     reversed=True)
        # email = request.form.get('email')
        # phone = request.form.get('phone')
        Users.update(name=name).where(Users.id == g.user).execute()

        return redirect(url_for('profile', nickname=my_nickname))
    return render_template('editprofile.html')


# Инициализация необходимых функций

def init_db():
    db.connect()
    db.drop_tables([Users, Posts, CommentsH, CommentsS, Notification, Messages], safe=True)
    db.create_tables([Users, Posts, CommentsH, CommentsS, Notification, Messages], safe=True)


if __name__ == '__main__':
    app.run()
