import MWB_Data_Reader as mb
import ast
import sys
from datetime import datetime

if len(sys.argv)<4:
    print("\nSyntaxe:\n")
    print("python datadownload.py - [a1, a2,...,an], d1, d2\n")
    print("Where an in the following format: ")
    print('{"Ticker" : ttt,')
    print(' "Source" : "Bloomberg"/"Databate"/"GoogleTrends/Basket",')
    print(' "Proxy ticker" : ttt,')
    print(' "Proxy source" : "Bloomberg"/"Databate"/"GoogleTrends/Basket"}')
    print("\nProxy ticker is optional\n")
    print("d1 and d2 are the start and end dates in the format yyyy-mm-dd\n")
else:
    tickers=ast.literal_eval(sys.argv[1])
    start_date= datetime.strptime(sys.argv[2],"%Y-%m-%d")
    end_date= datetime.strptime(sys.argv[3],"%Y-%m-%d")

    data=mb.BasketHistoricalData("Excel",tickers)
    #sources = [i["Source"] for i in tickers]
    #sources+=([i["Proxy source"] for i in tickers if "Proxy source" in i.keys()])

    data.loadFromBloomberg(start_date,end_date)
    data.loadFromDatabase(start_date,end_date)
    data.loadFromGoogleTrends(start_date,end_date)
    print(data.getData())
    data.getData().to_clipboard()
    

