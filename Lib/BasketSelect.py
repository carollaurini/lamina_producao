import sys
#import json
import sjtools
from datetime import date, datetime
from DatabaseSelect import DatabaseSelect
#from BasketSelect_Engine import getBasketDict
from PyQt5.QtWidgets import QComboBox, QDialog, QApplication, QMainWindow
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QItemDelegate, QLineEdit
from PyQt5 import QtWidgets
import warnings
warnings.filterwarnings("ignore")
import matplotlib as matplot
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
warnings.filterwarnings("error")

class SmartCombo(QComboBox):
    def onChange(self,value):
        self.sibling.setText(value)
        self.sibling=QComboBox()

    def setSibling(self, sibling):
        self.sibling=sibling
        
    def __init__(self, sibling=None, filespath='./'):
        super(SmartCombo, self).__init__()
        self.setSibling(sibling)
        self.addItem("Bloomberg")
        self.addItem("Database")

class BasketSelect(QDialog):

    def getTableSize(self, table):  
        w = table.verticalHeader().width() + 4  # +4 seems to be needed
        for i in range(table.columnCount()):
            w += table.columnWidth(i)  # seems to include gridline (on my machine)
        h=self.contentsRect().height()
        return QSize(w, h)

    def createRow(self, passeddict=None):

        self.combo1 = QComboBox()
        self.combo1.addItem("Equity")
        self.combo1.addItem("Credit")
        self.combo1.addItem("Fixed Income")
        self.combo1.addItem("Hedge Fund")
        self.combo2 = SmartCombo()
        self.combo3 = SmartCombo()
        

        self.dict = { \
            "Name": QTableWidgetItem(), \
            "Class": self.combo1, \
            "Source": self.combo2, \
            "Ticker": QTableWidgetItem(), \
            "Weight": QTableWidgetItem(), \
            "Min allocation": QTableWidgetItem(), \
            "Max allocation": QTableWidgetItem(), \
            "Proxy source": self.combo3, \
            "Proxy ticker": QTableWidgetItem(),\
            "Divider" : QTableWidgetItem()}

        #self.combo3.setSibling(self.dict["Proxy ticker"])
        
        self.dict["Divider"].setText("1")
        self.dict["Weight"].setText("0")
        self.dict["Min allocation"].setText("0")
        self.dict["Max allocation"].setText("0")
        if passeddict:
            for n in ["Name", "Ticker", "Weight", "Min allocation","Max allocation", "Proxy ticker", "Divider"]:
                self.dict[n].setText(passeddict[n])
            for n in ["Class", "Source", "Proxy source"]:
                self.dict[n].setCurrentIndex(self.dict[n].findText(passeddict[n]))

        self.rows.append(self.dict)
        self.table.setItem(len(self.rows)-1, 0, self.rows[-1]["Name"])
        self.table.setCellWidget(len(self.rows)-1, 1, self.rows[-1]["Class"])
        self.table.setCellWidget(len(self.rows)-1, 2, self.rows[-1]["Source"])
        self.table.setItem(len(self.rows)-1, 3, self.rows[-1]["Ticker"])
        self.table.setItem(len(self.rows)-1, 4, self.rows[-1]["Weight"])
        self.table.setItem(len(self.rows)-1, 5, self.rows[-1]["Min allocation"])
        self.table.setItem(len(self.rows)-1, 6, self.rows[-1]["Max allocation"])
        self.table.setCellWidget(len(self.rows)-1, 7, self.rows[-1]["Proxy source"])
        self.table.setItem(len(self.rows)-1, 8, self.rows[-1]["Proxy ticker"])
        self.table.setItem(len(self.rows)-1, 9, self.rows[-1]["Divider"])


    def __init__(self, parent=None):
        super(BasketSelect, self).__init__(parent)

        self.setWindowTitle("Basket Selector")
        self.row_count = 1
        self.column_count = 9
        self.rows=[]
        self.header_labels=["Name","Class","Source","Ticker","Weight (0.0)","Min allocation","Max allocatiion","Proxy source","Proxy ticker","Divider"]
        self.create_widgets()
        
    def create_widgets(self):
        self.layout = QtWidgets.QHBoxLayout(self)
        self.table = QTableWidget(self.row_count, self.column_count, self)
        self.table.cellChanged.connect(self.cellChanged)

        for i in range(self.row_count):
            self.createRow()
        
        self.addRow_button = QtWidgets.QPushButton('Add Row', self)
        self.addRow_button.clicked.connect(self.addRow)
        self.addRow_button.setMaximumWidth(150)
        self.save_lineEdit = QtWidgets.QLineEdit()
        self.total_weight = QtWidgets.QLineEdit()
        self.save_button = QtWidgets.QPushButton('Save', self)
        self.save_button.clicked.connect(self.save)
        self.save_button.setMaximumWidth(150)
        self.database_button = QtWidgets.QPushButton('Database', self)
        self.database_button.clicked.connect(self.viewDatabase)
        self.database_button.setMaximumWidth(150)
        self.load_button = QtWidgets.QPushButton('Load', self)
        self.load_button.clicked.connect(self.load)
        self.load_button.setMaximumWidth(150)
        self.pie_button = QtWidgets.QPushButton('Pie chart', self)
        self.pie_button.clicked.connect(self.pieChart)
        self.pie_button.setMaximumWidth(150)
        self.ranges_button = QtWidgets.QPushButton('Ranges chart', self)
        self.ranges_button.clicked.connect(self.rangeChart)
        self.ranges_button.setMaximumWidth(150)
        self.ok_button = QtWidgets.QPushButton('OK', self)
        self.ok_button.setMaximumWidth(150)
        self.cancel_button = QtWidgets.QPushButton('Cancel', self)
        self.cancel_button.setMaximumWidth(150)
        self.comboBox = QtWidgets.QComboBox(self)
        self.baskets=sjtools.get_basket_names()
        self.comboBox.addItems(b for b in self.baskets)
        self.sublayout = QtWidgets.QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.addWidget(self.table)
        self.sublayout.setSpacing(10)
        self.sublayout.addWidget(self.comboBox)
        self.sublayout.addWidget(self.database_button, alignment=Qt.AlignHCenter)
        self.sublayout.addWidget(self.load_button, alignment=Qt.AlignHCenter)
        self.sublayout.addWidget(self.save_lineEdit)
        self.sublayout.addWidget(self.save_button, alignment= Qt.AlignHCenter)
        self.sublayout.addWidget(self.addRow_button, alignment= Qt.AlignHCenter)
        self.sublayout.addWidget(self.pie_button, alignment= Qt.AlignHCenter)
        self.sublayout.addWidget(self.ranges_button, alignment= Qt.AlignHCenter)
        self.sublayout.addWidget(self.ok_button, alignment= Qt.AlignHCenter)
        self.sublayout.addWidget(self.cancel_button, alignment=Qt.AlignHCenter)
        self.sublayout.addStretch(0)
        self.layout.addLayout(self.sublayout)
        self.table.setHorizontalHeaderLabels(self.header_labels)
        self.table.setMaximumSize(self.getTableSize(self.table))
        self.table.setMinimumSize(self.getTableSize(self.table))
        self.setLayout(self.layout)

    def readJson(self):
        return None #readJson(self.filespath)

    def save(self):
        if self.name()!="":
            self.baskets=sjtools.get_basket_names()
            self.comboBox.clear()
            self.comboBox.addItems(b for b in self.baskets)
            sjtools.save_basket(self.name(),datetime.now(),self.to_dict())
        return 0

    def load(self):
        while self.rows:
            self.deleteRow(0)
        dat=sjtools.load_basket(self.comboBox.currentText())
        for r in dat:
            self.addRow(r)
        self.save_lineEdit.setText(self.comboBox.currentText())

    def name(self):
        return str(self.save_lineEdit.text())

    def addRow(self, passeddict=None):
        rowPosition = self.table.rowCount()
        self.table.insertRow(rowPosition)
        self.createRow(passeddict)

    def deleteRow(self, rowNumber=0):
        self.rows.pop(rowNumber)
        self.table.removeRow(rowNumber)

    def rowString(self, row):

        thisdict = {'Name' : row["Name"].text(),\
                    'Class' : row["Class"].currentText(), \
                    'Source' : row["Source"].currentText(),\
                    'Ticker'  : row["Ticker"].text(), \
                    'Weight' : row["Weight"].text(), \
                    'Max allocation' : row["Max allocation"].text(), \
                    'Min allocation' : row["Min allocation"].text(), \
                    'Proxy source' : row["Proxy source"].currentText(),  \
                    'Proxy ticker' : row["Proxy ticker"].text(),
                    "Divider" : row["Divider"].text()}
        return thisdict

    def rowDict(self, row):

        thisdict = {'Name' : row["Name"].text(),\
                    'Class' : row["Class"].currentText(), \
                    'Source' : row["Source"].currentText(),\
                    'Ticker'  : row["Ticker"].text(), \
                    'Weight' : float(row["Weight"].text()), \
                    'Max allocation' : float(row["Max allocation"].text()), \
                    'Min allocation' : float(row["Min allocation"].text()), \
                    'Proxy source' : row["Proxy source"].currentText(),  \
                    'Proxy ticker' : row["Proxy ticker"].text(),
                    "Divider" : float(row["Divider"].text())}
        return thisdict

    def jsonRecord(self):
        ret = [self.rowString(r) for r in self.rows]
        ret =[r for r in ret if r['Name']!='']
        return ret

    def to_dict(self):
        ret = [self.rowDict(r) for r in self.rows]
        ret =[r for r in ret if r['Name']!='']
        return ret

    def pieChart(self):

        ret = [self.rowString(r) for r in self.rows]
        labels = [r["Name"] for r in ret if float(r["Weight"])>0]
        sizes = [float(r["Weight"])*100 for r in ret if float(r["Weight"])>0]
        for i in range(0,len(labels)):
            labels[i] = labels[i] + "\n{0:.1f}%".format(sizes[i])
        fig1= plt.figure()
        fig1.suptitle("Alocação Neutra")
        ax1 = fig1.add_subplot(1,1,1)
        ax1.pie(sizes, labels=labels) #autopct='%1.1f%%'
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        fig1.canvas.set_window_title("Pie chart")
        fig1.show()

    def rangeChart(self):
        import matplotlib.ticker as mticker

        ret = [self.rowString(r) for r in self.rows]
        results ={}
        for r in [x for x in ret if (float(x["Weight"])>0)]:
            results[r["Name"]] = [float(r["Min allocation"]), float(r["Weight"]),float(r["Max allocation"])]

        labels = list(results.keys())
        data = [[results[r][0],results[r][1], results[r][2]] for r in results]
        lefts = [d[0] for d in data]
        widths = [d[2]-d[0] for d in data]

        fig1=plt.figure()
        fig1.suptitle("Faixas de alocação")
        ax1=fig1.add_subplot(1,1,1)

        for i in range(0,len(labels)):        
            bar = ax1.barh(labels[i],widths[i],left=lefts[i], color="lightgray", height=0.20)
            ax1.plot(data[i][1],labels[i],'bo', label="Alocação neutra")
            #ax1.text(data[i][0]+0.005,i+0.16,"["+str(round(data[i][0]*100,1))+"%"+","+str(round(data[i][2]*100,1))+"%]")
            ax1.text(data[i][0]+0.005,i,"["+str(round(data[i][0]*100,1))+"%"+","+str(round(data[i][2]*100,1))+"%]")

        ax1.set_xlim(xmin=0, xmax=max(data)[1]+0.15)
        #vals = ax1.get_xticks()
        ticks_loc = ax1.get_xticks().tolist()
        ax1.xaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
        ax1.set_xticklabels(['{:,.1%}'.format(x) for x in ticks_loc])
        dot = mlines.Line2D([],[],color="white", marker='o', linewidth=0, markerfacecolor="blue")
        ax1.legend((bar,dot),("Faixa de alocação","Alocação neutra"), loc="upper center", bbox_to_anchor=(0.5,-0.05), ncol=2, frameon=False)
        fig1.canvas.set_window_title("Range chart")
        fig1.set_tight_layout(False)
        fig1.show()

    def viewDatabase(self):
        x = DatabaseSelect(self)
        x.show()
        
    def cellChanged(self, row, column):
        total=0
        if column==4:
            for r in self.rows:
                total+=float(self.rowDict(r)["Weight"])
            self.header_labels[4]="Weight ("+str(total)+")"
            self.table.setHorizontalHeaderLabels(self.header_labels)
        
           
def run(path=None):
    app = QApplication(sys.argv)
    if path is not None:
        sheet = BasketSelect(filespath=path)
    else:
        sheet = BasketSelect()

    def ok_clicked():
        sheet.close()
    def cancel_clicked():
        sheet.close()
        
    sheet.ok_button.clicked.connect(ok_clicked)
    sheet.cancel_button.clicked.connect(cancel_clicked)
    sheet.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    run()