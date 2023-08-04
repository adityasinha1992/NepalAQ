#!/usr/bin/env python
# coding: utf-8

# Sensor Group ID: 1786
# Sensor members (170338-170343)
# 118489 Birendarnagar
# 99035 Bharatpur-27
# 170015 Bhimnagar
# 99215 Fulbari
# 169991 Krishnapur
# 160173 Bharatpur-3

# File Setup

# In[110]:


import requests
import pandas as pd
from datetime import datetime
from datetime import timedelta
import time
import json
import os
from os.path import join, getsize
from pathlib import Path
import glob
from io import StringIO
import matplotlib.pyplot as plt
import seaborn as sns
import earthpy as et
import pytz
import numpy as np
import matplotlib.patches as mpatches
from matplotlib.dates import DateFormatter
import matplotlib.ticker as mticker

# API Keys 
key_read  = 'insert-read-key-here'
key_write = 'insert-write-key-here'

# Sleep Seconds, recommended by purple air and to not atempt to pull too much data at once, adjustable per computer specs
sleep_seconds = 3

#Start and end Dates
bdate = '04-10-2023'
edate = '04-20-2023'
#Set group id, make sure to add members and create group on Purple air website beforehand 
groupid = '1786'
#set averaging time
average_time=60 
#set folderpath for output
folderpath = r'/Users/jonathanpallotto/Documents/'


# Sensor list

# In[111]:


#Creates Sensors List out of group ID
def get_sensorslist(groupid,key_read):
    # PurpleAir API URL
    root_url = 'https://api.purpleair.com/v1/groups/'

    fields_list = ['id','sensor_index','created'] 
            
    # Final API URL
    api_url = root_url + groupid + f'?api_key={key_read}'
    print(api_url)
    
    # Getting data
    response = requests.get(api_url)

    if response.status_code == 200:
        print(response.text)
        json_data = json.loads(response.content)['members']
        df = pd.DataFrame.from_records(json_data)
        df.columns = fields_list
    else:
        raise requests.exceptions.RequestException
    
    filename = folderpath + '\sensors_list.csv'
    df.to_csv(filename, index=False, header=True)
            
    # Creating a Sensors 
    sensorslist = list(df.id)
    print(sensorslist)
    return sensorslist


# Get Historical Data

# In[112]:


#Creates API URLS and writes data to csv files
def get_historicaldata(sensors_list,bdate,edate,average_time,key_read):
    
    # Historical API URL
    root_api_url = 'https://api.purpleair.com/v1/groups/' + groupid + '/members/'
    
    # Average time: The desired average in minutes, one of the following:0 (real-time),10 (default if not specified),30,60
    average_api = f'&average={average_time}'

    # Creating fields api url from fields list to download the data: Note: Sensor ID/Index will not be downloaded as default
    # Secondary data file fields (A)
    fields_list_sec_a = ['0.3_um_count_a', '0.5_um_count_a', '1.0_um_count_a', '2.5_um_count_a', '5.0_um_count_a', '10.0_um_count_a', 
               'pm1.0_atm_a', 'pm10.0_atm_a']
    for i,f in enumerate(fields_list_sec_a):
        if (i == 0):
            fields_api_url_seca = f'&fields={f}'
        else:
            fields_api_url_seca += f'%2C{f}'

    # Secondary data file fields (B)
    fields_list_sec_b = ['0.3_um_count_b', '0.5_um_count_b', '1.0_um_count_b', '2.5_um_count_b', '5.0_um_count_b', '10.0_um_count_b', 
               'pm1.0_atm_b', 'pm10.0_atm_b']
    for i,f in enumerate(fields_list_sec_b):
        if (i == 0):
            fields_api_url_secb = f'&fields={f}'
        else:
            fields_api_url_secb += f'%2C{f}'

    # Primary data file fields (A)
    fields_list_pri_a = ['pm1.0_cf_1_a', 'pm2.5_cf_1_a', 'pm10.0_cf_1_a', 'uptime', 'rssi', 'temperature_a', 
               'humidity_a','pm2.5_atm_a']
    for i,f in enumerate(fields_list_pri_a):
        if (i == 0):
            fields_api_url_pria = f'&fields={f}'
        else:
            fields_api_url_pria += f'%2C{f}'

    # Primary data file fields (B)
    fields_list_pri_b = ['pm1.0_cf_1_b', 'pm2.5_cf_1_b', 'pm10.0_cf_1_b', 'uptime', 'analog_input', 'pressure', 
               'voc','pm2.5_atm_b']
    for i,f in enumerate(fields_list_pri_b):
        if (i == 0):
            fields_api_url_prib = f'&fields={f}'
        else:
            fields_api_url_prib += f'%2C{f}'

    # SD Data Fields
    fields_list_sd = ['firmware_version	', 'hardware', 'temperature_a', 'humidity_a', 'pressure_b', 'analog_input', 'memory', 'rssi', 'uptime', 'pm1.0_cf_1_a', 'pm2.5_cf_1_a', 'pm10.0_cf_1_a', 'pm1.0_atm_a', 'pm2.5_atm_a', 'pm10.0_atm_a',
                '0.3_um_count_a', '0.5_um_count_a','1.0_um_count_a','2.5_um_count_a','5.0_um_count_a','10.0_um_count_a','pm1.0_cf_1_b', 'pm2.5_cf_1_b', 'pm10.0_cf_1_b', 'pm1.0_atm_b', 'pm2.5_atm_b', 'pm10.0_atm_b',
                '0.3_um_count_b', '0.5_um_count_b','1.0_um_count_b','2.5_um_count_b','5.0_um_count_b','10.0_um_count_b']
    for i,f in enumerate(fields_list_sd):
        if (i == 0):
            fields_api_url_sd = f'&fields={f}'
        else:
            fields_api_url_sd += f'%2C{f}'          

    # Dates of Historical Data period
    begindate = datetime.strptime(bdate, '%m-%d-%Y')
    enddate   = datetime.strptime(edate, '%m-%d-%Y')
    #start time necessary in increments of 0, 10, 15, 60 increments longer than 2 weeks
    #end time can be split into any amount of week increments but preferbly in 2 week increments
    #program will divide 2 week increments for you
    # Download days based on average
    if (average_time == 60):
        date_list = pd.date_range(begindate,enddate,freq='14d') # for 14 days of data
    else:
        date_list = pd.date_range(begindate,enddate,freq='2d') # for 2 days of data
        
    # Converting to UNIX timestamp
    date_list_unix=[]
    for dt in date_list:
        date_list_unix.append(int(time.mktime(dt.timetuple())))

    # Reversing to get data from end date to start date
    date_list_unix.reverse()
    len_datelist = len(date_list_unix) - 1

    folderlist = list()
        
    # Gets Sensor Data
    for s in sensors_list:

        # Adding sensor_index & API Key
        hist_api_url = root_api_url + f'{s}/history/csv?api_key={key_read}'
        print(hist_api_url)

        # Special URL to grab sensor registration name
        name_api_url = root_api_url + f'{s}?fields=name&api_key={key_read}'

        #get sensor registration name:
        try:
            response = requests.get(name_api_url)
        except:
            print(name_api_url)

        try:
            assert response.status_code == requests.codes.ok
               
            namedf = pd.read_csv(StringIO(response.text), sep=",|:", header=None, skiprows=8, index_col=None, engine='python')

        except AssertionError:
            namedf = pd.DataFrame()
            print('Bad URL! Check dates and other inputs')

        #Response will be the registered name of the sensor            
        sensorname = str(namedf[1][0])
        sensorname = sensorname.strip()
        sensorname = sensorname.strip('\"')
        
        # Creating start and end date api url
        for i,d in enumerate(date_list_unix):
            # Wait time 
            time.sleep(sleep_seconds)
            
            if (i < len_datelist):
                print('Downloading for PA: %s for Dates: %s and %s.' 
                      %(s,datetime.fromtimestamp(date_list_unix[i+1]),datetime.fromtimestamp(d)))
                dates_api_url = f'&start_timestamp={date_list_unix[i+1]}&end_timestamp={d}'

                # Creates final URLs that download data in the format of previous PA downloads and SD card data
                api_url_a = hist_api_url + dates_api_url + average_api + fields_api_url_seca
                api_url_b = hist_api_url + dates_api_url + average_api + fields_api_url_secb
                api_url_c = hist_api_url + dates_api_url + average_api + fields_api_url_pria
                api_url_d = hist_api_url + dates_api_url + average_api + fields_api_url_prib
                api_url_e = hist_api_url + dates_api_url + average_api + fields_api_url_sd

                #creates list of all URLs
                URL_List = [api_url_a,api_url_b,api_url_c,api_url_d,api_url_e]

                for x in URL_List:
                    #queries URLs for data
                    try:
                        response = requests.get(x)
                    except:
                        print(x)
                    #
                    try:
                        assert response.status_code == requests.codes.ok
                
                        # Creating a Pandas DataFrame
                        df = pd.read_csv(StringIO(response.text), sep=",", header=0)
                
                    except AssertionError:
                        df = pd.DataFrame()
                        print('Bad URL!')
            
                    if df.empty:
                        print('------------- No Data Available -------------')
                    else:
                        # Adding Sensor Index/ID
                        df['id'] = s
                
                        #
                        date_time_utc=[]
                        for index, row in df.iterrows():
                            date_time_utc.append(datetime.utcfromtimestamp(row['time_stamp']))
                        df['date_time_utc'] = date_time_utc
                        # Duplicate rows may be created here, not sure why or how but just going to remove them
                        # May cause an issue when trying to match time stamp rows
                        # Dropping duplicate rows
                        df = df.drop_duplicates(subset=None, keep='first', inplace=False)
                        df = df.sort_values(by=['time_stamp'],ascending=True,ignore_index=True)
                    
                        # Writing to Postgres Table (Optional)
                        # df.to_sql('tablename', con=engine, if_exists='append', index=False)
                    
                        # writing to csv file
                        folderpath1 = folderpath
                        folderpathdir = folderpath1 + '\\' + bdate + '_to_' + edate
                        if not os.path.exists(folderpathdir):
                            os.makedirs(folderpathdir)

                        folderpath = folderpathdir + '\\' + sensorname
                        if not os.path.exists(folderpath):
                            os.makedirs(folderpath)
                            
                        if x in api_url_b:

                            evenmorespecificpath = folderpath + '\Secondary_B'
                            if not os.path.exists(evenmorespecificpath):
                                os.makedirs(evenmorespecificpath)
                            filename = evenmorespecificpath + '\%s_%s_%s_b.csv' % (sensorname,datetime.fromtimestamp(date_list_unix[i+1]).strftime('%m-%d-%Y'),datetime.fromtimestamp(d).strftime('%m-%d-%Y'))
                            df.to_csv(filename, index=False, header=True)

                            folderlist.append(evenmorespecificpath)

                        elif x in api_url_a:
                            
                            evenmorespecificpath = folderpath + '\Secondary_A'
                            if not os.path.exists(evenmorespecificpath):
                                os.makedirs(evenmorespecificpath)
                            filename = evenmorespecificpath + '\%s_%s_%s.csv' % (sensorname,datetime.fromtimestamp(date_list_unix[i+1]).strftime('%m-%d-%Y'),datetime.fromtimestamp(d).strftime('%m-%d-%Y'))
                            df.to_csv(filename, index=False, header=True)

                            folderlist.append(evenmorespecificpath)

                        elif x in api_url_c:
                            
                            evenmorespecificpath = folderpath + '\Primary_A'
                            if not os.path.exists(evenmorespecificpath):
                                os.makedirs(evenmorespecificpath)
                            filename = evenmorespecificpath + '\%s_%s_%s.csv' % (sensorname,datetime.fromtimestamp(date_list_unix[i+1]).strftime('%m-%d-%Y'),datetime.fromtimestamp(d).strftime('%m-%d-%Y'))
                            df.to_csv(filename, index=False, header=True)

                            folderlist.append(evenmorespecificpath)

                        elif x in api_url_d:

                            evenmorespecificpath = folderpath + '\Primary_B'
                            if not os.path.exists(evenmorespecificpath):
                                os.makedirs(evenmorespecificpath)
                            filename = evenmorespecificpath + '\%s_%s_%s_b.csv' % (sensorname,datetime.fromtimestamp(date_list_unix[i+1]).strftime('%m-%d-%Y'),datetime.fromtimestamp(d).strftime('%m-%d-%Y'))
                            df.to_csv(filename, index=False, header=True)

                            folderlist.append(evenmorespecificpath)

                        else:

                            evenmorespecificpath = folderpath + '\SD_Format'
                            if not os.path.exists(evenmorespecificpath):
                                os.makedirs(evenmorespecificpath)
                            filename = evenmorespecificpath + '\%s_%s_%s.csv' % (sensorname,datetime.fromtimestamp(date_list_unix[i+1]).strftime('%m-%d-%Y'),datetime.fromtimestamp(d).strftime('%m-%d-%Y'))
                            df.to_csv(filename, index=False, header=True)

                            folderlist.append(evenmorespecificpath)

    return folderlist


