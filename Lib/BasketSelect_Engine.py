#import json
import logging
import sjtools

"""
def readJson(basketname):

    try:
        #json_file = open(filespath+'baskets.json')
        #raw_data = json.load(json_file)
        #raw_data=sjtools.loadJSON("baskets","baskets.json")
        raw_data=sjtools.load_basket(basketname)
        data={}
        for i in sorted(raw_data.keys()):
            data[i] = raw_data[i]

        for b in data:
            for i in data[b]:
                if "Weight" not in i.keys():
                    i["Weight"]="0"
                if "Min allocation" not in i.keys():
                    if "Allocation range" in i.keys():
                        i["Min allocation"] = str(float(i["Weight"])-float(i["Allocation range"]))
                    else:
                        i["Min allocation"] = i["Weight"]
                if "Max allocation" not in i.keys():
                    if "Allocation range" in i.keys():
                        i["Max allocation"] = str(float(i["Weight"])+float(i["Allocation range"]))
                    else:
                        i["Max allocation"] = i["Weight"]
                
        #json_file.close()
        
    except FileNotFoundError:
        data={}
    return data
"""

def getBasketDict(basketname):
    dic=sjtools.load_basket(basketname)
    #if basketname in data.keys():
    #    dic=data[basketname]
    #else:
    #    logging.warning("Could not load basket: "+basketname)
    #    dic={}
    return dic
