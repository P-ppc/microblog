from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, TextAreaField, FileField
from wtforms.validators import DataRequired, Length
from app.models import User
from app import db

class LoginForm(Form):
    username = StringField('username', validators = [DataRequired()])
    email = StringField('email', validators = [DataRequired()])
    code = StringField('code', validators = [DataRequired()])
    remember_me = BooleanField('remember_me', default = False)
    
    def __init__(self, g_code):
        Form.__init__(self)
        self.g_code = g_code

    def validate(self):
        if not Form.validate(self):
            return False

        # for code
        if self.g_code == '' or self.g_code != self.code.data:
            self.code.errors.append('Wrong code!')
            return False

        user_by_name = User.query.filter_by(nickname = self.username.data).first()
        user_by_email = User.query.filter_by(email = self.email.data).first()
        if user_by_name is None and user_by_email is None:
            user = User(nickname = self.username.data, email = self.email.data)
            db.session.add(user)
            db.session.commit()
            return True
        
        if user_by_name is None and user_by_email is not None:
            self.username.errors.append('This username is not exist and email is exist.')
            return False
        if user_by_name is not None and user_by_email is None:
            self.email.errors.append('This email is not exist and username is exist.')
            return False
    
        if user_by_name is not None and user_by_email is not None:
            if user_by_name.nickname == user_by_email.nickname:
                return True
            else:
                self.email.errors.append("wrong email with username.")
                return False
        return True
        

class EditForm(Form):
    username = StringField('username', validators = [DataRequired()])
    about_me = TextAreaField('about_me', validators = [Length(min = 0, max = 140)])
    
    def __init__(self, original_username, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.original_username = original_username

    def validate(self):
        if not Form.validate(self):
            return False
        if self.username.data == self.original_username:
            return True
        user = User.query.fliter_by(nickname = self.username.data).first()
        if user != None:
            self.username.errors.append('This username is already in use.')
            return False
        return True

class SearchForm(Form):
    search = StringField('search', validators = [DataRequired()])
