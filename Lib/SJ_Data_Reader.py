from datetime import datetime
import blpapi
import numpy as np
import pandas as pd
from optparse import OptionParser
import pymysql.cursors
import logging
from pytrends.request import TrendReq
import sj_lib.sjtools as sj
from typing import Optional
import warnings


class BloombergHistoricalData:
    """
    Opens a bloomberg connection and returns a dataframe with one column for each security broken in sub-
    columns if there is more than one field passed.
    Raises exception when not connected to bloomberg terminal
    Does not drop N/A's
    Use getData() to retrieve dataframe with all downloaded data
    """
    def __init__(self, startDate, endDate, securities, fields=["PX_LAST"], periodicity = "DAILY", nonTradingDayFillOption="ACTIVE_DAYS_ONLY",nonTradingDayFillMethod="PREVIOUS_VALUE", overrides_dict=None):
        if not isinstance(securities,list):
            raise TypeError("BloombergHistoricalData: securities must be a list")
        self.startDate = startDate
        self.endDate = endDate
        self.securities = securities
        self.fields = fields
        self.periodicity = periodicity
        self.nonTradingDayFillOption = nonTradingDayFillOption
        self.nonTradingDayFillMethod=nonTradingDayFillMethod
        self.overrides_dict=overrides_dict
        parser = OptionParser(description="Retrieve reference data.")
        parser.add_option("-a","--ip",dest="host",help="server name or IP (default: %default)",metavar="ipAddress",default="localhost")
        parser.add_option("-p",dest="port",type="int",help="server port (default: %default)",metavar="tcpPort",default=8194)
        (options, args) = parser.parse_args()
        
        sessionOptions = blpapi.SessionOptions()
        sessionOptions.setServerHost(options.host)
        sessionOptions.setServerPort(options.port)
        session = blpapi.Session(sessionOptions)
        if not session.start():
            logging.error("Failed to start session. Are you logged to you Bloomberg Terminal? Rasing exception.")
            raise Exception("Failed to start session. Are you logged to you Bloomberg Terminal?")
            return
        if not session.openService("//blp/refdata"):
            logging.error("Failed to open //blp/refdata")
            raise Exception("Failed to open //blp/refdata")
            return

        request = session.getService("//blp/refdata").createRequest("HistoricalDataRequest")
        for security in self.securities:
            request.getElement("securities").appendValue(security)
        for f in fields:
            request.getElement("fields").appendValue(f)
            
        request.set("nonTradingDayFillOption", self.nonTradingDayFillOption)
        request.set("nonTradingDayFillMethod", self.nonTradingDayFillMethod)
        request.set("periodicitySelection", self.periodicity)
        request.set("startDate", self.startDate.strftime("%Y%m%d"))
        request.set("endDate", self.endDate.strftime("%Y%m%d"))

        if self.overrides_dict is not None:
            overrides = request.getElement("overrides")
            for f in self.overrides_dict:
                ov = overrides.appendElement()
                ov.setElement("fieldId", f)
                ov.setElement("value", self.overrides_dict[f])

        session.sendRequest(request)
        series = {}
        while (True):
            # We provide timeout to give the chance for Ctrl+C handling:
            ev = session.nextEvent(500)
            for msg in ev:
                if msg.hasElement("securityData"):
                    rows=[]
                    secname = msg.getElement("securityData").getElementAsString("security")
                    dataArray = msg.getElement("securityData").getElement("fieldData")
                    for i in range(dataArray.numValues()):
                        d = dataArray.getValueAsElement(i)
                        elements=[]
                        for f in self.fields:
                            if d.hasElement(f):
                                elements.append(d.getElementAsFloat(f))
                            else:
                                elements.append(np.NaN)
                        rows.append([pd.Timestamp(d.getElementAsDatetime("date"))]+elements)

                    #dfColumnIndex = pd.MultiIndex.from_product([[secname], ["Date"]+self.fields],names=["Security", "Field"])
                    columns=["Date"]+self.fields
                    columns=[(secname,k)for k in columns]
                    series[secname] = pd.DataFrame(rows, columns=columns)
                    series[secname].set_index(keys=columns[0], inplace=True)
                    series[secname].index.names = ['Date']
            if ev.eventType() == blpapi.Event.RESPONSE:
                # Response completly received, so we could exit
                self.data = pd.concat([series[k] for k in series.keys()], axis=1)
                self.data.columns= pd.MultiIndex.from_tuples(self.data.columns)
                session.stop()
                break
            #if ev.eventType()== blpapi.Event.TIMEOUT:
            #    logging.error("Bloomberg timed out while downloading data:")
            #    logging.error(self.startDate.strftime("%Y%m%d")+" to "+self.endDate.strftime("%Y%m%d"))
            #    logging.error(self.securities)
            
        session.stop()

    def getData(self):
        if len(self.data) ==0:
            return None
        else:
            return self.data

