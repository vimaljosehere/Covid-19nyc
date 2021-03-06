from pages import index, peace, reflection, shopping, todo
from datetime import datetime, date, time, timedelta
from dash.dependencies import Input, Output, State
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc
from sqlalchemy import create_engine
import dash_html_components as html
import plotly.figure_factory as ff
from urllib.request import urlopen
from urllib.error import HTTPError
import dash_core_components as dcc
import plotly.graph_objects as go
import plotly.express as px
import pytz
from pytz import timezone
import mysql.connector
from app import app
import pandas as pd
import numpy as np
import sqlalchemy
import requests
import psycopg2
import json
import dash


mapbox_access_token = "pk.eyJ1IjoibGlseXN1IiwiYSI6ImNrN2txb28zYjAwNjMzZWxvc2liOTFveGMifQ.wuFm9PLDxO3lhL_bVqMvaA"
engine = create_engine('postgresql+psycopg2://postgres:postgres@postgres2.chtkfsooypac.us-east-1.rds.amazonaws.com:5432/postgres', echo=False)

#HTTPError catching in case github is down, dataframes are read from S3 bucket
try:
    diff_from_day_before_County= pd.read_csv("https://raw.githubusercontent.com/LilySu/Covid-19nyc/master/df_ny/diff_from_day_before_County.csv")
except HTTPError as e:
    diff_from_day_before_County= pd.read_csv("https://covidnyc.s3.us-east-1.amazonaws.com/df_ny/diff_from_day_before_County.csv")

try:
    diff_from_day_before_nyc = pd.read_csv("https://raw.githubusercontent.com/LilySu/Covid-19nyc/master/df_nyc/daily_num_cases_nyc.csv")
except HTTPError as e:
    diff_from_day_before_nyc= pd.read_csv("https://covidnyc.s3.us-east-1.amazonaws.com/df_nyc/daily_num_cases_nyc.csv")

try:
    df_percentage_change = pd.read_csv("https://raw.githubusercontent.com/LilySu/Covid-19nyc/master/df_ny/percentage_change_County.csv")
except HTTPError as e:
    df_percentage_change = pd.read_csv("https://covidnyc.s3.us-east-1.amazonaws.com/df_ny/percentage_change_County.csv")

try:
    df_combined_county_table = pd.read_csv("https://raw.githubusercontent.com/LilySu/Covid-19nyc/master/df_ny/df_combined_county_table.csv")
except HTTPError as e:
    df_combined_county_table = pd.read_csv("https://covidnyc.s3.us-east-1.amazonaws.com/df_ny/df_combined_county_table.csv")

try:
    df_scraped_county_table = pd.read_csv("https://raw.githubusercontent.com/LilySu/Covid-19nyc/master/df_ny/df_scraped_county_table.csv")
except HTTPError as e:
    df_scraped_county_table = pd.read_csv("https://covidnyc.s3.us-east-1.amazonaws.com/df_ny/df_scraped_county_table.csv")


#Geojson imports
try:
    with urlopen('https://raw.githubusercontent.com/LilySu/Covid-19nyc/master/nyc_geojson/nyc_zip_code_tabulation_areas_polygons.geojson') as response:
        geojson = json.load(response)
except HTTPError as e:
    with urlopen('https://covidnyc.s3.us-east-1.amazonaws.com/nyc_geojson/nyc_zip_code_tabulation_areas_polygons.geojson') as response:
        geojson = json.load(response)

try:
    with urlopen('https://raw.githubusercontent.com/LilySu/Covid-19nyc/master/nys_geojson/new-york-counties.geojson') as response:
        geojson_counties = json.load(response)
except HTTPError as e:
    with urlopen('https://covidnyc.s3.us-east-1.amazonaws.com/nys_geojson/new-york-counties.geojson') as response:
        geojson_counties = json.load(response)


def get_nyc_zipcode_data():
  sql = f'''
  SELECT * 
  FROM nyc_zipcode_table;
  '''
  with engine.connect() as conn:
    return [record for record in conn.execute(sql)]

try:
    data = get_nyc_zipcode_data()
    df_main_map = pd.DataFrame(data, columns= ['MODZCTA', 'Positive', 'Total', 'zcta_cum.perc_pos', 'ZIP', 'LAT',
       'LNG', 'zip', 'lat', 'lng', 'city', 'state_id', 'state_name', 'zcta',
       'parent_zcta', 'population', 'density', 'county_fips', 'county_name',
       'county_weights', 'county_names_all', 'county_fips_all', 'imprecise',
       'military', 'timezone', 'Positive_Percentage_of_Population'])
except (sqlalchemy.exc.ProgrammingError, ValueError) as err:
    df_main_map = pd.read_csv('https://raw.githubusercontent.com/LilySu/Covid-19nyc/master/df_nyc/nyc_zipcode.csv')
except HTTPError as e:
    df_main_map = pd.read_csv('https://covidnyc.s3.us-east-1.amazonaws.com/df_nyc/nyc_zipcode.csv')



def get_today_counties_records():
  sql = f'''
  SELECT * 
  FROM scraped_county_table;
  '''
  with engine.connect() as conn:
    return [record for record in conn.execute(sql)]

try:
    data = get_today_counties_records()
    county = pd.DataFrame(data, columns= ['County', 'Confirmed', 'Deaths', 'Recoveries', ' Population','lastupdate'])
except (sqlalchemy.exc.ProgrammingError, ValueError) as err:
    county = df_scraped_county_table[::-1]

nyc_confirmed_latest = county['Confirmed'][0]
nyc_confirmed_latest_date = county['lastupdate'][0]
nyc_death_latest = county['Deaths'][0]
df_counties_overtime = county.head(12)


today_for_range = datetime.now(timezone('UTC')) + timedelta(days=1)
first_date_recorded = 'March 23 2020'
first_date_recorded = datetime.strptime(first_date_recorded,'%B %d %Y')
first_date_recorded = first_date_recorded.astimezone(timezone('UTC'))
date_list = pd.date_range(first_date_recorded, today_for_range).tolist()
date_list = [i.astimezone(timezone('EST')) for i in date_list]
date_list = [i.strftime('%B %d') for i in date_list]

def get_historical_nyc_data():
  sql = f'''
  SELECT * 
  FROM historical_nyc_table;
  '''
  with engine.connect() as conn:
    return [record for record in conn.execute(sql)]

data = get_historical_nyc_data()

headers = ['BOROUGH_GROUP']+date_list
try: 
    df_historical_nyc = pd.DataFrame(data, columns=headers)
except (sqlalchemy.exc.ProgrammingError, ValueError) as err:
    today_for_range = datetime.now(timezone('UTC'))
    date_list = pd.date_range(first_date_recorded, today_for_range).tolist()
    date_list = [i.astimezone(timezone('EST')) for i in date_list]
    date_list = [i.strftime('%B %d') for i in date_list]
    headers = ['BOROUGH_GROUP']+date_list
    df_historical_nyc = pd.DataFrame(data, columns=headers)
except:
    df_historical_nyc = pd.read_csv('https://covidnyc.s3.us-east-1.amazonaws.com/df_nyc/df_horizontal_nyc.csv')

df_nyc = df_historical_nyc.T
df_nyc = df_nyc.reset_index()
df_nyc.columns = df_nyc.iloc[0]
df_nyc = df_nyc.drop(df_nyc.index[0])
df_nyc = df_nyc.rename(columns={'BOROUGH_GROUP': 'date', 'The Bronx':'Bronx'})
collist = ['Bronx','Brooklyn','Manhattan','Queens','Staten Island']
df_nyc['total'] = df_nyc[collist].astype(int).sum(axis=1)

[queens_confirmed] = df_nyc.iloc[[-1]]['Queens'].values
total_uninfected = 2273000 - queens_confirmed

def get_age_nyc_data():
  sql = f'''
  SELECT * 
  FROM age_nyc_table;
  '''
  with engine.connect() as conn:
    return [record for record in conn.execute(sql)]

data = get_age_nyc_data()
headers = ['AGE_GROUP', 'COVID_CASE_RATE', 'HOSPITALIZED_CASE_RATE', 'DEATH_RATE']

try:
    age = pd.DataFrame(data, columns=headers)
except (sqlalchemy.exc.ProgrammingError, ValueError) as err:
    age = pd.read_csv('https://raw.githubusercontent.com/nychealth/coronavirus-data/master/by-age.csv')
except HTTPError as e:
    age = pd.read_csv('https://covidnyc.s3.us-east-1.amazonaws.com/df_nyc/by-age.csv')

p_case_age = []
for i in age['COVID_CASE_RATE']:
  p_case_age.append(i)

p_death_age = []
for i in age['DEATH_RATE']:
  p_death_age.append(i)  

def get_sex_nyc_data():
  sql = f'''
  SELECT * 
  FROM sex_nyc_table;
  '''
  with engine.connect() as conn:
    return [record for record in conn.execute(sql)]

data = get_sex_nyc_data()
headers = ['AGE_GROUP', 'COVID_CASE_RATE', 'HOSPITALIZED_CASE_RATE', 'DEATH_RATE']

try:
    sex = pd.DataFrame(data, columns=headers)
except (sqlalchemy.exc.ProgrammingError, ValueError) as err:
    sex = pd.read_csv('https://raw.githubusercontent.com/nychealth/coronavirus-data/master/by-sex.csv')
except HTTPError as e:
    sex = pd.read_csv('https://covidnyc.s3.us-east-1.amazonaws.com/df_nyc/by-sex.csv')

p_case_sex = []
for i in sex['COVID_CASE_RATE']:
  p_case_sex.append(i)

p_death_sex = []
for i in sex['DEATH_RATE']:
  p_death_sex.append(i)


def get_counties_timeslider_data():
  sql = f'''
  SELECT * 
  FROM counties_timeslider_table;
  '''
  with engine.connect() as conn:
    return [record for record in conn.execute(sql)]

today_for_range = datetime.now(timezone('UTC')) + timedelta(days=1)
first_date_recorded = 'March 02 2020'
first_date_recorded = datetime.strptime(first_date_recorded,'%B %d %Y')
first_date_recorded = first_date_recorded.astimezone(timezone('UTC'))
date_list = pd.date_range(first_date_recorded, today_for_range).tolist()
date_list = [i.astimezone(timezone('EST')) for i in date_list]
date_list = [i.strftime('%B %d') for i in date_list]

data = get_counties_timeslider_data()
headers = ['county']+[date_list[0]]+['date']+date_list[1::]+['total','total_normalized','county_full']
try: 
    df_new_york_counties_timeslider = pd.DataFrame(data, columns=headers)
except (sqlalchemy.exc.ProgrammingError, ValueError) as err:
    df_new_york_counties_timeslider = pd.read_csv("https://raw.githubusercontent.com/LilySu/Covid-19nyc/master/df_ny/new_york_counties_timeslider.csv")
except HTTPError as e:
    df_new_york_counties_timeslider = pd.read_csv("https://covidnyc.s3.us-east-1.amazonaws.com/df_ny/new_york_counties_timeslider.csv")



def get_china_data():
  sql = f'''
  SELECT * 
  FROM world_china_table;
  '''
  with engine.connect() as conn:
    return [record for record in conn.execute(sql)]

data = get_china_data()
headers = ['date', 'index', 'Confirmed', 'Deaths', 'Recovered', 'FIPS', 'Lat',
       'Long_', 'log_conf', 'new_Confirmed', 'new_Recovered', 'new_Deaths',
       'p_new_Confirmed', 'p_new_Recovered', 'p_new_Deaths']
try:
    df_china = pd.DataFrame(data, columns=headers)
except (sqlalchemy.exc.ProgrammingError, ValueError) as err:
    df_china = pd.read_csv("https://raw.githubusercontent.com/LilySu/Covid-19nyc/master/df_world/China_Covid19.csv")
except HTTPError as e:
    df_china = pd.read_csv("https://covidnyc.s3.us-east-1.amazonaws.com/df_world/China_Covid19.csv")

def get_italy_data():
  sql = f'''
  SELECT * 
  FROM world_italy_table;
  '''
  with engine.connect() as conn:
    return [record for record in conn.execute(sql)]

data = get_italy_data()
headers = ['date', 'index', 'Confirmed', 'Deaths', 'Recovered', 'FIPS', 'Lat',
       'Long_', 'log_conf', 'new_Confirmed', 'new_Recovered', 'new_Deaths',
       'p_new_Confirmed', 'p_new_Recovered', 'p_new_Deaths']
try:
    df_italy = pd.DataFrame(data, columns=headers)
except (sqlalchemy.exc.ProgrammingError, ValueError) as err:
    df_italy = pd.read_csv("https://raw.githubusercontent.com/LilySu/Covid-19nyc/master/df_world/Italy_Covid19.csv")
except HTTPError as e:
    df_italy = pd.read_csv("https://covidnyc.s3.us-east-1.amazonaws.com/df_world/Italy_Covid19.csv")

