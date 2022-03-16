import sqlite3
import csv
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from Classes import goalieNums
from Classes import ranges
from Classes import WEEK

conn = sqlite3.connect('database.db')
c = conn.cursor()

# temp table deletion
# c.execute("DROP TABLE IF EXISTS players")


# create player table
c.execute("""
            CREATE TABLE IF NOT EXISTS players (
            id integer,
            name text,
            position text,
            type text,
            team text,
            discordID integer
            )""")

# create games table
# status = home ball,away ball,faceoffhome, faceoffaway,penaltyhome,penaltyaway
c.execute("""
            CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            home text,
            away text,
            channelID integer,
            period integer DEFAULT 1 NOT NULL,
            moves integer DEFAULT 25 NOT NULL,
            status integer DEFAULT 1 NOT NULL,
            cleanPasses integer DEFAULT 0 NOT NULL,
            homeScore integer DEFAULT 0 NOT NULL,
            awayScore integer DEFAULT 0 NOT NULL,
            homePositionWaiting Text DEFAULT 'Forward' NOT NULL,
            awayPositionWaiting Text DEFAULT 'Forward' NOT NULL,
            possession Text DEFAULT 'Home' NOT NULL,
            defenseNum integer DEFAULT -1 NOT NULL,
            goalieHome integer DEFAULT 1 NOT NULL,
            goalieAway integer DEFAULT 1 NOT NULL,
            hGoaliePulled integer DEFAULT 0 NOT NULL,
            aGoaliePulled integer DEFAULT 0 NOT NULL,
            last_message_time TEXT DEFAULT '' NOT NULL)""")



conn.commit()


# goalie csv stuff
def updateGoalieDict():
    f = open('goalienum.csv', 'r+')
    reader = csv.reader(f)
    goalieNums.clear()

    for row in reader:
        id = int(row[0])
        numList = row[1:]
        numList = [int(i) for i in numList]
        goalieNums[id] = numList
    f.close()
    return

def updateGoalieCSV():
    f = open('goalienum.csv', 'w+', newline='')
    writer = csv.writer(f)

    for key, value in goalieNums.items():
        goalieList = value.copy()
        goalieList.insert(0, key)
        writer.writerow(goalieList)
    f.close()
    return

# gamelog
# you'll have to change these to your credentials
scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name('fnhlcreds.json', scope)
googleClient = gspread.authorize(creds)
sheet = googleClient.open("FNHL Gamelog").get_worksheet(0)
data = sheet.get_all_values()

def addToGamelog(insertRow):
    try:
        sheet.append_row(insertRow)
        time.sleep(1)
    except Exception as e:
        print(e)
        print(insertRow)
        with open('tempdb.txt', 'a') as f:
            f.write('\n{}'.format(','.join([str(i) for i in insertRow])))

def setRangesDict():
    f = open('ranges.csv', 'r+')
    reader = csv.reader(f)
    ranges.clear()
    count = 0
    for row in reader:
        if row[1] == "pulled":
            ranges.setdefault(row[0], {})
            ranges[row[0]].setdefault(row[1], [])
            # create list of tuples
            rangeNums = row[2:]
            for i in rangeNums:
                s1 = i.split("|")
                s2 = s1[0].split("-")
                tup = (int(s2[0]), int(s2[1]), s1[1].lower())
                ranges[row[0]][row[1]].append(tup)
        elif row[2] == "open":
            ranges.setdefault(row[0], {})
            ranges[row[0]].setdefault(int(row[1]), [])
            ranges[row[0]][int(row[1])].setdefault(row[2], [])
            # create list of tuples
            rangeNums = row[3:]
            for i in rangeNums:
                s1 = i.split("|")
                s2 = s1[0].split("-")
                tup = (int(s2[0]), int(s2[1]), s1[1].lower())
                ranges[row[0]][int(row[1])][row[2]].append(tup)
        elif row[0] == "pass" or row[0] == "deke" or row[0] == "penalty":
            ranges.setdefault(row[0], {})
            ranges[row[0]].setdefault(row[1], [])
            # create list of tuples
            rangeNums = row[2:]
            for i in rangeNums:
                s1 = i.split("|")
                s2 = s1[0].split("-")
                tup = (int(s2[0]), int(s2[1]), s1[1].lower())
                ranges[row[0]][row[1]].append(tup)
        elif row[0] == "shot":
            ranges.setdefault(row[0], {})
            ranges[row[0]].setdefault(int(row[1]), {})
            ranges[row[0]][int(row[1])].setdefault(row[2], {})
            ranges[row[0]][int(row[1])][row[2]].setdefault(row[3], [])
            # create list of tuples
            rangeNums = row[4:]
            for i in rangeNums:
                s1 = i.split("|")
                s2 = s1[0].split("-")
                tup = (int(s2[0]), int(s2[1]), s1[1].lower())
                ranges[row[0]][int(row[1])][row[2]][row[3]].append(tup)

    f.close()
    return

