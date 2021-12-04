import sys
sys.path.insert(0,'.\Lib')
from MWB_Data_Reader import bd_per_year, BasketHistoricalData
import datetime as dt
from datetime import date
from datetime import timedelta
from datetime import datetime
import calendar
import sys 

"""
    basket_array is an array of dictionaries with the following fields
    {"Ticker" : ttt, "Source" : "Bloomberg"/"Databate"/"GoogleTrends",
      "Proxy ticker" : ttt, "Proxy source" : "Bloomberg"/"Databate"/"GoogleTrends"}
      Proxy ticker is optional
"""

def f_extracao_de_dados(arr_ativos,arr_bench,arr_fonte,dt_min,ano_base):
    dic = {}
    basket_array = []
    for i in range(len(arr_ativos)):
        dic["Ticker"] = arr_ativos[i]
        dic["Source"] =arr_fonte[i]
        basket_array.append(dic)
              
    data = BasketHistoricalData("Nome", basket_array)


    today = datetime.strptime(dt.date.today().strftime("%Y-%m-%d"), "%Y-%m-%d")
    ano_base= 1900
    
    flag=0
    i=1
    delta = dt.timedelta(days=1)
    print(basket_array)
    if len(list(set(arr_fonte))) == 1 and list(set(arr_fonte))[0] == "Database": #Soment sql
        min_d = dt_min

        print(min_d)
        print(today)
        print(basket_array)
        
        data.loadFromDatabase(min_d, today)
        flag = 1                                
    else:
        print('else')
        #if dt_min!="": #Existe sql
##        min_d = datetime.strptime(dt_min, "%m/%d/%Y")
##        data.loadFromBloomberg(min_d, min_d + delta)
##        while True:
##            try:
##                data.loadFromBloomberg(min_d, min_d + delta)
##                flag = 1
##                break        
##            except:
##                min_d += 2*delta
##                if min_d.year >2021:
##                    break
##                pass    
##        if flag == 1:
##            data.loadFromDatabase(min_d, today)  
##            data.loadFromBloomberg(min_d, today)
           
    prices = data.getData(dropna=False, useproxies=True)
    return prices       
        
        
#Exception: Database securities with insuficient data
#Exception: Failed to start session. Are you logged to you Bloomberg Terminal?
#NotImplementedError: Index._join_level on non-unique index is not implemented