class DatabaseHistoricalData:
    """
    Gets data for selected securities from the hedgefunds database
    Use getData() to retrieve dataframe with all downloaded data
    """
    
    def __init__(self, startDate, endDate, securities, dates = None):
        if not isinstance(securities,list):
            raise TypeError("DatabaseHistoricalData: securities must be a list")
        database="hedgefunds"
        host = "192.168.40.4"
        self.mydb = pymysql.connect(
            host=host,
            user="armory",
            passwd="19qd$SD#",
            charset='utf8mb4',
            database=database,
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor)
        
        self.crsr=self.mydb.cursor()
        select_stmt = "SELECT data, Product, FinancialPrice FROM `Database` WHERE (data>='"+startDate.strftime("%Y%m%d")+"' AND data<='"+endDate.strftime("%Y%m%d") +"') AND ("
        select_stmt = select_stmt + "Product = '" + securities[0] + "'"
        for s in securities[1:]:
            select_stmt = select_stmt + " OR Product = '" + s + "'"
        select_stmt = select_stmt + ") ORDER BY data;"

        self.crsr.execute(select_stmt)
        rows = self.crsr.fetchall()
        series={}
        for s in securities:
            data=[[row["data"],row["FinancialPrice"]] for row in filter(lambda row : row["Product"]==s, rows)]
            if dates is not None:
                data = [row for row in filter(lambda row : row["data"] in dates, rows)]

            columns=[(s,"Date"), (s,"PX_LAST")]               
            series[s]=pd.DataFrame(data=  data,  columns=columns)
            series[s].set_index(keys=columns[0], inplace=True)
            series[s].index.names = ['Date']
            
        nodata = ""
        for s in securities:
            if len(series[s].index)<=1:
                nodata = nodata + "\n* " + s
        if nodata!="":
            raise ValueError('Database securities with insuficient data: '+ nodata)

        self.data=pd.DataFrame([])
        self.data = self.data.join([series[s] for s in series.keys()], how='outer')
        self.data.columns= pd.MultiIndex.from_tuples(self.data.columns)
        
    def getData(self):
        if len(self.data) == 0:
            return None
        else:
            return self.data

class GoogleTrendsHistoricalData:
    """
    Gets historical interest in a list o keywords from google Trends
    """
    
    def __init__(self, startDate, endDate, keyword_list, language='en-US', geo="US"):
         #or 'pt-BR' geo = "BR"
        if not isinstance(keyword_list,list):
            raise TypeError("GoogleTrendsHistoricalData: keyword_list must be a list")
        self.startDate = startDate.strftime("%Y-%m-%d")
        self.endDate = endDate.strftime("%Y-%m-%d")
        self.keyword_list = keyword_list
        warnings.simplefilter("ignore", ResourceWarning)
        self.pytrend = TrendReq(hl=language)
        self.pytrend.build_payload(kw_list=keyword_list, timeframe=self.startDate+" "+self.endDate, geo=geo)# Interest by Region
        data =self.pytrend.interest_over_time()
        self.data=data.drop("isPartial", axis=1)
        idx = pd.MultiIndex.from_product([list(self.data.columns.values),["PX_LAST"]]) #, names=["Security","Field"])
        self.data.columns=idx
        warnings.simplefilter("default", ResourceWarning)
        
        
    def getData(self):
        if len(self.data) == 0:
            return None
        else:
            return self.data