# File combiner

# In[113]:


#Combines all purple air files into single folder repository, doesnt work perfectly
def combine_files(folderlist):

    # Combines csv files in sensor folders into a combined file
    for s in folderlist:

        os.chdir(s)
        extension = 'csv'
        
        all_filenames = [i for i in glob.glob('*.csv')]

        combined_csv = pd.concat([pd.read_csv(f) for f in all_filenames ])
        combined_csv.to_csv( "combined_files.csv", index=False, encoding='utf-8-sig')

        if "Secondary_A" in s:

            x=Path(s)
            
            lessspecificDir = str(x.parent)
            y=Path(lessspecificDir)
           
            evenlessspecific = str(y.parent)
            z=Path(evenlessspecific)

            filename = str(y.name)+".csv"
            filepath = Path(filename)
            if filepath.is_file():
                os.remove(filepath)

            newname = evenlessspecific + "\WeeklyCheck"
            
            if not os.path.exists(newname):
                os.makedirs(newname)

            os.chdir(newname)

            combined_csv.to_csv(filename, index=False, encoding='utf-8-sig')
        

        elif "Secondary_B" in s:

            x=Path(s)

            lessspecificDir = str(x.parent)
            y=Path(lessspecificDir)
            
            evenlessspecific = str(y.parent)
            z=Path(evenlessspecific)

            filename = str(y.name) + " B.csv"
            filepath = Path(filename)
            if filepath.is_file():
                os.remove(filepath)            

            newname = evenlessspecific + "\WeeklyCheck"
            
            if not os.path.exists(newname):
                os.makedirs(newname)

            os.chdir(newname)

            combined_csv.to_csv(filename, index=False, encoding='utf-8-sig') 


# This portion above still needs debugging to ensure data completeness. Purple Air Download tool seems easier to use and just have a script to combine all of those files into one

# Date Row Operations Used to apply opperations to rows on dataframes

# In[114]:


def second_check(row):
    """Checks minute in hour"""
    if pd.isnull(row['Local_time']):
        return None 
    else: 
        return int(row['Local_time'].second)

def minute_check(row):
    """Checks minute in hour"""
    if pd.isnull(row['Local_time']):
        return None
    else: 
        return int(row['Local_time'].minute)
    
def hour_check(row):
    """Checks the Hour of the Day"""
    if pd.isnull(row['Local_time']):
        return None
    else: 
        return int(row['Local_time'].hour)

