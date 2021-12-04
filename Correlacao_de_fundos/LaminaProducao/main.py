
#Libs criadas
from MWB_data import function_extracao
import lamina
import dataprep
import graficos
import extracao_de_dados

#Libs do sistema
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
import datetime as dt
import time
from win32com.client import Dispatch
import win32com.client
import os
from datetime import datetime
#sys.path.insert(0,'p:\ciencia_de_dados\Correlacao_de_fundos\LaminaProducao')
#os.system("p:\venv\scripts\activate.bat")

## Front End
##df_array = []
##ticker_names = []
##while True:
##    
##        book_name,janela,ticker_array = function_extracao()
##        df = dataprep.function_dataprep(janela,book_name)
##        df_array.append(df)
##        
##        ticker_names = ticker_names + ticker_array #Somando arrays kkkk
##        
##        exite_var = input("Gostaria de extrair ativos em outra janela? (y/n)")
##        if exite_var == 'y':
##            continue
##        if exite_var == 'n':
##            break  
##        else:
##            print('Erro, tente novamente.')
##            quit()
##        
##nome_benchmark = input("Digite o nome do benchmark: ")
##print(nome_benchmark)
##
###Fundos sem o benchmark
##col_fundos_input =  [x for x in ticker_names if x != nome_benchmark]
##
##
##df = pd.concat(df_array)



arr_ativos = sys.argv[1].split(',')
arr_bench = sys.argv[2].split(',')
arr_fonte = sys.argv[3].split(',')
dt_min = sys.argv[4].split(',')
ano_base = sys.argv[5]

dt_min2 = [datetime.strptime(i, "%m/%d/%Y") for i in dt_min]

df_fonte = extracao_de_dados.f_extracao_de_dados(arr_ativos,arr_bench,arr_fonte,max(dt_min2),ano_base)
print(df_fonte)
print('fim')
df = dataprep.function_dataprep(df_fonte,12)


tempo = 12 


df1 = pd.read_csv('W:\\ciencia_de_dados\\Correlacao_de_fundos\\Bases\\IBOXHY Index_diaria.csv')
df2 = pd.read_csv('W:\\ciencia_de_dados\\Correlacao_de_fundos\\Bases\\book_pagaya_riverview_mensal.csv')

dff = pd.merge(df1,df2,left_on = 'Unnamed: 0',right_on='Unnamed: 0', how='left')
print(dff)

df = dataprep.function_dataprep(dff,12)
ticker_names = ['Pagaya Opportunity Fund','Riverview ALF','IBOXHY Index']
col_fundos_input = ['Pagaya Opportunity Fund','Riverview ALF']
nome_benchmark = "IBOXHY Index"


##  Lamina univariada
#Marcação dos pontos positivos e negativos
df['Retorno_Positivo'] = np.where(df.Retorno >= 0, 1, 0)
df['Retorno_Negativo'] = np.where(df.Retorno < 0, 1, 0)

#Reshape dataframe para algumas funções
df_sub = df.pivot(index=["data","Ano","Mes"], columns="Product", values="Retorno_1")
df_sub = df_sub.reset_index()
df_sub = df_sub.dropna()

#Calculo do tracking error  
df_sub1 = df_sub.apply(lambda x: lamina.function_tracking_error(x,df_sub,nome_benchmark) if x.name in col_fundos_input else x)
df_concat = pd.concat([df_sub, df_sub1[col_fundos_input].add_suffix('_spread')], axis=1, join="inner")
col_fundos_spread = df_concat.columns[3:]

df.sort_values(by=["Product",'data'],ascending=False,inplace=True)
table = df.groupby('Product').agg({"Retorno": ['max','min','mean',lambda y: lamina.vol_anualizada(y,tempo)] ,"Retorno_Negativo":lamina.Meses_Negativos,"Retorno_Positivo": lamina.Meses_Positivos,"Retorno_1" : [lamina.retorno_total, lambda x: lamina.retorno_anualizado(x,tempo)]})

