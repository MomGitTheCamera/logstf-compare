import os
import requests
import json
import csv
from urllib.parse import urlparse

#build:
#pyinstaller --onefile --hidden-import queue --hidden-import urllib3 spreadsheetifyer.py

def main():
    __location__ = os.path.realpath( os.path.join(os.getcwd(), os.path.dirname(__file__)))

    f = open(os.path.join(__location__, 'logs.txt'))
    logURLs = f.readlines()

    IDset = set()
    for line in logURLs:
        IDset.add(str(urlparse(line).path))

    statsDict = dict()
    classNumDict = {'scout' : 0, 'soldier' : 1, 'pyro' : 2, 'demoman' : 3, 'heavyweapons' : 4, 'medic' : 5, 'engineer' : 6, 'sniper' : 7, 'spy' : 8}
    for ID in IDset:
        logData = get_log(ID[1:])

        for steamID, nameUsed in logData['names'].items():
            statsDict = addNewToDict(statsDict, steamID)
            statsDict[steamID][9]['names'].append(nameUsed)

            playerData = logData['players'][steamID]
            playerClassStats = logData['players'][steamID]['class_stats']

            for classPlayed in playerClassStats:
                className = classPlayed['type']
                classNum = classNumDict[className]
                classStats = statsDict[steamID][classNum][className]

                classStats['gp'] += 1
                classStats['time'] += classPlayed['total_time']
                classStats['kills'] += classPlayed['kills']
                classStats['assists'] += classPlayed['assists']
                classStats['deaths'] += classPlayed['deaths']
                classStats['damage'] += classPlayed['dmg']

                if className == 'sniper' or className == 'spy':
                    classStats['headshots'] += playerData['headshots_hit']

                if className == 'spy':
                    classStats['backstabs'] += playerData['backstabs']
                elif className == 'soldier' or className == 'pyro' or className == 'demoman':
                    classStats['as'] += playerData['as']
                elif className == 'medic':
                    classStats['healing'] += logData['players'][steamID]['heal']
                    classStats['ubers'] += playerData['ubers']
                    classStats['drops'] += playerData['drops']

    toCSV(statsDict, classNumDict)
    f.close()
    print("Finished")

