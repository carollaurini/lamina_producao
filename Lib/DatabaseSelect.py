from PyQt5.QtWidgets import *
from PyQt5.Qt import QClipboard, QApplication
import sys
#import pyodbc
#pip install pymysql
import pymysql.cursors
import pymysql
import logging


class ReadDatabase():
    def __init__(self, isFlagship = True, isStaleAfter = 12):
        super(ReadDatabase,self).__init__()
        
        #self.conn_str = (
        #r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        #r'DBQ=//192.168.40.4/data$/Hedge Funds/HedgeFunds.accdb;'
        #)
        log = logging.getLogger("ReadDatabase.__init()__")
        log.debug("Trying to connect to database")
        try:
            mydb = pymysql.connect(
            host="192.168.40.4",
            user="armory",
            passwd="19qd$SD#",
            charset='utf8mb4',
            database="HedgeFunds",
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor)
            log.debug("Connected to database")

            with mydb.cursor() as cursor:
                select_stmt = "SELECT Product, Monthcount FROM FundHistoryLength WHERE Dataage < "+str(isStaleAfter)
                if isFlagship is True:
                    select_stmt +=" AND (IsFlagship=1)"
                select_stmt += " ORDER BY product;"
                log.debug(select_stmt)
                cursor.execute(select_stmt)
                rows = cursor.fetchall()
            log.debug("Loaded: "+str(len(rows))+" rows")
        except:
            msg=QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Error acessing HedgeFunds database")
            msg.setInformativeText("Check ReadDatabase.__init()__\nfrom file \Python\Lib\DatabaseSelect.py")
            msg.setWindowTitle("Database error")
            #msg.setDetailedText("The details are as follows:")
            msg.exec_()
            rows=[]
        self.data=[]
        for r in rows:
            self.data.append([r[i] for i in r.keys()])

    

class DatabaseSelect(QDialog):

    def LoadItems(self, items):
        self.listwidget.setColumnCount(2)
        self.listwidget.setMinimumWidth(450)
        self.listwidget.setColumnWidth(0,350)
        self.listwidget.setColumnWidth(1,50)
        self.listwidget.setHorizontalHeaderItem(0,QTableWidgetItem("Name"))
        self.listwidget.setHorizontalHeaderItem(1,QTableWidgetItem("Months"))
        
        self.listwidget.setRowCount(len(items))
        #self.listwidget = QTableWidget(len(items),2)
        for n,d in enumerate(items):
            self.listwidget.setItem(n,0,QTableWidgetItem(d[0]))
            y= QTableWidgetItem(str(d[1]))
            self.listwidget.setItem(n,1,y)
        self.listwidget.update()
        #self.repaint()

    def Clicked(self, item):
        self.clipboard.setText(item.text())
        self.statusBar.showMessage("Copied to clipboard",1000)

    def Refresh(self):
        self.listwidget.clear()
        if self.checkbox_includestale.isChecked() is True:
            self.LoadItems(ReadDatabase(isFlagship=self.checkbox_isflagship.isChecked(), isStaleAfter=2400).data)
        else:
            self.LoadItems(ReadDatabase(isFlagship=self.checkbox_isflagship.isChecked()).data)

    def __init__(self, parent=None):
        super(DatabaseSelect, self).__init__(parent)
        self.setWindowTitle("Database Funds")
        self.rows=[]
        #data=ReadDatabase().data
        self.layout=QVBoxLayout(self)
        self.setLayout(self.layout)
        self.checkbox_row = QHBoxLayout(self)
        self.checkbox_isflagship = QCheckBox("Flagship only")
        self.checkbox_includestale = QCheckBox("Include stale")
        self.checkbox_isflagship.setChecked(True)
        self.checkbox_includestale.setChecked(False)
        self.pushbutton_refresh=QPushButton("Refresh")
        self.checkbox_row.addWidget(self.checkbox_isflagship)
        self.checkbox_row.addWidget(self.checkbox_includestale)
        self.checkbox_row.addWidget(self.pushbutton_refresh)
        self.listwidget = QTableWidget()
        
        self.listwidget.itemClicked.connect(self.Clicked)
        self.pushbutton_refresh.clicked.connect(self.Refresh)
        self.statusBar=QStatusBar()
        self.LoadItems(ReadDatabase().data)
            
        self.layout.addLayout(self.checkbox_row)
        self.layout.addWidget(self.listwidget)
        self.layout.addWidget(self.statusBar)
        self.clipboard= QApplication.clipboard()
        
        
def run():
    app = QApplication(sys.argv)
    sheet = DatabaseSelect()
    sheet.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    run()
    logging.basicConfig(level=logging.DEBUG)
#run()