class PortfolioHistoricalData:
    def __init__(self, startDate, endDate, portfolioname):
        if not isinstance(portfolioname,str):
            raise TypeError("PortfolioHistoricalData: portfolio name must be a string with the name of just one portfolio")
        self.name=portfolioname
        self.all_baskets=sj.load_all_baskets()
        self.portfolio=self.all_baskets[portfolioname]
        reduced_portfolio=[x for x in self.portfolio if x["Source"]!="Portfolio"]
        dt=BasketHistoricalData("Hook",startDate, endDate, reduced_portfolio)
        self.data=dt.getData()#.droplevel(1,axis=1)
        for i in [x["Ticker"] for x in self.portfolio if x["Source"]=="Portfolio"]:
            y=self.loadBasket(startDate,endDate,i)
            self.data=pd.concat([self.data,y], axis=1).dropna(how="any")


    def loadBasket(self, startDate, endDate, basketname):
        x=PortfolioHistoricalData(startDate,endDate,basketname)
        return x.getData()

    def getData(self, dropna=True, useproxies = True):
        w=pd.Series({(i["Ticker"],"PX_LAST"): float(i["Weight"]) for i in self.portfolio})
        z=pd.DataFrame(data=self.data/self.data.shift(+1)-1)
        z=pd.DataFrame(data=((w*z).sum(axis=1)+1).cumprod(), columns=pd.MultiIndex.from_tuples([(self.name,"PX_LAST")]))
        x=z
        return x            

