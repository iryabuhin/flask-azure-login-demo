from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class APIUrlInputField(FlaskForm):
    url = StringField('name', validators=[DataRequired()])
