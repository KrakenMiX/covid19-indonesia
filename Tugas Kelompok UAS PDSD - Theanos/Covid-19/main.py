from sklearn.preprocessing import MinMaxScaler
import pandas as pd
from datetime import datetime as dt
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import geopandas as gpd
import textwrap
import streamlit as st
import folium
from folium.plugins import MarkerCluster
from folium.plugins import HeatMap
import plotly.express as px
import plotly.graph_objects as go


#Membuka Raw Data Covid-19 dan mengambil tiap-tiap data yang diperlukan
def covid():
    st.title('Data Covid-19 di Indonesia')
    
    df=pd.read_csv('covid-19.csv')
    df = df.rename(columns={'Date':'tanggal','Location':'lokasi'})
    df = df.drop(['Location Level','New Deaths per Million','Total Active Cases','Growth Factor of New Deaths','Growth Factor of New Cases','Total Deaths per 100rb','Total Deaths per Million','City or Regency','Special Status','New Cases per Million','Total Cases per Million','Time Zone', 'Island','Continent','Total Regencies','Total Cities','Total Districts','Total Urban Villages','Total Rural Villages','Area (km2)','Population','Population Density','Case Fatality Rate','Case Recovered Rate'], axis=1)

    df['tanggal'] = pd.to_datetime(df['tanggal'], format='%Y-%m-%d')
    df['bulan'] = df['tanggal'].dt.month   
    df['tahun'] = df['tanggal'].dt.year

    df = df[df['lokasi'] != 'Indonesia']
    

    bantu = []
    for i in df['Total Cases']:
        listBantu = ''
        if (i < 1000):
            listBantu= 'Ringan'
        elif (i < 10000):
            listBantu = 'Menengah'
        elif (i < 50000):
            listBantu= 'Kuat'
        else:
            listBantu = 'Sangat kuat'
        bantu.append(listBantu)
    df['Kategori Kasus'] = bantu

  
    bantu= []
    for i in df['Total Recovered']:
        listBantu = ''
        if (i < 250):
            listBantu = 'Sedikit'
        elif (i < 5000):
            listBantu = 'Sedang'
        else:
            listBantu = 'Tinggi'
        bantu.append(listBantu)
    df['kategori Total Recovered'] = bantu
    return df

def bantu(data):
    bantuvar = data
    return list(data.lokasi.unique())

st.set_page_config(layout="wide")

data = covid()

#Sidebar Filtering
st.sidebar.title('Pilihan Filtering')

#Filtering Tanggal
try:
    data['tanggal'] = data['tanggal'].dt.date
    dts = st.sidebar.date_input(label='Date Range ',
                value=(dt(year=2020, month=1, day=1),
                        dt(year=2022, month=12, day=31)),
                min_value=dt(year=2020,month=1, day=1),
                max_value=dt(year=2022,month=12, day=31),
                key='#date_range',
                help="The start and end date time")
    if not dts:
        data = data
        dts = ''
    else:
        data = data[data['tanggal'].isin(pd.date_range(start=dts[0].date(), end=dts[1].date(), inclusive="both"))]

except:
    pass

#Filtering Provinsi
try:
    prv = st.sidebar.multiselect('Provinsi', list(data['Province'].unique()))
    
    if not prv:
        data = data
        prv = ''
    else:
        data = data[data['Province'].isin(prv)]
        prv = f"Province: {', '.join(prv)}"
        
except:
    pass

#Filtering Kategori kasus
try:
    kasus = st.sidebar.multiselect('Kategori Kasus',list(data['Kategori Kasus'].unique()))
    if not kasus:
        data = data

        kasus = ''
    else:
        data = data[data['Kategori Kasus'].isin(kasus)]
        kasus = f"Kategori Kasus: {', '.join(kasus)}"
except:
    pass