updateGoalieDict()
setRangesDict()

def deleteGame(gameID):
    c.execute("DELETE FROM games WHERE id=?", (gameID,))
    conn.commit()

def returnPlayersFromTeam(team):
    c.execute("SELECT * FROM players WHERE team=?", (team,))
    conn.commit()
    playerTuple = c.fetchall()
    return playerTuple

def getPlayerFromTeamAndPosition(team, position):
    c.execute("SELECT * FROM players WHERE team=? AND position=?", (team, position))
    conn.commit()
    player = c.fetchone()
    return player

def checkIfChannelOccupied(channel):
    c.execute("SELECT * FROM games WHERE channelID=?", (channel,))
    conn.commit()
    games = c.fetchall()
    if games.__len__() > 0:
        return True
    else:
        return False

def getGameData(id):
    c.execute("SELECT * FROM games WHERE id=?", (id,))
    conn.commit()
    game = c.fetchone()
    if game is None:
        return "No game found."

    gameStr = """id: {}
home: {}
away: {}
channelID: {}
period: {}
moves: {}
status: {}
cleanPasses: {}
homeScore: {}
awayScore: {}
homePositionWaiting: {}
awayPositionWaiting: {}
possession: {}
defenseNum: xx
goalieHome: {}
goalieAway: {}
hGoaliePulled: {}
aGoaliePulled: {}
last_message_time: {}
 """.format(game[0], game[1], game[2], game[3], game[4], game[5], game[6], game[7], game[8], game[9], game[10], game[11], game[12], game[14], game[15], game[16], game[17], game[18])
    return gameStr

def addGame(home, away, channelID):
    c.execute("INSERT INTO games (home, away, channelID) VALUES (?, ?, ?)", (home, away, channelID))
    conn.commit()

def getAllGames():
    c.execute("SELECT * FROM games")
    conn.commit()
    return c.fetchall()

def getPlayersFromPID(id):
    c.execute("SELECT * FROM players WHERE discordID=?", (id,))
    conn.commit()
    player = c.fetchone()
    return player

def getGameFromTeam(team):
    c.execute("SELECT * FROM games WHERE home=? OR away=?", (team, team))
    conn.commit()
    team = c.fetchone()
    return team

def returnAllGames():
    c.execute("SELECT * FROM games")
    conn.commit()
    games = c.fetchall()
    return games

def updateDefensiveNum(id, number):
    c.execute("UPDATE games SET defenseNum=? WHERE id=?", (number, id))
    conn.commit()

def updateWaiting(id, status, hPositionWaiting, aPosWaiting, homeAway):
    c.execute("UPDATE games SET status=? AND homePositionWaiting=? AND awayPositionWaiting=? AND homeAwayWaiting=? WHERE id=?", (status, hPositionWaiting, aPosWaiting, homeAway, id))
    conn.commit()