class BasketHistoricalData:
    """
    This class downloads a basket of prices from different sources
    extends returns weth proxies and returns a dataframe with all the
    prices

    basket_array is an array of dictionaries with the following fields
    {"Ticker" : string, 
     "Source" : "Bloomberg"/"Databate"/"GoogleTrends"/"Portfolio",
     "Proxy ticker" : string, 
     "Proxy source" : "Bloomberg"/"Databate"/"GoogleTrends"/"Portfolio"}
      Proxy ticker and source are optional
    """
    def __init__(self, name:str, start_date: datetime, end_date: datetime, basket_array: Optional[list]  =None):
        self.name=name
        self.data=None
        self.dbdata=None
        self.bbdata=None
        self.gtdata=None
        self.ppdata=None
        self.start_date= start_date
        self.end_date = end_date
        if basket_array is not None:
            for x in range(0,len(basket_array)):
                if "Proxy source" not in basket_array[x].keys():
                    basket_array[x]["Proxy source"]=None
                    basket_array[x]["Proxy ticker"]=None
        else:
            basket_array=[]

        self.basket_array=basket_array    
        self.tickers =[t["Ticker"] for t in basket_array]
        #print(basket_array)
        
    def addSecurity(self, ticker, source, proxy_ticker=None, proxy_source=None):
        x = [i["Ticker"].upper()==ticker.upper() for i in self.basket_array]
        if not any(x):
            self.basket_array.append({"Ticker":ticker, "Source":source, "Proxy ticker":proxy_ticker, "Proxy source":proxy_source})
            self.tickers =[t["Ticker"] for t in self.basket_array]
            if source == "Bloomberg" or proxy_source=="Bloomberg":
                self.bbdata=None
            if source == "Database" or proxy_source=="Database":
                self.dbdata=None
            if source == "GoogleTrends" or proxy_source=="GoogleTrends":
                self.gtdata=None
            if source == "Portfolio" or proxy_source=="Portfolio":
                self.ppdata=None

    def __str__(self):
        r = "Basket historical data for: "+self.name+":\n"
        if self.bbdata is None:
            r+="No bloomberg data loaded.\n"
        else:
            r+="bloomberg data loaded.\n"
        if self.dbdata is None:
            r+="No database data loaded.\n"
        else:
            r+="Database data loaded.\n"
        if self.dtdata is None:
            r+="No googleTrends data loaded.\n"
        else:
            r+="googleTrends data loaded.\n"
        return r

    def loadFromBloomberg(self,fields=["PX_LAST"], periodicity = "DAILY", nonTradingDayFillOption="ACTIVE_DAYS_ONLY",nonTradingDayFillMethod="PREVIOUS_VALUE", overrides_dict=None):
        """
        nonTradingDayFillMethod=PREVIOUS_VALUE/ NIL_VALUE
        nonTradingDayFillOption=ACTIVE_DAYS_ONLY/ ALL_CALENDAR_DAYS/ NON_TRADING_WEEKDAYS
        """    
        startDate=self.start_date
        endDate=self.end_date
        bb=[t["Ticker"] for t in self.basket_array if t["Source"]=="Bloomberg" and t["Ticker"]!=""]
        bb=bb+[t["Proxy ticker"] for t in self.basket_array if t["Proxy source"]=="Bloomberg" and t["Proxy ticker"]!="" and t["Proxy ticker"]is not None]
        bloomberg_tickers=bb

        if len(bloomberg_tickers)>0:
            try:
                bb = BloombergHistoricalData(startDate, endDate,bloomberg_tickers, fields= fields,periodicity=periodicity, nonTradingDayFillOption=nonTradingDayFillOption, nonTradingDayFillMethod=nonTradingDayFillMethod, overrides_dict=overrides_dict)
                self.bbdata=bb.getData()
            except Exception as err:
                self.bbdata=None
                raise Exception(err)
        else:
            self.bbdata=None

    def loadFromDatabase(self):
        startDate=self.start_date
        endDate=self.end_date
        db=[t["Ticker"] for t in self.basket_array if t["Source"]=="Database" and t["Ticker"]!=""]
        db=db+[t["Proxy ticker"] for t in self.basket_array if t["Proxy source"]=="Database" and t["Proxy ticker"]!=""]
        database_tickers=db

        if len(database_tickers)>0:
            try:
                db = DatabaseHistoricalData(startDate, endDate,database_tickers)
                self.dbdata=db.getData()
            except Exception as err:
                logging.error("loadFromDatabase Exception raised")
                self.dbdata=None
                raise Exception(str(err))
        else:
            self.dbdata=None

    def loadFromGoogleTrends(self, language='en-US', geo="US"):
        startDate=self.start_date
        endDate=self.end_date
        gt=[t["Ticker"] for t in self.basket_array if t["Source"]=="GoogleTrends" and t["Ticker"]!=""]
        gt=gt+[t["Proxy ticker"] for t in self.basket_array if t["Proxy source"]=="GoogleTrends" and t["Proxy ticker"]!=""]
        if len(gt)>0:
            try:
                gt = GoogleTrendsHistoricalData(startDate, endDate, gt, language, geo)
                self.gtdata=gt.getData()
            except Exception as err:
                logging.error("loadFromGoogleTrends Exception raised")
                self.gtdata=None
                raise Exception(str(err))
        else:
            self.gtdata=None

    def loadFromPortfolio(self):
        ports=[i["Ticker"] for i in self.basket_array if i["Source"]=="Portfolio"]
        ports+=[i["Proxy ticker"] for i in self.basket_array if i["Proxy source"]=="Portfolio"]
        series={}
        for s in ports:             
            x = PortfolioHistoricalData(self.start_date,self.end_date,s)
            series[s]=x.getData()
            
        nodata = ""
        for s in ports:
            if len(series[s].index)<=1:
                nodata = nodata + "\n" + s
        if nodata!="":
            raise ValueError('Portfolio securities with insuficient data: '+ nodata)

        data=pd.DataFrame([])
        data = data.join([series[s] for s in series.keys()], how='outer')
        data.columns= pd.MultiIndex.from_tuples(data.columns)
        self.ppdata=data

    def getData(self, dropna=True, useproxies = True):
        def TotGoogle():   #### Not finished
            data=[]
            for i in range(0,len(self.dbdata.index)):
                x = self.gtdata.loc[self.gtdata.index>self.dbdata.index[i]]
                x = x.loc[x.index<=self.dbdata.index[i+1]]
                data.append(x.mean())
            print(data)

        sources = [i["Source"] for i in self.basket_array]
        sources += [i["Proxy source"] for i in self.basket_array if i["Proxy source"] is not None]
        sources = list(set(sources))
    
        if ("Bloomberg" in sources) and self.bbdata is None:
            self.loadFromBloomberg()
        if ("Database" in sources) and self.dbdata is None:
            self.loadFromDatabase()
        if ("GoogleTrends" in sources) and self.gtdata is None:
            self.loadFromGoogleTrends()
        if ("Portfolio" in sources) and self.ppdata is None:
            self.loadFromPortfolio()

        sources=[self.bbdata,self.dbdata,self.gtdata,self.ppdata]
        if all(n is None for n in sources):
            raise Exception("Basket is empty: "+self.name)
        elif any(n.index.is_unique is False for n in sources if n is not None):
            raise Exception("There are duplicate dates in some of the data sources.")
        else:
            self.data=pd.concat([x for x in sources if x is not None],axis=1)

        if useproxies:
            self.applyProxies()
        if dropna:
            return self.data[self.tickers].dropna(how="any")
        else:
            return self.data[self.tickers]

    def applyProxies(self):
        for s in self.basket_array:
            if s["Proxy ticker"]:
                dSec = self.data[s["Ticker"]]["PX_LAST"].dropna().index.min()
                dProxy = self.data[s["Proxy ticker"]]["PX_LAST"].dropna().index.min()
                if dProxy<dSec :  #Proxy has more data
                    #find latest date when both intercept
                    lastdate=None
                    for d in self.data[s["Proxy ticker"]]["PX_LAST"].dropna().index:
                        if d in self.data[s["Ticker"]]["PX_LAST"].dropna().index:
                            lastdate=d
                        if d>=dSec:
                            break
                    if lastdate is not None: #An intersection was found. Clear rest of ticker data and replace by proxy
                        oldTicker=self.data.loc[self.data.index==lastdate,(s["Ticker"],"PX_LAST")].values[0]
                        oldProxy=self.data.loc[self.data.index==lastdate,(s["Proxy ticker"],"PX_LAST")].values[0]
                        self.data.loc[self.data.index<lastdate,(s["Ticker"],"PX_LAST")]=np.NaN                        
                        for d in self.data[s["Proxy ticker"]].dropna().index[self.data[s["Proxy ticker"]].dropna().index<lastdate][::-1]:
                            proxyvar=self.data.loc[self.data.index==d,(s["Proxy ticker"],"PX_LAST")].values[0]/oldProxy
                            self.data.loc[self.data.index==d,(s["Ticker"],"PX_LAST")]=proxyvar*oldTicker
                            oldTicker=self.data.loc[self.data.index==d,(s["Ticker"],"PX_LAST")].values[0]
                            oldProxy=self.data.loc[self.data.index==d,(s["Proxy ticker"],"PX_LAST")].values[0]
                    else:
                        logging.warning("Proxy ignored as it does not intersect with security")
        return

    def saveToPickle(self):
        self.getData(dropna=False).to_pickle(self.name+".pkl")

    def loadFromPickle(self):
        self.data = pd.read_pickle(self.name+".pkl")