#Filtering Kategori total recovered
try:
    options = list(data['kategori Total Recovered'].unique())
    trecor = st.sidebar.radio('Kategori Total Recovered', ["Semua"] + options)
    if trecor== "Semua":
        data = data
        trecor = ''
    else:
        data = data[data['kategori Total Recovered'] == trecor]
        trecor = f"kategori Total Recovered: {trecor}"

except:
    pass

#Tabel
st.dataframe(data)
st.empty()

#Metric data kasus
datas = data.copy()
lokasi = list(datas['lokasi'].unique())
bantu =  list(datas['lokasi'].values)
varBantu = {}
for s in bantu:
    if s in varBantu:
        varBantu[s] += 1
    else:
        varBantu[s] = 1

df_covid = pd.DataFrame.from_dict(varBantu, orient='index')
df_covid = df_covid.reset_index()
df_covid = df_covid.rename(columns = {'index':'lokasi',0:'total hari'})

# mengelompokkan data berdasarkan lokasi dan menjumlahkan data
df_covid19 = data.pivot_table(index = 'lokasi')
df_covid19 = df_covid19[['Latitude','Longitude']]
df_covid19 = df_covid19.reset_index()
join_data= pd.merge(df_covid, df_covid19, on='lokasi', how='inner')
maksimal = {}
minimal = {}
for total_kasus in datas['lokasi'].unique():
    maksimal[total_kasus ] = datas[datas['lokasi'].isin([total_kasus ])]['Total Deaths'].max()
    minimal[total_kasus ] = datas[datas['lokasi'].isin([total_kasus ])]['Total Deaths'].min()


maksimal = pd.DataFrame.from_dict(maksimal, orient='index').reset_index()
maksimal = maksimal.rename(columns = {'index':'lokasi',0:'Kematian_Tertinggi'})
minimal = pd.DataFrame.from_dict(minimal, orient='index').reset_index()
minimal = minimal.rename(columns = {'index':'lokasi',0:'Kematian_Terendah'})

#menggabungkan data
join_data =pd.merge(join_data,maksimal, on='lokasi', how='inner')
join_data =pd.merge(join_data,minimal, on='lokasi', how='inner')

#Data Kasus
st.title('Data Kasus')
col1, col2 = st.columns(2)
st.dataframe(join_data)
with col1:
    st.subheader('Total Kasus Covid Tertinggi Tercatat Dalam Hari ')
    st.metric(join_data['lokasi'][join_data['total hari'].idxmax()],
              join_data['total hari'][join_data['total hari'].idxmax()])

with col2:
    st.subheader('Total Kasus Kematian Tertinggi')
    st.metric(join_data['lokasi'][join_data['Kematian_Tertinggi'].idxmax()],join_data['Kematian_Tertinggi'][join_data['Kematian_Tertinggi'].idxmax()])

#with col3:
#    st.subheader('Total Kasus Kematian Terendah')
#    st.metric(join_data['lokasi'][join_data['Kematian_Terendah'].idxmax()],join_data['Kematian_Terendah'][join_data['Kematian_Terendah'].idxmin()])

#Mentotalkan nilai data-data dari macam kategori kasus untuk grafik total kasus  
total_cases = data[data['Tahun'] >= 2020]['Total Cases'].sum()
total_recovered = data[data['Tahun'] >= 2020]['Total Recovered'].sum()
total_deaths = data[data['Tahun'] >= 2020]['Total Deaths'].sum()
sum_data = {'Total Cases': total_cases, 'Total Recovered': total_recovered, 'Total Deaths': total_deaths}
df = pd.DataFrame(list(sum_data.items()), columns=['Categories', 'Data'])

#Grafik Total Kasus
st.title('Grafik Total Kasus')
st.set_option('deprecation.showPyplotGlobalUse', False)
data_type = st.radio('Pilih Tipe Data', ('Tahun', 'Bulan'))

