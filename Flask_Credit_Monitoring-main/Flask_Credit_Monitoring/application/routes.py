from flask.globals import request
from pandas.core.frame import DataFrame
from application import app
from flask import render_template, url_for, redirect,flash
from application.form import *
from application.models import IncomeExpenses
from application import db
import pandas as pd
import numpy as np
import json
import pickle
import plotly.graph_objects as go
import plotly
import re 
import os
from ExtractTable import ExtractTable

df = pd.read_excel(r"new_data.xlsx",header=[0,1],index_col=0)
df.index = range(len(df))
df_index = df
@app.route('/<int:page>', methods = ["POST", "GET"])
def index(page):
    global df_index
    form = CountryForm()
    form2 = SearchForm()
    flag = request.args.get('flag')
    if flag == '0':
        df_index = df
    if form.validate_on_submit():
        country = form.field.data
        subset = get_by_country(country)
        df_index = subset
        return redirect(url_for("index",page='1'))
    
    if form2.validate_on_submit():
        name = form2.name.data
        try:
            subset = get_by_name(name)
        except:
            flash(f"cannot find {name} in the database", "danger")
            return redirect(url_for("index",page='1'))
        df_index = subset
        return redirect(url_for("index",page='1'))


    page = int(page)
    eps_per_page = 13
    begin_index = (page-1) * eps_per_page 
    end_index = page * eps_per_page
    max = len(df_index)//13
    #entries = IncomeExpenses.query.order_by(IncomeExpenses.date.desc()).all()
    entries = df_index[begin_index:end_index]
    return render_template('index.html', entries = entries,page = page,max=max,form = form,form2 = form2)


@app.route('/add', methods = ["POST", "GET"])
def add_entreprise():
    form = AddEntrepriseForm()
    if form.validate_on_submit():
        form_entry = handle_form_data(form)
        name = form_entry[0].split()[0]
        if name in df['name-country'][0].tolist():
            flash(f"entreprise {name} already exists", "danger")
            return redirect(url_for('index',page=1,flag=0))
        add_to_df(form_entry)
        flash(f"entreprise {name} has been added", "success")
        return redirect(url_for('index',page=1,flag=0))
    return render_template('add.html', title="Add Entreprise", form=form)
    
    
def get_by_country(country):
    global df
    subset = df[df['name-country'][1] == country]
    return subset

def handle_form_data(form):
    form_entry = []
    form_entry.append(form.name.data + " " + form.country.data)
    form_entry.append(form.total_actifs.data)
    form_entry.append(form.total_passifs.data)
    form_entry.append(form.capitaux_propres.data)
    form_entry.append(form.free_cash_flow.data)
    form_entry.append(form.dette_nette.data)
    form_entry.append(form.resultat_net.data)
    form_entry.append(form.resultat_exploitation.data)
    form_entry.append(form.chiffre_affaires.data)
    form_entry.append(form.capitalisation.data)
    return form_entry

def add_to_df(form_entry):
    new_entry = {}
    values = []
    global df
    for field in form_entry:
        for sub_field in field.split():
            try:
                values.append(np.float64(sub_field))
            except:
                values.append(sub_field)
    for (i,key) in enumerate(df.columns):
        new_entry[key] = values[i]
    df = df.append(pd.Series(new_entry,name=df.tail(1).index[0]+1))
    with pd.ExcelWriter(r"new_data.xlsx") as writer:
        df.to_excel(writer, startrow=0, startcol=0)

           