def day_check(row):
   """Checks the Day of the month"""
   if pd.isnull(row['Local_time']):
        return None
   else:
    return int(row['Local_time'].day)

def month_check(row):
    """Checks the month"""
    if pd.isnull(row['Local_time']):
        return None
    else:
        return int(row['Local_time'].month)

def year_check(row):
    """Checks the year"""
    if pd.isnull(row['Local_time']):
        return None
    else:
        return int(row['Local_time'].year)

def season_check(row):
    """Checks the season"""
    month = row['Local_time'].month
    day = row['Local_time'].day
    if pd.isnull(month) or pd.isnull(day):
        return "None1"
    elif month == 1 or month == 2 or month == 3:
        if month == 3 and day <= 15:
            return "Winter"
        elif month == 3 and day > 15:
            return "Spring"
        elif month == 1 and day <= 15:
            return "Late Autumn"
        elif month == 1 and day > 15:
            return "Winter"
        else:
            return "Winter"
    elif month == 4 or month == 5 or month == 6:
        if month == 6 and day <= 15:
            return "Spring"
        elif month == 6 and day > 15:
            return "Summer"
        else:
            return "Spring"
    elif month == 7 or month == 8 or month == 9:
        if month == 9 and day <= 15:
            return "Monsoon"
        elif month == 9 and day > 15:
            return "Autumn"
        else:
            return "Monsoon"
    elif month == 10 or month == 11 or month == 12:
        if month == 12:
            return "Late Autumn"
        else:
            return "Autumn"
    

def add_stat(row):
    return "Stationary"

def location_check(row):
    """Checks row in dataframe for sensor ID, sets location based on ID"""
    if row['Sensor_ID'] == "118489":
        return "Birendarnagar"
    elif row['Sensor_ID'] == "99035":
        return "Bharatpur-27"
    elif row['Sensor_ID'] == "170015":
        return "Bhimnagar"
    elif row['Sensor_ID'] == "99215":
        return "Fulbari"
    elif row['Sensor_ID'] == "169991":
        return "Krishnapur"
    elif row['Sensor_ID'] == "160173":
        return "Bharatpur-3"

def local_time_check(row):
    """Converts from UTC to Nepal Time"""
    temp = row['time_stamp']
    temp1 = temp[0:10]
    temp2 = temp1 + " " + temp[11:19]
    utc_time = datetime.strptime(temp2, '%Y-%m-%d %H:%M:%S')
    local_timezone = pytz.timezone('Asia/Kathmandu')
    local_datetime = local_timezone.localize(utc_time)
    return local_datetime + timedelta(minutes= 45, hours = 5)

def temp_check(row):
    if row['Date'] != "Errored Line":
        return (str(row['Date']) + " " + str(row['Time']))
    
def add_range(row):
    temp = row['temperature']
    if temp >= -4 and temp <= 32:
        return "-20C to 0C"
    elif temp > 32 and temp <= 50:
        return "0C to 10C"
    elif temp > 50 and temp <= 59:
        return "10C to 15C"
    elif temp > 59 and temp <= 68:
        return "15C to 20C"
    elif temp > 68 and temp <= 77:
        return "20C to 25C"
    elif temp > 77 and temp <= 86:
        return "25C to 30C"
    elif temp > 86 and temp <= 95:
        return '30C to 35C'
    elif temp > 95:
        return "Above 35C"
    else:
        return "Below 0C"
    
def check_humidity(row):
    humidity = row['humidity']
    if humidity >= 0 and humidity <= 10:
        return "0-10%"
    elif humidity > 10 and humidity <= 20:
        return "10-20%"
    elif humidity > 20 and humidity <= 30:
        return "20-30%"
    elif humidity > 30 and humidity <= 40:
        return "30-40%"
    elif humidity > 40 and humidity <= 50:
        return "40-50%"
    elif humidity > 50 and humidity <= 60:
        return "50-60%"
    elif humidity > 60 and humidity <= 70:
        return "60-70%"
    elif humidity > 70 and humidity <= 80:
        return "70-80%"
    elif humidity > 80 and humidity <= 90:
        return "80-90%"
    elif humidity > 90 and humidity <= 1000:
        return "90-100%"
    
def Convert_to_celsius(x):
    return (x-32) * (5/9)


# File Combination methods. Still need to fix micropem combiner to reduce compiling time. Need to fix column names in master combiner

# In[115]:


#For Purple Air
def combine_purple():
    """Combines Purple Air CSV files into a single dataframe, applies check processes to create flags.  Takes all files in specified directory with *CSV
    Return:
    df (dataframe) = data frame of purple air sensors"""
    counter = 0
    filepath = r"/Users/jonathanpallotto/Desktop/CSC Project/ssds2/"
    os.chdir(filepath)
    df = pd.DataFrame()
    for file in glob.glob(filepath + '/*.csv'):
        with open(file) as f:
            df_temp=pd.read_csv(f)
            filename2 = str(f).split()
            sensor_id_temp = filename2[2]
            sensor_id = sensor_id_temp[14:]
            df_temp.insert(1, "Sensor_ID", sensor_id)
            if counter == 0:
                df = df_temp
                counter += 1
            else:
               df = pd.concat([df,df_temp], ignore_index=True)
    #Apply row opperations       
    df["temperature"] = df["temperature"].apply(Convert_to_celsius) 
    df['Location'] = df.apply(lambda row: location_check(row), axis=1)
    df['Local_time'] = df.apply(lambda row: local_time_check(row), axis=1)
    df['Day'] = df.apply(lambda row: day_check(row), axis=1)
    df['Hour'] = df.apply(lambda row: hour_check(row), axis=1)
    df['Month'] = df.apply(lambda row: month_check(row), axis=1)
    df['Year'] = df.apply(lambda row: year_check(row), axis=1)
    df["Season"] = df.apply(lambda row: season_check(row), axis=1)
    arr1 = list(df['Local_time'].astype(str))
    arr1 = [w.replace('+05:45', '') for w in arr1]
    arr1 = pd.to_datetime(pd.Series(arr1), format='%Y-%m-%d %H:%M:%S')
    df['timestamp'] = arr1
    return df

def combine_stat_atmo():
    """Combines Atmotube files with  STAT_COLLOC file prefixes into single dataframe, applies check processes to create flags. Takes all files in specified directory with *CSV
     Return:
    df (dataframe) = data frame of Atmotube sensors"""
    counter = 0
    filepath = r"/Users/jonathanpallotto/Desktop/CSC Project/atmotube2/"
    os.chdir(filepath)
    df = pd.DataFrame()
    for file in glob.glob(filepath + '/*.csv'):
        with open(file) as f:
            temper =pd.read_csv(f)
            filename2 = str(f).split()
            sensor_num = filename2[3][22:25]
            temper.insert(1, "Sensor_Num", sensor_num)
            if counter == 0:
                df = temper
                counter += 1
            else:
               df = pd.concat([df,temper], ignore_index=True)
    df['Local_time'] = pd.to_datetime(df['Date'], format="%Y-%m-%d %H:%M:%S")
    df['Minute'] = df.apply(lambda row: minute_check(row), axis=1 )
    df['Day'] = df.apply(lambda row: day_check(row), axis=1)
    df['Hour'] = df.apply(lambda row: hour_check(row), axis=1)
    df['Month'] = df.apply(lambda row: month_check(row), axis=1)
    df['Year'] = df.apply(lambda row: year_check(row), axis=1)
    df['Season'] = df.apply(lambda row: season_check(row), axis=1)
    df['Location'] = df.apply(lambda row: add_stat(row), axis=1)
    return df