def updateGameVariable(id, varStr, var):
    c.execute("UPDATE games SET {}=? WHERE id=?".format(varStr), (var, id))
    conn.commit()


# S2
"""
c.execute("INSERT INTO players VALUES (0, 'Drew Ekstrum','Forward','Sniper (F)','Boston',294335981442564096)")
c.execute("INSERT INTO players VALUES (1, 'Andrew Fisher','Defense','Offensive Defenseman (D)','Boston',429547988168474637)")
c.execute("INSERT INTO players VALUES (2, 'Hornet Hives','Goalie','','Boston',500805562376650758)")
#c.execute("INSERT INTO players VALUES (3, 'Nils Pöglander','Forward','Playmaker (F)','Montreal',243912771027206155)")
c.execute("INSERT INTO players VALUES (4, 'Tony Zamboni','Defense','Two-Way Defenseman (D)','Montreal',438226264608735232)")
c.execute("INSERT INTO players VALUES (5, 'Nicholas Fouss','Goalie','','Montreal',182233101349421067)")
c.execute("INSERT INTO players VALUES (6, 'Vin4DaWin','Forward','Sniper (F)','Toronto',442105563115945999)")
c.execute("INSERT INTO players VALUES (7, 'Spanksy Banks','Defense','Offensive Defenseman (D)','Toronto',275272288394280962)")
#c.execute("INSERT INTO players VALUES (8, 'Kirby Birch','Goalie','','Toronto',623890584259526657)")
c.execute("INSERT INTO players VALUES (9, 'Taro Tsujimoto','Forward','Sniper (F)','New York',302242686281318400)")
#c.execute("INSERT INTO players VALUES (10, 'Primal Cookie','Defense','Offensive Defenseman (D)','New York',482253546939613205)")
c.execute("INSERT INTO players VALUES (11, 'Pierre Gasly','Goalie','','New York',326127044163403776)")
c.execute("INSERT INTO players VALUES (12, 'Tole Do','Forward','Playmaker (F)','Philadelphia',701221250776825856)")
c.execute("INSERT INTO players VALUES (13, 'G.I. Braltar','Defense','Offensive Defenseman (D)','Philadelphia',237234603981537280)")
c.execute("INSERT INTO players VALUES (14, 'Johnny B. Goode','Goalie','','Philadelphia',401556713364389918)")
c.execute("INSERT INTO players VALUES (15, 'Joshua Average','Forward','Playmaker (F)','Pittsburgh',364417838997438464)")
c.execute("INSERT INTO players VALUES (16, 'Judge Reinhold','Defense','Offensive Defenseman (D)','Pittsburgh',597898996530413583)")
c.execute("INSERT INTO players VALUES (17, 'Georges Othello Albert Tender','Goalie','','Pittsburgh',199065947795881984)")
c.execute("INSERT INTO players VALUES (18, 'Viking Fishbird','Forward','Sniper (F)','Detroit',276493774648246272)")
c.execute("INSERT INTO players VALUES (19, 'Bokaj Snakob','Defense','Offensive Defenseman (D)','Detroit',401534971065532417)")
c.execute("INSERT INTO players VALUES (20, 'Michael Scarn','Goalie','','Detroit',401754031556657153)")
c.execute("INSERT INTO players VALUES (21, 'Damien Andrews','Forward','Sniper (F)','Columbus',287662129673142273)")
c.execute("INSERT INTO players VALUES (22, 'Matt Seventeen','Defense','Two-Way Defenseman (D)','Columbus',534010044182822914)")
c.execute("INSERT INTO players VALUES (23, 'Craig Stethchetolovichovgibolokolaskiv','Goalie','','Columbus',419640789925363712)")
c.execute("INSERT INTO players VALUES (24, 'Garfield Chubbs','Forward','Sniper (F)','Washington',173407845503467520)")
c.execute("INSERT INTO players VALUES (25, 'Cloud Giroux','Defense','Offensive Defenseman (D)','Washington',586397313992359937)")
c.execute("INSERT INTO players VALUES (26, 'Jonathan Choochoo','Goalie','','Washington',476519588155228162)")
c.execute("INSERT INTO players VALUES (27, 'Pope Coswi','Forward','Sniper (F)','Carolina',454711089582833685)")
c.execute("INSERT INTO players VALUES (28, 'Pingu','Defense','Offensive Defenseman (D)','Carolina',706698513710579762)")
c.execute("INSERT INTO players VALUES (29, 'Thelonius Junk','Goalie','','Carolina',183195160358813697)")
c.execute("INSERT INTO players VALUES (30, 'Tex Wolfe','Forward','Playmaker (F)','Nashville',592213329204871170)")
c.execute("INSERT INTO players VALUES (31, 'JZ but not the rapper','Defense','Two-Way Defenseman (D)','Nashville',254774534274547713)")
c.execute("INSERT INTO players VALUES (32, 'Keyo','Goalie','','Nashville',114529305219956739)")
c.execute("INSERT INTO players VALUES (33, 'Slowlow','Forward','Playmaker (F)','Tampa Bay',341365184021004290)")
#c.execute("INSERT INTO players VALUES (34, 'Longrod Von Hugendong','Defense','Two-Way Defenseman (D)','Tampa Bay',352849361920851968)")
c.execute("INSERT INTO players VALUES (35, 'Arm N. Hammer','Goalie','','Tampa Bay',203362581363032064)")
c.execute("INSERT INTO players VALUES (36, 'Sticky Mickey Ricci','Forward','Sniper (F)','St. Louis',539593078273605645)")
c.execute("INSERT INTO players VALUES (37, 'Emerson Austin','Defense','Offensive Defenseman (D)','St. Louis',461562661184995328)")
c.execute("INSERT INTO players VALUES (38, 'Atlas Quin','Goalie','','St. Louis',148920755189579776)")
c.execute("INSERT INTO players VALUES (39, 'Oliver Raymond','Forward','Playmaker (F)','Chicago',353210912645316611)")
c.execute("INSERT INTO players VALUES (40, 'LaPrince Frye','Defense','Finesser (D)','Chicago',416715978391420928)")
#c.execute("INSERT INTO players VALUES (41, 'Cannibal Johnson','Goalie','','Chicago',459192270537621504)")
c.execute("INSERT INTO players VALUES (42, 'Chris P. Bacon','Forward','Sniper (F)','Dallas',403329467511996418)")
c.execute("INSERT INTO players VALUES (43, 'Giles Sweeney','Defense','Two-Way Defenseman (D)','Dallas',771075367749943376)")
c.execute("INSERT INTO players VALUES (45, 'Juuse Djoos','Forward','Sniper (F)','Minnesota',148425866588848128)")
c.execute("INSERT INTO players VALUES (46, 'Haloick Oasis','Defense','Two-Way Defenseman (D)','Minnesota',121814608313843713)")
c.execute("INSERT INTO players VALUES (47, 'Jacques Bellamont','Goalie','','Minnesota',521530275759652874)")
#c.execute("INSERT INTO players VALUES (48, 'Dimitri Petrovich','Forward','Playmaker (F)','Vegas',355934424061181972)")
c.execute("INSERT INTO players VALUES (49, 'Holden Tudix','Defense','Two-Way Defenseman (D)','Vegas',198274387831422976)")
c.execute("INSERT INTO players VALUES (50, 'Eduardo Bellquatro','Goalie','','Vegas',679431701981823026)")
c.execute("INSERT INTO players VALUES (51, 'Remy McQueen','Forward','Playmaker (F)','Edmonton',320396094817304576)")
c.execute("INSERT INTO players VALUES (52, 'Joey Wray','Defense','Two-Way Defenseman (D)','Edmonton',144969605977341953)")
#c.execute("INSERT INTO players VALUES (53, 'Max Wasson','Goalie','','Edmonton',134507698103255040)")
c.execute("INSERT INTO players VALUES (54, 'John Smith','Forward','Playmaker (F)','Vancouver',517414932745027615)")
#c.execute("INSERT INTO players VALUES (55, 'Anthony Billanti','Defense','Offensive Defenseman (D)','Vancouver',99969994074378240)")
#c.execute("INSERT INTO players VALUES (56, 'Macho Man','Goalie','','Vancouver',728305662236557422)")
#c.execute("INSERT INTO players VALUES (57, 'Cheesy Camburger','Forward','Dangler (F)','Calgary',368414494772428801)")
#c.execute("INSERT INTO players VALUES (58, 'Jay-Z the Rapper','Defense','Two-Way Defenseman (D)','Calgary',373703526347440129)")
#c.execute("INSERT INTO players VALUES (59, 'Evgeni Konstantinov','Goalie','','Calgary',240572831333613569)")
c.execute("INSERT INTO players VALUES (60, 'xXGoalScorer69420Xx','Forward','Sniper (F)','Seattle',521532303508242432)")
c.execute("INSERT INTO players VALUES (61, 'Tenny','Defense','Offensive Defenseman (D)','Seattle',477216596667006996)")
c.execute("INSERT INTO players VALUES (62, 'Stefan Frei Jr.','Goalie','','Seattle',117857003145134081)")
c.execute("INSERT INTO players VALUES (63, 'Rusty Kuntz','Forward','Sniper (F)','San Jose',356901926077464576)")
c.execute("INSERT INTO players VALUES (64, 'Smoke Anderson','Defense','Offensive Defenseman (D)','San Jose',284831116207194122)")
#c.execute("INSERT INTO players VALUES (65, 'Anton Volchenkov','Goalie','','San Jose',246762932703068162)")
c.execute("INSERT INTO players VALUES (66, 'Vulf Zilla','Forward','Sniper (F)','Anaheim',466035881682141185)")
c.execute("INSERT INTO players VALUES (67, 'Demetrios Ooga','Defense','Two-Way Defenseman (D)','Anaheim',319330358636314634)")
c.execute("INSERT INTO players VALUES (68, 'Ferda Bois','Goalie','','Anaheim',404782639824764951)")
c.execute("INSERT INTO players VALUES (69, 'Connor McDaddy','Forward','Sniper (F)','Los Angeles',306609698340339714)")
#c.execute("INSERT INTO players VALUES (70, 'Mikhail Grigorev','Defense','Offensive Defenseman (D)','Los Angeles',414316350324998144)")
#c.execute("INSERT INTO players VALUES (71, 'Red Arrow','Goalie','','Los Angeles',272034904127045633)")
c.execute("INSERT INTO players VALUES (72, 'Slav Polinski','Forward','Sniper (F)','Rochester',268566559746686986)")
#c.execute("INSERT INTO players VALUES (73, 'Brent Schumacher','Defense','Offensive Defenseman (D)','Pittsburgh',482976539651211291)")
c.execute("INSERT INTO players VALUES (74, 'Dirk Digglet','Goalie','','Chicago',636749752683200523)")
c.execute("INSERT INTO players VALUES (75, 'Bud Tuggli','Forward','Sniper (F)','Vegas',195544830481268736)")
c.execute("INSERT INTO players VALUES (76, 'Julio Escobar','Defense','Offensive Defenseman (D)','Calgary',391151653358665728)")
c.execute("INSERT INTO players VALUES (77, 'Hunter Scott','Goalie','','Los Angeles',841095606172778527)")
c.execute("INSERT INTO players VALUES (78, 'Lane Drew','Forward','Sniper (F)','Montreal',215354400720420866)")
#c.execute("INSERT INTO players VALUES (79, 'Garitek','Defense','Two-Way Defenseman (D)','Belleville',201437703328235520)")
c.execute("INSERT INTO players VALUES (80, 'Polybius Belfour','Goalie','','Belleville',699797364281704538)")
c.execute("INSERT INTO players VALUES (81, 'Dominus Nominus','Defense','Two-Way Defenseman (D)','Tampa Bay',198821468317024256)")
c.execute("INSERT INTO players VALUES (82, 'Joe Pidgeon','Defense','Offensive Defenseman (D)','New York',430014697174073364)")
c.execute("INSERT INTO players VALUES (83, 'Bertie O''Brien','Goalie','','Calgary',205443196401090561)")
c.execute("INSERT INTO players VALUES (84, 'Val Pix','Forward','Playmaker (F)','Tucson',231100460482691074)")
c.execute("INSERT INTO players VALUES (85, 'Phil Coulson','Defense','Two-Way Defenseman (D)','Tucson',218554095533817856)")
c.execute("INSERT INTO players VALUES (86, 'Matt McNeverStopThings','Goalie','','Edmonton',267844339365838848)")
c.execute("INSERT INTO players VALUES (87, 'Whitt Bass','Forward','Sniper (F)','Calgary',211904717981220865)")
c.execute("INSERT INTO players VALUES (88, 'Charlie Bae','Defense','Two-Way Defenseman (D)','Manitoba',217141905807376385)")
#c.execute("INSERT INTO players VALUES (89, 'Pope Lindros','Goalie','','Manitoba',706723219012452404)")
c.execute("INSERT INTO players VALUES (90, 'Norse Whalewing','Forward','Playmaker (F)','Fighting Fishbirds',750645478353272864)")
c.execute("INSERT INTO players VALUES (91, 'Dutch Troutowl','Defense','Two-Way Defenseman (D)','Fighting Fishbirds',750647785354690561)")
c.execute("INSERT INTO players VALUES (92, 'Swede Sharkswallow','Goalie','','Fighting Fishbirds',750649318243041351)")
c.execute("INSERT INTO players VALUES (93, 'Goldface','Forward','Dangler (F)','Threat Level Midnight',750650770419875840)")
c.execute("INSERT INTO players VALUES (94, 'Catherine Zeta-Scarn','Defense','Finesser (D)','Threat Level Midnight',750651851841601546)")
c.execute("INSERT INTO players VALUES (95, 'Samuel L. Chang','Goalie','','Threat Level Midnight',750652639506858034)")
c.execute("INSERT INTO players VALUES (96, 'Alexis Sabor','Goalie','','Toronto',158306211568025600)")
c.execute("INSERT INTO players VALUES (97, 'Ananias Thomson II','Goalie','','Vancouver',380832803127951362)")
c.execute("INSERT INTO players VALUES (98, 'Buttersqauch','Goalie','','San Jose',103321319608700928)")
c.execute("INSERT INTO players VALUES (99, 'garitek','Defense','Two-Way Defenseman (D)','Vancouver',201437703328235520)")
c.execute("INSERT INTO players VALUES (100, 'Snussu','Goalie','','Dallas',207577359438577664)")
c.execute("INSERT INTO players VALUES (101, 'Brian Taylor','Defense','Two-Way Defenseman (D)','Los Angeles',263736081000824832)")
"""

