from wtforms import Form, StringField, RadioField, TextAreaField, PasswordField, validators

class RegistrationForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=30)])
    email = StringField('Email', [validators.Length(min=6, max=30)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.Length(min=6, max=30),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


class ReviewForm(Form):
    rating = RadioField(choices = [('1', ''), ('2', ''), ('3', ''), ('4', ''), ('5', '')])
    review = TextAreaField('', [validators.Length(min=4, max=200)])