def combine_loc_atmo():
    """Combines Atmotube files with LOCATION NAME file prefixes into single dataframe, applies check processes to create flags. Takes all files in specified directory with *CSV
     Return:
    df (dataframe) = data frame of Atmotube sensors"""
    counter = 0
    filepath = r"/Users/jonathanpallotto/Desktop/CSC Project/atmotube/"
    os.chdir(filepath)
    df = pd.DataFrame()
    for file in glob.glob(filepath + '/*.csv'):
        with open(file) as f:
            temper = pd.read_csv(f)
            temploc = str(f).split()
            temploc2 = temploc[2].split("/")
            temploc3 = temploc2[2].split("_")
            location = temploc3[2]
            if location == "Parsadhap":
                location = "Bharatpur-27"
            elif location == "Bharatpur3":
                location = "Bharatpur-3"
            temper.insert(1, "Location", location)
            if counter == 0:
                df = temper
                counter += 1
            else:
               df = pd.concat([df,temper], ignore_index=True)
    df['Local_time'] = pd.to_datetime(df['Date'], format="%Y-%m-%d %H:%M:%S")
    df['Minute'] = df.apply(lambda row: minute_check(row), axis=1 )
    df['Day'] = df.apply(lambda row: day_check(row), axis=1)
    df['Hour'] = df.apply(lambda row: hour_check(row), axis=1)
    df['Month'] = df.apply(lambda row: month_check(row), axis=1)
    df['Year'] = df.apply(lambda row: year_check(row), axis=1)
    df['Season'] = df.apply(lambda row: season_check(row), axis=1)
    return df

def combine_loc_micro():
    counter = 0
    filepath = r"/Users/jonathanpallotto/Desktop/CSC Project/micropem/"
    os.chdir(filepath)
    df = pd.DataFrame()
    for file in glob.glob(filepath + '/*.csv'):
        with open(file) as f:
            #skip non data portions of micropem file
            temper = pd.read_csv(f, skiprows=23, low_memory=False, index_col=False)
            temper = temper.drop([0])
            temploc = str(f).split()
            temploc2 = temploc[2].split("/")
            temploc3 = temploc2[2].split("_")
            location = temploc3[2]
            device = temploc3[3]
            #only works for filter ids of 3 numbers
            filterw = temploc3[4][:3]
            if location == "Parsadhap":
                location = "Bharatpur-27"
            elif location == "Bharatpur3":
                location = "Bharatpur-3"
            temper.insert(1, "Location", location)
            temper.insert(2, "Device", device)
            temper.insert(3, "Filter_ID", filterw)
            if counter == 0:
                df = temper
                counter += 1
            else:
               df = pd.concat([df,temper], ignore_index=True)
    df["Ignore"] = df.apply(lambda row: temp_check(row), axis=1)
    df['Local_time'] = pd.to_datetime(df['Ignore'], format="%m/%d/%Y %H:%M:%S")
    df['Second'] = df.apply(lambda row: second_check(row), axis=1 )
    df['Minute'] = df.apply(lambda row: minute_check(row), axis=1 )
    df['Day'] = df.apply(lambda row: day_check(row), axis=1)
    df['Hour'] = df.apply(lambda row: hour_check(row), axis=1)
    df['Month'] = df.apply(lambda row: month_check(row), axis=1)
    df['Year'] = df.apply(lambda row: year_check(row), axis=1)
    df['Season'] = df.apply(lambda row: season_check(row), axis=1)
    
    return df

def combine_stat_micro():
    counter = 0
    filepath = r"/Users/jonathanpallotto/Desktop/CSC Project/micropem1/"
    os.chdir(filepath)
    df = pd.DataFrame()
    for file in glob.glob(filepath + '/*.csv'):
        with open(file) as f:
            #skip non data portions of micropem file
            temper = pd.read_csv(f, skiprows=23, low_memory=False, index_col=False)
            temper = temper.drop([0])
            temploc = str(f).split()
            temploc2 = temploc[3].split("_")
            device = temploc2[3]
            #only works for filter ids of 3 numbers
            filterw = temploc2[4][:3]
            temper.insert(2, "Device", device)
            temper.insert(3, "Filter_ID", filterw)
            if counter == 0:
                df = temper
                counter += 1
            else:
               df = pd.concat([df,temper], ignore_index=True)
    df["Ignore"] = df.apply(lambda row: temp_check(row), axis=1)
    df['Local_time'] = pd.to_datetime(df['Ignore'], format="%m/%d/%Y %H:%M:%S")
    df['Second'] = df.apply(lambda row: second_check(row), axis=1 )
    df['Minute'] = df.apply(lambda row: minute_check(row), axis=1 )
    df['Day'] = df.apply(lambda row: day_check(row), axis=1)
    df['Hour'] = df.apply(lambda row: hour_check(row), axis=1)
    df['Month'] = df.apply(lambda row: month_check(row), axis=1)
    df['Year'] = df.apply(lambda row: year_check(row), axis=1)
    df['Season'] = df.apply(lambda row: season_check(row), axis=1)
    df['Location'] = df.apply(lambda row: add_stat(row), axis=1)
    
    return df

def master_creator():
    df1 = combine_purple()
    df2 = combine_loc_atmo
    df3 = combine_stat_atmo
    df4 = combine_loc_micro
    df5 = combine_stat_micro
    df = pd.concat([df1,df2,df3,df4,df5], ignore_index=True)
    return df
#Drop seconds and group by minutes to create averages
#make sure to preserve original dataframe at some point


# Filter dictionary, can swtich to different representation but not sure how it will be added in in the future

# In[116]:


#filter pm2.5 in micrograms per m3
dict_filter = dict()
dict_filter['filter_ID'] = ['101', '104', '106', '107', '109', '110' , '111', '112']
dict_filter['pm2_5'] = [4, 133, 65, 100, 125, 128 , 37, 92]


# In[117]:


df_filter = pd.DataFrame(dict_filter)


# Graph Portion of the Code, Will mark graphs used for poster. Should update all graph functions with subplots to graph in loops rather than in string. Need to adjust
# to master data files once finished

# In[126]:


#Graphing functions will all be combined into their respective plot types and will be changed. Wont be seperate for each sensor!!!
def plot_montly_season():
    """Grapher for Purple Air Seasons and Months""" #USED for poster 
    df = combine_purple()
    fig, axes = plt.subplots(figsize=(12,6))
    sns.set_style(style='whitegrid')
    fig.suptitle("Seasonal and Monthly PM2.5 Trends based on Location",fontsize=30) 
    season = sns.boxplot(ax=axes, data=df, x="Season", y="pm2.5_atm", hue='Location', palette="bright", fliersize=1)
    season.set_ylim(0,400)
    #season.set(title="Seasonal PM2.5 Trends by Location", ylabel="PM2.5 (ug/m^3)")
    season.set(ylabel="PM2.5 (ug/m^3)")
    #month = sns.boxplot(ax=axes[1], data=df, x="Month", y="pm2.5_atm", hue='Location', palette="bright", fliersize=1)
    #month.set_ylim(0,600)
    #month.set(title="Monthly PM2.5 Trends by Location", ylabel="PM2.5 (ug/m^3)")
    plt.rcParams.update({'font.size': 14,'text.color': "#050203",'axes.labelcolor': "#050203"})
    plt.legend(fontsize=12)
    plt.show()

def plot_diurnal():
    """Not Used, previous representation"""
    df = combine_purple()
    d1 = df.groupby('Hour', as_index=False)['temperature'].mean()
    d1['range'] = d1.apply(lambda row: add_range(row), axis=1)
    df = df.merge(d1, on=['Hour'], how='left')
    ax1 = sns.set_style(style=None, rc=None )
    fig, ax1 = plt.subplots(figsize=(12,6))
    diurnal = sns.boxplot(data=df, x='Hour', y='pm2.5_atm', fliersize=1, hue='range', ax= ax1)
    diurnal.set(title='Diurnal PM2.5 Trends of Chitwan Valley', ylabel="PM2.5 (ug/m^3)")
    diurnal.set_ylim(0,400)
    plt.axhline(y=df['pm2.5_atm'].mean(), xmin = 0, xmax = 1,linestyle='dashed')
    handles, _ = ax1.get_legend_handles_labels()
    handles.append(ax1.axhline(y=df['pm2.5_atm'].mean(), xmin = 0, xmax = 1,linestyle='dashed'))
    labels = ["20-25C", "25-30C", "30-35C", "Above 35C", "Average PM2.5"]
    # Slice list to remove first handle
    plt.legend(handles = handles, labels = labels, bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0, title="Humidity",fontsize=12,title_fontsize=14)
    #plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0)
    plt.show()
    #return d1, df


