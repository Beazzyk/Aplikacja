from datetime import datetime

from flask import Flask, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import InputRequired, Length
from werkzeug.security import generate_password_hash, check_password_hash
from forms import TaskForm


app = Flask(__name__)
app.secret_key = 'twoj_bardzo_tajny_klucz'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///czas_pracy.db'
app.config['SQLALCHEMY_BINDS'] = {
    'opinie': 'sqlite:///opinie.db'
}
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80))
    entries = db.relationship('TimeEntry', backref='user', lazy='dynamic')


class TimeEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class TimeEntryForm(FlaskForm):
    start_time = StringField('Czas rozpoczęcia (YYYY-MM-DD HH:MM)', validators=[InputRequired(), Length(max=50)])
    end_time = StringField('Czas zakończenia (YYYY-MM-DD HH:MM)', validators=[InputRequired(), Length(max=50)])
    submit = SubmitField('Dodaj zapis')

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    deadline = db.Column(db.Date, nullable=True)

class Feedback(db.Model):
    __bind_key__ = 'opinie'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)


    def __repr__(self):
        return '<Feedback {}>'.format(self.id)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def main():
    if current_user.is_authenticated:
        entries = TimeEntry.query.filter_by(user_id=current_user.id).all()
        return render_template('main.html', entries=entries)
    else:
        return render_template('main.html')


@app.route('/add_entry', methods=['GET', 'POST'])
def add_entry():
    form = TimeEntryForm()
    if form.validate_on_submit():
        try:
            start_time = datetime.strptime(form.start_time.data, '%Y-%m-%d %H:%M')
            end_time = datetime.strptime(form.end_time.data, '%Y-%m-%d %H:%M')
            if start_time < end_time:
                entry = TimeEntry(start_time=start_time, end_time=end_time, user=current_user)
                db.session.add(entry)
                db.session.commit()
                flash('Zapisano czas pracy.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Czas rozpoczęcia musi być wcześniejszy niż czas zakończenia.', 'danger')
        except ValueError:
            flash('Bledny format czasu. Poprawny format to YYYY-MM-DD HH:MM.', 'danger')
    return render_template('add_entry.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Zalogowano pomyślnie.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Nieprawidłowa nazwa użytkownika lub hasło.', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Nazwa użytkownika jest już zajęta.', 'danger')
        elif password != confirm_password:
            flash('Hasła nie pasują do siebie.', 'danger')
        else:
            new_user = User(username=username, password=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            flash('Konto zostało utworzone. Możesz się teraz zalogować.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    entries = TimeEntry.query.all()
    return render_template('dashboard.html', entries = entries)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/view_reports')
@login_required
def view_reports():
    reports = TimeEntry.query.all()
    return render_template('reports.html', reports=reports)


from flask import request


@app.route('/manage_tasks', methods=['GET', 'POST'])
@login_required
def manage_tasks():
    form = TaskForm()

    if form.validate_on_submit():
        task = Task(name=form.name.data, description=form.description.data, deadline=form.deadline.data)
        db.session.add(task)
        db.session.commit()
        flash('Zadanie zostało dodane!')
        return redirect(url_for('manage_tasks'))

    if 'delete' in request.form:
        task_id = request.form['delete']
        task = Task.query.get(task_id)
        if task:
            db.session.delete(task)
            db.session.commit()
            flash('Zadanie zostało usunięte.')

    if 'edit' in request.form:
        task_id = request.form['edit']
        task = Task.query.get(task_id)
        if task:
            return redirect(url_for('edit_task', task_id=task_id))

    tasks = Task.query.all()
    return render_template('manage_tasks.html', form=form, tasks=tasks)

@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    form = TaskForm(obj=task)
    if form.validate_on_submit():
        task.name = form.name.data
        task.description = form.description.data
        task.deadline = form.deadline.data
        db.session.commit()
        flash('Zadanie zostało zaktualizowane.')
        return redirect(url_for('manage_tasks'))
    return render_template('edit_task.html', form=form, task=task)

@app.route('/delete_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash('Zadanie zostało usunięte.')
    return redirect(url_for('manage_tasks'))


@app.route('/view_calendar')
@login_required
def view_calendar():
    return render_template('view_calendar.html')

@app.route('/user_settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    if request.method == 'POST':
        new_password = request.form.get('password')
        current_user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Hasło zostało zmienione.')
        return redirect(url_for('user_settings'))

    return render_template('user_settings.html')

@app.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    if request.method == 'POST':
        content = request.form.get('feedback')
        new_feedback = Feedback(content=content, user_id=current_user.id)
        db.session.add(new_feedback)
        db.session.commit()
        flash('Dziękujemy za Twoją opinię!', 'success')
        return redirect(url_for('feedback'))

    feedbacks = Feedback.query.all()
    return render_template('feedback.html', feedbacks=feedbacks)





if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

with app.app_context():
    db.create_all()