#Filtering grafik tahun
if data_type == 'Tahun':
    years = data[data['Tahun'] >= 2020]['Tahun'].unique()

    year_selected = st.selectbox("Pilih Tahun", years)
    filtered_data = data[data['Tahun'] == year_selected]

    total_cases = filtered_data['Total Cases'].sum()
    total_recovered = filtered_data['Total Recovered'].sum()
    total_deaths = filtered_data['Total Deaths'].sum()

    sum_data = {'Total Cases': total_cases, 'Total Recovered': total_recovered, 'Total Deaths': total_deaths}
    df = pd.DataFrame(list(sum_data.items()), columns=['Categories', 'Data'])

    plt.figure(figsize=(12, 6))
    df = df.rename(columns={'Categories': 'Kategori Kasus', 'Data': 'Data total keseluruhan kasus'})
    sns.barplot(x='Kategori Kasus', y='Data total keseluruhan kasus', data=df)
    plt.title("Data Covid-19 Tahun " + str(year_selected))
    st.pyplot()

#Filtering grafik bulan
if data_type == 'Bulan':
    months = data['Bulan'].unique()
    years = data[data['Tahun'] >= 2020]['Tahun'].unique()
    
    year_selected = st.selectbox("Pilih Tahun", years)
    month_selected = st.selectbox("Pilih Bulan", months)
    filtered_data = data[(data['Bulan'] == month_selected) & (data['Tahun'] == year_selected)]
    
    total_cases = filtered_data['Total Cases'].sum()
    total_recovered = filtered_data['Total Recovered'].sum()
    total_deaths = filtered_data['Total Deaths'].sum()

    sum_data = {'Total Cases': total_cases, 'Total Recovered': total_recovered, 'Total Deaths': total_deaths}
    df = pd.DataFrame(list(sum_data.items()), columns=['Categories', 'Data'])

    plt.figure(figsize=(12, 6))
    df = df.rename(columns={'Categories': 'Kategori Kasus', 'Data': 'Data total keseluruhan kasus'})
    sns.barplot(x='Kategori Kasus', y='Data total keseluruhan kasus', data=df)
    plt.title(f"Data Covid-19 Bulan {month_selected} Tahun {year_selected}")
    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.pyplot()

st.caption('*Kategori kasus berisikan Total kasus,Total Sembuh dan juga Total kematian dari Total data Covid-19 di Indonesia')
st.caption('*Angka 1.0 dari Total Kasus keseluruhan kasus mewakilkan nilai 1 juta kasus')

#Mapping Kasus
st.title('Mapping Penyebaran kasus Covid-19 di Indonesia')
tahun = st.slider('Pilih Tahun', min_value=2020, max_value=2022, value=2020, step=1)
if st.button("Buka Map"):
    # Filtering data berdasarkan tahun yang dipilih
    filtered_data = data[data.Tahun == tahun]

    # Buat GeoDataFrame dari filtering data 
    geometry = gpd.points_from_xy(filtered_data.Longitude, filtered_data.Latitude)
    geo_data = gpd.GeoDataFrame(filtered_data[["Latitude", "Longitude", "lokasi", "Tahun", "Total Cases"]],
                                geometry=geometry)

    world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    fig, ax = plt.subplots(figsize=(24, 18))
    world[world.continent == 'Asia'].plot(ax=ax, color='white', edgecolor='black')
    geo_data.plot(column="Total Cases", ax=ax, legend=True, figsize=(24, 18))

    st.pyplot() 

#data covid dunia
st.title('Data Covid-19 di dunia')  

df1=pd.read_csv('covid_data_dunia_cleaned.csv')  
df1 = df1.rename(columns={'Country,Other':'negara','Location':'lokasi'})

negara_pilihan = st.multiselect("Pilih negara:", df1['negara'].unique())

if negara_pilihan:
    df_negara_terpilih = df1[df1['negara'].isin(negara_pilihan)]
else:
    df_negara_terpilih = df1

st.dataframe(df_negara_terpilih)

 
 