def plot_diurnal2():
    """Not Used, Previous Representation"""
    df = combine_purple()
    df['humidity_range'] = df.apply(lambda row: check_humidity(row), axis=1)
    ax1 = sns.set_style(style=None, rc=None )
    fig, ax1 = plt.subplots(figsize=(12,6))
    diurnal = sns.boxplot(data=df, x='Hour', y='pm2.5_atm', fliersize=1, hue='humidity_range', ax= ax1)
    diurnal.set(title='Diurnal PM2.5 Trends of Chitwan Valley', ylabel="PM2.5 (ug/m^3)")
    diurnal.set_ylim(0,400)
    #av_line = sns.lineplot(data=df, x="Hour", y=df['pm2.5_atm'].mean(), ax=ax1)
    plt.axhline(y=df['pm2.5_atm'].mean(), xmin = 0, xmax = 1,linestyle='dashed')
    handles, _ = ax1.get_legend_handles_labels()
    #La = plt.legend(title= "Sensor Number", fontsize=12,title_fontsize=14)
    handles.append(ax1.axhline(y=df['pm2.5_atm'].mean(), xmin = 0, xmax = 1,linestyle='dashed'))
    labels = ["0-10%", "20-30%", "30-40%", "40-50%", "50-60%", "60-70%", "70-80%", "80-90%", "90-100%", "Average PM2.5"]
    # Slice list to remove first handle
    plt.legend(handles = handles, labels = labels, bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0, title="Humidity",fontsize=12,title_fontsize=14)
    #plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0)
    plt.show()
    #return d1, df

def plot_diurnal3():
    """Not used, previous representation"""
    df = combine_purple()
    d1 = df.groupby('Hour', as_index=False)['humidity'].mean()
    d1['humidity_range'] = df.apply(lambda row: check_humidity(row), axis=1)
    df = df.merge(d1, on=['Hour'], how='left')
    ax1 = sns.set_style(style=None, rc=None )
    fig, ax1 = plt.subplots(figsize=(12,6))
    diurnal = sns.boxplot(data=df, x='Hour', y='pm2.5_atm', fliersize=1, hue='humidity_range', ax= ax1)
    diurnal.set(title='Diurnal PM2.5 Trends of Chitwan Valley', ylabel="PM2.5 (ug/m^3)")
    diurnal.set_ylim(0,400)
    #av_line = sns.lineplot(data=df, x="Hour", y=df['pm2.5_atm'].mean(), ax=ax1)
    plt.axhline(y=df['pm2.5_atm'].mean(), xmin = 0, xmax = 1,linestyle='dashed')
    handles, _ = ax1.get_legend_handles_labels()
    handles.append(ax1.axhline(y=df['pm2.5_atm'].mean(), xmin = 0, xmax = 1,linestyle='dashed'))
    labels = ["0-10%", "20-30%", "30-40%", "40-50%", "Average PM2.5"]
    # Slice list to remove first handle
    plt.legend(handles = handles, labels = labels, bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0, title="Humidity",fontsize=12,title_fontsize=14)
    #plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0)
    plt.show()
    #return d1, df


def plot_diurnal_loc():
    """Not Used, previous represntation"""
    df = combine_purple()
    ax1 = sns.set_style(style=None, rc=None )
    fig, ax1 = plt.subplots(figsize=(25,15))
    diurnal = sns.lineplot(data=df, x='Hour', y='pm2.5_atm', hue = "Location", ax=ax1, errorbar='se')
    plt.title=('Diurnal PM2.5 Trends by Site')
    plt.ylabel("PM2.5 (ug/m^3)")
    plt.ylim(0,400)
    #plt.axhline(y=df['pm2.5_atm'].mean(), xmin = 0, xmax = 1,linestyle='dashed')
    av_line = sns.lineplot(data = df, x = 'Hour', y=df['pm2.5_atm'], ax=ax1,linestyle='dashed', label = 'Average PM2.5') 
    #handles, _ = ax1.get_legend_handles_labels()
    #handles.append(ax1.axhline(y=df['pm2.5_atm'].mean(), xmin = 0, xmax = 1,linestyle='dashed'))
    #handles.append(av_line)
    #labels = ["Krishnapur", "Birendarnagar", "Bharatpur-3", "Bhimnagar", "Bharatpur-27", "Fulbari", 'Average PM2.5']
    #plt.legend(handles = handles, labels = labels, bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0, title="Location",fontsize=20,title_fontsize=25)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0, title="Location",fontsize=20,title_fontsize=25)
    plt.show()

def plot_micro_neph():
    "Not Used"
    """Grapher for micropem neph vs filter"""
    listA = ['Nephelometer Mean', 'pm2_5']
    d2 = combine_loc_micro()
    d1 = combine_stat_micro()
    ax1 = sns.set_style(style=None, rc=None)
    df = pd.concat([d2,d1], ignore_index=True)
    df = df.merge(df_filter, left_on='Filter_ID', right_on='filter_ID', how='left')
    df['RH-Corrected Nephelometer'] = df['RH-Corrected Nephelometer'].astype('float64')
    df['pm2_5'] = df['pm2_5'].astype('float64')
    d3 = df.groupby('Filter_ID', as_index=False)['RH-Corrected Nephelometer'].mean()
    d3 = d3.rename(columns={"RH-Corrected Nephelometer": "Nephelometer Mean"})
    d3['Nephelometer Mean'] = d3['Nephelometer Mean'].astype('object')
    df = df.merge(d3, on = 'Filter_ID', how='left')
    #df["Nepholometer Mean", 'pm2_5'].plot.bar(x="Filter_ID")
    dfs = df[['Filter_ID','Nephelometer Mean', 'pm2_5']].copy()
    tidy = dfs.melt(id_vars='Filter_ID').rename(columns=str.title)
    fig, ax1 = plt.subplots(figsize=(25,15))
    fig.suptitle("Nephelometer Vs Filter Readings")
    sns.barplot(x='Filter_Id', y='Value', hue='Variable', data=tidy, ax=ax1)
    #df.plot.bar(ax=ax1, x='Filter_ID', y=["Nephelometer Mean", 'pm2_5'])
    #sns.barplot(ax=ax1, data=df, x="filter_ID", y='pm2_5', palette="bright")
    #sns.violinplot(ax=ax1, data=df, x="Day", y=df[criteria], hue='Sensor_Num', saturation=0.75, palette="pastel")
    #sns.violinplot(ax=ax1, data=df, x="Hour", y=df[criteria], hue="Sensor_Num", saturation=0.75, palette="pastel")
    La = plt.legend(title= "Sensor Type", fontsize=12,title_fontsize=14)
    La.get_texts()[0].set_text('Nephelometer')
    La.get_texts()[1].set_text('Filter Measurement')
    ax1.set_ylabel("PM2.5 (ug/m^3)")
    ax1.set_xlabel("Filter ID")
    for p in ax1.patches: 
        ax1.annotate(np.round(p.get_height(),decimals=2), (p.get_x()+p.get_width()/2., p.get_height()))
    plt.show()

