import pandas as pd
from numpy import log, exp
from MWB_Data_Reader import bd_per_year

month_dict={1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez', 13: 'Total'}

class Security:
    'Creates a price series from a string of returns and provides analytics'
    def __init__(self, returns=None, prices=None, name=None):
        if returns is not None:
            self.returns = pd.Series(data=returns.values, index=returns.index)
            self.prices = pd.Series(data=exp(self.returns.values.cumsum()), index=self.returns.index)
        else:
            self.prices = pd.Series(data=prices.values, index=prices.index)
            self.returns = pd.Series(data=log(prices/prices.shift(1)), index = prices.index)
            self.returns = self.returns.dropna(how="any")
            
        
        self.bd_per_year = bd_per_year(self.returns)
        self.name=name

    def __str__(self):
        if self.name is None:
            r = "MWB Security: None" + "\n"
        else:
            r = "MWB Security: " + self.name+ "\n"
        df=pd.concat([self.prices, self.returns],axis=1)
        df.columns=["Prices", "Returns"]
        #r+=df.to_string()
        r+=df.head().to_string()
        r+="\n...\n"
        r+=df.tail().to_string(header=False, index_names=False)+"\n"
        return r


    def __max_drawdown(self):
        most_recent_high= last_high = last_low = list(self.prices.iteritems())[0]
        drawdown=0
        for p in self.prices.iteritems():
                if p[1] > most_recent_high[1]:
                        most_recent_high = p
                if p[1]/most_recent_high[1]-1 < drawdown:
                        drawdown=p[1]/most_recent_high[1]-1
                        last_high=most_recent_high
                        last_low = p
        if drawdown>=0:
            last_low=last_high
        return drawdown, last_high[0], last_low[0]

    def worst_window(self, nper):
        if self.prices.size<nper:
            return None
        worst_return = self.prices.iloc[0+nper-1]/self.prices.iloc[0] -1
        for i in range (1, self.prices.size-nper):
            if self.prices.iloc[i+nper-1]/self.prices.iloc[i]-1 < worst_return:
                worst_return = self.prices.iloc[i+nper-1]/self.prices.iloc[i]-1
        return worst_return
        
    
    def max_drawdown_size(self):
        return self.__max_drawdown()[0]

    def max_drawdown_dates(self):
        return self.__max_drawdown()[1:]

    def show_drawdowns(self, hurdle):
        most_recent_high= last_high = last_low = list(self.prices.iteritems())[0]
        drawdown=0
        drawdowns = []
        count=0
        while count in range(0,len(self.prices)):
                p = [self.prices.index[count], self.prices[count]]
                drawdowncount = count
                drawdown=0                     #reset drawdown measure
                while p[1]/most_recent_high[1]-1 < 0:  #Drawdown begins
                        p = [self.prices.index[drawdowncount], self.prices[drawdowncount]]
                        if p[1]/most_recent_high[1]-1 < drawdown:
                            drawdown = p[1]/most_recent_high[1]-1
                            last_low = p
                        count = drawdowncount
                        drawdowncount=drawdowncount+1    
                        if drawdowncount >= len(self.prices):
                            break
                last_high=most_recent_high
                if drawdown<hurdle:
                    drawdowns.append([last_high[0], last_low[0], drawdown])
                if p[1] > most_recent_high[1]:
                        most_recent_high = p
                count=count+1
        drawdowns = pd.DataFrame(data=drawdowns, columns = ["Start","End","Drawdown"])
        return drawdowns

    def all_time_high_date(self):
        return self.prices.idxmax()

    def historical_risk_stats(self):  #[mean, vol, sharpe]
        '''Returns [meanreturn, vol, sharpe].'''
        mean= (exp(self.returns.mean()*self.bd_per_year)-1)
        vol = (exp(self.returns.var()*self.bd_per_year)-1)
        return [mean, vol**0.5, mean/(vol**0.5)]

    def max_rolling_vol(self, lookback):
        '''Returns the maximum vol in any window with size equal to lookback.'''
        maxvol=0
        for n in range(lookback, len(self.returns)):
            vol = (exp(self.returns.iloc[n-lookback:n].var()*self.bd_per_year)-1)
            if vol>maxvol:
                maxvol=vol
        return maxvol**0.5

    def avg_daily_return(self):
        return self.returns.mean()

    def daily_stDev(self):
        return self.returns.std()

    def tracking_error(self, benchmark_prices):
        prices = pd.concat([benchmark_prices.prices, self.prices], axis=1)
        data = log(prices/prices.shift(1)).dropna(how="any")
        data = Security(data[0] - data[1])
        TE = data.historical_risk_stats()[1]
        return TE
        
    def return_table(self, from_year=None, to_year=None):
        if from_year is None:
            from_year=self.prices.index.min().year
        if to_year is None:
            to_year=self.prices.index.max().year

        table={}
        for y in range(from_year, to_year+1):
            ym=self.returns[self.returns.index.year==y]
            dat=["" for i in range(0,13)]
            for m in range(1,13):
                mm=ym[ym.index.month==m]
                if len(mm)!=0:
                    #print((exp(mm.cumsum())-1)[-1])
                    dat[m-1]='{:05.2f}'.format(((exp(mm.cumsum())-1)[-1])*100)+'%'
            if len(ym)!=0:
                dat[12]='{:05.2f}'.format(((exp(ym.cumsum())-1)[-1])*100)+'%'
            table[y]=pd.Series(data=dat ,index=[month_dict[n] for n in month_dict])
        return pd.DataFrame(data = table)

    def price_band(self, percentage_above):
        p = self.prices.sort_values(ascending=False)
        cut = int(round(len(p)*percentage_above,0))
        return (p.iloc[cut])
        
        
                
class Portfolio:
    def __init__(self, tickers, startDate, endDate, name=None):
        BBTickers = tickers[:,tickers[0]=="Bloomberg"][1]
        SQLTickers = tickers[:,tickers[0]=="Database"][1]
        #GenTickers = tickers[:,tickers[0]=="Generator"][1]
        try:
            dat = getPriceData(startDate, endDate, bloombergTickers=BBTickers, SQLTickers=SQLTickers, generatorTicker = None, peridiocity="DAILY", proxy_dict =None)
        except ValueError as err:
            messageBox=ctypes.windll.user32.MessageBoxW
            messageBox(None, err.args[0]+err.args[1], 'Data Error', 0)
            sys.exit()
        dat = dat.dropna(how="any")
        returns = log(dat/dat.shift(1))
        returns = returns.dropna(how="all")
        self.securities = {n : Security(returns[n],name=n) for n in returns.columns}

    def securities(self):
        return self.securities

