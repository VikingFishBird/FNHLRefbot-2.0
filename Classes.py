import enum

WEEK = 8
POWERPLAYID = 763682731270995969

teamNicknames = {
    'Boston': 'Bruins',
    'Montreal': 'Canadiens',
    'Toronto': 'Maple Leafs',
    'New York': 'Rangers',
    'Philadelphia': 'Flyers',
    'Pittsburgh': 'Penguins',
    'Detroit': 'Red Wings',
    'Columbus': 'Blue Jackets',
    'St. Louis': 'Blues',
    'Chicago': 'Blackhawks',
    'Dallas': 'Stars',
    'Vegas': 'Golden Knights',
    'Seattle': 'Kraken',
    'San Jose': 'Sharks',
    'Calgary': 'Flames',
    'Los Angeles': 'Kings',
    'Anaheim': 'Ducks',
    'Carolina': 'Hurricanes',
    'Edmonton': 'Oilers',
    'Minnesota': 'Wild',
    'Nashville': 'Predators',
    'Tampa Bay': 'Lightning',
    'Vancouver': 'Canucks',
    'Washington': 'Capitals',
    'Threat Level Midnight': '',
    'Fighting Fishbirds': '',
    'Free Agent Team 1': '',
    'Free Agent Team 2': '',
    'Team Gasly': '',
    'Team Johnson': '',
    'Team Giroux': '',
    'Team Anev': '',
    'Tucson': 'Roadrunners',
    'Milwaukee': 'Admirals',
    'Belleville': 'Senators',
    'Manitoba': 'Moose',
    'Hershey': 'Bears',
    'Rochester': 'Americans',
    'Team Vulf': '',
    'Team Pope': '',
    'Team Ooga': '',
    'Team Brady': ''
}

teamEmoji = {
    'Boston': 590287759277686784,
    'Montreal': 590287761454661635,
    'Toronto': 590287763719323649,
    'New York': 590287764726218752,
    'Philadelphia': 590287758560591872,
    'Pittsburgh': 590287765095055371,
    'Detroit': 590287763719323749,
    'Columbus': 750326441278832650,
    'St. Louis': 590287761802657914,
    'Chicago': 590287763899809836,
    'Dallas': 750136925821599864,
    'Vegas': 750137583903834153,
    'Seattle': 749740583299317800,
    'San Jose': 750136732313190481,
    'Calgary': 750136587983257681,
    'Los Angeles': 590287759218835456,
    'Anaheim': 814947411365462046,
    'Carolina': 805877282052767804,
    'Edmonton': 805876290490073138,
    'Minnesota': 805876257379975188,
    'Nashville': 805876127939690556,
    'Tampa Bay': 805875276022022144,
    'Vancouver': 805876274001084418,
    'Washington': 805876232964276305,
    'Threat Level Midnight': 750632252681093120,
    'Fighting Fishbirds': 751146938065485835,
    'Free Agent Team 1': 763865342187143218,
    'Free Agent Team 2': 763865342257659944,
    'Team Gasly': 782364181936209950,
    'Team Johnson': 782364182224961547,
    'Team Giroux': 782364183534239785,
    'Team Anev': 782364183206428693,
    'Tucson': 785824139033968641,
    'Milwaukee': 785824139151671296,
    'Belleville': 785824138093920266,
    'Manitoba': 785824348623339540,
    'Hershey': 785824138177937459,
    'Rochester': 787053254756270101,
    'Team Vulf': 868912037701509241,
    'Team Pope': 868911444874391624,
    'Team Ooga': 868911444584955934,
    'Team Brady': 868911444933115994
}

resultStringConversion = {
    'breakaway': '',
    'clean': '',
    'sloppy': '',
    'offsides': '',
    'turnover': '',
    'penalty': '',
    'oppgoal': '',
    'dekesuccess': '',
    'dekefail': '',
    'goal': '',
    'rebound': '',
    'save': '',
    'block': '',

}

goalieNums = {}
ranges = {}

"""
class PlayType(enum):
    PASS = 1
    SHOT = 2
    DEKE = 3

class GameStatus(enum):
    HOMEShotPass = 1    
    AWAY = 2
    FACEOFFHOME = 3
    FACEOFFAWAY = 4
    PENALTYHOME = 5
    PENALTYAWAY = 6
    BREAKAWAYHOME = 7
    BREAKAWAYAWAY = 8

0 Normal
1 Faceoff
2 Penalty
3 Breakaway

2 WatingOnHomeOffense
3 WatingOnAwayOffense
4 WatingOnHomeDefense
5 WatingOnAwayDefense

# Faceoff
6 WatingOnHomeOffense
7 WatingOnAwayOffense
8 WatingOnHomeDefense
9 WatingOnAwayDefense

# Penalty/Breakaway
10 WatingOnHomeOffense
11 WatingOnAwayOffense
12 WatingOnHomeDefense
13 WatingOnAwayDefense

"""

class Team:
    def __init__(self):
        self.location = ""
        self.nickname = ""


class Game:
    def __init__(self, home, away):
        self.home = home
        self.away = away