def plot_filter_atmo():
    """Previous representation, not used"""
    d1 = combine_loc_micro()
    d2 = combine_loc_atmo()
    d1['RH-Corrected Nephelometer'] = d1['RH-Corrected Nephelometer'].astype('float64')
    datmo = d2.groupby('Location', as_index=False)['PM2.5, ug/m3'].mean()
    dmicro = d1.groupby('Location', as_index=False)['RH-Corrected Nephelometer'].mean()
    df3 = datmo.merge(dmicro, how='outer')
    df3["Filter Weight"] = [65, 133, 100, 92, 37,4]
    dfinal = df3.melt(id_vars='Location').rename(columns=str.title)
    fig, ax1 = plt.subplots(figsize=(25,15))
    fig.suptitle("PM2.5 measurements of Atmotube vs Nepelometer vs Gravemetric Filter")
    sns.barplot(x='Location', y='Value', hue='Variable', data=dfinal, ax=ax1)
    La = plt.legend(title= "Measurement type", fontsize=12,title_fontsize=14)
    La.get_texts()[0].set_text('Atmotube')
    La.get_texts()[1].set_text('Nephelometer')
    La.get_texts()[2].set_text('Filter')
    ax1.set_ylabel("PM2.5 (ug/m^3)")
    ax1.set_xlabel("Location")
    for p in ax1.patches: 
        ax1.annotate(np.round(p.get_height(),decimals=2), (p.get_x()+p.get_width()/2., p.get_height()))
    plt.show()

def plot_filter_atmo2():
    """Comparison of 17 atmotubes vs 2 micropem filters and atmotube mean, used for poster"""
    #d1 = pd.DataFrame({'Filter': [109,110], "PM2_5": [125,128]})
    d2 = combine_stat_atmo()
    res = d2[(d2['Local_time'] > pd.to_datetime('2023-03-04 15:00:00'))]
    fig, ax1 = plt.subplots(figsize=(25,15))
    fig.suptitle("PM2.5 Analysis during Preliminary Colocation in March 2023 of 17 Atmotubes Compared to 2 Gravemetric Filters", fontsize=30, x = 0.59)
    #sns.lineplot(data = d1, x=d2['Local_time'], y="PM2_5", hue= 'Filter')
    plt.axhline(y = 125, xmin = 0, xmax = 1, color = 'red',linestyle='dashed')
    plt.axhline(y = 128, xmin = 0, xmax = 1, color = 'green',linestyle='dashed')
    plt.axhline(y = d2["PM2.5, ug/m3"].mean(), xmin = 0, xmax = 1, color = 'black',linestyle='dashed')
    sns.lineplot(x='Local_time', y="PM2.5, ug/m3", hue = "Sensor_Num", data=res, ax=ax1, palette='Spectral')
    sns.lineplot(data = res, x = 'Local_time', y="PM2.5, ug/m3", ax=ax1, label = 'Average PM2.5', linestyle='dashed', errorbar=None, color = 'black')
    handles, _ = ax1.get_legend_handles_labels()
    handles.append(ax1.axhline(y = res["PM2.5, ug/m3"].mean(), xmin = 0, xmax = 1, color = 'blue',linestyle='dashed'))
    handles.append(ax1.axhline(y = 128, xmin = 0, xmax = 1, color = 'green',linestyle='dashed'))
    handles.append(ax1.axhline(y = 125, xmin = 0, xmax = 1, color = 'red',linestyle='dashed'))
    labels = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "13", "14", "15","16","17",'Mean PM2.5', "Atmotube Average", "Filter 1", "Filter 2"]
    # Slice list to remove first handle
    plt.legend(handles = handles, labels = labels, bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0, title="Device Number", title_fontsize=40, fontsize=30)
    ax1.set_ylabel("PM2.5 (ug/m^3)", fontsize=40)
    ax1.set_xlabel("Local Nepal Time", fontsize=40)
    ax1.tick_params(axis='x', labelsize=25)
    ax1.tick_params(axis='y', labelsize=25)
    ax1.set_xlim(left=pd.to_datetime('2023-03-04 22:00:00'),right=pd.to_datetime('2023-03-06 09:00:00') )
    plt.rcParams.update({'font.size': 14,'text.color': "#050203",'axes.labelcolor': "#050203"})
    plt.ylim(0,350)
    plt.show()


# In[141]:


def plot_diurnal_loc2():
    """Diurnal PM2.5 trends based on location, will put into a for loop so its not so long"""
    df = combine_purple()
    d1 = df.loc[df['Location'] == 'Krishnapur']
    d2 = df.loc[df['Location'] == 'Birendarnagar']
    d3 = df.loc[df['Location'] == 'Bharatpur-3']
    d4 = df.loc[df['Location'] == 'Bhimnagar']
    d5 = df.loc[df['Location'] == 'Bharatpur-27']
    d6 = df.loc[df['Location'] == 'Fulbari']
    ax1 = sns.set_style(style=None, rc=None )
    fig, ax1 = plt.subplots(2,3,figsize=(20,10))
    sns.lineplot(data=d1, x='Hour', y='pm2.5_atm', ax=ax1[0,0], estimator=np.median, 
                  errorbar=lambda x: (np.quantile(x, 0.25), np.quantile(x, 0.75)), label = 'Median PM2.5')
    sns.lineplot(data = d1, x = 'Hour', y='pm2.5_atm', ax=ax1[0,0],linestyle='dashed', label = 'Mean PM2.5', errorbar=None)
    sns.lineplot(data=d2, x='Hour', y='pm2.5_atm', ax=ax1[0,1], estimator=np.median, 
                  errorbar=lambda x: (np.quantile(x, 0.25), np.quantile(x, 0.75)), label = 'Median PM2.5')
    sns.lineplot(data = d2, x = 'Hour', y='pm2.5_atm', ax=ax1[0,1],linestyle='dashed', label = 'Mean PM2.5',errorbar=None)
    sns.lineplot(data=d3, x='Hour', y='pm2.5_atm', ax=ax1[0,2], estimator=np.median, 
                  errorbar=lambda x: (np.quantile(x, 0.25), np.quantile(x, 0.75)), label = 'Median PM2.5')
    sns.lineplot(data = d3, x = 'Hour', y='pm2.5_atm', ax=ax1[0,2],linestyle='dashed', label = 'Mean PM2.5',errorbar=None)
    sns.lineplot(data=d4, x='Hour', y='pm2.5_atm', ax=ax1[1,0], estimator=np.median, 
                  errorbar=lambda x: (np.quantile(x, 0.25), np.quantile(x, 0.75)), label = 'Median PM2.5')
    sns.lineplot(data = d4, x = 'Hour', y='pm2.5_atm', ax=ax1[1,0],linestyle='dashed', label = 'Mean PM2.5',errorbar=None)
    sns.lineplot(data=d5, x='Hour', y='pm2.5_atm', ax=ax1[1,1], estimator=np.median, 
                  errorbar=lambda x: (np.quantile(x, 0.25), np.quantile(x, 0.75)), label = 'Median PM2.5')
    sns.lineplot(data = d5, x = 'Hour', y='pm2.5_atm', ax=ax1[1,1],linestyle='dashed', label = 'Mean PM2.5',errorbar=None)
    sns.lineplot(data=d6, x='Hour', y='pm2.5_atm', ax=ax1[1,2], estimator=np.median, 
                  errorbar=lambda x: (np.quantile(x, 0.25), np.quantile(x, 0.75)), label = 'Median PM2.5')
    sns.lineplot(data = d6, x = 'Hour', y='pm2.5_atm', ax=ax1[1,2],linestyle='dashed', label = 'Mean PM2.5',errorbar=None)
    #plt.title=('Diurnal PM2.5 Trends by Site')
    #plt.ylabel("PM2.5 (ug/m^3)")
    #plt.ylim(0,400)
    #plt.axhline(y=df['pm2.5_atm'].mean(), xmin = 0, xmax = 1,linestyle='dashed')
    #av_line = sns.lineplot(data = df, x = 'Hour', y=df['pm2.5_atm'], ax=ax1,linestyle='dashed', label = 'Average PM2.5') 
    #handles, _ = ax1.get_legend_handles_labels()
    #handles.append(ax1.axhline(y=df['pm2.5_atm'].mean(), xmin = 0, xmax = 1,linestyle='dashed'))
    #handles.append(av_line)
    #labels = ["Krishnapur", "Birendarnagar", "Bharatpur-3", "Bhimnagar", "Bharatpur-27", "Fulbari", 'Average PM2.5']
    #plt.legend(handles = handles, labels = labels, bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0, title="Location",fontsize=20,title_fontsize=25)
    #plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0, title="Location",fontsize=20,title_fontsize=25)
    ax1[0, 0].set_title("Krishnapur", fontsize=35)
    ax1[0,0].set_ylabel("PM2.5 (ug/m^3)", fontsize=18)
    ax1[0,0].set_xlabel("Hour of Day", fontsize=18)
    ax1[0, 1].set_title("Birendarnagar", fontsize=35)
    ax1[0,1].set_ylabel("PM2.5 (ug/m^3)", fontsize=18)
    ax1[0,1].set_xlabel("Hour of Day", fontsize=18)
    ax1[0, 2].set_title("Bharatpur-3",  fontsize=35)
    ax1[0,2].set_ylabel("PM2.5 (ug/m^3)", fontsize=18)
    ax1[0,2].set_xlabel("Hour of Day", fontsize=18)
    ax1[1, 0].set_title("Bhimnagar",  fontsize=35)
    ax1[1,0].set_ylabel("PM2.5 (ug/m^3)", fontsize=18)
    ax1[1,0].set_xlabel("Hour of Day", fontsize=18)
    ax1[1, 1].set_title("Bharatpur-27",  fontsize=35)
    ax1[1,1].set_ylabel("PM2.5 (ug/m^3)", fontsize=18)
    ax1[1,1].set_xlabel("Hour of Day", fontsize=18)
    ax1[1, 2].set_title("Fulbari",  fontsize=35)
    ax1[1,2].set_ylabel("PM2.5 (ug/m^3)", fontsize=18)
    ax1[1,2].set_xlabel("Hour of Day", fontsize=18)
    xlim = (0,23)
    ylim = (0,200)
    plt.rcParams.update({'font.size': 12,'text.color': "#050203",'axes.labelcolor': "#050203"})
    plt.setp(ax1, xlim=xlim, ylim=ylim) #ylabel="PM2.5 (ug/m^3)", xlabel = "Hour of Day")
    fig.suptitle("Diurnal Trends of PM2.5 Based on Location with Interquartile Range", fontsize=30, x = 0.5)
    fig.subplots_adjust(hspace=0.4, wspace=0.4)
    plt.show()

