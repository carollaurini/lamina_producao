import sys
import os
import pandas as pd
import sklearn 
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import numpy as np
from sklearn import feature_selection
import seaborn as sns
import scipy.stats
from matplotlib import pyplot as plt
import math
import openpyxl
from  matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
import xlsxwriter
from sklearn import feature_selection
import datetime

def function_tracking_error(x,df,nome_benchmark):
    print(x.name)
    return (x.div(df[nome_benchmark]))#divisao entre o o retorno do fundo com o do benchmark

def periodo_MDD(df,x):
    data_x = df[df.Product == x]
    data_x.loc[:,'dd'] = ((data_x.FinancialPrice/data_x.FinancialPrice.cummax(skipna=True))-1)
    data_x.loc[:,'picos'] = data_x.FinancialPrice.cummax()
    
    index_picos = data_x[(data_x.FinancialPrice== data_x.FinancialPrice.cummax())].reset_index()[['index','FinancialPrice','MesAno']]
    
    mdd = pd.merge(data_x.reset_index(),index_picos,left_on = 'picos',right_on='FinancialPrice', how='left')
    
    data_pico = mdd[mdd.dd == min(mdd.dd[mdd.Product == x])].MesAno_y.values[0]
    data_ref = mdd[mdd.dd == min(mdd.dd[mdd.Product == x])].MesAno_x.values[0]
    
    if data_pico == data_ref:
        return np.NaN
    return  data_pico + ' a '+ data_ref

#Tabela de Retorno Mensal 
def function_retorno(df,i,const,col_fundos):

    pivot_table = pd.pivot_table(df,index=['Ano'],values=[col_fundos[i]],fill_value=1,aggfunc='prod',columns=['Mes'])#,margins=True,margins_name="Year")
    pivot_table=pivot_table.rename(columns={1: 'Jan', 2:"Feb",3:"Mar", 4:"Apr", 5:"May", 6:"Jun",7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"})
    
    ITD_Matrix = [df[df.Ano <= i_ano][col_fundos[i]].prod() for i_ano in df.Ano.unique()]
    YTD_Matrix = [df[df.Ano == i_ano][col_fundos[i]].prod() for i_ano in df.Ano.unique()]
    
    ITD_df=pd.DataFrame(ITD_Matrix, columns = [col_fundos[i]] ,index=df.Ano.unique())
    YTD_df=pd.DataFrame(YTD_Matrix, columns = [col_fundos[i]] ,index=df.Ano.unique())
    
    ITD_df.columns = pd.MultiIndex.from_product([ITD_df.columns, ['Retorno LTD']])
    YTD_df.columns = pd.MultiIndex.from_product([YTD_df.columns, ['Retorno YTD']])
    
    pivot_table = pd.concat([pivot_table,YTD_df,ITD_df],axis=1)
    pivot_table = pivot_table-1
    
    # backgroung color mapping
    my_cmap=LinearSegmentedColormap.from_list('rg',["r", "w", "g"], N=256)
    pivot_table.index.name="Retorno Mensal"
  
    return pivot_table

def vol_anualizada(x,tempo):
    z = x.std() * (tempo**(1/2))
    return z

def retorno_anualizado(x,tempo):
    return (x.product()**(tempo/float(x.count())) - 1)

def MDD(x):
    return min(((x/x.cummax()) - 1))

def retorno_total(x):
    return (x.prod() - 1)

def Meses_Positivos(x): #Gambiarra para nomear sum
    return x.sum()

def Meses_Negativos(x):
    return x.sum()

def Periodo(x):
    return datetime.datetime.strptime(str(min(x)), '%Y-%m-%d %H:%M:%S').strftime('%b-%Y') +' a ' + datetime.datetime.strptime(str(max(x)), '%Y-%m-%d %H:%M:%S').strftime('%b-%Y')

def regressao_linear(df,nome_do_fundo,nome_benchmark): 
    df['Retorno100'] = df['Retorno']*100
    df_fundo = df.loc[df.Product == nome_do_fundo,['data','Retorno100']]
    df_bench = df.loc[df.Product == nome_benchmark,['data','Retorno100']]

    df_fundo.index = df_fundo['data']
    df_bench.index = df_bench['data']
    df_join =pd.merge(df_bench, df_fundo,how='inner',left_index=True, right_index=True).dropna()[['Retorno100_x','Retorno100_y']]

    #Regressao Linear total
    x = (df_join['Retorno100_x']).values.reshape((-1, 1))
    y= (df_join['Retorno100_y']).values.reshape((-1, 1))
    
    regr = sklearn.linear_model.LinearRegression()
    regr.fit(x, y)
    return regr.coef_[0][0],regr.intercept_[0]
