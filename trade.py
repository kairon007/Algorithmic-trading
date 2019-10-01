from fyers_api import accessToken
from fyers_api import fyersModel
import pandas as pd
from pandas import DataFrame
import time
import datetime
import time
import xlrd
import requests
from datetime import datetime
from datetime import timedelta
from datetime import date
import schedule
import os.path
import logging
clist = []
date_time = ""
logger = ""
#import stock3


#Here we generate the authorization_code to authorize the app 
#In visual studio code we have to print the response to get the authorization_code
try:
    app_id = open("api_id.txt", "r").read()  #app_id is given by fyers
except IOError:
    print("api_id.txt file does not exist")

try:
    app_secret = open("app_secret.txt", "r").read()  #app_secret is given by fyers   
except IOError:
    print("app_secret.txt file does not exist")    
app_session = accessToken.SessionModel(app_id, app_secret)
response = app_session.auth()
#print (response)    #to generate authorization_code remove #



#Now we generate the access token
#you have toh generate the authorization_code after in active
#Again we comment the app_session.generate_token(), we copy the token
try:
    authorization_code = open("authorization_code.txt", "r").read()   
except IOError:
    print("authorization_code.txt file does not exist")
app_session.set_token(authorization_code)
app_session.generate_token()
#print(app_session.generate_token())   #to generate token remove #

#Here we check we connected to the api or not
#comment the print(fyers) after check
#you have toh generate the token after in active
try:
    token = open("token.txt", "r").read()   
except IOError:
    print("app_secret.txt file does not exist")
is_async = False #(By default False, Change to True for asnyc API calls.))
fyers = fyersModel.FyersModel(is_async)
#print(fyers)

#Here we check the profile through the token
#comment the print so we can't get again and agian profile
"""profile = fyers.get_profile(token = token)
print(profile)"""

op=0
cl=0
cname = ""
name=""
#This is fileread function which read the excel file where we store the Symbol, Cash value, Heikin Ashi (open & close)
def fileread():
    try:
        excel_file = 'company.xls' #file present in same directory so its realtive path
        
    except IOError:
        print("company.xls' file does not exist")
    df3 = pd.read_excel(excel_file)
    conv(df3)
    
######## SYMBOL FETCHING DATA FUNCTION START ###########    
#This is xyz function which fetch the historical data of 1 min & we consolidate the 1 min data to 15 min data
#We call the fileread function here to to read the excel file 
def xyz(fr,to,tim, df3):
    global date_time
    newdf = pd.DataFrame()
    for row in df3.iterrows():
        global name
        name=row[1][0]
        cname="NSE:"+name+"-EQ"
        op=row[1][1]
        cl=row[1][2]
        cash=row[1][3]
       
           
        data1 = fyers.get_historical_OHLCV(
        token = token,
        data = {
        "symbol" : cname,
        "resolution" : "1",
        "From" :fr ,
        "to" :to

        }
        )
        
        i=0
        lo=0
        up=0
        
        df = pd.DataFrame(data1['data']) 
    
        ct=df['o'].count()
        
        loop = int(ct/tim)
       
        for i in range(int(loop)):
            
            ho=9
            mini=15
            lo=tim*i+0
                
            up=tim*(i+1)-1
            mini=mini+(i+1)*tim
            ho=ho+int(mini/60)
            
            mini=mini%60
            for _ in df[lo:up+1]:
                cl=df.at[up,'c']
                hi=max(df[lo:up+1]['h'])
                #print ("hi -->", hi)
                low=min(df[lo:up+1]['l'])
                op=df.at[lo,'o']
            ran=abs(hi-low)
            body=abs(op-cl)
            half=ran/2
        newdf = newdf.append({'cash': cash, 'Symbol':row[1][0],'Open' : op, 'High' : hi, 'Low' : low, 'Close' : cl, 'Time' : datetime.fromtimestamp(int(fr))},  ignore_index = True)
    HA(newdf, cash, cname, fr)           
    
######## SYMBOL FETCHING DATA FUNCTION END ###########    
   
####### HEIKIN ASHI FUNCTION START #############   
# This is Heikin Ashi function were we convert the 15min consolidate data into heikin ashi candle
# Heikin ashi candle values are based on the Heikin ashi fourmulas
# There are total 4 fourmulas in which 3 are simple but to calculate the Heikin ashi Open first candle we have to take previous day Heikin ashi (Open + Close)/2
# Therefore we store Heikin ashi Open & Close value into company.xls file
# In this function we generate the alert system and get a alert on telegram
ovalue = []				
cvalue = []