table.columns = table.columns.droplevel(0)
table.columns = ["Retorno Mensal Máximo","Retorno Mensal Minimo", "Média dos Retornos Mensais",'Volatilidade Anualizada','Meses Negativos','Meses Positivos','Retorno Total','Retorno Anualizado']
table["Sharpe"] = (table["Retorno Anualizado"] / table["Volatilidade Anualizada"])

#Criando o DrawDown
df.sort_values(by=["Product",'data'],ascending=True,inplace=True)
table2 = df.groupby('Product').agg({"FinancialPrice":lamina.MDD}).rename(columns={"FinancialPrice":"Maximo Drawdown"})

#Adiciona o DrawDown na tabela principal
x=pd.concat([table,table2],axis=1)
df_univar = x.T
df_univar.index.name=lamina.Periodo(df.data)

#Data drawdown
df.sort_values(by=["Product",'data'],ascending=True,inplace=True)
v=[]
for i in df_univar.columns:
    print(i)
    v.append(lamina.periodo_MDD(df,i))
    
df_univar.loc['Período do DrawDown'] = [x for x in v]

##  Bivariada  
#Regressao:
k=0
v = []
for i in col_fundos_input:
    v.append(lamina.regressao_linear(df,i,nome_benchmark))

df_bivar = pd.DataFrame(v,index=col_fundos_input).rename(columns = {0:'Beta',1:'Alpha'}).T
df_bivar = df_bivar.reindex(sorted(df_bivar.columns), axis=1)

#Tracking Error:
v=[]
for i in col_fundos_input:
    v.append(np.std(df_sub1[i]))
df_bivar.loc['Tracking Error'] = [x for x in v]
df_bivar.index.name = ' '


##  Plotagem

#Porcentualizando os retornos para plotar os graficos
df_sub[ticker_names] = (df_sub[ticker_names] *100)-100

#Densidade
graficos.graf_densidade_retorno(df_sub[ticker_names])
#Matriz de Regressoes
df.reset_index()
graficos.graf_linear_reg(df)
#Matriz das correlacoes 

graficos.graf_correlacao(df_sub[ticker_names])

##################################################################################################################################################  Escrevendo no Excel

# Create a Pandas Excel writer using XlsxWriter as the engine.


writer = pd.ExcelWriter('.\Laminas\Lamina.xlsx', engine='xlsxwriter')
workbook = writer.book
worksheet = workbook.add_worksheet('Sumario')
options = {
    'width': 256,
    'height': 100,
    'x_offset': 10,
    'y_offset': 10,

    'font': {'color': 'white',
             'size': 20},
    'align': {'vertical': 'middle',
              'horizontal': 'center'
              },
    'gradient': {'colors': ['#3E9EBC',
                            '#2F778D',
                            ]},
}
options2 = {
    'width': 200,
    'height': 20,
    'x_offset': 10,
    'y_offset': 10,

    'font': {'color': 'white',
             'size': 10},
    'align': {'vertical': 'middle',
              'horizontal': 'center'
              },
    'gradient': {'colors': ['#800000',
                            '#800000',
                            ]},
}
options3 = {
    'width': 200,
    'height': 20,
    'x_offset': 10,
    'y_offset': 10,

    'font': {'color': 'white',
             'size': 10},
    'align': {'vertical': 'middle',
              'horizontal': 'center'
              },
    'gradient': {'colors': ['#3E9EBC',
                            '#2F778D',
                            ]},
}



worksheet.insert_textbox('B2', 'Lâmina',options)
writer.sheets['Sumario'] = worksheet


spread_names = [s for s in df_concat.columns[3:] if 'spread' in s]
#Tabela de retornos coloridos

table_size = len(df.Ano.unique()) + 4

const = 12

def highlight_cells():
    # provide your criteria for highlighting the cells here
    return ['background-color: #EAEAEA']

df_concat.style.apply(highlight_cells)
for i in range(len(col_fundos_spread)):
    lamina.function_retorno(df_concat,i,const,col_fundos_spread).to_excel(writer,sheet_name = 'Sumario',startrow=(8 + table_size*i), startcol=1,index_label='Retorno')
    if col_fundos_spread[i] in spread_names:
        worksheet.insert_textbox('C'+ str((8 + table_size*i)), 'Spread do Retorno',options2)
    else:    
        worksheet.insert_textbox('C'+ str((8 + table_size*i)), 'Retorno',options3)
    