"""all-star s1
c.execute("INSERT INTO players VALUES (73, 'Viking Fishbird','Forward','Sniper (F)','Team Gasly',276493774648246272)")
c.execute("INSERT INTO players VALUES (74, 'Papa Coswi','Defense','Two-Way Defenseman (D)','Team Gasly',454711089582833685)")
c.execute("INSERT INTO players VALUES (75, 'Pierre Gasly','Goalie','','Team Gasly',326127044163403776)")
c.execute("INSERT INTO players VALUES (76, 'Remy McQueen','Forward','Playmaker (F)','Team Johnson',320396094817304576)")
c.execute("INSERT INTO players VALUES (77, 'Tenny','Defense','Offensive Defenseman (D)','Team Johnson',477216596667006996)")
c.execute("INSERT INTO players VALUES (78, 'Cannibal Johnson','Goalie','','Team Johnson',459192270537621504)")
c.execute("INSERT INTO players VALUES (79, 'Chris P. Bacon','Forward','Sniper (F)','Team Giroux',403329467511996418)")
c.execute("INSERT INTO players VALUES (80, 'Cloud Giroux','Defense','Offensive Defenseman (D)','Team Giroux',586397313992359937)")
c.execute("INSERT INTO players VALUES (81, 'Kirby Birch','Goalie','','Team Giroux',623890584259526657)")
c.execute("INSERT INTO players VALUES (82, 'Oliver Raymond','Forward','Playmaker (F)','Team Anev',353210912645316611)")
c.execute("INSERT INTO players VALUES (83, 'Christ Anev','Defense','Two-Way Defenseman (D)','Team Anev',243912771027206155)")
c.execute("INSERT INTO players VALUES (84, 'G.I. Bralter','Goalie','','Team Anev',237234603981537280)")

c.execute("INSERT INTO players VALUES (64, 'Bud Tuggli','Forward','Sniper (F)','Free Agent Team 2',195544830481268736)")
c.execute("INSERT INTO players VALUES (65, 'Tony Zamboni','Defense','Two-Way Defenseman (D)','Free Agent Team 2',438226264608735232)")
c.execute("INSERT INTO players VALUES (66, 'CoerdePirate','Goalie','','Free Agent Team 2',688932450008563740)")

c.execute("INSERT INTO players VALUES (58, 'Tex Wolfe','Forward','Playmaker (F)','Free Agent Team 1',592213329204871170)")
c.execute("INSERT INTO players VALUES (70, 'Ferda Bois','Defense','Offensive Defenseman (D)','Free Agent Team 1',404782639824764951)")
c.execute("INSERT INTO players VALUES (72, 'Turts','Goalie','','Free Agent Team 1',623164301267435541)")
"""