def HA(df, cash, cname, fr):
    cna=""
    a = (df['Open']+ df['High']+ df['Low']+df['Close'])/4.0
    a1 = round(a/ 0.05) * 0.05
    df['HA_Close'] = round(a1, 2)
    workbook = xlrd.open_workbook('company.xls')
    worksheet = workbook.sheet_by_name('Sheet1')
    idx = df.index.name
    df.reset_index(inplace=True)
    temp=1	
    for i in range(0, len(df)):
        if (str(df.iloc[i]['Time']) == date_time):
            b = (worksheet.cell_value(temp, 1) + (worksheet.cell_value(temp, 2))) / float(2)
            b1 = round(b/ 0.05)*0.05
            df.set_value(i, 'HA_Open', b1)
            temp = temp + 1
            ovalue.append(df.iloc[i]['HA_Open'])
            cvalue.append(df.iloc[i]['HA_Close'])
            

        else:
            b = (ovalue[i] + cvalue[i]) / float(2)
            b1 = round(b/ 0.05) * 0.05
            df.set_value(i, 'HA_Open', b1)
            ovalue[i] = df.iloc[i]['HA_Open']
            cvalue[i] = df.iloc[i]['HA_Close']
            
   

    if idx:
        df.set_index(idx, inplace=True)

    c = df[['HA_Open','HA_Close','High']].max(axis=1)
    c1 = round(c/ 0.05) * 0.05
    df['HA_High']= round(c1, 2)
    
    d = df[['HA_Open','HA_Close','Low']].min(axis=1)
    d1 = round(d/ 0.05) * 0.05
    df['HA_Low']=round(d1, 2)
    df = df.reindex(columns=['Symbol','Open','High','Low','Close','HA_Close','HA_High','HA_Low','HA_Open','Time', 'cash'])
    print(df)
    
    
    for r in range(len(df)):
        ran=float(abs(df.iloc[r]['HA_High']-df.iloc[r]['HA_Low']))
        body=float(abs(df.iloc[r]['HA_Open']-df.iloc[r]['HA_Close']))
        half=ran/5
        cna = df.iloc[r]['Symbol'] #Isme for loop abhi jis company ka naam read kr rha h uska naam h (symbol)
        cash = worksheet.cell_value(r+1, 3) #excel symbol location + increment
        if cna not in clist:
            if body > half and(cash/2) < ran <= (cash*1.01):         #ran <= cash
                company = ("STOCK = "+df.iloc[r]['Symbol'])
                a = ("Date and Time="+str(datetime.fromtimestamp(int(fr))))
                clist.append(df.iloc[r]['Symbol'])
                tele(a,company,(df.iloc[r]['HA_Close']),(df.iloc[r]['HA_High']),(df.iloc[r]['HA_Low']),(df.iloc[r]['HA_Open']))
            

        

        
    
   

####### HEIKIN ASHI FUNCTION END #############            
            
            
        
####THIS IS A TELEGRAM FUNCTION ########
# This is a telegram function which is use only to generate the alert on channel #@algotradealert (Channel name)
def tele(a,company,cl,hi,low,op):
    bot_token = '986625783:AAEmqQ2WVKVi3TgYn79Fd5aYvXoSKdObRZw'
    bot_chatID = '@algotradealert'
    bot_message = company + "\n" + a + "\n" + "Open =" +  str(op) + "\n" + "High =" + str(hi) + "\n" + "Low =" + str(low) + "\n" + "Close =" + str(cl)
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
    response = requests.get(send_text)
    return response.json()
    
                  
##### TELEGRAM FUNCTION END #########     

#This is time & date converter function
# To fectch the historical data by using fyers api we have to take Unix timestamp time format which a little bit difficult to understand
# So here we firstaly convert the time into Unix timestamp and send it to the xyz function and then print the local time
def conv(df3):
    global date_time
   
    #now = datetime.today() - timedelta(days=1)
    
    now = datetime.now()
    



    dti=now.strftime("%Y-%m-%d")
    date_time=dti+" 09:25:00"
    pattern = '%Y-%m-%d %H:%M:%S'
    fr = int(time.mktime(time.strptime(date_time, pattern)))
    fr=str(fr)
    
    
    dt_string = now.strftime("%d.%m.%Y")
    dt_string = now.strftime("%d.%m.%Y")+" 09:35:00"
    pattern = '%d.%m.%Y %H:%M:%S'
    to = int(time.mktime(time.strptime(dt_string, pattern)))
    to=str(to)
    
    
    tim=10 # time change time is now 10
    
    for _ in range(42):
        
        xyz(fr,to,tim,df3)
        fr=str(int(fr)+600)
        to=str(int(to)+600)
        time.sleep(1)

fileread()




