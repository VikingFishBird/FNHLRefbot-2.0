from Classes import goalieNums
import Database

def getWaitingOn(game):
    teamHA = ""
    position = ""
    type = "DM"

    if game[14] == 1 and game[15] == 1:
        teamHA = "Both"
        position = "Goalie"
        return "Waiting on DM from both goalies.", teamHA, position, type
    elif game[14] == 1:
        teamHA = game[1]
        position = "Goalie"
        return "Waiting on DM from home goalie.", teamHA, position, type
    elif game[15] == 1:
        teamHA = game[2]
        position = "Goalie"
        return "Waiting on DM from away goalie.", teamHA, position, type

    elif game[12] == "Home":
        if game[13] == -1:
            teamHA = game[2]
            position = game[11]
            return "Waiting on defensive number from away {}.".format(game[11]), teamHA, position, type
        else:
            teamHA = game[1]
            position = game[10]
            type = "Server Message"
            return "Waiting on offensive number from home {}.".format(game[10]), teamHA, position, type
    else:
        if game[13] == -1:
            teamHA = game[1]
            position = game[10]
            return "Waiting on defensive number from home {}.".format(game[10]), teamHA, position, type
        else:
            teamHA = game[2]
            position = game[11]
            type = "Server Message"
            return "Waiting on offensive number from away {}.".format(game[11]), teamHA, position, type

def getDifference(oNum, dNum):
    dif = abs(oNum-dNum)
    if dif > 500:
        dif = 1000-dif
    return dif