"""
all-star s2
c.execute("INSERT INTO players VALUES (102, 'Vulf Zilla','Forward','Sniper (F)','Team Vulf',466035881682141185)")
c.execute("INSERT INTO players VALUES (103, 'Tenny','Defense','Offensive Defenseman (D)','Team Vulf',477216596667006996)")
c.execute("INSERT INTO players VALUES (104, 'Johnny B. Goode','Goalie','','Team Vulf',401556713364389918)")

c.execute("INSERT INTO players VALUES (105, 'Pope Coswi','Forward','Sniper (F)','Team Pope',454711089582833685)")
c.execute("INSERT INTO players VALUES (106, 'Bokaj Snakob','Defense','Offensive Defenseman (D)','Team Pope',401534971065532417)")
c.execute("INSERT INTO players VALUES (107, 'Jonathan Choochoo','Goalie','','Team Pope',476519588155228162)")

c.execute("INSERT INTO players VALUES (108, 'Viking Fishbird','Forward','Sniper (F)','Team Ooga',276493774648246272)")
c.execute("INSERT INTO players VALUES (109, 'Demetrios Ooga','Defense','Two-Way Defenseman (D)','Team Ooga',319330358636314634)")
c.execute("INSERT INTO players VALUES (110, 'Dirk Digglet','Goalie','','Team Ooga',636749752683200523)")

c.execute("INSERT INTO players VALUES (111, 'xXGoalScorer69420Xx','Forward','Sniper (F)','Team Brady',521532303508242432)")
c.execute("INSERT INTO players VALUES (112, 'Haloick Oasis','Defense','Two-Way Defenseman (D)','Team Brady',121814608313843713)")
c.execute("INSERT INTO players VALUES (113, 'Nicholas Fouss','Goalie','','Team Brady',182233101349421067)")
"""