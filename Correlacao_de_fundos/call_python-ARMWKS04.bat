path = p:\blpapi;p:\sjpython\scripts\;%PATH%
SET PYTHONPATH = p:\lib;p:\blpapi
call p:\sjpython\scripts\activate.bat
p:

cd p:\ciencia_de_dados\Correlacao_de_fundos\LaminaProducao

python main.py %1 %2 %3 %4 %5
pause