def plot_temp_hum():
    """Diurnal temperature and humidity trends based on locations, used on poster"""
    df = combine_purple()
    fig, axes = plt.subplots(2,3, figsize=(20,10))
    sns.set_style("white")
    for i,ax in enumerate(axes.flat, start=1):
        if i == 1:
            temp = "Krishnapur"
        elif i == 2:
            temp = 'Birendarnagar'
        elif i == 3:
            temp = 'Bharatpur-3'
        elif i == 4:
            temp = 'Bhimnagar'
        elif i == 5:
            temp = 'Bharatpur-27'
        elif i == 6:
            temp = 'Fulbari'
        dfs = df[df['Location'] == temp]
        ax2 = ax.twinx()
        sns.lineplot(data=dfs, x='Hour', y='temperature', ax=ax, estimator=np.median, 
                  errorbar=lambda x: (np.quantile(x, 0.25), np.quantile(x, 0.75)), label = 'Med Temp', color="red")
        sns.lineplot(data=dfs, x='Hour', y='humidity', ax=ax2, estimator=np.median,
                  errorbar=lambda x: (np.quantile(x, 0.25), np.quantile(x, 0.75)), label = 'Med Hum', color='blue')
        ax.set_title(temp, size = 35)
        ax.legend(labels = ['Median Temperature'], loc = "upper left")
        ax2.legend(labels = ['Median Humidity'], loc = "upper right")
        ax.set_xlabel('Hour of Day', fontsize = 20)
        ax.set_ylabel( 'Temperature (C)', fontsize = 20)
        ax2.set_ylabel('Humidity (%)', fontsize = 20)
        plt.setp(ax, xlim=(0,23), ylim=(15,45))
        plt.setp(ax2, xlim=(0,23), ylim=(0,100))
    plt.rcParams.update({'font.size': 18,'text.color': "#050203",'axes.labelcolor': "#050203"})
    fig.suptitle("Diurnal Trends of Temperature and Humidity Based on Location with Interquartile Range", fontsize=30, x = 0.5)
    fig.subplots_adjust(hspace=0.4, wspace=0.4)
    plt.show()

