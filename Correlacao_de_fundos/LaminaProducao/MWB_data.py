import sys
sys.path.insert(0,'p:/Lib')
from MWB_Data_Reader import bd_per_year, BasketHistoricalData
from datetime import datetime

def function_extracao():
    """
        basket_array is an array of dictionaries with the following fields
        {"Ticker" : ttt, "Source" : "Bloomberg"/"Databate"/"GoogleTrends",
          "Proxy ticker" : 'FOCUS GENERATION-J', "Proxy source" : "Bloomberg"/"Databate"/"GoogleTrends"}
          Proxy ticker is optional
    """
    basket_array = []
    exite_var = 'y'
    ticker_array = []
    print('\n\n ATENCAO: As series de precos de cada fundo devem possuir a mesma janela de tempo, caso contrario, extraia em dois ou mais arquivos diferentes')
    janela = input("Digite a janela: (diaria, semanal ou mensal)")
    book_name = input("Digite o nome da base de saida: ")
    flag=True

    while flag==True:
      try:
        min_d = input('Digite a data inicial (aaa-mm-dd):')
        min_d = datetime.strptime(min_d, "%Y-%m-%d")
        max_d = input('Digite a data final (aaa-mm-dd):')
        max_d = datetime.strptime(max_d, "%Y-%m-%d")
        flag = False
      except:
        print('Tente novamente')
        pass # doing nothing on exception


    while True:
      try:
        # block raising an exception
        if exite_var != 'y':
          break
        ticker = input("Digite o ticker do fundo:")
        ticker_array.append(ticker)
        print("Exemplos de fontes: 'Bloomberg/Databate/GoogleTrends' ou 'Database' , onde Database eh a chave para o banco de dados SQL")
        source = input("Digite a fonte:")
        dicionario = {'Ticker' : ticker,"Source": source}
        basket_array.append(dicionario)
        exite_var = input("Deseja extrair outro fundo? (y/n)")
      except:
        print('Tente novamente')
        pass # doing nothing on exception

    data = BasketHistoricalData("Nome", basket_array)
    data.loadFromDatabase(min_d, max_d)
    prices=data.getData(dropna=False, useproxies=True)
    print(prices)

    prices.to_csv('P:\\ciencia_de_dados\\Correlacao_de_fundos\\LaminaProducao\\bases\\bases_extraidas\\'+ book_name +'_' + janela +'.csv')
    return book_name,janela,ticker_array