def get_usa_data():
  sql = f'''
  SELECT * 
  FROM world_usa_table;
  '''
  with engine.connect() as conn:
    return [record for record in conn.execute(sql)]

data = get_usa_data()
headers = ['date', 'index', 'Confirmed', 'Deaths', 'Recovered', 'FIPS', 'Lat',
       'Long_', 'log_conf', 'new_Confirmed', 'new_Recovered', 'new_Deaths',
       'p_new_Confirmed', 'p_new_Recovered', 'p_new_Deaths']
try:
    df_usa = pd.DataFrame(data, columns=headers)
except (sqlalchemy.exc.ProgrammingError, ValueError) as err:
    df_usa = pd.read_csv("https://raw.githubusercontent.com/LilySu/Covid-19nyc/master/df_world/Usa_Covid19.csv")
except HTTPError as e:
    df_usa = pd.read_csv("https://covidnyc.s3.us-east-1.amazonaws.com/df_world/Usa_Covid19.csv")


#-----------------------fig_bar_nyc_last_5_days


def get_combined_counties_records():
  sql = f'''
  SELECT * 
  FROM combined_county_table;
  '''
  with engine.connect() as conn:
    return [record for record in conn.execute(sql)]

try: 
    data = get_combined_counties_records()
    df_county = pd.DataFrame(data, columns= ['Albany', 'Allegany', 'Bronx', 'Broome', 'Cattaraugus', 'Cayuga',
        'Chautauqua', 'Chemung', 'Chenango', 'Clinton', 'Columbia', 'Cortland',
        'Delaware', 'Dutchess', 'Erie', 'Essex', 'Franklin', 'Fulton',
        'Genesee', 'Greene', 'Hamilton', 'Herkimer', 'Jefferson', 'Kings',
        'Lewis', 'Livingston', 'Madison', 'Monroe', 'Montgomery', 'Nassau',
        'New York', 'Niagara', 'Oneida', 'Onondaga', 'Ontario', 'Orange',
        'Orleans', 'Oswego', 'Otsego', 'Putnam', 'Queens', 'Rensselaer',
        'Richmond', 'Rockland', 'Saratoga', 'Schenectady', 'Schoharie',
        'Schuyler', 'Seneca', 'St Lawrence', 'Steuben', 'Suffolk', 'Sullivan',
        'Tioga', 'Tompkins', 'Ulster', 'Warren', 'Washington', 'Wayne',
        'Westchester', 'Wyoming', 'Yates', 'date','total'])
    df_county = df_county[::-1]
except (sqlalchemy.exc.ProgrammingError, ValueError) as err:
    df_county = df_combined_county_table[::-1]

top5 = df_county.tail()
fig_bar_nyc_last_5_days = px.bar(top5, x='date', y='New York',
             hover_data=['New York', 'date'], color='New York',
             color_continuous_scale=[(0.00, "#553000"), (0.25, "#BF1F58"), (0.5, "#F2B2C0"),(0.75, "#94D6CC"),  (1.00, "#003D30")],
             labels={'date':'Date'},
             text = 'New York', height = 220
             )
fig_bar_nyc_last_5_days.update_traces(texttemplate='%{text}', textposition='inside')
fig_bar_nyc_last_5_days.update_layout(
    showlegend=False,
    font=dict(
    size=12,
    color="#a3a3a3"
    ),
    xaxis_title="",
    yaxis_title="",
    plot_bgcolor='white',
    margin=dict(l=0, r=0, t=0, b=0),
    )
fig_bar_nyc_last_5_days.update_layout(coloraxis_showscale=False)
fig_bar_nyc_last_5_days.update_xaxes(showticklabels=True)
fig_bar_nyc_last_5_days.update_yaxes(showticklabels=False)
fig_bar_nyc_last_5_days.layout.margin.update({'t':0, 'b':0, 'r': 0, 'l': 0})

#---------------------------------------------

def get_historic_counties_records():
  sql = f'''
  SELECT * 
  FROM nyc_percentage_daily_change_table;
  '''
  with engine.connect() as conn:
    return [record for record in conn.execute(sql)]

try:
    data = get_historic_counties_records()
    table_h = pd.DataFrame(data, columns= ['New York','dates'])
except (sqlalchemy.exc.ProgrammingError, ValueError) as err:
    table_h = df_percentage_change

table_h = table_h.tail(7)
fig_area_nyc_percentage_change = go.Figure()
fig_area_nyc_percentage_change = px.area(table_h, x='dates', y='New York',
             hover_data=['New York', 'dates'],
             text = 'New York',
             color_discrete_sequence=px.colors.qualitative.Pastel,
             line_shape='spline',
             height=210
             )
fig_area_nyc_percentage_change.update_layout(
    plot_bgcolor='white',
    showlegend=False,
    font_color="#a3a3a3",
    )
fig_area_nyc_percentage_change.layout.margin.update({'t':0, 'b':0, 'r': 0, 'l': 0})

#-------------------------------------------------------------POPULATION OF PEOPLE POSITIVE IN QUEENS

pop_queens =["Queens Residents Positive with Covid-19","Rest of Queens Residents"]
color_pop_queens = ["#C02059","#94D7CD"]

[queens_confirmed] = df_nyc.iloc[[-1]]['Queens'].values
total_uninfected_queens = 2273000 - queens_confirmed

fig_pie_pop_queens = go.Figure(data=[go.Pie(labels=pop_queens, values=[queens_confirmed,total_uninfected_queens],marker=dict(colors=color_pop_queens))])#,pull=[0.4, 0]
fig_pie_pop_queens.update_traces(hole=.4, hoverinfo="label+percent+name+value",
                  hovertemplate = '<b>%{label}</b>'
                        '<br><b>Percentage</b>: %{percent}<br>'
                        '<b><b>Number of People</b>: %{value}<br>',
                  textposition='inside', textinfo='percent+label+value')