def plot_micro_atmo_filter():
    """Plot of stationary collocation with atmotube, micropems, and purple air based on locations""" #Used for poster
    d1 = combine_loc_micro()
    d2 = combine_loc_atmo()
    d3 = combine_purple()
    d1 = d1.dropna(how="all")
    d2 = d2.dropna(how="all")
    d1['RH-Corrected Nephelometer'] = pd.to_numeric(d1['RH-Corrected Nephelometer'])
    d2["PM2.5, ug/m3"] = pd.to_numeric(d2["PM2.5, ug/m3"])
    d3['pm2.5_atm'] = pd.to_numeric(d3['pm2.5_atm'])
    #d1 = d1[(d1['Local_time'] > pd.to_datetime('2023-03-07 11:00:00'))]
    #d1 = d1[(d1['Local_time'] < pd.to_datetime('2023-03-08 17:00:00'))]
    #d2 = d2[(d2['Local_time'] > pd.to_datetime('2023-03-07 11:00:00'))]
    #d2 = d2[(d2['Local_time'] < pd.to_datetime('2023-03-08 17:00:00'))]
    #df = d1.merge(d2, how='outer')
    Filter_Weight_dict = {"Bharatpur-3":65, 'Bhimnagar':133, 'Birendarnagar':100, "Fulbari":92, "Bharatpur-27":37, "Krishnapur":4}
    fig, axes = plt.subplots(2,3, figsize=(20,10))
    sns.set_style("white")
    for i,ax in enumerate(axes.flat, start=1):
        if i == 1:
            temp = "Krishnapur"
            dtemp = d1[(d1['Local_time'] > pd.to_datetime('2023-03-02 00:00:00'))]
            dtemp = dtemp[(dtemp['Local_time'] < pd.to_datetime('2023-03-04 17:00:00'))]
            dtemp1 = d2[(d2['Local_time'] > pd.to_datetime('2023-03-02 00:00:00'))]
            dtemp1 = dtemp1[(dtemp1['Local_time'] < pd.to_datetime('2023-03-04 17:00:00'))]
            dtemp2 = d3[(d3['timestamp'] > pd.to_datetime('2023-03-02 00:00:00'))]
            dtemp2 = dtemp2[(dtemp2['timestamp'] < pd.to_datetime('2023-03-04 17:00:00'))]
        elif i == 2:
            temp = 'Birendarnagar'
            dtemp = d1[(d1['Local_time'] > pd.to_datetime('2023-03-03 10:00:00'))]
            dtemp = dtemp[(dtemp['Local_time'] < pd.to_datetime('2023-03-04 17:00:00'))]
            dtemp1 = d2[(d2['Local_time'] > pd.to_datetime('2023-03-03 10:00:00'))]
            dtemp1 = dtemp1[(dtemp1['Local_time'] < pd.to_datetime('2023-03-04 17:00:00'))]
            dtemp2 = d3[(d3['timestamp'] > pd.to_datetime('2023-03-03 10:00:00'))]
            dtemp2 = dtemp2[(dtemp2['timestamp'] < pd.to_datetime('2023-03-04 17:00:00'))]
        elif i == 3:
            temp = 'Bharatpur-3'
            dtemp = d1[(d1['Local_time'] > pd.to_datetime('2023-03-03 18:00:00'))]
            dtemp = dtemp[(dtemp['Local_time'] < pd.to_datetime('2023-03-04 03:10:00'))]
            dtemp1 = d2[(d2['Local_time'] > pd.to_datetime('2023-03-03 18:00:00'))]
            dtemp1 = dtemp1[(dtemp1['Local_time'] < pd.to_datetime('2023-03-04 03:10:00'))]
            dtemp2 = d3[(d3['timestamp'] > pd.to_datetime('2023-03-03 18:00:00'))]
            dtemp2 = dtemp2[(dtemp2['timestamp'] < pd.to_datetime('2023-03-04 03:10:00'))]
        elif i == 4:
            temp = 'Bhimnagar'
            dtemp = d1[(d1['Local_time'] > pd.to_datetime('2023-03-03 10:00:00'))]
            dtemp = dtemp[(dtemp['Local_time'] < pd.to_datetime('2023-03-04 17:00:00'))]
            dtemp1 = d2[(d2['Local_time'] > pd.to_datetime('2023-03-03 10:00:00'))]
            dtemp1 = dtemp1[(dtemp1['Local_time'] < pd.to_datetime('2023-03-04 17:00:00'))]
            dtemp2 = d3[(d3['timestamp'] > pd.to_datetime('2023-03-03 10:00:00'))]
            dtemp2 = dtemp2[(dtemp2['timestamp'] < pd.to_datetime('2023-03-04 17:00:00'))]
        elif i == 5:
            temp = 'Bharatpur-27'
            dtemp = d1[(d1['Local_time'] > pd.to_datetime('2023-03-06 13:00:00'))]
            dtemp = dtemp[(dtemp['Local_time'] < pd.to_datetime('2023-03-08 13:00:00'))]
            dtemp1 = d2[(d2['Local_time'] > pd.to_datetime('2023-03-06 13:00:00'))]
            dtemp1 = dtemp1[(dtemp1['Local_time'] < pd.to_datetime('2023-03-08 13:00:00'))]
            dtemp2 = d3[(d3['timestamp'] > pd.to_datetime('2023-03-06 13:00:00'))]
            dtemp2 = dtemp2[(dtemp2['timestamp'] < pd.to_datetime('2023-03-08 13:00:00'))]
        elif i == 6:
            temp = 'Fulbari'
            dtemp = d1[(d1['Local_time'] > pd.to_datetime('2023-03-07 11:00:00'))]
            dtemp = dtemp[(dtemp['Local_time'] < pd.to_datetime('2023-03-08 06:00:00'))]
            dtemp1 = d2[(d2['Local_time'] > pd.to_datetime('2023-03-07 11:00:00'))]
            dtemp1 = dtemp1[(dtemp1['Local_time'] < pd.to_datetime('2023-03-08 06:00:00'))]
            dtemp2 = d3[(d3['timestamp'] > pd.to_datetime('2023-03-07 11:00:00'))]
            dtemp2 = dtemp2[(dtemp2['timestamp'] < pd.to_datetime('2023-03-08 06:00:00'))]
        df1 = dtemp[dtemp['Location'] == temp]
        df2 = dtemp1[dtemp1['Location'] == temp]
        df3 = dtemp2[dtemp2['Location'] == temp]
        sns.scatterplot(data=df1, x='Local_time', y='RH-Corrected Nephelometer', ax=ax, label = 'MicroPEM Nepholometer', color="red", alpha = 0.3)
        sns.scatterplot(data=df2, x='Local_time', y='PM2.5, ug/m3', ax=ax, label = 'Atmotube', color='blue', alpha = 0.3)
        sns.lineplot(data =df3, x="timestamp", y='pm2.5_atm', linestyle='dashed', label="Purple Air", ax = ax, color='black')
        ax.axhline(y=Filter_Weight_dict[temp], xmin=0, xmax=1, color='green', label="Filter Weight", alpha = 1)
        ax.set_title(temp, size = 20)
        #ax.legend(labels = [''], loc = "upper left")
        ax.set_xlabel('Local Nepal Time', fontsize = 20)
        ax.set_ylabel( 'PM2.5 (ug/m^3)', fontsize = 20)
        ax.set_xlim(dtemp['Local_time'].iloc[0], dtemp['Local_time'].iloc[-1])
        plt.setp(ax, ylim=(0,350))
        ax.xaxis.set_major_locator(plt.MaxNLocator(4))
        ax.yaxis.set_major_locator(plt.MaxNLocator(6))
        ax.tick_params(axis = 'x', which = 'major', direction = 'in', labelbottom=True, labelsize=15, rotation = 35)
        legend = ax.legend(loc='upper right', fontsize='xx-small')
    fig.suptitle("Precision Analysis for Site Co-locations of Atmotube vs Purple Air vs MicroPEM", fontsize=30, x = 0.5)
    fig.subplots_adjust(hspace=0.6, wspace= 0.2)
    plt.show()
    #return d1, d2


# Percent deviation for atmotubes

# In[ ]:


#Percent deviation calculator
def percent_dev():
    total = 0
    counter = 0
    df = combine_stat_atmo()
    mean = df["PM2.5, ug/m3"].mean(skipna=True)
    print(mean)
    #df["PM2.5, ug/m3"].fillna((df["PM2.5, ug/m3"].mean()), inplace=False)
    sensor_mean_df = df.groupby("Sensor_Num")["PM2.5, ug/m3"].mean()
    for i in sensor_mean_df:
        dev = (abs(i) - abs(mean)) / (abs(mean)*100)
        counter += 1
        total += abs(dev)
        dev = 0
    print(total)
    print(counter)
    print('Percent Dev: ' + str((total/counter)*100))
    


# Main

# In[142]:


import requests
import pandas as pd
from datetime import datetime
from datetime import timedelta
import time
import json
import os
from os.path import join, getsize
from pathlib import Path
import glob
from io import StringIO
import matplotlib.pyplot as plt
import seaborn as sns
import earthpy as et
import pytz

#sensors_list = get_sensorslist(groupid,key_read)
#folderlist = get_historicaldata(sensors_list,bdate,edate,average_time,key_read)
#combine_files(folderlist)
#df = csv_combiner()
#plot_grapher("temperature")
#plot_grapher("pm2.5_atm")
#df = csv_combiner2()
#print(df["Day"])
#ploter_grapher("Temperature, °C")
#ploter_grapher("PM2.5, ug/m3")
#display(df)
#@percent_dev()
#pd.set_option('display.max_rows', None)
#a = combine_purple()
#print(a.value_counts("Month"))
#print(a.value_counts("Season"))

#plot_montly_season()
#plot_diurnal()
#plot_diurnal2()
#plot_diurnal3()
#plot_diurnal_loc3()
#plot_diurnal_loc2()
#plot_temp_hum()
#plot_montly_season()

#df = combine_purple()
#d1 = df.groupby('Hour', as_index=False)['temperature'].mean()
#d1['range'] = df.apply(lambda row: add_range(row), axis=1)
#display(d1)
#df = combine_loc_micro()
#display(df)
#df.rename(columns={"Temp":"temperature", "Filter_ID":'filter'}, inplace=True)
#df
#plot_diurnal()
#plot_micro_neph()
#d1, d2 = plot_micro_atmo_filter()
#plot_micro_atmo_filter()
#d2 = d2.groupby('Location', as_index=False)['PM2.5, ug/m3'].mean()
#display(d1['Location'])
#display(d2['Location'])
#plot_filter_atmo2()


# In[127]:


#plot_filter_atmo2()

