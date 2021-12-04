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

def graf_densidade_retorno(df):
    sns.pairplot(data=df,kind="reg",plot_kws={'line_kws':{'color':'red','lw':1},'scatter_kws': {'s': 3}},corner= True)
    plt.savefig('.\Graficos\PairplotRegressaoLin.png')
    plt.close()
    
def graf_linear_reg(df):
    sns.kdeplot(data=df,x = 'Retorno',hue = 'Product',fill=True)
    plt.savefig('.\Graficos\Retorno_density_distribution.png')
    plt.close()
    
def graf_correlacao(df):
    corr = df.corr()

    ax = sns.heatmap(
        corr,
        annot=True, 
        vmin=-1, vmax=1, center=0,
        square=True,
        cmap=sns.diverging_palette(20, 220, n=200)
        )

    ax.set_xticklabels(
        ax.get_xticklabels(),
        rotation=45,
        horizontalalignment='right'
    );
    plt.tight_layout()
    plt.savefig( '.\Graficos\CorrelationMatrix.png',dpi=200)
    plt.close()