"""
def extend_proxies(data, proxy_dict):
    for k in data.columns:
        if k in proxy_dict:
            #if data[prohxy_dict[k]["Ticker"]].dropna().index.min() < data[k].dropna().index.min():
                #print(k, " has a longer proxy history")
            #else:
                #print(k, " does not need to be proxied")    
            if data[k].dropna().empty:   #No data for security, use proxy prices for everything 
                data[k]=data[proxy_dict[k]["Ticker"]].dropna()
            else: #there is data for the security, so merge proxy with security
                if data[proxy_dict[k]["Ticker"]].dropna().index.min()< data[k].dropna().index.min():   #proxy has more data
                    limit_date = data[k].dropna().index.min()
                    proxy_rets= np.log(data[proxy_dict[k]["Ticker"]].dropna()/data[proxy_dict[k]["Ticker"]].dropna().shift(-1))
                    proxy_prices=np.exp(proxy_rets[proxy_rets.index<limit_date][::-1].cumsum())[::-1]*data[k][limit_date]
                    s = data[k].dropna(how="all")
                    data[k]= s.combine_first(proxy_prices)
            #print(k, data[k].dropna().index.min())
            
    return data          
"""

def bd_per_year(returns):  # business days per year
    days = (returns.tail(1).index-returns.head(1).index).days[0]
    bdperyear = (returns.index.size/days) * 365     #businessday per year
    return bdperyear