fig_pie_pop_queens.update_layout(
    annotations = [dict(text=pop_queens[0], x=0.498, y=0.998, font_size=11, showarrow=True)],
    title={
        'text':"PERCENTAGE OF PEOPLE WITH COVID-19 IN<br>QUEENS NYC ASSUMING THE POPULATION IS <br>2.273 MILLION AS OF " + nyc_confirmed_latest_date,
        'y':.95,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'},
    font_size=11,
    font_color="#05b9f0",
    showlegend=True
    )


#-------------------------------------------------------------POPULATION OF PEOPLE POSITIVE IN NYC

pop_nyc =["NYC Residents Positive with Covid-19","Rest of NYC Residents"]
color_pop_nyc = ["#C02059","#003C30"]
total_uninfected_nyc = 8500000 - nyc_confirmed_latest

fig_pie_pop_nyc = go.Figure(data=[go.Pie(labels=pop_nyc, values=[nyc_confirmed_latest,total_uninfected_nyc],marker=dict(colors=color_pop_nyc))])#,pull=[0.4, 0]
fig_pie_pop_nyc.update_traces(hole=.4, hoverinfo="label+percent+name+value",
                  hovertemplate = '<b>%{label}</b>'
                        '<br><b>Percentage</b>: %{percent}<br>'
                        '<b><b>Number of People</b>: %{value}<br>',
                  textposition='inside', textinfo='percent+label+value')

fig_pie_pop_nyc.update_layout(
    annotations = [dict(text=pop_nyc[0], x=0.498, y=0.998, font_size=11, showarrow=True)],
    title={
        'text':"PERCENTAGE OF PEOPLE WITH COVID-19 IN<br>ALL OF NYC ASSUMING THE POPULATION IS <br>8.5 MILLION AS OF " + nyc_confirmed_latest_date,
        'y':.95,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'},
    font_size=11,
    font_color="#05b9f0",
    showlegend=True
    )


#-------------------------------------------------------------AGE RANGE OF PEOPLE POSITIVE

age = ["0 to 17<br>years old", "18 to 44<br>years old", "45 to 64<br>years old", "65 to 74<br>years old", "75 years old<br>and over", "Unknown"]
age_color = ["#94D6CC","#003D30","#F3B3C3","#ffcece","#543000", "#047484"]

fig_pie_nyc_age = go.Figure(data=[go.Pie(labels=age, values=p_case_age, name="Age Group",marker=dict(colors=age_color))])#,pull=[0.4, 0]
fig_pie_nyc_age.update_traces(hole=.4, hoverinfo="label+percent+name+value",
                  hovertemplate = '<b>%{label}</b>'
                        '<br><b>Percentage</b>: %{percent}<br>'
                        '<b><b>Number of People</b>: %{value}<br>',
                  textposition='inside', textinfo='percent+label+value')
fig_pie_nyc_age.update_layout(
    title={
        'text':"AGE RANGE OF PEOPLE <br>WITH COVID-19 IN<br>NYC AS OF " + nyc_confirmed_latest_date,
        'y':0.95,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'},
    font_size=11,
    font_color="#05b9f0",
    showlegend=False
    )


#-------------------------------------------------------------AGE RANGE OF PEOPLE POSITIVE


gender =["Female","Male"]
gender_color = ["#94D6CC","#003C30"]

fig_pie_nyc_gender = go.Figure(data=[go.Pie(labels=gender, values=p_case_sex, name="Gender",marker=dict(colors=gender_color))])#,pull=[0.4, 0]
fig_pie_nyc_gender.update_traces(hole=.4, hoverinfo="label+percent+name+value",
                  hovertemplate = '<b>%{label}</b>'
                        '<br><b>Percentage</b>: %{percent}<br>'
                        '<b><b>Number of People</b>: %{value}<br>',
                  textposition='inside', textinfo='percent+label+value')
fig_pie_nyc_gender.update_layout(
    title={
        'text':"GENDER IDENTITY OF PEOPLE <br>WITH COVID-19 IN<br>NYC AS OF " + nyc_confirmed_latest_date,
        'y':0.95,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'},
    font_size=11,
    font_color="#05b9f0",
    showlegend=False)

#-------------------------------------------------------------AGE RANGE OF PEOPLE PASSED AWAY

age_of_death = ["0 to 17", "18 to 44", "45 to 64", "65 to 74 ", "75 and over"]
death_age_color = ["#94D6CC","#003D30","#F3B3C3","#ffcece","#047484"]

fig_pie_nyc_death_age = go.Figure(data=[go.Pie(labels=age_of_death, values=p_death_age, name="Age of Death",marker=dict(colors=death_age_color))])#,pull=[0.4, 0]
fig_pie_nyc_death_age.update_traces(hole=.4, hoverinfo="label+percent+name+value",
                  hovertemplate = '<b>%{label}</b>'
                        '<br><b>Percentage</b>: %{percent}<br>'
                        '<b><b>Number of People</b>: %{value}<br>',
                  textposition='inside', textinfo='percent+label+value'
                  )
fig_pie_nyc_death_age.update_layout(
    title={
        'text':"AGE RANGE RATE OF PEOPLE WHO<br>PASSED AWAY FROM WITH COVID-19 IN<br>NYC AS OF "+ nyc_confirmed_latest_date,
        'y':0.95,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'},
    font_size=11,
    font_color="#05b9f0",
    showlegend=False
    )

#-------------------------------------------------------------GENDER IDENTITY OF PEOPLE PASSED AWAY

gender_death =["Female","Male"]
color_gender_death = ["#94D6CC","#003C30"]

fig_pie_nyc_death_gender = go.Figure(data=[go.Pie(labels=gender_death, values=p_death_sex, name="Age of Death",marker=dict(colors=color_gender_death))])#,pull=[0.4, 0]
fig_pie_nyc_death_gender.update_traces(hole=.4, hoverinfo="label+percent+name+value",
                  hovertemplate = '<b>%{label}</b>'
                        '<br><b>Percentage</b>: %{percent}<br>'
                        '<b><b>Number of People</b>: %{value}<br>',
                  textposition='inside', textinfo='percent+label+value')
fig_pie_nyc_death_gender.update_layout(
    title={
        'text':"GENDER IDENTITY OF PEOPLE<br>AND DEATH RATE IN<br>NYC AS OF " + nyc_confirmed_latest_date,
        'y':0.95,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'},
    font_size=11,
    font_color="#05b9f0",
    showlegend=False)

#-------------------------------------------------------------UNDERLYING ILLNESS OF PEOPLE PASSED AWAY 

underlying_illness =["Had Underlying Illness","Did Not", "Unknown"]
underlying_illness_color = ["#BF1F57","#94D7CD","#003C2F"]

fig_pie_nyc_death_illness = go.Figure(data=[go.Pie(labels=underlying_illness, values=[7474,61,2755], name="Age of Death",marker=dict(colors=underlying_illness_color))])#,pull=[0.4, 0]
fig_pie_nyc_death_illness.update_traces(hole=.4, hoverinfo="label+percent+name+value",
                  hovertemplate = '<b>%{label}</b>'
                        '<br><b>Percentage</b>: %{percent}<br>'
                        '<b><b>Number of People</b>: %{value}<br>',
                  textposition='inside', textinfo='percent+label+value'
                  )
fig_pie_nyc_death_illness.update_layout(
    title={
        'text':"EXISTENCE OF UNDERLYING ILLNESS OF PEOPLE WHO<br>PASSED AWAY FROM WITH COVID-19<br> (10,290 with 5121, or 33 percent additional probable)<br>NYC AS OF April 10, no further updates has been released",
        'y':0.95,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'},
    font_size=11,
    font_color="#05b9f0",
    showlegend=False)

#---------------------------------------------#Main Map

fig_map_top_center = go.Figure()
fig_map_top_center = go.Figure(go.Choroplethmapbox(geojson=geojson, #locations=df.FIPS, z=df.Confirmed,
                                     z=df_main_map['Positive'],
                                     locations=df_main_map["MODZCTA"], #zipcode in dataframe
                                     featureidkey="properties.postalcode",
                                     text= df_main_map[["MODZCTA", "Positive",'Positive_Percentage_of_Population']],
                                      hovertemplate ='<b>Zipcode</b>: %{text[0]}<br>'+
                                    '<b>Confirmed</b>:  %{text[1]}<br>'#+
                                    '<b>Percentage of Population Positive</b>: %{text[2]:.2f}'+'%',
                                     ))
                                    #colorscale="YlOrRd", zmin=0, zmax=3,
                                    #marker_opacity=0.08, marker_line_width=0))
fig_map_top_center.update_traces(showscale=True, 
                   marker_opacity=.5,
                   colorscale = [(0, "#94D6CC"), (0.25, "#00755c"),(0.5, "#553000"), (0.75, "#F2B2C0"), (1.00, "#BF1F57")],
                   )
fig_map_top_center.update_layout(
    mapbox_layers=[
        {
            "below": 'traces',
            "sourcetype": "raster",
            "source": [
                       #"https://api.mapbox.com/styles/v1/lilysu/ck81nlmtm0fwq1iqkv33jiu2r/tiles/256/{z}/{x}/{y}@2x?access_token=pk.eyJ1IjoibGlseXN1IiwiYSI6ImNrN2txb28zYjAwNjMzZWxvc2liOTFveGMifQ.wuFm9PLDxO3lhL_bVqMvaA"
                        "https://api.mapbox.com/styles/v1/lilysu/ck81nlmtm0fwq1iqkv33jiu2r/tiles/256/{z}/{x}/{y}@2x?access_token=pk.eyJ1IjoibGlseXN1IiwiYSI6ImNrN2txb28zYjAwNjMzZWxvc2liOTFveGMifQ.wuFm9PLDxO3lhL_bVqMvaA"
            ] 
        },
      ],
    autosize=True,
    height=600,
    hovermode='closest',
    showlegend=False,
    mapbox=dict(
        style='white-bg',
        accesstoken=mapbox_access_token,
        bearing=0,
        center=dict(
            lat=40.7374253,
            lon=-73.9559889
        ),
        pitch=0,
        zoom=10,
    ),
)
fig_map_top_center.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

#---------------------------------------------#Positive Cases by Population


fig_cases_by_zipcode_population = go.Figure()
fig_cases_by_zipcode_population = go.Figure(go.Choroplethmapbox(geojson=geojson, #locations=df.FIPS, z=df.Confirmed,
                                     z=df_main_map['Positive_Percentage_of_Population'],
                                     locations=df_main_map["MODZCTA"], #zipcode in dataframe
                                     featureidkey="properties.postalcode",
                                     text= df_main_map[["MODZCTA", "Positive",'Positive_Percentage_of_Population','population','density']],
                                      hovertemplate = '<b>Percentage of Population Positive</b>: %{text[2]:.2f}'+'%<br>'+
                                      '<b>Zipcode</b>: %{text[0]}<br>'+
                                    '<b>Confirmed</b>:  %{text[1]}<br>'+
                                     '<b>Population in Zip Code</b>:  %{text[3]}<br>'+
                                     '<b>Density</b>:  %{text[4]}<br>'
                                     ))
fig_cases_by_zipcode_population.update_traces(showscale=True, 
                   marker_opacity=.8,
                   colorscale = [(0, "#DEDBD2"), (0.25, "#F7E1D7"),(0.5, "#EDAFB8"), (0.75, "#B0C4B1"), (1.00, "#4A5759")],
                   )
fig_cases_by_zipcode_population.update_layout(
    mapbox_layers=[
        {
            "below": 'traces',
            "sourcetype": "raster",
            "source": [
                       "https://api.mapbox.com/styles/v1/lilysu/ck81nlmtm0fwq1iqkv33jiu2r/tiles/256/{z}/{x}/{y}@2x?access_token=pk.eyJ1IjoibGlseXN1IiwiYSI6ImNrN2txb28zYjAwNjMzZWxvc2liOTFveGMifQ.wuFm9PLDxO3lhL_bVqMvaA"
            ] 
        },
      ],
    autosize=True,
    height=800,
    hovermode='closest',
    showlegend=False,
    mapbox=dict(
        style='white-bg',
        accesstoken=mapbox_access_token,
        bearing=0,
        center=dict(
            lat=40.7374253,
            lon=-73.9559889
        ),
        pitch=0,
        zoom=10,
    ),
)
fig_cases_by_zipcode_population.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

#---------------------------------------------------------------------------LINE CHART BY BOROUGH

borough = ['Bronx', 'Brooklyn', 'Manhattan', 'Queens', 'Staten Island']
borough_colors = ['#553000','#94D6CC','#F3B3C2', '#008064','#BF1F57']
fig_line_nyc_borough_day_change = go.Figure()
for i,j in zip(borough, borough_colors):
  fig_line_nyc_borough_day_change.add_trace(go.Scatter(x=df_nyc['date'], y=df_nyc[i], name = i, text=df_nyc[i],mode='lines+markers',hoverinfo='text+name', line=dict(color=j, width=4))
  )
fig_line_nyc_borough_day_change.update_layout(
    plot_bgcolor='white',
    showlegend=True,
    autosize=True,
    title_text='DAILY NUMBER OF CASES OF COVID-19 BY BOROUGH'
)
annotations = [ dict(xref='paper', yref='paper', x=0.5, y=-0.4,
                              xanchor='center', yanchor='top',
                              text='Data Provided by the New York City Department of Health',
                              font=dict(family='Arial',
                                        size=12,
                                        color='rgb(150,150,150)'),
                              showarrow=False)]
fig_line_nyc_borough_day_change.update_layout(annotations=annotations)

fig_line_nyc_borough_day_change.update_layout(
    plot_bgcolor='white'
)

#---------------------------------------------------------------------------BOROUGH STACKED CASES DAY TO DAY


fig_stacked_change_borough_cases = go.Figure()
borough = ['Bronx', 'Brooklyn', 'Manhattan', 'Queens', 'Staten Island']
borough_colors = ['#553000','#94D6CC','#F3B3C2', '#008064','#BF1F57']
for i,j in zip(borough, borough_colors):
  fig_stacked_change_borough_cases.add_trace(go.Scatter(x = df_nyc['date'], y = df_nyc[i],line_shape='spline', mode='lines', stackgroup='one', # define stack group
                           name = i, text=df_nyc[i], hoveron = 'points+fills', fillcolor=j,line=dict(width=0.5, color=j),
                           hovertemplate = "<b>" + i +"<br><b>%{text}</b>"+" Total Cases <br>on " + df_nyc['date']))   
fig_stacked_change_borough_cases.update_traces(hoverinfo='text+name', mode='lines+markers')
fig_stacked_change_borough_cases.update_layout(
    plot_bgcolor='white',
    showlegend=True,
    title_text='NUMBER OF POSITIVE CASES OF COVID-19 BY BOROUGH STACKED TOGETHER'
)
annotations = [ dict(xref='paper', yref='paper', x=0.5, y=-0.13,
                              xanchor='center', yanchor='top',
                              text='Data Provided by the New York City Department of Health',
                              font=dict(family='Arial',
                                        size=12,
                                        color='rgb(150,150,150)'),
                              showarrow=False)]
fig_stacked_change_borough_cases.update_layout(annotations=annotations)
fig_stacked_change_borough_cases.update_layout(
    showlegend=False,
    annotations=[
        dict(
            x=0,
            y=-3500,
            xref="x",
            yref="y",
            text="10764<br> total",
            showarrow=False,
            ax=0,
            ay=-40,
            font=dict(size=8, color='rgb(150,150,150)'),
        )
    ]
)
annotation_borough = []
for i,j in zip(range(len(df_nyc['total'])), df_nyc['total']):
  annotation_borough.append(
        dict(
            x=i,
            y=-8000,
            xref="x",
            yref="y",
            text=str(j) +"<br> total",
            font=dict(family='Arial',
            size=8,
            color='rgb(150,150,150)'),
            showarrow=False,
            ax=0,
            ay=-40))
annotation_borough.append(
  dict(xref='paper', yref='paper', x=0.5, y=-0.4,
  xanchor='center', yanchor='top',
  text='Data Provided by the New York City Department of Health',
  font=dict(family='Arial',
            size=8,
            color='rgb(150,150,150)'),
  showarrow=False))
fig_stacked_change_borough_cases.update_layout(
    plot_bgcolor='white',
    showlegend=True,
    annotations = annotation_borough
)


#---------------------------------------------------------------------------TIMESLIDER

try:
    fig_map_nyc_timeslider = px.choropleth_mapbox(df_new_york_counties_timeslider, geojson=geojson_counties, 
                            animation_frame="date", animation_group="total",
                            locations="county_full", 
                            featureidkey="properties.name",
                            center={"lat": 42.85, "lon":-75.9},
                            mapbox_style="carto-positron", zoom=5.7,
                            opacity = .7,
                            height = 720,
                            color = 'total_normalized',
                            color_continuous_scale=px.colors.sequential.Teal,
                            #color_continuous_scale=[(0.00, "#F2B2C0"), (0.25, "#94D6CC"), (0.5, "#00755c"),(0.75, "#553000"),  (1.00, "#BF1F57")],#553000
                            custom_data = ['April 23'],################################################CHANGE THIS
                            #hover_data = ["date"],
                            labels = {"total":"Positive Cases", "county_full": "location"},
                            )
    fig_map_nyc_timeslider.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
    fig_map_nyc_timeslider.update_layout(coloraxis_showscale = False, showlegend = False)
    timeslider_not_working = False
except ValueError as e:
    timeslider_not_working = True

#------------------------------------------------------------------------------------------COUNTY CASES


fig_line_ny_cumulative = px.bar(df_counties_overtime, x='County', y='Confirmed', 
             text='Confirmed', 
             color = 'Confirmed',
             height = 350,
             color_continuous_scale=[(0.00, "#553000"), (0.25, "#BF1F58"), (0.5, "#F2B2C0"),(0.75, "#94D6CC"),  (1.00, "#003D30")],
             labels={'Confirmed':'Confirmed as of last update'})
fig_line_ny_cumulative.update_traces(texttemplate='%{text}', textposition='outside')
fig_line_ny_cumulative.update_layout(
    plot_bgcolor='white',
    showlegend=False,
    autosize=True,
    xaxis_title="",
    font=dict(
    color="#a3a3a3",)
    # title_text='NUMBER OF POSITIVE CASES OF COVID-19 BY COUNTY FOR THE TOP 20 COUNTIES'
)
fig_line_ny_cumulative.update_layout(coloraxis_showscale=False)
fig_line_ny_cumulative.update_layout(margin={"r":0,"t":15,"l":0,"b":0})

#------------------------------------------------------------------------------------------COUNTY day-to-day changes

df_county_20r = df_county.tail(20)

collist = ['Nassau','New York', 'Suffolk', 'Rockland', 'Dutchess', 'Monroe','Dutchess', 'Westchester']
colors = [ '#94D7CD', '#BF1F57', '#F3B3C2', "#008064","#F3B3C3","#ffcece",'#4bd2fb']#'#99d1ce',
fig_line_ny_overtime = go.Figure()
for i, j in zip(collist, colors):
    fig_line_ny_overtime.add_trace(go.Scatter(x=df_county_20r['date'], y=df_county_20r[i], name = i, text=df_county_20r[i],mode='lines+markers',
    hoverinfo='text+name',line=dict(color=j, width=4)))
fig_line_ny_overtime.update_layout(
    yaxis=dict(
        title_text="Confirmed Cases"
    ),
    autosize=True,
    height=220,
    plot_bgcolor='white',
    showlegend=True,
    #title_text='DAILY NUMBER OF CASES BY COUNTY'
    font=dict(
    # family="Arial",
    color="#a3a3a3")
)
# annotations = [ dict(xref='paper', yref='paper', x=0.5, y=-0.35,
#                               xanchor='center', yanchor='top',
#                               text='Data Provided by the New York State Department of Health',
#                               font=dict(family='Arial',
#                                         size=12,
#                                         color="#a3a3a3"),
#                               showarrow=False)]
# fig_line_ny_overtime.update_layout(annotations=annotations)
fig_line_ny_overtime.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

#-------------------------------------------------------------------------------------STACKED COUNTIES

def get_counties_new_daily_cases():
  sql = f'''
  SELECT * 
  FROM counties_new_daily_cases_table;
  '''
  with engine.connect() as conn:
    return [record for record in conn.execute(sql)]

try:
    data = get_counties_new_daily_cases()
    diff_from_day_before = pd.DataFrame(data, columns=['Albany', 'Allegany', 'Broome', 'Cattaraugus', 'Cayuga', 'Chautauqua',
        'Chemung', 'Chenango', 'Clinton', 'Columbia', 'Cortland', 'Delaware',
        'Dutchess', 'Erie', 'Essex', 'Franklin', 'Fulton', 'Genesee', 'Greene',
        'Hamilton', 'Herkimer', 'Jefferson', 'Lewis', 'Livingston', 'Madison',
        'Monroe', 'Montgomery', 'Nassau', 'Niagara', 'Oneida', 'Onondaga',
        'Ontario', 'Orange', 'Orleans', 'Oswego', 'Otsego', 'Putnam',
        'Rensselaer', 'Rockland', 'Saratoga', 'Schenectady', 'Schoharie',
        'Schuyler', 'Seneca', 'St Lawrence', 'Steuben', 'Suffolk', 'Sullivan',
        'Tioga', 'Tompkins', 'Ulster', 'Warren', 'Washington', 'Wayne',
        'Westchester', 'Wyoming', 'Yates', 'New York', 'Queens', 'Kings',
        'Richmond', 'Bronx', 'date', 'total', 'average'])
except (sqlalchemy.exc.ProgrammingError, ValueError) as err:
    diff_from_day_before = diff_from_day_before_County
fig_stacked_change_county_cases = go.Figure()
collist = ['Albany', 'Allegany', 'Broome',
       'Chenango', 'Clinton', 'Columbia', 'Delaware', 'Dutchess', 'Erie',
       'Essex', 'Fulton', 'Genesee', 'Greene', 'Hamilton', 'Herkimer',
       'Jefferson', 'Livingston', 'Monroe', 'Montgomery', 'Nassau',
       'New York', 'Niagara', 'Oneida', 'Onondaga', 'Ontario', 'Orange',
       'Putnam','Rensselaer', 'Rockland', 'Saratoga',
       'Schenectady', 'Schoharie', 'Steuben', 'Suffolk', 'Sullivan', 'Tioga',
       'Tompkins', 'Ulster', 'Warren', 'Washington', 'Wayne', 'Westchester',
       'Wyoming']

color43=["#4ed4b7", "#EA8AA1","#92CBD2", "#58B69A","#102A6B", "#103D58","#4788A8","#C979A6", "#F2DFE7", "#C5B6DF",
         "#443947","#764D62","#4ec5d4", "#EA8AA1","#92CBD2", "#58B69A","#102A6B", "#103D58","#4788A8","#C979A6", 
         "#F2DFE7", "#C5B6DF","#443947","#764D62","#EAE324", "#EA8AA1","#92CBD2", "#58B69A","#102A6B", "#103D58",
         "#EAE324", "#EA8AA1","#92CBD2", "#58B69A","#102A6B", "#103D58","#4788A8","#C979A6", "#94D6CC", "#C5B6DF",
         "#443947","#764D62"]


for i,j in zip(collist, color43):
  fig_stacked_change_county_cases.add_trace(go.Scatter(x = diff_from_day_before['date'], y = diff_from_day_before[i],line_shape='spline', mode='lines', stackgroup='one', # define stack group
                           name = i, text=diff_from_day_before[i], hoveron = 'points+fills', fillcolor=j,line=dict(width=2.5, color=j),
                           hovertemplate = "<b>" + i + " County</b>" +"<br><b>%{text} </b>"+" New Cases <br>on " + diff_from_day_before['date'])
                           )
fig_stacked_change_county_cases.update_traces(hoverinfo='text+name', mode='lines+markers')
fig_stacked_change_county_cases.update_layout(
    title_text='DAY-TO-DAY CHANGES IN NEW ADDITIONAL POSITIVE CASES BY COUNTY (drag-zoom to see detail)'
)
annotations = [ dict(xref='paper', yref='paper', x=0.5, y=-0.13,
                              xanchor='center', yanchor='top',
                              text='Data Provided by the New York State Department of Health (Missing March 16th)',
                              font=dict(family='Arial',
                                        size=12,
                                        color='rgb(150,150,150)'),
                              showarrow=False)]
fig_stacked_change_county_cases.update_layout(annotations=annotations)
fig_stacked_change_county_cases.update_layout(
    showlegend=False,
    annotations=[
        dict(
            x=15,
            y=5,
            xref="x",
            yref="y",
            text="missing data",
            showarrow=True,
            arrowhead=7,
            ax=0,
            ay=-40
        )
    ]
)
annotation4 = []
for i,j in zip(range(len(diff_from_day_before['total'])), diff_from_day_before['total']):
  annotation4.append(
        dict(
            x=i,
            y=-1100,
            xref="x",
            yref="y",
            text=str(j)[:-2]+"<br> more",
            font=dict(family='Arial',
            size=8,
            color='rgb(150,150,150)'),
            showarrow=False,
            #arrowhead=7,
            ax=0,
            ay=-40)
            )
fig_stacked_change_county_cases.update_layout(
    plot_bgcolor='white',
    showlegend=True,
    annotations = annotation4
)



#-----------------------------------------------------------SINGLE STACK NEW YORK



fig_stacked_ny = go.Figure()
collist = ['New York']
color43=["rgba(122, 226, 235, 0.62)"]
for i,j in zip(collist, color43):
  fig_stacked_ny.add_trace(go.Scatter(x = diff_from_day_before['date'], y = diff_from_day_before[i],line_shape='spline', mode='lines', stackgroup='one', # define stack group
                           name = i, text=diff_from_day_before[i], hoveron = 'points+fills', fillcolor=j,line=dict(width=2.5, color=j),
                           hovertemplate = "<b>" + i + " County</b>" +"<br><b>%{text} </b>"+" New Cases <br>on " + diff_from_day_before['date'])
                           )
fig_stacked_ny.update_traces(hoverinfo='text+name', mode='lines+markers')
fig_stacked_ny.update_layout(
    title_text='DAY-TO-DAY CHANGES IN NEW ADDITIONAL POSITIVE CASES NEW YORK'
)
annotations = [ dict(xref='paper', yref='paper', x=0.5, y=-0.13,
                              xanchor='center', yanchor='top',
                              text='Data Provided by the New York State Department of Health (Missing March 16th)',
                              font=dict(family='Arial',
                                        size=12,
                                        color='rgb(150,150,150)'),
                              showarrow=False)]
fig_stacked_ny.update_layout(annotations=annotations)
fig_stacked_ny.update_layout(
    showlegend=False,
    annotations=[
        dict(
            x=15,
            y=5,
            xref="x",
            yref="y",
            text="missing data",
            showarrow=True,
            arrowhead=7,
            ax=0,
            ay=-40
        )
    ]
)
annotation4 = []
for i,j in zip(range(len(diff_from_day_before['total'])), diff_from_day_before['New York']):
  annotation4.append(
        dict(
            x=i,
            y=-700,
            xref="x",
            yref="y",
            text=str(j)[:-2]+"<br> more",#<br> NYC <br>total <br> change
            font=dict(family='Arial',
            size=8,
            color='rgb(150,150,150)'),
            showarrow=False,
            #arrowhead=7,
            ax=0,
            ay=-40)
            )
fig_stacked_ny.update_layout(
    plot_bgcolor='white',
    showlegend=True,
    annotations = annotation4
)


#------------------------------------------FIG 2

fig_area_world_day_changes = go.Figure()
# fig_area_world_day_changes.add_trace(go.Scatter(x=df_italy["date"], y=df_italy["new_Confirmed"], #fill='tozeroy',fillcolor='#B0DAAE',
#                     mode= 'lines', name = 'Italy',legendgroup="group3",
#                     stackgroup='two',
#                     line=dict(width=0.5, color='rgba(157, 231, 222, 0.68)'),
#                     text="Italy<br>New Confirmed Cases <br>from the day before",hoveron = 'points+fills', 
#                     hoverinfo = 'x+text+y'))
fig_area_world_day_changes.add_trace(go.Scatter(x=df_usa["date"], y=df_usa["new_Confirmed"],##fill='toself',fillcolor='rgba(133, 70, 216, 0.3)',
                    mode='lines',legendgroup="group2",
                    stackgroup='one',
                    line=dict(width=0.5, color='rgba(238, 175, 206, 0.82)'),
                    text="U.S.<br>New Confirmed Cases <br>from the day before",hoveron = 'points+fills', name = 'U.S.',
                    hoverinfo = 'x+text+y' # override default markers+lines
                    ))
# fig_area_world_day_changes.add_trace(go.Scatter(x=df_china["date"], y=df_china["new_Confirmed"], #fill='tozeroy',fillcolor='#F4DBE5',
#                     mode='lines', legendgroup="group1",
#                     stackgroup='three',
#                     line=dict(width=0.5, color='rgba(103, 87, 66, 0.62)'),
#                     text="China<br>New Confirmed Cases <br>from the day before",hoveron = 'points+fills', name = 'China',
#                     hoverinfo = 'x+text+y' # override default markers+lines
#                     ))
annotat = []
annotat.append(dict(xref='paper', yref='paper', x=0.5, y=-0.35,
            xanchor='center', yanchor='top',
            text='Data Provided by the Johns Hopkins University Center for Systems Science and Engineering (JHU CSSE)',
            font=dict(family='Arial',
                    size=12,
                    color="#a3a3a3"),
            showarrow=False))
fig_area_world_day_changes.update_layout(
    annotations = annotat,
    yaxis=dict(title_text="Confirmed Cases",color='#a3a3a3'),
    title = "DAY-TO-DAY NEW ADDITIONS IN CONFIRMED CASES IN THE U.S. ",paper_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Arial',
    color='rgb(37,37,37)'),
    plot_bgcolor='rgba(0,0,0,0)', 
)



#--------------------------------------------------fig_line_cumulative_us_italy_china


fig_line_cumulative_us_italy_china = go.Figure()
fig_line_cumulative_us_italy_china.add_trace(go.Scatter(x=df_usa['date'], y=df_usa['Confirmed'],
                    name = "US",
                    hovertext=df_usa["Confirmed"],
                    hoverinfo='text',
                    hovertemplate =
                    '<i>Date: </i>: %{x}'+
                    '<br><b>Confirmed: </b>: %{y:,}<br>',
                    line_shape='spline',
                    line_color='#68CEF3',
                    ))
fig_line_cumulative_us_italy_china.add_trace(go.Scatter(x=df_italy['date'], y=df_italy['Confirmed'],
                    name = "Italy",
                    hovertext=df_italy["Confirmed"],
                    hoverinfo='text',
                    hovertemplate =
                    '<i>Date: </i>: %{x}'+
                    '<br><b>Confirmed: </b>: %{y:,}<br>',
                    line_shape='spline',
                    line_color='#008064',
                    ))
fig_line_cumulative_us_italy_china.add_trace(go.Scatter(x=df_china['date'], y=df_china['Confirmed'],
                    name = "China",
                    hovertext=df_china["Confirmed"],
                    hoverinfo='text',
                    hovertemplate =
                    '<i>Date: </i>: %{x}'+
                    '<br><b>Confirmed: </b>: %{y:,}<br>',
                    line_shape='spline',
                    line_color = '#e7b1c7',
                    ))
fig_line_cumulative_us_italy_china.update_traces(hoverinfo='text+name', mode='lines+markers')

fig_line_cumulative_us_italy_china.update_layout(
    xaxis=dict(
        showline=True,
        showgrid=False,
        showticklabels=True,
        linecolor='rgb(204, 204, 204)',
        linewidth=2,
        ticks='outside',
        tickfont=dict(
            family='Arial',
            size=12,
            color='rgb(82, 82, 82)',
        ),
    ),
    yaxis=dict(
        showgrid=False,
        zeroline=False,
        showline=False,
        showticklabels=True,
    ),
    autosize=True,
    margin=dict(
        autoexpand=False,
        l=100,
        r=20,
        t=110,
    ),
    showlegend=False,
    plot_bgcolor='white'
)

# Update 3D scene options
fig_line_cumulative_us_italy_china.update_scenes(
    aspectratio=dict(x=1, y=1, z=0.7),
    aspectmode="manual"
)
annotations = []
annotations.append(dict(xref='paper', x=.992, y=df_italy['Confirmed'].iloc[-1],
                              xanchor='right', yanchor='bottom',
                              text='Italy',
                              font=dict(family='Arial',
                                        color='#008064',
                                        size=20),
                              showarrow=False))
annotations.append(dict(xref='paper',  x=.992, y=df_usa['Confirmed'].iloc[-1],
                              xanchor='right', yanchor='bottom',
                              text='U.S.',
                              font=dict(family='Arial',
                                        color='#68CEF3',
                                        size=20),
                              showarrow=False))
annotations.append(dict(xref='paper', x=1.001, y=df_china['Confirmed'].iloc[-1],
                              xanchor='right', yanchor='bottom',
                              text='China',
                              font=dict(family='Arial',
                                        color = '#e7b1c7',
                                        size=20),
                              showarrow=False))
annotations.append(dict(xref='paper', yref='paper', x=0.0, y=1.05,
                              xanchor='left', yanchor='bottom',
                              text='CHINA VS. ITALY VS. UNITED STATES, COVID-19 CONFIRMED CASES',
                              font=dict(family='Arial',
                                        size=20,
                                        color='rgb(37,37,37)'),
                              showarrow=False))
annotations.append(dict(xref='paper', yref='paper', x=0.5, y=-0.35,
                              xanchor='center', yanchor='top',
                              text='Data Provided by the Johns Hopkins University Center for Systems Science and Engineering (JHU CSSE)',
                              font=dict(family='Arial',
                                        size=12,
                                        color='rgb(150,150,150)'),
                              showarrow=False))
all_annotations = [dict(xref='paper', x=1.002, y=df_china['Confirmed'].iloc[-1],
                              xanchor='right', yanchor='bottom',
                              text='China',
                              font=dict(family='Arial',
                                        color = '#e7b1c7',
                                        size=20),
                              showarrow=False),
                   dict(xref='paper', x=0.992, y=df_italy['Confirmed'].iloc[-1],
                              xanchor='right', yanchor='bottom',
                              text='Italy',
                              font=dict(family='Arial',
                                        color='#008064',
                                        size=20),
                              showarrow=False),
                     dict(xref='paper', x=0.992, y=df_usa['Confirmed'].iloc[-1],
                              xanchor='right', yanchor='bottom',
                              text='U.S.',
                              font=dict(family='Arial',
                                        color='#68CEF3',
                                        size=20),
                              showarrow=False),
                     dict(xref='paper', yref='paper', x=0.0, y=1.05,
                              xanchor='left', yanchor='bottom',
                              text='CHINA VS. ITALY VS. UNITED STATES, COVID-19 CONFIRMED CASES',
                              font=dict(family='Arial',
                                        size=20,
                                        color='rgb(37,37,37)'),
                              showarrow=False),
                     dict(xref='paper', yref='paper', x=0.5, y=-0.35,
                              xanchor='center', yanchor='top',
                              text='Data Provided by the Johns Hopkins University Center for Systems Science and Engineering (JHU CSSE)',
                              font=dict(family='Arial',
                                        size=12,
                                        color='rgb(150,150,150)'),
                              showarrow=False)]
italy_annotations = [dict(xref='paper', x=0.992, y=df_italy['Confirmed'].iloc[-1],
                              xanchor='right', yanchor='bottom',
                              text='Italy',
                              font=dict(family='Arial',
                                        color='#008064',
                                        size=20),
                              showarrow=False),
                     dict(xref='paper', x=0.992, y=df_usa['Confirmed'].iloc[-1],
                              xanchor='right', yanchor='bottom',
                              text='U.S.',
                              font=dict(family='Arial',
                                        color='#68CEF3',
                                        size=20),
                              showarrow=False),
                     dict(xref='paper', yref='paper', x=0.0, y=1.05,
                              xanchor='left', yanchor='bottom',
                              text='CHINA VS. ITALY VS. UNITED STATES, COVID-19 CONFIRMED CASES',
                              font=dict(family='Arial',
                                        size=20,
                                        color='rgb(37,37,37)'),
                              showarrow=False),
                     dict(xref='paper', yref='paper', x=0.5, y=-0.35,
                              xanchor='center', yanchor='top',
                              text='Data Provided by the Johns Hopkins University Center for Systems Science and Engineering (JHU CSSE)',
                              font=dict(family='Arial',
                                        size=12,
                                        color='rgb(150,150,150)'),
                              showarrow=False)]
china_annotations = [dict(xref='paper', x=0.992, y=df_china['Confirmed'].iloc[-1],
                              xanchor='right', yanchor='bottom',
                              text='China',
                              font=dict(family='Arial',
                                        color = '#e7b1c7',
                                        size=20),
                              showarrow=False),
                     dict(xref='paper', x=0.992, y=df_usa['Confirmed'].iloc[-1],
                              xanchor='right', yanchor='bottom',
                              text='U.S.',
                              font=dict(family='Arial',
                                        color='#68CEF3',
                                        size=20),
                              showarrow=False),
                     dict(xref='paper', yref='paper', x=0.0, y=1.05,
                              xanchor='left', yanchor='bottom',
                              text='CHINA VS. ITALY VS. UNITED STATES, COVID-19 CONFIRMED CASES',
                              font=dict(family='Arial',
                                        size=20,
                                        color='rgb(37,37,37)'),
                              showarrow=False),
                     dict(xref='paper', yref='paper', x=0.5, y=-0.35,
                              xanchor='center', yanchor='top',
                              text='Data Provided by the Johns Hopkins University Center for Systems Science and Engineering (JHU CSSE)',
                              font=dict(family='Arial',
                                        size=12,
                                        color='rgb(150,150,150)'),
                              showarrow=False)]
fig_line_cumulative_us_italy_china.update_layout(
    height=550,
    updatemenus=[
        dict(
            type="buttons",
            direction="right",
            active=0,
            pad={"r": 10, "t": 40},
            showactive=True,
            x=0.06,
            xanchor="left",
            y=1.1,
            buttons=list([
                dict(label="Show All",
                     method="update",
                     args=[{"visible": [True, True, True]},
                           {
                            "annotations": all_annotations}]),
                dict(label="Compare with Italy",
                     method="update",
                     args=[{"visible": [True, True, False]},
                           {
                            "annotations": italy_annotations}]),
                dict(label="Compare with China",
                     method="update",
                     args=[{"visible": [True, False, True]},
                           {
                            "annotations": china_annotations}]),
            ]),
        )
    ])
fig_line_cumulative_us_italy_china.update_layout(annotations=annotations)
#-------------------------------------------------------------------------------COLUMN START

columnTopAlert = dbc.Col(
    [
        html.Center(
            children=[
                # html.Img(src=app.get_asset_url('topBanner.png'), style={'display': 'block', 'height':80})
                #html.H6('New York State: 30,811 Confirmed cases', style={'fontSize':12, 'color':'#05b9f0', 'marginTop':0, 'marginBottom':8}),
                #html.H6('Data Above from the New York State Dept. of Health march 25, 2 pm', style={'fontSize':12, 'color':'#05b9f0', 'marginTop':10, 'marginBottom':15}),
            ]
        ),
    ],
    md=12,
)

columnTopLeft = dbc.Col(
    [
        html.Center(
            children=[
            html.H6('NYC', style={'fontSize':19, 'color':'#05b9f0', 'marginTop':0, 'marginBottom':5}),
            html.H6('Confirmed Cases', style={'fontSize':13, 'color':'#05b9f0', 'marginTop':0, 'marginBottom':0}),
            html.H6('Last 5 Days', style={'fontSize':10, 'color':'#05b9f0', 'marginTop':10, 'marginBottom':10}),
            # html.H1('38', style={'fontSize':60, 'color':'#05b9f0', 'marginBottom':0}),#fig_line_cumulative_us_italy_china
            ]
        ),
        dcc.Graph(figure=fig_bar_nyc_last_5_days),
        html.Center(
            children=[
            html.H6('Day-to-day % Increases', style={'fontSize':14, 'color':'#05b9f0', 'marginTop':10, 'marginBottom':10}),
            html.H6('in Number of', style={'fontSize':10, 'color':'#05b9f0', 'marginTop':6, 'marginBottom':0}),
            html.H6('Confirmed Cases', style={'fontSize':10, 'color':'#05b9f0', 'marginTop':6, 'marginBottom':0}),
            html.H6('NYC', style={'fontSize':19, 'color':'#05b9f0', 'marginTop':6, 'marginBottom':10}),
            ]
        ),
        dcc.Graph(figure=fig_area_nyc_percentage_change),
        html.Center(
            children=[
        html.H6('Data from NY State DOH on ' + nyc_confirmed_latest_date, style={'fontSize':12, 'color':'#05b9f0', 'marginTop':10, 'marginBottom':8}),
            ]
        ),
    ],
    md=3,
)

columnTopCenter = dbc.Col(
    [
        html.Center(
            children=[
                html.H6('Confirmed Cases of Covid-19 by Zip Code', style={'fontSize':14, 'color':'#05b9f0', 'marginTop':0, 'marginBottom':5}),#fig_line_cumulative_us_italy_china
                
            ]),
        dcc.Graph(figure=fig_map_top_center,style={'paddingTop':0, 'paddingBottom':0}),
        html.Center(
            children=[
                html.H6('Please hover over dots for more info. Confirmed cases is only a function availability and willingness to test.', style={'fontSize':12, 'color':'#05b9f0', 'marginTop':15, 'marginBottom':0}),#fig_line_cumulative_us_italy_china
                html.H6('Data Provided by the New York City Department of Health on ' + nyc_confirmed_latest_date, style={'fontSize':12, 'color':'#05b9f0', 'marginTop':0, 'marginBottom':0}),#fig_line_cumulative_us_italy_china
            ]
        ),
    ],
    md=6,
    )


columnTopRight = dbc.Col(
    [
        html.Center(
            children=[
            html.H6('Positive Cases NYC', style={'fontSize':20, 'color':'#14c5fa', 'marginTop':0, 'marginBottom':10}),#fig_line_cumulative_us_italy_china
            html.H6('As of '+ nyc_confirmed_latest_date, style={'fontSize':12, 'color':'#05b9f0', 'marginTop':0, 'marginBottom':8}),
            html.H1(nyc_confirmed_latest, style={'fontSize':50, 'color':'#5CD8FE', 'marginBottom':0}),#fig_line_cumulative_us_italy_china
            html.H6('Deaths NYC', style={'fontSize':18, 'color':'#14c5fa', 'marginTop':10, 'marginBottom':10}),#fig_line_cumulative_us_italy_china
            html.H6('As of '+ nyc_confirmed_latest_date, style={'fontSize':12, 'color':'#05b9f0', 'marginTop':0, 'marginBottom':0}),
            html.H6(nyc_death_latest, style={'fontSize':42, 'color':'#5CD8FE', 'marginTop':10}),
            html.H6('Positive Cases by Borough', style={'fontSize':20, 'color':'#208fb1', 'marginTop':20}),
            html.H6('As of May 03', style={'fontSize':12, 'color':'#05b9f0', 'marginTop':0, 'marginBottom':0}),
            html.Img(src=app.get_asset_url('NYC_Covid-19_Cases_today.png'), style={'display': 'block', 'height':300}),
            html.H6('Data from NY State Dept. of Health', style={'fontSize':12, 'color':'#05b9f0', 'marginTop':30, 'marginBottom':8}),
            ]
        ),
    ],
    md=3,
)


columnNeighborhoods = dbc.Col(
    [
        html.Center(
            children=[
                # html.Img(src=app.get_asset_url('ConfirmedCasesByNeighborhood.jpg'), style={'display': 'block', 'width':'100%', 'marginTop':170}),
                # html.H6('Map Released by the  NYC DOH, on March 30', style={'fontSize':12, 'color':'#05b9f0', 'marginTop':30, 'marginBottom':8}),
                # html.Img(src=app.get_asset_url('covid-19-hospital_rates.jpg'), style={'display': 'block', 'width':'90%', 'marginTop':70}),
                # html.H6('Line Chart Released by the  NYC DOH, on April 9', style={'fontSize':12, 'color':'#05b9f0', 'marginTop':30, 'marginBottom':8}),
                # html.Img(src=app.get_asset_url('confirmed_by_zipcode.PNG'), style={'display': 'block', 'width':'85%', 'marginTop':70}),
                html.H6('Confirmed Cases of Covid-19 as a Percentage of Census Population in Corresponding Zip Code', style={'fontSize':18, 'color':'#05b9f0', 'marginTop':50, 'marginBottom':5}),
                dcc.Graph(figure=fig_cases_by_zipcode_population),
                html.H6('Data Released by the  NYC DOH, on ' + nyc_confirmed_latest_date + '. Please be aware that confirmed cases is only a function of availability of testing and willingness to test. Only those who show up to a hospital with select symptoms and those who can show up to the testing sites in a vehicle are tested at this time.', style={'fontSize':10, 'color':'#05b9f0', 'marginTop':10, 'marginBottom':100}),
            ]
        )
    ],md=10,
)


column_nyc_stats = dbc.Col(
    [
        html.Center(
            children=[
                dcc.Graph(figure=fig_line_nyc_borough_day_change),
                dcc.Graph(figure=fig_stacked_change_borough_cases),
            ]
        )
    ],
    md=10
)

column_pie_queens_pop = dbc.Col(
    [
        html.Center(
            children=[
                dcc.Graph(figure=fig_pie_pop_queens),
            ]
        )
    ],
    md=6
)

column_pie_nyc_pop = dbc.Col(
    [
        html.Center(
            children=[
                dcc.Graph(figure=fig_pie_pop_nyc),
            ]
        )
    ],
    md=6
)

column_pie_age_positive = dbc.Col(
    [
        html.Center(
            children=[
                dcc.Graph(figure=fig_pie_nyc_age),
            ]
        )
    ],
    md=6
) 

column_pie_gender_positive = dbc.Col(
    [
        html.Center(
            children=[
                dcc.Graph(figure=fig_pie_nyc_gender),
            ]
        )
    ],
    md=6
) 

column_pie_age_passed = dbc.Col(
    [
        html.Center(
            children=[
                dcc.Graph(figure=fig_pie_nyc_death_age),
            ]
        )
    ],
    md=4
) 

column_pie_gender_passed = dbc.Col(
    [
        html.Center(
            children=[
                dcc.Graph(figure=fig_pie_nyc_death_gender),
            ]
        )
    ],
    md=4
) 

column_pie_illness_passed = dbc.Col(
    [
        html.Center(
            children=[
                dcc.Graph(figure=fig_pie_nyc_death_illness),
            ]
        )
    ],
    md=4
) 



columnpiebottom = dbc.Col(
    [
        html.Center(
            children=[
            html.H6('Data for above pie charts from NYC DOH', style={'fontSize':12, 'color':'#05b9f0', 'marginTop':0, 'marginBottom':80}),
            ]
        )
    ],
    md=12,
)

if timeslider_not_working == True:
    column1Left = dbc.Col(
        [
            html.Center(
                children=[
                html.H6('NYC', style={'fontSize':19, 'color':'#05b9f0', 'marginTop':0, 'marginBottom':5}),
                html.H6('Confirmed Cases', style={'fontSize':13, 'color':'#05b9f0', 'marginTop':0, 'marginBottom':0}),
                html.H6('Last 5 Days', style={'fontSize':10, 'color':'#05b9f0', 'marginTop':10, 'marginBottom':10}),
                # html.H1('38', style={'fontSize':60, 'color':'#05b9f0', 'marginBottom':0}),#fig_line_cumulative_us_italy_china
                ]
            ),
            dcc.Graph(figure=fig_bar_nyc_last_5_days),
            html.Center(
                children=[
                html.H6('Day-to-day % Increases', style={'fontSize':14, 'color':'#05b9f0', 'marginTop':10, 'marginBottom':10}),
                html.H6('in Number of', style={'fontSize':10, 'color':'#05b9f0', 'marginTop':6, 'marginBottom':0}),
                html.H6('Confirmed Cases', style={'fontSize':10, 'color':'#05b9f0', 'marginTop':6, 'marginBottom':0}),
                html.H6('NYC', style={'fontSize':19, 'color':'#05b9f0', 'marginTop':6, 'marginBottom':10}),
                ]
            ),
            dcc.Graph(figure=fig_area_nyc_percentage_change),
            html.Center(
                children=[
            html.H6('Data from NY State DOH on ' + nyc_confirmed_latest_date, style={'fontSize':12, 'color':'#05b9f0', 'marginTop':10, 'marginBottom':8}),
                ]
            ),
        ],
        md=6,
    )
else:
    column1Left = dbc.Col(
        [
            html.Center(
                children=[
                    dcc.Graph(figure=fig_map_nyc_timeslider),
                ]
            )
        ],
        md=6
    )
column1Right = dbc.Col(
    [
        html.Center(
            children=[
                html.H6('NUMBER OF POSITIVE CASES OF COVID-19 BY COUNTY', style={'fontSize':18, 'color':'#05b9f0', 'marginTop':40, 'marginBottom':10}),
                html.H6('FOR THE TOP 12 COUNTIES RANKED BY THE MOST CASES', style={'fontSize':12, 'color':'#05b9f0', 'marginTop':0, 'marginBottom':0}),
                dcc.Graph(figure=fig_line_ny_cumulative),
                html.H6('TOTAL POSITIVE CASES OF COVID-19 BY COUNTY OVER TIME', style={'fontSize':18, 'color':'#05b9f0', 'marginTop':0, 'marginBottom':10}),
                html.H6('FOR THE TOP 8 COUNTIES RANKED BY THE MOST CASES', style={'fontSize':12, 'color':'#05b9f0', 'marginTop':0, 'marginBottom':0}),
                dcc.Graph(figure=fig_line_ny_overtime),
            ]
        )
    ],
    md=6
)
column1bottomCenter = dbc.Col(
    [
        html.Center(
            children=[
            html.H6('Data for above interactive charts from NY State DOH Updated '+ nyc_confirmed_latest_date, style={'fontSize':12, 'color':'#05b9f0', 'marginTop':20, 'marginBottom':20}),
            ]
        )
    ],
    md=12,
)


column2Center = dbc.Col(
    [
        html.Center(
            children=[
            html.Br(),
            html.Span(' ', className='mr-1'),
            html.H6('NUMBER OF CONFIRMED CASES OF COVID-19', style={'fontSize':19, 'color':'#05b9f0', 'marginTop':60, 'marginBottom':10}),
            html.H6('IN NEW YORK STATE BY COUNTY', style={'fontSize':19, 'color':'#05b9f0', 'marginTop':10, 'marginBottom':10}),
            html.Img(src=app.get_asset_url('Covid-19_Cases_NYS_annotated.png'), style={'display': 'block', 'width':'70%'}),
            ]
        )
    ],
    md=12,
)

column2bottomCenter = dbc.Col(
    [
        html.Center(
            children=[
            html.H6('Data from NY State DOH, last updated ' + nyc_confirmed_latest_date, style={'fontSize':12, 'color':'#05b9f0', 'marginTop':0, 'marginBottom':8}),#fig_line_cumulative_us_italy_china
            ]
        )
    ],
    md=12,
)
columnStackedCounty = dbc.Col(
    [
        html.Center(
            children=[
            dcc.Graph(figure=fig_stacked_ny),
            dcc.Graph(figure=fig_stacked_change_county_cases),
            html.H6('Data from NY State DOH, last updated on ' + nyc_confirmed_latest_date, style={'fontSize':12, 'color':'#05b9f0', 'marginTop':0, 'marginBottom':8}),#fig_line_cumulative_us_italy_china
            html.H6('Please be mindful that only a limited amount of people are given tests at this time.', style={'fontSize':12, 'color':'#05b9f0', 'marginTop':0, 'marginBottom':8}),#fig_line_cumulative_us_italy_china
            ]
        )
    ],
    md=12,
)


column3CenterAll = dbc.Col(
    [
        html.Center(
            children=[
                html.Br(),
                html.Span(' ', className='mr-1'),
                html.Br(),
                html.Span(' ', className='mr-1'),
                #html.H6('DAY-TO-DAY CHANGES IN CONFIRMED CASES ITALY VS U.S. VS CHINA', style={'fontSize':19, 'color':'#05b9f0', 'marginTop':10, 'marginBottom':10}),
                dcc.Graph(figure=fig_area_world_day_changes),
            ]
        )
    ]
)


column4CenterAll = dbc.Col(
    [
        html.Br(),
        html.Span(' ', className='mr-1'),
        dcc.Graph(figure=fig_line_cumulative_us_italy_china),
        html.Br(),
        html.Span(' ', className='mr-1'),
        html.Br(),
        html.Span(' ', className='mr-1'),
        html.Br(),
        html.Span(' ', className='mr-1'),
    ]
)




column_predictions = dbc.Col(
    [
        html.Center(
            children=[
                html.H6('Our Prediction for the next few days for the United States' , style={'fontSize':23, 'color':'#05b9f0', 'marginTop':70, 'marginBottom':8}),
                html.Hr(className="my-2"),
                html.P('This is a basic prediction using logistic regression with Facebook Prophet, setting the carrying capacity at 500,000 on April 3, 1,000,000 for May 2. The capacity is the most optimistic projection to fit the existing data. We believe this graph is helpful in understanding the best case scenario for how long it will take for life to get back to normal.', style={'fontSize':16, 'color':'link', 'marginTop':0, 'marginBottom':0}),
                html.P('The black dots are existing recorded information for the United States. We believe that any prediction after April 12 is obsolete.', style={'fontSize':16, 'color':'link', 'marginTop':0, 'marginBottom':0}),
                html.Img(src=app.get_asset_url('fb_prophet_confirmed_500000_4_03.png'), style={'display': 'block', 'width':'100%','marginTop':20,'marginBottom':0}),
                html.Img(src=app.get_asset_url('fb_prophet_confirmed_1000000_5_02.png'), style={'display': 'block', 'width':'100%','marginTop':20,'marginBottom':0}),
                html.P('Prediction of deaths in the next few days with a carrying capacity going towards 80,000 in within the next 14 days.', style={'fontSize':16, 'color':'link', 'marginTop':0, 'marginBottom':0}),
                html.Img(src=app.get_asset_url('fb_prophet_deaths_20000_4_03.png'), style={'display': 'block', 'width':'100%','marginTop':20,'marginBottom':0}),
                html.Img(src=app.get_asset_url('fb_prophet_deaths_80000_5_02.png'), style={'display': 'block', 'width':'100%','marginTop':20,'marginBottom':0}),
                html.P('Our conclusion from this prediction is that in the best case scenario, the curve will flatten for the whole of the U.S. within this month and everyone should be assuming their normal life in late May.', style={'fontSize':16, 'color':'link', 'marginTop':15, 'marginBottom':0}),
                html.P('Here is the Law of Population Growth formula we are using to show you how we define carrying capacity:', style={'fontSize':16, 'color':'link', 'marginTop':15, 'marginBottom':0}),
                html.Img(src=app.get_asset_url('logistic_regression_population_growth.PNG'), style={'display': 'block', 'width':'75%','marginTop':20,'marginBottom':0}),
                html.P('Data Provided by the Johns Hopkins University Center for Systems Science and Engineering (JHU CSSE)', style={'fontSize':12, 'color':'link', 'marginTop':15, 'marginBottom':0}),
                dbc.Button('More on Logistic Regression', size="sm", color="link",href = "https://en.wikipedia.org/wiki/Logistic_function",style={'marginBottom':100, 'marginTop':15}), 
                dbc.Button('More about Facebook Prophet',size="sm", color="link",href = "https://facebook.github.io/prophet/docs/saturating_forecasts.html#forecasting-growth",style={'marginBottom':100, 'marginTop':15}), 
                html.Img(src=app.get_asset_url('revolution.jpg'), style={'display': 'block', 'width':'40%','marginTop':20,'marginBottom':170}),
            ]
        ),
    ],
    md=8,
)


column_data_sources = dbc.Col(
    [
        html.Center(
            children=[
                html.H6('Data Sources' , style={'fontSize':23, 'color':'#05b9f0', 'marginTop':0, 'marginBottom':8}),
                html.Hr(className="my-2"),
                dbc.Button('New York City Government Department of Health', color="link",href = "https://www1.nyc.gov/assets/doh/downloads/pdf/imm/covid-19-daily-data-summary-04052020-1.pdf",style={'marginBottom':0, 'marginTop':0}), 
                html.P('The official New York City Government Department of Health website.', style={'fontSize':16, 'color':'link', 'marginTop':0, 'marginBottom':0}),
                dbc.Button('New York State Government Department of Health', color="link",href = "https://coronavirus.health.ny.gov/county-county-breakdown-positive-cases",style={'marginBottom':0, 'marginTop':0}), 
                html.P('The official New York State Government Department of Health website.', style={'fontSize':16, 'color':'link', 'marginTop':0, 'marginBottom':0}),
                dbc.Button('Johns Hopkins University Center for Systems Science and Engineering (JHU CSSE)', color="link",href = "https://github.com/CSSEGISandData/COVID-19",style={'marginBottom':0, 'marginTop':0}), 
                html.P('An open source data repository that pools current data from the WHO and CDC for conversion into programmable data formats.', style={'fontSize':16, 'color':'link', 'marginTop':0, 'marginBottom':0}),
                dbc.Button('United States Centers for Disease Control and Prevention', color="link",href = "https://www.cdc.gov/coronavirus/2019-ncov/index.html",style={'marginBottom':0, 'marginTop':0}), 
                html.P('Official United States of America COVID-19 resource provided by the CDC.', style={'fontSize':16, 'color':'link', 'marginTop':0, 'marginBottom':0}),
                dbc.Button('World Health Organization (WHO)', color="link",href = "https://www.who.int/",style={'marginBottom':0, 'marginTop':0}), 
                html.P("The World Health Organization directs international health within the United Nations' system and leads partners in global health responses.", style={'fontSize':16, 'color':'link', 'marginTop':0, 'marginBottom':40}),

                html.Hr(className="my-2"),
                html.P('Please note that the data provided on this site is only as accurate and recent as the sources cited.' , style={'fontSize':16, 'color':'#0496c3', 'marginTop':0, 'marginBottom':8}),
                html.P('Confirmed number of cases is only an indication of the availability of testing and willingness of those infected to test.', style={'fontSize':16, 'color':'#0496c3', 'marginTop':10, 'marginBottom':0}),
                html.P('We recommend using the death count as a more accurate guideline for actual number of cases.', style={'fontSize':16, 'color':'#0496c3', 'marginTop':10, 'marginBottom':0}),
                html.P('The death rate of Covid-19 is believed to be around 3%.', style={'fontSize':16, 'color':'#0496c3', 'marginTop':10, 'marginBottom':0}),
                html.P('Please also be aware that there may be a delay in reporting by the above sources on any numbers displayed.', style={'fontSize':16, 'color':'#0496c3', 'marginTop':10, 'marginBottom':200}),
            
                html.H6('Our Mission' , style={'fontSize':23, 'color':'#05b9f0', 'marginTop':0, 'marginBottom':8}),
                html.Hr(className="my-2"),
                html.P("Our goal is to inform NYC residents of the current state of the Covid-19 pandemic as it pertains to the local community.", style={'fontSize':16, 'color':'link', 'marginTop':0, 'marginBottom':0}),
                html.P("We seek to provide the best possible tools in which to understand the data gathered from trusted, recognizable sources.", style={'fontSize':16, 'color':'link', 'marginTop':10, 'marginBottom':0}),
                html.P("As the situation develops, we will continue to help provide the best information possible.", style={'fontSize':16, 'color':'link', 'marginTop':10, 'marginBottom':0}),
                html.P("Below, we have provided curated content that helps to enhance our connection to humanity, to allow ourselves to be more at peace within, and to be better prepared for what is ahead. Please read on...", style={'fontSize':16, 'color':'link', 'marginTop':10, 'marginBottom':230}),

            ]
        ),
    ],
    md=8,
)








#----------------------------------------------------------------------------------------------------------













selectedWritingsHeaderCenter = dbc.Col(
    [
        html.Center(
            children=[
                #html.Img(src=app.get_asset_url('Covid19-Website-R7-000_0038_Layer-28.png'), style={'display': 'block', 'width':'100%'}),
                html.Img(src=app.get_asset_url('mindfulnessShopping.gif'), style={'display': 'block', 'width':'100%', 'marginTop':30}),
                html.Br(),
                html.Span(' ', className='mr-1'),
            ]
        )
    ],
    md=8,
)


collapseEniqueArticle = dbc.Col(
    [
        html.Center(
            html.Div(
                [
                    dbc.Card(
                        dbc.CardBody(
                        [
                            html.H4("Mindfulness When Shopping",className="card-text",style={'fontSize':32, 'marginTop':40, 'marginBottom':55}),
                            html.P(
                                "It’s difficult to stay home during this crisis if we’re ill-prepared. We have to stock up on food, snacks, vitamins, hand sanitizer and, of course, toilet paper. It’s important to have a clean booty during a pandemic.",className="card-text",style={'text-align':'left'}
                            ),
                            html.P(
                                "That’s why shopping for quarantine life has become an event. Thanks to the hours of predictive programming instilled into our minds by post-apocalyptic movies centering on societal collapse, we haven’t been reduced to chaotic creatures. However, as someone who is still assisting customers, both young and old, I have noticed an array of mindfulness and lack thereof when it comes to shopping. ",className="card-text",style={'text-align':'left'}
                            ),
                            html.P(
                                "So here are a few tips you can use to protect yourself and others when shopping.",className="card-text",style={'text-align':'left'}
                            ),
                            html.H5("Mask & Gloves ",className="card-text",style={'fontSize':26, 'marginTop':35, 'marginBottom':35}),
                            html.P(
                                "Seriously. We’re at a point where you have to assume someone has touched the item you just grabbed, whether it’s an employee or another customer. It helps you, the employees, fellow customers, and your loved ones. The addition of the mask can help ease any anxieties that employees may have, and it adds a layer of protection for you, too. ",className="card-text",style={'text-align':'left'}
                            ),
                            html.P(
                                "According to the Centers for Disease Control and Prevention (CDC), It is recommended to use nitrile gloves, natural rubber gloves, or polychloroprene gloves, as they provide higher elasticity than vinyl gloves. ",style={'text-align':'left'}
                            ),
                            html.P(
                                "For masks, as you may already know, the N-95 Respirator comes highly recommended, for its tight fight and ability to reduce 95 percent of the wearer’s exposure to small particles and large droplets. A surgical mask may work in a pinch, however, it will not provide the needed protection against smaller airborne particles.",style={'text-align':'left'}
                            ),
                            html.P(
                                "Ideally, it is suggested that these masks be thrown away after each use. But given the current deficiencies of Personal Protective Equipment (PPE) that hospitals are facing, it would be considerate if you did not hoard masks, which could be accomplished by giving each individual mask a longer service life.",style={'text-align':'left'}
                            ),
                            html.P(
                                "If possible, you can help by reaching out to local hospitals and donating masks. ",style={'text-align':'left'}
                            ),
                            html.H5("What to Do",className="card-text",style={'fontSize':26, 'marginTop':35, 'marginBottom':35}),
                            html.P(
                                "One store will not operate like the other, especially if you are frequenting independent pharmacies, grocery stores, and food processors. Make an attempt to learn their style of operations, checkout procedures, payment options, hours, and safety precautions.For example, Stop and Shop allow senior citizens (60-year-olds and over) to shop between 6-7:30 am, while Trader Joe’s is only allowing 30 customers in the store at one time.",className="card-text",style={'text-align':'left'}
                            ),
                            html.P(
                                "Generally, you can avoid the crowds during the early mornings, because as the saying goes: the early bird catches the worm. Just pay attention to any updates that shops may have via their social media accounts, or call ahead if you’re not sure.",className="card-text",style={'text-align':'left'}
                            ),
                            html.H5("Know What You Want",className="card-text",style={'fontSize':26, 'marginTop':35, 'marginBottom':35}),
                            html.P(
                                "For real, this isn’t the time to be window shopping. With the ever-increasing descent upon grocery stores and pharmacies, it’s imperative to have a list of the items you will be needing. ",style={'text-align':'left'}
                            ),
                            html.P(
                                "The quicker you are the quicker the checkout line will move, which will result in shorter exposure times. If you need help figuring out how to shop, refer to the god-awful film, “Jingle All the Way” starring Arnold Schwarzenegger and Sinbad.",className="card-text",style={'text-align':'left'}
                            ),
                            html.H5("Gimme Some Space",className="card-text",style={'fontSize':26, 'marginTop':35, 'marginBottom':35}),
                            html.P(
                                "People are touching, smiling, and not respecting your personal space. The whole time my mind is thinking, 'Gimme some space, bro!' ",style={'text-align':'left'}
                            ),
                            html.P(
                                "Do you people even understand what’s happening out here? I’m not trying to add to the fear-mongering tactics some have accused the media of using, but if we don’t take this seriously we will be risking people’s health by extending this pandemic’s life span.",className="card-text",style={'text-align':'left'}
                            ),
                            html.P(
                                "Please practice social distancing. Communicate clearly and thoroughly from the recommended six-foot distance. Keep in mind, that if you’re on a possible collision course with someone waving is one of the best non-verbal cues that you can rely on if you’re having trouble commanding a person’s attention.",className="card-text",style={'text-align':'left'}
                            ),
                            html.P(
                                "Remember, if you can smell someone’s breath, cologne, or body odor you are too close.",className="card-text",style={'text-align':'left'}
                            ),
                            html.H5("Wipe Everything Down",className="card-text",style={'fontSize':26, 'marginTop':35, 'marginBottom':35}),
                            html.P(
                                "Once you’re home, it’s important to wipe down any of the items you may have purchased, whether it’s packaged food products, produce, or home supplies. If it’s possible, designate an area at home that will be used to place outside items on. Wipe down this area after everything is put away. ",className="card-text",style={'text-align':'left'}
                            ),
                            html.P(
                                "A thorough cleaning of fruits and veggies is crucial before they are stored away, even for fruits that are protected by an out layer, like oranges, bananas, and melons. A simple soak/wash in a bowl of water with vinegar (apple cider vinegar or white vinegar) and a gentle scrub with soap would suffice.",className="card-text",style={'text-align':'left'}
                            ),
                            html.P(
                                "For those of you that use reusable bags, especially those made from cloth, it’s also essential to clean the bag, too. ",className="card-text",style={'text-align':'left'}
                            ),
                            html.H5("R-E-S-P-E-C-T",className="card-text",style={'fontSize':26, 'marginTop':35, 'marginBottom':35}),
                            html.P(
                                "In America, we live in such a desensitized society that people watch police killings on their phones while eating their avocado toast. ",className="card-text",style={'text-align':'left'}
                            ),
                            html.P(
                                "We lack empathy.", className="blockquote"
                            ),
                            html.P(
                                "You don’t care about my plight or the social injustices that affect me? Whatever. That was before this new situation engulfed America, and now we’re in this together.",className="card-text",style={'text-align':'left'}
                            ),
                            html.P(
                                "So you may have looked down on or ignored the so-called low-skilled workers two months ago, but now we’re the ones you seek for cleanliness, supplies, food, transportation, education, and the normality that dissolved, due to this pandemic, yet you still yearn for to calm your anxieties. ",className="card-text",style={'text-align':'left'}
                            ),
                            html.P(
                                "We don’t want to be out here, but we are. We’re risking our own health and that of our loved ones, which is making your life easier. Please take the time to show your appreciation in a non-condescending fashion. We are essential workers. ",className="card-text",style={'text-align':'left'}
                            ),
                            html.Hr(),
                            html.P(
                                "Written by:",style={'fontSize':14, 'marginTop':40, 'marginBottom':0},
                                className="card-text"),
                            dbc.Button('Enrique Grijalva', color="link",href = "https://www.linkedin.com/in/enrique-grijalva-15833059", size="sm",style={'marginBottom':0, 'marginTop':0}), 
                            ]
                        ), color="light"
                    )
                ]
            )
        )
    ],
    md=8,
)




restoringPeaceCenter = dbc.Col(
    [
        html.Center(
            children=[
                html.Img(src=app.get_asset_url('restoringPeace.png'), style={'marginTop':60,'display': 'block', 'width':'100%'}),
                html.Br(),
                html.Span(' ', className='mr-1'),
                html.Div(
                    [
                        dbc.Card(
                            dbc.CardBody(
                            [
                                html.H4("Restoring Peace Within Yourself",className="card-text",style={'fontSize':32, 'marginTop':40, 'marginBottom':55}),
                                html.P(
                                    "We understand how a pandemic can create anxiety, panic and stress, especially with how fast the worldwide spread has been. We would like to help you restore peace of mind within yourself by introducing the mindfulness practice taught by Thich Nhat Hanh, the father of mindfulness. The following comes from the chapter “Restoring Peace Within Yourself” from his book True Love.",className="blockquote",style={'text-align':'left'}
                                ),
                                html.P(
                                    "During the day, if you practice walking meditation, each step brings you back to the present moment; each step enables you to touch what is beautiful, what is true. And in this way, after a few weeks of practice, joy will become something possible, you will be able to undo many knots within yourself, and you will be able to transform negative energies into joy and peace. The Buddha said this: “The object of your practice should first of all be yourself. Your love for the other, your ability to love another person, depends on your ability to love yourself.” If you are not able to take care of yourself, if you are not able to accept yourself, how could you accept another person and how could you love him or her? So it is necessary to come back to yourself in order to be able to achieve the transformation.",className="card-text",style={'text-align':'left'}
                                ),
                                html.P(
                                    "Each of us is a king who reigns over a very vast territory that has five rivers. The first river is our body, which we do not know well enough. The second is the river of sensations. Each sensation is a drop of water in this river. There are pleasant sensations, others that are unpleasant, and neutral sensations. To meditate is to sit down on the bank of the river of sensations and identify each sensation as it arises. The third is the river of perceptions, which it is necessary to observe. You must look deeply into their nature in order to understand. The fourth is the river of mental formations, of which there are fifty-one. And finally, the fifth is the river of consciousness.",className="card-text",style={'text-align':'left'}
                                ),
                                html.P(
                                    "Our territory is really very vast, but we are not responsible kings or queens. We always try to dodge away and we do not keep up a real surveillance of our territory. We have the feeling that there are immense conflicts there, too much suffering, too much pain—that is the reason we are very hesitant to get back to our territory. Our daily practice consists in running away. If we have a moment free, we will make use of it to watch television or read a magazine article so we will not have to go back to our territory. We are afraid of the suffering that is inside us, afraid of war and conflicts.",className="card-text",style={'text-align':'left'}
                                ),
                                html.P(
                                    "The practice of mindfulness, the practice of meditation, consists of coming back to ourselves in order to restore peace and harmony. The energy with which we can do this is the energy of mindfulness. Mindfulness is a kind of energy that carries with it concentration, understanding, and love. If we come back to ourselves to restore peace and harmony, then helping another person will be a much easier thing.",className="card-text",style={'text-align':'left'}
                                ),
                                html.P(
                                    "Caring for yourself, reestablishing peace in yourself, is the basic condition for helping someone else. So that the other can stop being a bomb, a source of pain for ourselves and others, you really have to help him to defuse the bomb. To be able to provide help, we have to have a little calm, a little joy, a little compassion in ourselves. This is what we get from mindfulness in everyday life, because mindfulness is not something that is only done in a meditation hall; it is also done in the kitchen, in the garden, when we are on the telephone, when we are driving a car, when we are doing the dishes.",className="card-text",style={'text-align':'left'}
                                ),
                                html.P(
                                    "If you can do it this way, three weeks are enough to transform the pain inside you, to bring back your joy in living, to cultivate the energy of compassion with which you can help the person you love. The practice of being there with what is beautiful and with what is healing is something we should do every day, and it is possible to do this in everyday life.",className="card-text",style={'text-align':'left'}
                                ),
                                html.P(
                                    "In order to support your mindfulness practice, you might be interested in trying some mobile apps, such as Insight Timer, Calm, Headspace, with which you can practice mindfulness wherever you go. Hope peace of mind and love be with you, especially in this extraordinarily challenging time!", className="blockquote",style={'text-align':'left'}
                                ),
                                dbc.CardLink("More on Insight Timer", href="https://insighttimer.com/", style={'color':'#16849c'}),
                                dbc.CardLink("More on Calm", href="https://www.calm.com/", style={'color':'#16849c'}),
                                dbc.CardLink("More on Headspace", href="https://www.headspace.com/", style={'color':'#16849c'}),
                                html.Hr(),
                                html.P('Excerpt from Zen Master Thich Nhat Hanh. "True Love: A Practice for Awakening the Heart."Penguin Random House, 2004. Chapter 8.',style={'fontSize':14, 'marginTop':45}, className="card-text"),
                                html.P('Intro and Afterword by',style={'fontSize':14},className="card-text"),
                                dbc.Button('Wen Ping Lin', color="link",href = "https://www.linkedin.com/in/wenpinglin", size="sm",style={'marginBottom':0, 'marginTop':0}), 
                            ]), color="light"
                        )
                    ])
                ]
            )
    ],
    md=8,
)



onSelfReflectionCenter = dbc.Col(
    [
        html.Center(
            children=[
                html.Img(src=app.get_asset_url('onSelfReflection.jpg'), style={'marginTop':60,'display': 'block', 'width':'100%'}),
                html.Br(),
                html.Span(' ', className='mr-1'),
                html.Div(
                    [
                        dbc.Card(
                            dbc.CardBody(
                            [
                                html.H4("Self-Reflection as a Fundamental Activity",className="card-text",style={'fontSize':32, 'marginTop':40, 'marginBottom':55}),
                                html.P(
                                    "Approaching the second week of self-isolation has felt momentous. The first week was filled with anxiety of the unknown and the flurry of stocking up at the supermarket and pharmacy. But now having found some semblance of a routine - grocery shopping once a week, rotating working areas within the apartment to keep things stimulating, taking up new hobbies, and reconnecting with friends and family, this all feels a bit more bearable. ",className="card-text",style={'text-align':'left'}
                                ),
                                html.P(
                                    "But more time indoors has meant more time for introspection. This means getting reacquainted with the self, all of the neuroses, nagging thoughts, and feelings. For many, life is just too busy to allow for moments of self-reflection. Coming face to face with your own thoughts is also not easy. But now that we have more time and less distractions to hide behind, we are being forced to do so. Remember that one time you tried to meditate? Yes, I mean sitting with ALL of your thoughts and feelings and letting them go. Even on a normal day this is difficult to do. But worries are running higher than normal around the well-being of family, job security, parenting and working from home, and general uncertainty of the future.",className="card-text",style={'text-align':'left'}
                                ),
                                html.P(
                                    "We need to understand that the only way is working through these complex thoughts and feelings. The truth is, this is a great time for self-reflection as individuals and as humanity. Are you living your best self? What do you truly value? What should we as humanity value? What is fundamentally broken in our society? How can we fix it? What is our civic role and duty in society? What does it mean to be interconnected? Perhaps this introspection will mean we can be better sons and daughters, mothers and fathers, citizens, citizens of the world when we emerge from the other side.",className="card-text",style={'text-align':'left'}
                                ),
                                html.P(
                                    "I have resolved to embrace this moment in time. To view this as a profound lesson. Rather than fighting feelings of anxiety, depression, or loneliness, accept them, learn from them and let them go. I invite you to join me to do the same! My hope is that this moment in time will be a great learning opportunity for individuals. Embrace yourself and others. Be kind to one another in awareness that we are all going through a difficult time together.",className="card-text",style={'text-align':'left'}
                                ),
                                html.P(
                                    "Here are some ways to ease into a mindset that is open to self-reflection:",className="card-text",style={'text-align':'left'}
                                ),
                                html.H5("Meditation",className="card-text",style={'fontSize':26, 'marginTop':35, 'marginBottom':35}),

                                html.P(
                                    "As mentioned, the ultimate practice for sitting with the self is meditation. There are some amazing apps, my favorite being Insight Timer, for home meditation. ",className="card-text",style={'text-align':'left'}
                                ),
                                html.P(
                                    "If you find it difficult to meditate alone, set aside time with those you live with or schedule a session virtually with friends! For beginners who find it difficult to sit in one place for a long time, you can easily adopt other mindfulness practices including mindful eating and mindful walking in the local park.",className="card-text",style={'text-align':'left'}
                                ),
                                dbc.CardLink("More on Insight Timer", href="https://insighttimer.com/", style={'color':'#16849c'}),
                                dbc.CardLink("Helpful Link for Mindful Eating", href="https://www.health.harvard.edu/staying-healthy/8-steps-to-mindful-eating", style={'color':'#16849c'}),
                                dbc.CardLink("Helpful Link for Mindful Walking", href="https://chopra.com/articles/mindful-walking-practice-how-to-get-started", style={'color':'#16849c'}),
                                html.H5("Journaling",className="card-text",style={'fontSize':26, 'marginTop':35, 'marginBottom':35}),
                                html.P(
                                    "Whether you are a seasoned journaler or not, writing out your thoughts and feelings can be a therapeutic way to decompress. What can be helpful is setting aside a time to write regularly around the same time. For instance, every Sunday evening before bed. Keeping a gratitude journal of sorts can help as well. For those who struggle with writing you can write one sentence daily on what you are grateful for. ", className="card-text",style={'text-align':'left'}
                                ),
                                dbc.CardLink("On Keeping a Gratitude Journal", href="https://greatergood.berkeley.edu/article/item/tips_for_keeping_a_gratitude_journal", style={'color':'#16849c'}),
                                html.H5("Walking",className="card-text",style={'fontSize':26, 'marginTop':35, 'marginBottom':35}),
                                html.P(
                                    "Getting outside in the fresh air for a short while (preferably alone) can be helpful. If there is a garden or park nearby take advantage of it and soak in the spring breeze! Walking has been known to improve creativity and the thought process according to a study by Stanford University. You can opt to walk with a companion but considering the number of restrictions in many countries regarding self-isolation this is not advised unless you live with them. That being said, solo is probably best so you can focus on your thoughts.", className="card-text",style={'text-align':'left'}
                                ),
                                dbc.CardLink("Study on the Correlation Between Walking & Creativity", href="https://news.stanford.edu/2014/04/24/walking-vs-sitting-042414/", style={'color':'#16849c'}),
                                html.H5("Exploring Happiness",className="card-text",style={'fontSize':26, 'marginTop':35, 'marginBottom':35}),
                                html.P(
                                    "Lots of people have the misconception of what happiness means. For many it is something that is a sustained state to aspire to. But in reality, happiness is constantly in a flux and related to self-resilience. Resilience means building the muscle to allow for living joyfully while in full awareness of life’s inherent ups and downs. This is a great moment in time to exercise that muscle! Two great resources include “The Happiness Project” by Gretchen Rubin and a free Coursera module, “The Science of Well-Being,” taught by Professor Laurie Santos at Yale University.", className="card-text",style={'text-align':'left'}
                                ),
                                dbc.CardLink("Article on How Resilience is Tied to Happiness", href="https://qz.com/1289236/resilience-is-the-new-happiness/", style={'color':'#16849c'}),
                                html.Hr(),
                                html.P(
                                    "Written by:",style={'fontSize':14, 'marginTop':40, 'marginBottom':0},
                                    className="card-text"),
                                dbc.Button('Jenny Kai', color="link",href = "https://www.linkedin.com/in/jenny-a-kai-06b89329/", size="sm",style={'marginBottom':0, 'marginTop':0}), 
                            ]), color="light"
                        )
                    ])
                ]
            )
    ],
    md=8,
)

singleColumn = dbc.Col([],md=1)
doubleColumn = dbc.Col([],md=2)

tab1_data_content = dbc.Card(
    dbc.CardBody(
        [
        dbc.Row([columnTopAlert]),
        dbc.Row([columnTopLeft, columnTopCenter, columnTopRight]),

        dbc.Row([singleColumn,columnNeighborhoods, singleColumn]), 
        dbc.Row([singleColumn,column_nyc_stats, singleColumn]),

        dbc.Row([column_pie_queens_pop, column_pie_nyc_pop]),
        dbc.Row([column_pie_age_positive, column_pie_gender_positive]),
        dbc.Row([column_pie_age_passed, column_pie_gender_passed, column_pie_illness_passed]),


        dbc.Row([columnpiebottom]),
    
        dbc.Row([column1Left,column1Right]),
        dbc.Row([column1bottomCenter]),

        # dbc.Row([column2Center]), #, column2Right New York State Counties Map Pink Purple
        # dbc.Row([column2bottomCenter]),

        dbc.Row([columnStackedCounty]),

        dbc.Row([column3CenterAll]),# New Cases Worldwide
        dbc.Row([column4CenterAll]),#Confirmed cases Italy, China US


        #Deaths, Confirmed, Recovered
        # dbc.Row([columnDistC, columnDistR, columnDistL]),
        # dbc.Row([columnDistbottomCenter]),  

        dbc.Row([doubleColumn,column_predictions,doubleColumn]),
        dbc.Row([doubleColumn,column_data_sources,doubleColumn]),
        ]
    ),
    className="mt-3",
)


nav = dbc.Col(
    [
        dbc.Nav(
            [
                dbc.NavItem(dbc.NavLink("Things To Do", href="/todo", className='nav-link')),
                dbc.NavItem(dbc.NavLink("On Self-Reflection", href="/reflection", className='nav-link')),
                dbc.NavItem(dbc.NavLink("On Peace Within", href="/peace", className='nav-link')),
                dbc.NavItem(dbc.NavLink("Mindfulness Shopping", href="/shopping", className='nav-link')),
                # dbc.DropdownMenu(
                #     [dbc.DropdownMenuItem("Mindfulness When Shopping"), dbc.DropdownMenuItem("Item 2")],
                #     label="Mindfulness",
                #     nav=True,
                # ),
            ],fill=True
        )
    ],md=12
)

tab2_actions_content = dbc.Card(
    dbc.CardBody(
        [
            dbc.Row([nav]),  
            dbc.Row([doubleColumn, selectedWritingsHeaderCenter, doubleColumn]),
            dbc.Row([doubleColumn,collapseEniqueArticle, doubleColumn]),
            dbc.Row([doubleColumn,restoringPeaceCenter, doubleColumn]),
            dbc.Row([doubleColumn,onSelfReflectionCenter, doubleColumn]),     
        ]
    ),
    className="mt-3",
)


tabs = dbc.Tabs(
    [
        dbc.Tab(tab1_data_content, label="DATA", label_style={'fontSize':24}, labelClassName="text-info"),
        dbc.Tab(tab2_actions_content, label="ACTIONS", label_style={'fontSize':24}, labelClassName="text-info"),
    ]
)





singleColumn = dbc.Col([],md=1)
doubleColumn = dbc.Col([],md=2)
tripleColumn = dbc.Col([],md=3)

navbar = dbc.Col([
    dbc.Nav([dbc.NavItem(tabs)],fill=True)
],md=10)



layout = [
        dbc.Row([singleColumn, navbar, singleColumn]),  
        ]

