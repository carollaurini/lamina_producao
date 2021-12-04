import pymysql
import json

table_dict = {"basketsimulations" : "SimulationName",
              "baskets" : "BasketName"}

def get_db(autocommit = True):
    host = "192.168.40.4"
    mydb = pymysql.connect(
            host=host,
            user="armory",
            passwd="19qd$SD#",
            charset='utf8mb4',
            database="sjtools",
            autocommit=autocommit,
            cursorclass=pymysql.cursors.DictCursor)
    return mydb

def saveJSON(table,key_name,dt,json_dict):
    db=get_db()
    crsr=db.cursor()
    select_stmt = ("INSERT INTO "+table+" ("+table_dict[table]+ ",SaveDate,JSON) "
                       "VALUES ('"+key_name+"','"+dt.strftime("%Y-%m-%d %H:%M:%S")+"','"+json.dumps(json_dict)+"') "
                       "ON DUPLICATE KEY UPDATE SaveDate='"+dt.strftime("%Y-%m-%d %H:%M:%S")+"', JSON= '"+json.dumps(json_dict)+"';")
    crsr.execute(select_stmt)       
    db.close()      

def loadJSON(table,key_name):
    db=get_db()
    crsr=db.cursor()
    select_stmt = "SELECT JSON FROM "+table+" WHERE "+table_dict[table]+"='"+key_name+"';"
    crsr.execute(select_stmt)       
    row = crsr.fetchone()
    json_dict=json.loads(row["JSON"])
    db.close()      
    return json_dict
"""
Name' : row["Name"].text(),
                    'Class' : row["Class"].currentText(), 
                    'Source' : row["Source"].currentText(),
                    'Ticker'  : row["Ticker"].text(), 
                    'Weight' : row["Weight"].text(), 
                    'Max allocation' : row["Max allocation"].text(), 
                    'Min allocation' : row["Min allocation"].text(), 
                    'Proxy source' : row["Proxy source"].currentText(),  
                    'Proxy ticker' : row["Proxy ticker"].text(),
                    "Divider" : row["Divider"].text()}
"""
def save_basket(name, dt, members):
    db=get_db(False)
    crsr=db.cursor()
    select_stmt = "DELETE FROM Baskets WHERE BasketName = '"+name+"';"
    crsr.execute(select_stmt)
    select_stmt = "INSERT INTO Baskets (BasketName, SaveDate) VALUES('"+name+"','"+dt.strftime("%Y-%m-%d %H:%M:%S")+"');"
    crsr.execute(select_stmt)
    select_stmt = "INSERT INTO BasketMembers VALUES "
    values=""
    for m in members:
        values += "("
        values +="'"+name+"',"
        values +="'"+m["Name"]+"',"
        values +="'"+m["Class"]+"',"
        values +="'"+m["Source"]+"',"
        values +="'"+m["Ticker"]+"',"
        values +=str(m["Weight"])+","
        values +=str(m["Divider"])+","
        values +="'"+m["Proxy source"]+"',"
        values +="'"+m["Proxy ticker"]+"',"
        values +=str(m["Min allocation"])+","
        values +=str(m["Max allocation"])+"),"
    values=values[:-1]+";"
    select_stmt+=values
    crsr.execute(select_stmt)
    db.commit()
    db.close

def load_basket(name):
    db=get_db()
    crsr=db.cursor()
    select_stmt = "SELECT * FROM BasketMembers WHERE BasketName = '"+name+"';"
    crsr.execute(select_stmt)
    
    rows = crsr.fetchall()
    ret=[]
    for r in rows:
        d = {"Name"   :r["MemberName"],
             "Class"  :r["Class"],
             "Source" :r["Source"],
             "Ticker" :r["Ticker"],
             "Weight" :str(r["Weight"]),
             "Max allocation": str(r["Max_weight"]),
             "Min allocation": str(r["Min_weight"]),
             "Proxy source"  : r["Proxy_source"],
             "Proxy ticker"  : r["Proxy_ticker"],
             "Divider"       : str(r["Divider"])
        }
        ret.append(d)
    db.close
    return ret

def load_all_baskets():
    db=get_db()
    crsr=db.cursor()
    select_stmt = "SELECT * FROM BasketMembers;"
    crsr.execute(select_stmt)
    rows = crsr.fetchall()
    ret_dict={}
    for r in rows:
        d = {"Name"   :r["MemberName"],
             "Class"  :r["Class"],
             "Source" :r["Source"],
             "Ticker" :r["Ticker"],
             "Weight" :str(r["Weight"]),
             "Max allocation": str(r["Max_weight"]),
             "Min allocation": str(r["Min_weight"]),
             "Proxy source"  : r["Proxy_source"],
             "Proxy ticker"  : r["Proxy_ticker"],
             "Divider"       : str(r["Divider"])
        }
        if r["BasketName"] not in ret_dict.keys():
            ret_dict[r["BasketName"]]=[]
        ret_dict[r["BasketName"]].append(d)
    db.close
    return ret_dict

def get_basket_names():
    db=get_db()
    crsr=db.cursor()
    select_stmt = "SELECT BasketName FROM baskets ORDER BY BasketName;"
    crsr.execute(select_stmt)
    rows = crsr.fetchall()
    ret=[x["BasketName"] for x in rows]
    return ret