def daily_to_annual_return(ret, bd):
    return (np.exp(ret*bd)-1)

def parseCmdLine():
    parser = OptionParser(description="Retrieve reference data.")
    parser.add_option("-a",
                      "--ip",
                      dest="host",
                      help="server name or IP (default: %default)",
                      metavar="ipAddress",
                      default="localhost")
    parser.add_option("-p",
                      dest="port",
                      type="int",
                      help="server port (default: %default)",
                      metavar="tcpPort",
                      default=8194)

    (options, args) = parser.parse_args()

    return options

def parseRequest(session, startDate, endDate, securities, peridiocity, fields, override_dict):
    startDateStr= startDate.strftime("%Y%m%d")
    endDateStr= endDate.strftime("%Y%m%d")
    refDataService = session.getService("//blp/refdata")

    request = refDataService.createRequest("HistoricalDataRequest")
    for security in securities:
        request.getElement("securities").appendValue(security)
    for f in fields:
        request.getElement("fields").appendValue(f)
    request.set("periodicityAdjustment", "ACTUAL")
    request.set("nonTradingDayFillOption", "ACTIVE_DAYS_ONLY")
    request.set("periodicitySelection", peridiocity)
    request.set("startDate", startDateStr)
    request.set("endDate", endDateStr)
    if override_dict is not None:
        overrides=request.getElement("overrides")
        for f in override_dict:
            ov = overrides.appendElement()
            ov.setElement("fieldId", f)
            ov.setElement("value", override_dict[f])
            
    
    #request.set("maxDataPoints", 300)
    return request

def getBloombergEventName(ev):
    switcher = {
        blpapi.Event.AUTHORIZATION_STATUS : "Authorization status",
        blpapi.Event.PARTIAL_RESPONSE : "Partial response",
        blpapi.Event.REQUEST : "Request",
        blpapi.Event.REQUEST_STATUS : "Resquest status",
        blpapi.Event.RESOLUTION_STATUS : "Resolution status",
        blpapi.Event.RESPONSE : "Response",
        blpapi.Event.SERVICE_STATUS : "Service status",
        blpapi.Event.SESSION_STATUS : "Session status",
        blpapi.Event.TIMEOUT : "Timeout"
    }
    if ev.eventType() not in switcher:
        return "Not defined"
    else:
        return switcher[ev.eventType()]

if __name__ =='__main__':
    d1=datetime.strptime("2015-12-31","%Y-%m-%d")
    d2=datetime.strptime("2017-12-31","%Y-%m-%d")
    basket=[{"Ticker":"Alphadyne", "Source": "Database", "Proxy ticker": "TCI FUND", "Proxy source": "Database"},
            {"Ticker":"M SQUARE BRAZIL", "Source" : "Database", "Proxy ticker": "R1", "Proxy source": "Portfolio"}]        
    pp=BasketHistoricalData("Teste", d1, d2, basket)
    #pp=PortfolioHistoricalData(d1,d2,"R1")
    print(pp.getData())

#bd = BloombergBulkData(["AO5457038 Corp"],["DES_CASH_FLOW"])
#bd = BloombergReferenceData(["EI4166209 Corp"],["PX_LAST"])