def toCSV(statsDict, classNumDict):
    for className, i in classNumDict.items():
        with open('stats_' + className + '.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)

            topRow = returnTopRow(className)
            writer.writerow(topRow)
            for steamID, datalist in statsDict.items():
                name = selectName(statsDict[steamID][9]['names'])
                data = datalist[i][className]
                if data['time'] > 0:
                    classRow = returnClassRow(className, name, data)
                    writer.writerow(classRow)
        csvfile.close()

def returnTopRow(className):
    topRowDict = {'scout' : ['Name', 'GP', 'Time played', 'Kills', 'K/M', 'Assists', 'A/M', 'Deaths', 'D/M', 'Damage', 'DA/M', 'KA/D', 'K/D'],
    'soldier' : ['Name', 'GP', 'Time played', 'Kills', 'K/M', 'Assists', 'A/M', 'Deaths', 'D/M', 'Damage', 'DA/M', 'KA/D', 'K/D', 'AS', 'AS/M'],
    'pyro' : ['Name', 'GP', 'Time played', 'Kills', 'K/M', 'Assists', 'A/M', 'Deaths', 'D/M', 'Damage', 'DA/M', 'KA/D', 'K/D', 'AS', 'AS/M'],
    'demoman' : ['Name', 'GP', 'Time played', 'Kills', 'K/M', 'Assists', 'A/M', 'Deaths', 'D/M', 'Damage', 'DA/M', 'KA/D', 'K/D', 'AS', 'AS/M'],
    'heavyweapons' : ['Name', 'GP', 'Time played', 'Kills', 'K/M', 'Assists', 'A/M', 'Deaths', 'D/M', 'Damage', 'DA/M', 'KA/D', 'K/D', 'DT', 'DT/M'],
    'medic' : ['Name', 'GP', 'Time played', 'Kills', 'K/M', 'Assists', 'A/M', 'Deaths', 'D/M', 'Damage', 'DA/M', 'KA/D', 'K/D', 'Healing', 'Ubers', 'Drops'],
    'engineer' : ['Name', 'GP', 'Time played', 'Kills', 'K/M', 'Assists', 'A/M', 'Deaths', 'D/M', 'Damage', 'DA/M', 'KA/D', 'K/D'],
    'sniper' : ['Name', 'GP', 'Time played', 'Kills', 'K/M', 'Assists', 'A/M', 'Deaths', 'D/M', 'Damage', 'DA/M', 'KA/D', 'K/D', 'HS'],
    'spy' : ['Name', 'GP', 'Time played', 'Kills', 'K/M', 'Assists', 'A/M', 'Deaths', 'D/M', 'Damage', 'DA/M', 'KA/D', 'K/D', 'HS', 'BS']}

    return topRowDict[className]

def returnClassRow(className, name, data):
    timestring, minutes = formatTime(data['time'])

    classRowDict = {'scout' : ("[name, data['gp'], timestring, data['kills'],"
                                "data['kills'] / minutes, data['assists'], data['assists'] / minutes,"
                                "data['deaths'], data['deaths'] / minutes, data['damage'],"
                                "data['damage'] / minutes, (data['kills'] + data['assists']) / data['deaths'],"
                                "data['kills'] / data['deaths']]"),

    'soldier' : ("[name, data['gp'], timestring, data['kills'],"
                "data['kills'] / minutes, data['assists'], data['assists'] / minutes,"
                "data['deaths'], data['deaths'] / minutes, data['damage'], data['damage'] / minutes,"
                "(data['kills'] + data['assists']) / data['deaths'], data['kills'] / data['deaths'],"
                "data['as'], data['as'] / minutes]"),

    'pyro' : ("[name, data['gp'], timestring, data['kills'],"
                "data['kills'] / minutes, data['assists'], data['assists'] / minutes,"
                "data['deaths'], data['deaths'] / minutes, data['damage'], data['damage'] / minutes,"
                "(data['kills'] + data['assists']) / data['deaths'], data['kills'] / data['deaths'],"
                "data['as'], data['as'] / minutes]"),

    'demoman' : ("[name, data['gp'], timestring, data['kills'],"
                "data['kills'] / minutes, data['assists'], data['assists'] / minutes,"
                "data['deaths'], data['deaths'] / minutes, data['damage'], data['damage'] / minutes,"
                "(data['kills'] + data['assists']) / data['deaths'], data['kills'] / data['deaths'],"
                "data['as'], data['as'] / minutes]"),

    'heavyweapons' : ("[name, data['gp'], timestring, data['kills'],"
                    "data['kills'] / minutes, data['assists'], data['assists'] / minutes,"
                    "data['deaths'], data['deaths'] / minutes, data['damage'], data['damage'] / minutes,"
                    "(data['kills'] + data['assists']) / data['deaths'], data['kills'] / data['deaths'],"
                    "data['dt'], data['dt'] / minutes]"),

    'medic' : ("[name, data['gp'], timestring, data['kills'],"
            "data['kills'] / minutes, data['assists'], data['assists'] / minutes,"
            "data['deaths'], data['deaths'] / minutes, data['damage'], data['damage'] / minutes,"
            "(data['kills'] + data['assists']) / data['deaths'], data['kills'] / data['deaths'],"
            "data['healing'], data['ubers'], data['drops']]"),

    'engineer' : ("[name, data['gp'], timestring, data['kills'],"
                "data['kills'] / minutes, data['assists'], data['assists'] / minutes,"
                "data['deaths'], data['deaths'] / minutes, data['damage'],"
                "data['damage'] / minutes, (data['kills'] + data['assists']) / data['deaths'],"
                "data['kills'] / data['deaths']]"),

    'sniper' : ("[name, data['gp'], timestring, data['kills'],"
            "data['kills'] / minutes, data['assists'], data['assists'] / minutes, data['deaths'],"
            "data['deaths'] / minutes, data['damage'], data['damage'] / minutes,"
            "(data['kills'] + data['assists']) / data['deaths'], data['kills'] / data['deaths'], data['headshots']]"),

    'spy' : ("[name, data['gp'], timestring, data['kills'], "
            "data['kills'] / minutes, data['assists'], data['assists'] / minutes,"
            "data['deaths'], data['deaths'] / minutes, data['damage'], data['damage'] / minutes,"
            "(data['kills'] + data['assists']) / data['deaths'], data['kills'] / data['deaths'],"
            "data['headshots'], data['backstabs']]")}

    classRow = eval(classRowDict[className])
    classRow = roundFloat(classRow)
    return classRow

def roundFloat(classRow):
    return [round(item, 2) if isinstance(item, float) else item for item in classRow]

def selectName(names):
    name = max(set(names), key=names.count)
    name = name.encode('ascii',errors='ignore')
    name = name.decode('utf-8')
    return name

def formatTime(time):
    minutes, s = divmod(time, 60)
    h, m = divmod(minutes, 60)
    timestring = "{}:{}:{}".format(h, m, s)
    return timestring, minutes

def get_log(log_ID):
    base_url = 'http://logs.tf/json/'

    print('Fetching log ID ' + log_ID)
    r = requests.get(base_url + log_ID)
    if r.status_code != 200:
        raise Exception('API returned error for ID {}, exiting. Status code: {}'.format(log_ID, r.status_code))
    api_result = r.json()

    """
    #keep this here for debug
    __location__ = os.path.realpath( os.path.join(os.getcwd(), os.path.dirname(__file__)))
    r = open(os.path.join(__location__, 'json.json'))
    api_result = json.load(r)
    """
    return api_result

def convertSteamID(steamID):
    

def addNewToDict(statsDict, steamID):
    if not steamID in statsDict:
        statsDict[steamID] = []
    statsDict[steamID].append({'scout': {'gp' : 0, 'time' : 0, 'kills' : 0, 'assists' : 0, 'deaths' : 0, 'damage' : 0}})
    statsDict[steamID].append({'soldier': {'gp' : 0, 'time' : 0, 'kills' : 0, 'assists' : 0, 'deaths' : 0, 'damage' : 0, 'as' : 0}})
    statsDict[steamID].append({'pyro': {'gp' : 0, 'time' : 0, 'kills' : 0, 'assists' : 0, 'deaths' : 0, 'damage' : 0, 'as' : 0}})
    statsDict[steamID].append({'demoman': {'gp' : 0, 'time' : 0, 'kills' : 0, 'assists' : 0, 'deaths' : 0, 'damage' : 0, 'as' : 0}})
    statsDict[steamID].append({'heavyweapons': {'gp' : 0, 'time' : 0, 'kills' : 0, 'assists' : 0, 'deaths' : 0, 'damage' : 0, 'dt' : 0, 'hr' : 0}})
    statsDict[steamID].append({'medic': {'gp' : 0, 'time' : 0, 'kills' : 0, 'assists' : 0, 'deaths' : 0, 'damage' : 0, 'healing' : 0, 'ubers' : 0, 'drops' : 0}})
    statsDict[steamID].append({'engineer': {'gp' : 0, 'time' : 0, 'kills' : 0, 'assists' : 0, 'deaths' : 0, 'damage' : 0}})
    statsDict[steamID].append({'sniper': {'gp' : 0, 'time' : 0, 'kills' : 0, 'assists' : 0, 'deaths' : 0, 'damage' : 0, 'headshots' : 0}})
    statsDict[steamID].append({'spy': {'gp' : 0, 'time' : 0, 'kills' : 0, 'assists' : 0, 'deaths' : 0, 'damage' : 0, 'headshots' : 0, 'backstabs' : 0}})
    statsDict[steamID].append({'names' : [], 'total_time' : 0})

    return statsDict

main()