@app.route('/delete-post/<int:entry_id>')
def delete(entry_id):
    global df
    df = df.drop(entry_id)
    with pd.ExcelWriter(r"new_data.xlsx") as writer:
        df.to_excel(writer, startrow=0, startcol=0)
    page = (entry_id // 13)+1
    flash("Entry deleted", "success")
    return redirect(url_for('index',page=page,flag=0))



def get_3_years_values(id,feature):
    return df.loc[id][feature].tolist()
names = ['Total Actifs', 'Total Passif', 'Capitaux Propres',
       'Free Cash Flow', 'Dette Nette', 'Résultat net',
       "Résultat d'exploitation (EBIT)", "Chiffre d'affaires",
       'Capitalisation']
def get_all_features(year,id):
    dic = {}
    for name in names:
        dic[name] = df.loc[id][name][year]
    return dic

 # Uploading the Linear Model

def needed_data(data1,data2):
    needed_data = []
    for i in range(len(data1)):
        needed_data.append(data1[i])
        needed_data.append(data2[i])
    return needed_data

def get_chiffre_affaires(id):
    with open(r"Linear_Model.pkl", 'rb') as file:  
        LR_Model = pickle.load(file)
    data_2019 = list(get_all_features('2019',id).values())
    data_2020 = list(get_all_features('2020',id).values())
    CA_2021 = LR_Model.predict([needed_data(data_2019,data_2020)])
    return CA_2021[0]

def get_by_id(id):
    return df.loc[id]

def get_by_name(entry_name):
    pattern = re.compile(r"#?"+entry_name+"#",flags=re.I)
    names = df['name-country'][0].tolist()
    find = re.findall(pattern,"".join(name+'#' for name in names))[0]
    name = find.replace('#','')
    match = df[df['name-country'][0] == name]
    return match

def create_plot(id):
    data=[
    go.Bar(name='Assets', x=['2018', '2019', '2020'], y=df.loc[id]['Total Actifs'] ),
    go.Bar(name='Liabilities', x=['2018', '2019', '2020'], y=df.loc[id]['Dette Nette']),
    go.Bar(name='Equity', x=['2018', '2019', '2020'], y=df.loc[id]['Capitaux Propres'])
    ]
    graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON


@app.route('/')
def dashboard_empty():
    flash("Welcome Back", "success")
    return redirect(url_for("upload_image"))  

@app.route('/dashboard/<int:idenreprise>/<string:year>',methods=['POST','GET'])
def dashboard(idenreprise,year):
    #if idenreprise == "":
        #flash("Entreprise id is NULL", "danger")
        #return redirect(url_for("index"))
    idenreprise = int(idenreprise)
    if not (idenreprise in df.index):
        flash("Entreprise id not found in the db", "danger")
        return redirect(url_for("index"))       
   
    name = get_by_id(idenreprise)["name-country"][0]
    country = get_by_id(idenreprise)["name-country"][1]
    income_expense = [get_all_features(year,idenreprise)['Total Actifs'] , get_all_features(year,idenreprise)['Total Passif']]
    income_category = [
        get_all_features(year,idenreprise)["Chiffre d'affaires"],
        get_all_features(year,idenreprise)['Résultat net'],
        get_all_features(year,idenreprise)['Free Cash Flow'],
        get_all_features(year,idenreprise)['Dette Nette']
    ]
    income_expense = [float(item) for item in income_expense]
    income_category = [float(item) for item in income_category]
    CA_2021 = get_chiffre_affaires(idenreprise)
    over_time_expenditure = get_3_years_values(idenreprise,"Chiffre d'affaires")
    
    dates_label = ['2018','2019','2020','2021']
    var = over_time_expenditure 
    var = [float(item) for item in var]
    var.append(CA_2021)
    bar = create_plot(idenreprise) 
    return render_template('dashboard.html',
                            income_vs_expense=json.dumps(income_expense),
                            income_category=json.dumps(income_category),
                            over_time_expenditure=json.dumps(var),
                            dates_label =json.dumps(dates_label),
                            plot = bar,
                            id = idenreprise,
                            name_country = (name,country)
                            )
@app.route('/dashboard1',methods=['POST','GET'])
def dashboard1():
    global country_1
    global name_1
    data = pd.read_excel (r'Balance sheet.xlsx')
    data=pd.DataFrame(data)
    print(data['Total Assets'][1])
    data1=df = pd.read_excel (r'Income Statements.xlsx')
    data2=pd.read_excel (r'Cash Flow.xlsx')
    features1(data)
    features2(data1)
    features3(data2)
    #CapitalStructure
    CapitalStructure_score = totalStockholderEquity/Total_Asset1
    # Debt Service Capacity 
    Debt_Service_Capacity =Net_income1/totalRevenue1
    #Efficiency 
    Efficiency =Net_income1/totalRevenue1
    #size
    size=totalRevenue1
    profitability()
    leverage()
    operating_efficiency()
    Piotroski()
    altman()
    print(profitability_score)
    print(leverage_score)
    print(operating_efficiency_score)
    print(piotroski_score)
    print(altman_score)
    get_score()
    r1=r[0]
    return render_template('dashboard1.html',profitability_scores=json.dumps(profitability_score),
                           leverage_scores=json.dumps(leverage_score),
                           operating_efficiencys=json.dumps(operating_efficiency_score),
                           Piotroski_scores=json.dumps(piotroski_score),
                           altman_scores=json.dumps(altman_score),
                           scores=json.dumps(int(r1)),
                           capitalStructure_scores=json.dumps(CapitalStructure_score),
                           Debt_Service_Capacity_score=json.dumps(Debt_Service_Capacity),
                           Efficiency_score=json.dumps(Efficiency ),
                           size_score=json.dumps(float(size)),
                           debt_ratios=json.dumps(float(debt_ratio)),
                           name_country = (country_1,name_1) )
def get_score():
    # load the model from disk
    filename = 'finalized_model.sav'
    loaded_model = pickle.load(open(filename, 'rb'))
    x=np.array([A_score, B_score, D_score ,E_score], ndmin=2)
    global r
    r = loaded_model.predict(x)

country_1 = ""
name_1 = ""    
UPLOAD_FOLDER = 'upload_file'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
@app.route("/New client", methods=["GET", "POST"])
def upload_image():
    global name_1
    global country_1
    form1 = AddClientForm()
    form2=addImage()
    name_1 = form1.name.data
    country_1 = form1.country.data
    if form1.validate_on_submit():
        return redirect(url_for('dashboard1'))
    if form2.validate_on_submit():
        if request.method == "POST":

            if request.files:

                image = request.files["image"]
                image.save(os.path.join(app.config["UPLOAD_FOLDER"], image.filename))
                print("Image saved")
                et_sess = ExtractTable(api_key='ipu42VbhR3zUDWXsIQ5tQFPt4YobNgz686NWd2S9')
                print(et_sess.check_usage()) 
                table_data = et_sess.process_file(filepath=os.path.join(app.config["UPLOAD_FOLDER"], image.filename), output_format="df")
                dft=pd.DataFrame(table_data[0])
                dft.index=dft['0']
                data=dft.T
                
                name=image.filename.replace((image.filename).rsplit('.', 1)[1],'').replace('.','')
                if 'Balance' in name:
                    features1(data)
                elif 'Income' in name:
                    features2(data)
                elif 'Cash' in name:
                    features3(data)
                data.to_excel(f"{name}.xlsx")
                print("data saved"+name)
                return redirect(request.url)
    return render_template('New client.html', title="New Client",form1 = form1,form2=form2) 



def features1(data):
    global Total_Asset1
    global Total_Asset2 
    global longTermDebt
    global totalCurrentAssets 
    global totalCurrentLiabilities
    global Retained
    global totalStockholderEquity
    Total_Asset1 = pd.to_numeric(data['Total Assets'][1].replace(",", ""), errors='coerce')
    Total_Asset2 = pd.to_numeric(data['Total Assets'][2].replace(",", ""), errors='coerce')
    longTermDebt = pd.to_numeric(data['> Long Term Debt And Capit...'][1].replace(",", ""), errors='coerce')
    totalCurrentAssets = pd.to_numeric(data['> Current Assets'][1].replace(",", ""), errors='coerce')
    totalCurrentLiabilities = pd.to_numeric(data['> Current Liabilities'][1].replace(",", ""), errors='coerce')
    Retained = pd.to_numeric(data['Retained Earnings'][1].replace(",", ""), errors='coerce')
    totalStockholderEquity = pd.to_numeric(data["Stockholders' Equity"][1].replace(",", ""), errors='coerce')
def features2(data1):
    global Net_income1 
    global Net_income2 
    global grossProfit1 
    global grossProfit2 
    global totalRevenue1 
    global totalRevenue2
    global EBIT     
    Net_income1 = pd.to_numeric(data1['> Net income'][1].replace(",", ""), errors='coerce')
    Net_income2 = pd.to_numeric(data1['> Net income'][2].replace(",", ""), errors='coerce') 
    grossProfit1 = pd.to_numeric(data1['Gross Profit'][1].replace(",", ""), errors='coerce')
    grossProfit2 = pd.to_numeric(data1['Gross Profit'][2].replace(",", ""), errors='coerce')
    totalRevenue1 = pd.to_numeric(data1['> Total Revenue'][1].replace(",", ""), errors='coerce')
    totalRevenue2 = pd.to_numeric(data1['> Total Revenue'][2].replace(",", ""), errors='coerce')
    EBIT = pd.to_numeric(data1['EBIT'][1].replace(",", ""), errors='coerce')
def features3(data3):
    global totalCashFromOperating 
    totalCashFromOperating = pd.to_numeric(data3['> Operating Cash Flow'][1].replace(",", ""), errors='coerce')
def profitability():
    global profitability_score
    ni_score = 1 if Net_income1 > 0 else 0
    ni_score_2 = 1 if Net_income1> Net_income2 else 0
    #Score #3 - operating cash flow
    op_cf = totalCashFromOperating
    op_cf_score = 1 if op_cf > 0 else 0
    #Score #4 - change in RoA
    avg_assets = (Total_Asset1+Total_Asset2) / 2
    RoA = Net_income1 / avg_assets
    RoA_py = Net_income2 / avg_assets
    RoA_score = 1 if RoA > RoA_py else 0
    #Score #5 - Accruals
    accruals = op_cf / Total_Asset1 - RoA
    ac_score = 1 if accruals > 0 else 0

    profitability_score = ni_score + ni_score_2 + op_cf_score + RoA_score + ac_score
def leverage():
    global leverage_score
    global debt_ratio
    global current_ratio
    #Score #6 - long-term debt ratio
    debt_ratio = longTermDebt / Total_Asset1
    debt_ratio_score = 1 if debt_ratio < 0.4 else 0
    #Score #7 - Current ratio
    current_ratio = totalCurrentAssets / totalCurrentLiabilities
    current_ratio_score = 1 if current_ratio > 1 else 0

    leverage_score = debt_ratio_score + current_ratio_score
    
def operating_efficiency():
    global operating_efficiency_score
    global gm
    #Score #8 - Gross margin
    gm = grossProfit1 / totalRevenue1
    gm_py = grossProfit2 / totalRevenue2
    gm_score = 1 if gm > gm_py else 0
    #Score #9 - Asset turnover
    avg_assets = (Total_Asset1+Total_Asset2) / 2
    at = totalRevenue1 / avg_assets #at = asset turnover
    at_py = totalRevenue2 / avg_assets
    at_score = 1 if at > at_py else 0

    operating_efficiency_score = gm_score + at_score 
    
def Piotroski():
    global piotroski_score
    piotroski_score=profitability_score+leverage_score+operating_efficiency_score  
def altman():
    global altman_score
    global A_score
    global B_score
    global D_score
    global E_score
    #A_score
    A_score = (totalCurrentAssets-totalCurrentLiabilities)/Total_Asset1
    #B_score
    B_score = Retained/Total_Asset1
    #C_score
    C_score = EBIT/Total_Asset1
    #D_score
    D_score = (1879*127500)/totalCurrentLiabilities
    #E_score
    E_score = totalRevenue1/Total_Asset1
    #CapitalStructure
    CapitalStructure_score = totalStockholderEquity/Total_Asset1
    #Altman Z-score
    altman_score=(1.2*A_score) + (1.4*B_score) + (3.3*C_score) + (0.6*D_score) + (1.0*E_score)