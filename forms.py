from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DateField
from wtforms.validators import InputRequired, Length, EqualTo, DataRequired


class LoginForm(FlaskForm):
    username = StringField('Nazwa użytkownika', validators=[InputRequired(), Length(max=80)])
    password = PasswordField('Hasło', validators=[InputRequired(), Length(min=6, max=80)])
    submit = SubmitField('Zaloguj')

class RegistrationForm(FlaskForm):
    username = StringField('Nazwa użytkownika', validators=[InputRequired(), Length(max=80)])
    password = PasswordField('Hasło', validators=[InputRequired(), Length(min=6, max=80)])
    confirm_password = PasswordField('Potwierdź hasło', validators=[InputRequired(), Length(min=6, max=80), EqualTo('password', message='Hasła muszą być identyczne.')])
    submit = SubmitField('Zarejestruj')

class TaskForm(FlaskForm):
        name = StringField('Nazwa Zadania', validators=[DataRequired()])
        description = TextAreaField('Opis', validators=[DataRequired()])
        deadline = DateField('Termin', format='%Y-%m-%d', validators=[DataRequired()])
        submit = SubmitField('Dodaj Zadanie')