#Graficos
i+=1
worksheet.insert_image('B'+ str((10 + table_size*i)),'.\Graficos\PairplotRegressaoLin.png')
worksheet.insert_image('S'+ str((8+ len(df_univar)+10)),'.\Graficos\Retorno_density_distribution.png')
worksheet.insert_image('U'+ str((8+ len(df_univar)+10)) ,'.\Graficos\CorrelationMatrix.png')#,{'x_scale': 2, 'y_scale': 2})    




#Tabelas com os resultados
df_univar = df_univar.reindex(sorted(df_univar.columns), axis=1)
first_column = df_univar.pop(nome_benchmark)
df_univar.insert(len(df_univar.columns), nome_benchmark, first_column)

df_univar.loc['Retorno Mensal Máximo'] = df_univar.loc['Retorno Mensal Máximo'].apply('{:.2%}'.format)
df_univar.loc['Retorno Mensal Minimo'] = df_univar.loc['Retorno Mensal Minimo'].apply('{:.2%}'.format)
df_univar.loc['Média dos Retornos Mensais'] = df_univar.loc['Média dos Retornos Mensais'].apply('{:.2%}'.format)
df_univar.loc['Volatilidade Anualizada'] = df_univar.loc['Volatilidade Anualizada'].apply('{:.2%}'.format)
df_univar.loc['Retorno Total'] = df_univar.loc['Retorno Total'].apply('{:.2%}'.format)
df_univar.loc['Retorno Anualizado'] = df_univar.loc['Retorno Anualizado'].apply('{:.2%}'.format)
df_univar.loc['Maximo Drawdown'] = df_univar.loc['Maximo Drawdown'].apply('{:.2%}'.format)
df_univar.loc['Sharpe'] = df_univar.loc['Sharpe'].apply('{:.2f}'.format)




df_bivar.loc['Beta'] = df_bivar.loc['Beta'].apply('{:.2f}'.format)
df_bivar.loc['Alpha'] = df_bivar.loc['Alpha'].apply('{:.2f}'.format)
df_bivar.loc['Tracking Error'] = df_bivar.loc['Tracking Error'].apply('{:.2%}'.format)

df_univar.to_excel(writer, sheet_name='Sumario',startrow=8,startcol = 18)
df_bivar.to_excel(writer, sheet_name='Sumario',startcol=18,startrow = (8+ len(df_univar)+2))


#Formatacao
format_dict={"number": writer.book.add_format({'num_format': '0.0','align':'center', 'valign':'vcenter'}),
            "percentage_one_decimal" : writer.book.add_format({'num_format': '0.0%','align':'center', 'valign':'vcenter'}),
            "paint_blank_cell": writer.book.add_format(),
            "centro": writer.book.add_format({'align':'center', 'valign':'vcenter'})}


format_dict['percentage_one_decimal'].set_bg_color('#EAEAEA') 

writer.sheets['Sumario'].set_column(17, 30, 30)
writer.sheets['Sumario'].set_column('N:P', 15,format_dict["percentage_one_decimal"])
writer.sheets['Sumario'].set_column('A:M',10,format_dict["percentage_one_decimal"])

format_dict["paint_blank_cell"].set_bg_color('#EAEAEA')
format_dict["paint_blank_cell"].set_right(1)

writer.sheets['Sumario'].set_column('Q:Q', 10,format_dict["paint_blank_cell"])

format_dict["centro"].set_bg_color('#FFFFFF') 
writer.sheets['Sumario'].set_column('R:BB', 40,format_dict["centro"])



df_sub.to_excel(writer,sheet_name = 'UnstackRetornosPercentuais')
df.to_excel(writer, sheet_name='StackRetornos1')



writer.save()


xl = Dispatch("Excel.Application")
xl.Visible = True # otherwise excel is hidden
print(os.getcwd())
# newest excel does not accept forward slash in path
wb = xl.Workbooks.Open(os.getcwd()+'\Laminas\Lamina.xlsx')
print('Fim')

