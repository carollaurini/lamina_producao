import sys
sys.path.insert(0,'p:/Lib')
from MWB_Data_Reader import bd_per_year, BasketHistoricalData

import datetime as dt
from datetime import date
from datetime import timedelta
from datetime import datetime
import calendar

arr_ativos = sys.argv[1].split(',')
arr_bench = sys.argv[2].split(',')
arr_fonte = sys.argv[3].split(',')
arr_data = sys.argv[4].split(',')

"""
    basket_array is an array of dictionaries with the following fields
    {"Ticker" : ttt, "Source" : "Bloomberg"/"Databate"/"GoogleTrends",
      "Proxy ticker" : ttt, "Proxy source" : "Bloomberg"/"Databate"/"GoogleTrends"}
      Proxy ticker is optional
"""
dic = {}
basket_array = []
for i in range(len(arr_ativos)):
    dic["Ticker"] = arr_ativos[i]
    dic["Source"] =arr_fonte[i]
    basket_array.append(dic)
    print(basket_array[i])

    

        
data = BasketHistoricalData("Nome", basket_array)
today = datetime.strptime(dt.date.today().strftime("%Y-%m-%d"), "%Y-%m-%d")

ano_base= 2016
i=1
flag=0
a = False
if a == True:
    #Tentativa na Database Mensal
    while True:
        try:
            # connect
            min_d = datetime.strptime(str(ano_base)+"-"+str(i) + "-"  + str(calendar.monthrange(ano_base, i)[1]),"%Y-%m-%d")
            max_d = datetime.strptime(str(ano_base)+"-"+str(i+1) + "-"  + str(calendar.monthrange(ano_base, i+1)[1]),"%Y-%m-%d")
            #print(min_d)
            #print(max_d)

            data.loadFromDatabase(min_d, max_d)
            flag = 1
            break 
        except:
            if ano_base>2021:           
                break       
            i+=1        
            if i > 12:
                i=1
                ano_base +=1
            pass

    if flag == 1:
        data.loadFromDatabase(min_d, today)  
        prices=data.getData(dropna=False, useproxies=True)
        print(prices)

    #Tentativa na Database diaria    

else:
    print("######################################################TENTANDO DIARIO##########################################################")
    delta = dt.timedelta(days=1)
    ano_base= 2017
    flag=0
    min_d = datetime.strptime(str(ano_base)+"-01-31","%Y-%m-%d")
    while True:
        try:
            # connect
            max_d = min_d + delta
            print(min_d)
            print(max_d)

            data.loadFromDatabase(min_d, max_d)
            prices=data.getData(dropna=False, useproxies=True)
            print(prices)
            flag = 1
            break 
        except:
            if min_d.year >2021:           
                break       
            min_d += 2*delta

            pass

    if flag == 1:
        data.loadFromDatabase(min_d, today)  
        prices=data.getData(dropna=False, useproxies=True)
        print(prices)
    else: print("Não existe dados historicos")








