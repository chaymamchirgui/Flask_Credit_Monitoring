from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, IntegerField
from wtforms import validators
from wtforms.fields.core import FloatField
from wtforms.validators import DataRequired

class UserDataForm(FlaskForm):
    type = SelectField('Type', validators=[DataRequired()],
                                choices=[('income', 'income'),
                                        ('expense', 'expense')])
    category = SelectField("Category", validators=[DataRequired()],
                                            choices =[('rent', 'rent'),
                                            ('salary', 'salary'),
                                            ('investment', 'investment'),
                                            ('side_hustle', 'side_hustle')
                                            ]
                            )
    amount = IntegerField('Amount', validators = [DataRequired()])                                   
    submit = SubmitField('Generate Report')  

class CountryForm(FlaskForm):
    field = SelectField("field" , validators=[DataRequired()] , choices=[
                                                                ('France', 'France'),
                                                                ('Allemagne','Allemagne'),
                                                                ('Etats-Unis', 'Etats-Unis'),
                                                                ('Canada', 'Canada'),
                                                                ('Chine', 'Chine'),
                                                                ('Hong Kong', 'Hong Kong'),
                                                                ('Tunisia', 'Tunisia')
                                                              ])      
                                                           
    submit = SubmitField('Filter')

class SearchForm(FlaskForm):
    name = StringField("name" , validators=[DataRequired()] )
    submit = SubmitField('find')

class AddEntrepriseForm(FlaskForm):
    name = StringField("name" , validators=[DataRequired()])
    country = SelectField("country" , validators=[DataRequired()] , choices=[
                                                                ('France', 'France'),
                                                                ('Allemagne','Allemagne'),
                                                                ('Etats-Unis', 'Etats-Unis'),
                                                                ('Canada', 'Canada'),
                                                                ('Chine', 'Chine'),
                                                                ('Hong Kong', 'Hong Kong'),
                                                                ('Tunisia', 'Tunisia')
                                                              ])   

    total_actifs = StringField("Total assets" , validators=[DataRequired()]) 
    total_passifs = StringField("Total Liabilities " , validators=[DataRequired()]) 
    capitaux_propres = StringField("Equity" , validators=[DataRequired()]) 
    free_cash_flow = StringField("Free cash flow" , validators=[DataRequired()]) 
    dette_nette = StringField("Net Debts" , validators=[DataRequired()]) 
    resultat_net = StringField("Net Income" , validators=[DataRequired()]) 
    resultat_exploitation = StringField("Operating Income" , validators=[DataRequired()]) 
    chiffre_affaires = StringField("Net sales" , validators=[DataRequired()]) 
    capitalisation = StringField("Capitalization" , validators=[DataRequired()]) 
    submit = SubmitField('Add')
class AddClientForm(FlaskForm):
    name = StringField("Company Name" , validators=[DataRequired()])
    country = SelectField("Country" , validators=[DataRequired()] , choices=[
                                                                ('France', 'France'),
                                                                ('Allemagne','Allemagne'),
                                                                ('Etats-Unis', 'Etats-Unis'),
                                                                ('Canada', 'Canada'),
                                                                ('Chine', 'Chine'),
                                                                ('Hong Kong', 'Hong Kong'),
                                                                ('Tunisia', 'Tunisia')
                                                              ])   
    phone=StringField("Phone Number" , validators=[DataRequired()])
    mail = StringField("Mail" , validators=[DataRequired()])
    adresse=StringField("Adress" , validators=[DataRequired()])
    submit = SubmitField('Generate')
class addImage(FlaskForm):
    submit=SubmitField('upload')