import os
import Database
import discord
import re
import Messages
import Utils
import time
import datetime
from Classes import goalieNums
from Classes import teamEmoji
from Classes import ranges
from Classes import WEEK
from Classes import POWERPLAYID
import random

PERIODLENGHT = 25
TOKEN = "TOKEN_GOES_HERE"
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print("{} has connected!".format(client.user))

@client.event
async def on_message(message):
    # Ignore messages sent by itself.
    if message.author == client.user:
        return

    ### FNHL commands ###
    # Returns the members of a given team.
    if message.content.lower().startswith("!pingteam"):
        try:
            teamToPing = message.content.lower().replace("!pingteam", "").strip()
            playerTuple = Database.returnPlayersFromTeam(teamToPing.title())
            if playerTuple.__len__() == 3:
                playerString = playerTuple[0][1] + "\n" + playerTuple[1][1] + "\n" + playerTuple[2][1]
                if playerString != "":
                    await message.channel.send(playerString)
                    time.sleep(1)
            else:
                print(playerTuple)
                await message.channel.send("Couldn't find players on team.")
                time.sleep(1)
        except:
            await message.channel.send("Unexpected command error: `!pingteam`.")
            time.sleep(1)

        return

    # Returns a scoreboard of active games.
    elif message.content.lower().startswith("!scoreboard"):
        games = Database.getAllGames()
        scoreboardStr = "**Week {} Scoreboard**".format(WEEK)
        for game in games:
            scoreboardStr += "\n{} {} - {} {} ({} moves | {})".format(client.get_emoji(teamEmoji[game[1]]), game[8], game[9],
                                                                            client.get_emoji(teamEmoji[game[2]]), game[5], getPeriodStr(game[4]))
        await message.channel.send(scoreboardStr)
        time.sleep(1)
        return

    elif message.content.lower().startswith("!whyvancouver"):
        return
        player = Database.getPlayersFromPID(201437703328235520)
        if player is None:
            print("cannot find player")
            return

        # player info
        playerName = player[1]
        playerPos = player[2]
        playerType = player[3]
        playerTeam = player[4]
        playerDID = player[5]

        # get game
        g = Database.getGameFromTeam(playerTeam)
        if g is None:
            # no game for player
            print(playerTeam)
            print('Cant find game')
            return
        msgStr, teamWO, positionWO, typeWO = Utils.getWaitingOn(g)
        print(g)
        print(str(g) + "\nmsgStr: " +
              msgStr + "\nteam: " +
              teamWO + "\npos: " +
              positionWO + "\ntype:" +
              typeWO)

        time.sleep(1)
        return

    # Given one of the teams in a game, returns the
    # team and player position the bot is waiting on.
    elif message.content.lower().startswith("!waitingon"):
        teamToPing = message.content.lower().replace("!waitingon", "").strip()
        game = Database.getGameFromTeam(teamToPing.title())
        if game is not None:
            msgStr, teamWO, positionWO, typeWO = Utils.getWaitingOn(game)
            last_msg_time = datetime.datetime.strptime(game[18], '%Y-%m-%d %H:%M:%S.%f')
            await message.channel.send(msgStr + '\nTime Waiting: {}'.format(datetime.datetime.now() - last_msg_time))
            time.sleep(1)
            # DoG Check
            return
            if (datetime.datetime.now() - last_msg_time).total_seconds() >= (16 * 60 * 60):
                print("DoG")
                if positionWO == 'Goalie':
                    await message.channel.send("Delay of game-goalie. Ping VFB because he didn't know how to handle this at 4 AM.")
                elif teamWO == game[1]:
                    # penalty on Home
                    Database.updateGameVariable(game[0], 'status', 2)
                    Database.updateGameVariable(game[0], 'defenseNum', 1)
                    Database.updateGameVariable(game[0], 'possession', 'Away')
                    Database.updateGameVariable(game[0], 'awayPositionWaiting', random.choice(['Forward', 'Defense']))
                    await message.channel.send("Delay of game on home team.")
                else:
                    # penalty on Away
                    Database.updateGameVariable(game[0], 'status', 2)
                    Database.updateGameVariable(game[0], 'defenseNum', 1)
                    Database.updateGameVariable(game[0], 'possession', 'Home')
                    Database.updateGameVariable(game[0], 'homePositionWaiting', random.choice(['Forward', 'Defense']))
                    await message.channel.send("Delay of game on away team.")
                time.sleep(1)

        else:
            await message.channel.send("Couldn't find game with team.")
            time.sleep(1)

        return

    # Get's a specific player on a team depending on
    # the given team/position.
    elif message.content.lower().startswith("!getposition"):
        commandInfo = []
        try:
            commandInfo = message.content.lower().replace("!getposition", "").strip().split(", ")
        except:
            await message.channel.send("Unable execute command. The format should be `!getPosition [team], [position]`")
            time.sleep(1)
        player = Database.getPlayerFromTeamAndPosition(commandInfo[0].title(), commandInfo[1].title())
        if player.__len__() <= 0:
            await message.channel.send("Unable to parse command. The format should be `!getPosition [team], [position]`")
            time.sleep(1)
        playerString = player[2] + " " + player[1] + " " + player[3]
        if playerString != "":
            await message.channel.send(playerString)
            time.sleep(1)

        return

    # Tests an output given play details.
    elif message.content.lower().startswith("!testrange"):
        # playtype,clean passes,player_type,ingoal,difference
        commandInfo = []
        try:
            commandInfo = message.content.lower().replace("!testrange", "").strip().split(", ")
            play_type = commandInfo[0]
            cp = commandInfo[1]
            player_type = commandInfo[2]
            in_goal = commandInfo[3]
            diff = commandInfo[4]

            p_types = {
                'playmaker (f)': 'Playmaker (F)',
                'sniper (f)': 'Sniper (F)',
                'dangler (f)': 'Dangler (F)',
                'offensive defenseman (d)': 'Offensive Defenseman (D)',
                'two-way defenseman (d)': 'Two-Way Defenseman (D)',
                'finesser (d)': 'Finesser (D)',
            }

            if play_type == 'shot':
                rangeTupleList = ranges[play_type][int(cp)][p_types[player_type]][in_goal]
            elif play_type == 'pass' or play_type == 'deke':
                rangeTupleList = ranges[play_type][p_types[player_type]]
            elif play_type == 'penalty':
                rangeTupleList = ranges[play_type][p_types[player_type]]
            time.sleep(1)
            for tup in rangeTupleList:
                if tup[0] <= int(diff) <= tup[1]:
                    result = tup[2]

            await message.channel.send(result)
        except:
            await message.channel.send(
                "Unable execute command. The format should be `!testrange playtype, clean passes, player_type, ingoal, difference`.")
            time.sleep(1)

    # Prints a list of the ongoing games.
    elif message.content.lower() == "!printactivegames":
        gamesList = Database.returnAllGames()
        if gamesList.__len__() <= 0:
            time.sleep(1)
            await message.channel.send("No active games.")
        else:
            for game in gamesList:
                await message.channel.send("{} {} @ {}".format(game[0], game[2], game[1]))
                time.sleep(1)

        return

    # Given a game_id, prints the statuses of the game.
    elif message.content.lower().startswith("!printgamedata"):
        gameID = -1
        try:
            commandInfo = message.content.lower().replace("!printgamedata", "").strip()
            gameID = int(commandInfo)
        except:
            time.sleep(1)
            await message.channel.send("Unable execute command. The format should be `!printgamedata [gameID]`")

        await message.channel.send(Database.getGameData(gameID))
        time.sleep(1)

    # Deletes a game.
    elif message.content.lower().startswith("!deletegame"):
        gameID = -1
        try:
            commandInfo = message.content.lower().replace("!deletegame", "").strip()
            gameID = int(commandInfo)
        except:
            time.sleep(1)
            await message.channel.send("Unable execute command. The format should be `!deletegame [gameID]`")

        Database.deleteGame(gameID)
        await message.channel.send("Game deleted.")
        time.sleep(1)

    # Starts a game.
    elif message.content.lower().startswith("!startgame"):
        commandInfo = []
        try:
            commandInfo = message.content.lower().replace("!startgame", "").strip().split(", ")
        except:
            await message.channel.send("Unable execute command. The format should be `!startgame [home], [away]`")
            time.sleep(1)
            return

        if commandInfo.__len__() != 2:
            await message.channel.send("Unable execute command. The format should be `!startgame [home], [away]`")
            time.sleep(1)
            return
        elif commandInfo[0].title() not in teamEmoji or commandInfo[1].title() not in teamEmoji:
            await message.channel.send("Could not find two valid teams.")
            time.sleep(1)
            return

        messageStr = Messages.processStartGame(message, commandInfo)
        await message.channel.send(messageStr)
        time.sleep(1)

        gameInfo = Database.getGameFromTeam(commandInfo[1].title())

        # remove goalie numbers
        homeGoalie = Database.getPlayerFromTeamAndPosition(gameInfo[1], "Goalie")
        goalieNums[homeGoalie[5]] = []
        awayGoalie = Database.getPlayerFromTeamAndPosition(gameInfo[2], "Goalie")
        goalieNums[awayGoalie[5]] = []
        Database.updateGoalieCSV()

        await message.channel.edit(topic="{} 0 - 0 {} ({} moves | 1st)".format(gameInfo[1], gameInfo[2], PERIODLENGHT))
        time.sleep(1)

        goalieMessage = createGoalieMessage(gameInfo)

        Database.updateGameVariable(gameInfo[0], 'last_message_time', str(datetime.datetime.now()))

        if homeGoalie is not None:
            user = client.get_user(homeGoalie[5])
            await user.send(goalieMessage)
        else:
            print("Could not find home goalie.")

        if awayGoalie is not None:
            user = client.get_user(awayGoalie[5])
            await user.send(goalieMessage)
        else:
            print("Could not find home goalie.")

        return

    # Goalie command to view their current number list.
    elif message.content.lower() == "!viewnumbers" and isinstance(message.channel, discord.channel.DMChannel):
        player = Database.getPlayersFromPID(message.author.id)
        if player is None:
            # cannot find player
            return

        if player[2] != "Goalie":
            return
        playerDID = player[5]
        numberList = goalieNums[playerDID]
        if numberList.__len__() <= 0:
            time.sleep(1)
            await message.channel.send("Your number list is empty.")
        else:
            numStr = ""
            for num in numberList:
                numStr = numStr + str(num) + "\n"
            time.sleep(1)
            await message.channel.send("Here's your goalie number list:\n{}".format(numStr))

        return

    ### Non-essential Commands ###
    elif message.content == "!gameoftheweek":
        await message.channel.send("Detroit | Columbus")
        time.sleep(1)
    elif message.content == "!emojitest":
        await message.channel.send(client.get_emoji(teamEmoji["Detroit"]))
        time.sleep(1)
    elif message.content == "!rigged":
        await message.channel.send("Nah")
        time.sleep(1)
    elif message.content == "!cry":
        await message.channel.send(":cry:")
        time.sleep(1)
    elif message.content == "!eku":
        await message.channel.send("https://tenor.com/O9G0.gif")
        time.sleep(1)
    elif message.content == "!pingme":
        await message.channel.send("Sure buddy. {}".format(message.author.mention))
        time.sleep(1)

    # SUPER ESSENTIAL COMMANDS :D
    elif "smaller cookie" in message.content.lower():
        await message.channel.send(":cookie: :)")
        time.sleep(1)
    elif "cookie" in message.content.lower():
        await message.channel.send(":cookie:")
        time.sleep(1)

    # Primary game commands.
    if isinstance(message.channel, discord.channel.DMChannel):
        # find player in database
        player = Database.getPlayersFromPID(message.author.id)
        if player is None:
            # cannot find player
            return

        # player info
        playerName = player[1]
        playerPos = player[2]
        playerType = player[3]
        playerTeam = player[4]
        playerDID = player[5]

        # get game
        g = Database.getGameFromTeam(playerTeam)
        if g is None:
            # no game for player
            return
        # game info
        gameID = g[0]
        gameHome = g[1]
        gameAway = g[2]
        gameChannelID = g[3]
        gamePeriod = g[4]
        gameMoves = g[5]
        status = g[6]
        gameCleanPasses = g[7]
        gameHomeScore = g[8]
        gameAwayScore = g[9]
        homePositionWaiting = g[10]
        awayPositionWaiting = g[11]
        possession = g[12]
        defNum = g[13]
        goalieHome = g[14]
        goalieAway = g[15]
        hGoaliePulled = g[16]
        aGoaliePulled = g[17]

        # get "waiting on" info
        msgStr, teamWO, positionWO, typeWO = Utils.getWaitingOn(g)

        # Waiting on goalie number.
        if playerPos == "Goalie":
            # goalie shit
            numList = re.findall('\d+', message.content)
            numList = [int(i) for i in numList]

            for i in range(numList.__len__()):
                if not (1 <= numList[i] <= 1000):
                    numList.pop(i)

            if numList.__len__() <= 0:
                await message.channel.send("Could not find numbers in message.")
                time.sleep(1)
                return

            if "replace" in message.content.lower():
                goalieNums[playerDID] = numList
                Database.updateGoalieCSV()
                # success
                await message.channel.send("Replaced number list. Call `!viewnumbers` to view your list.")
                time.sleep(1)
            else:
                goalieNums[playerDID] = goalieNums[playerDID] + numList
                Database.updateGoalieCSV()
                # success
                await message.channel.send("Appended numbers to list. Call `!viewnumbers` to view your list.")
                time.sleep(1)

            # update goalie database / check if both goalie submitted
            bothGoaliesSubmitted = 0  # 0 = true, 1 = home, 2 = away
            if playerTeam == gameHome:
                Database.updateGameVariable(gameID, "goalieHome", 0)
                Database.updateGameVariable(gameID, "last_message_time", str(datetime.datetime.now()))
                if goalieAway == 1:
                    bothGoaliesSubmitted = 2
            else:
                Database.updateGameVariable(gameID, "goalieAway", 0)
                Database.updateGameVariable(gameID, "last_message_time", str(datetime.datetime.now()))
                if goalieHome == 1:
                    bothGoaliesSubmitted = 1

            if bothGoaliesSubmitted == 0:
                # send next message
                Database.updateGameVariable(gameID, "last_message_time", str(datetime.datetime.now()))
                g = Database.getGameFromTeam(gameHome)
                woMSG, teamWO, positionWO, typeWO = Utils.getWaitingOn(g)
                playerWO = Database.getPlayerFromTeamAndPosition(teamWO, positionWO)
                user = client.get_user(playerWO[5])

                # send dm for faceoff/defense
                if status == 0:  # normal
                    msgStr = createMessage(g, 'defensive')
                    await user.send(msgStr)
                    return
                elif status == 1:  # faceoff
                    msgStr = createMessage(g, 'faceoff')
                    await user.send(msgStr)
                    return
                elif status == 2:  # penalty
                    msgStr = createMessage(g, 'penalty')
                    await user.send(msgStr)
                    return
                else:  # breakaway
                    msgStr = createMessage(g, 'breakaway')
                    await user.send(msgStr)
                    return
                return
            elif bothGoaliesSubmitted == 1:
                # send reminder to home goalie
                # homeGoalie = Database.getPlayerFromTeamAndPosition(gameHome, "Goalie")
                # user = client.get_user(homeGoalie[5])
                # await user.send("https://gph.is/2SPjlnv")
                return
            elif bothGoaliesSubmitted == 2:
                # send reminder to away goalie
                # awayGoalie = Database.getPlayerFromTeamAndPosition(gameAway, "Goalie")
                # user = client.get_user(awayGoalie[5])
                # await user.send("https://gph.is/2SPjlnv")
                return

        ### CHECKS ###
        # yo, get outta my dms bro. not waiting on you
        if typeWO != "DM":
            print("yo, get outta my dms bro. not waiting on you")
            return
        # is player on the team being waited on?
        if teamWO != "Both" and teamWO != playerTeam:
            print("is player on the team being waited on? {} != {}".format(playerTeam, teamWO))
            return
        # is player the position waited on?
        if positionWO != playerPos:
            print("is player the position waited on? {} != {}".format(playerPos, positionWO))
            return
        # number already submitted?
        if defNum != -1:
            print("number already submitted? yes")
            return

        elif positionWO == "Defense" or positionWO == "Forward":
            # defense or faceoff shit
            numList = re.findall('\d+', message.content)
            if numList.__len__() <= 0:
                await message.channel.send("Cannot find number in message.")
                time.sleep(1)
                return

            submittedNum = int(numList[0])
            if 1 <= submittedNum <= 1000:
                # success
                Database.updateDefensiveNum(gameID, submittedNum)
                await message.channel.send("Accepted Number: {}".format(submittedNum))
                time.sleep(1)
            else:
                await message.channel.send("Number must be between 1 and 1000 (inclusive).")
                time.sleep(1)
                return

            Database.updateGameVariable(gameID, "last_message_time", str(datetime.datetime.now()))
            g = Database.getGameFromTeam(gameHome)
            woMSG, teamWO, positionWO, typeWO = Utils.getWaitingOn(g)
            playerWO = Database.getPlayerFromTeamAndPosition(teamWO, positionWO)
            user = client.get_user(playerWO[5])
            disChannel = client.get_channel(gameChannelID)

            # send dm for faceoff/defense
            if status == 0:  # normal
                addStr = "\n"
                if hGoaliePulled == 1:
                    addStr += "{}'s goalie is pulled. ".format(gameHome)
                if aGoaliePulled == 1:
                    addStr += "{}'s goalie is pulled. ".format(gameAway)

                msgStr = createMessage(g, 'offensive')
                await disChannel.send(msgStr + " (pass/shot/deke) " + user.mention + addStr)
                return
            elif status == 1:  # faceoff
                msgStr = createMessage(g, 'faceoff')
                await disChannel.send(msgStr + " " + user.mention)
                return
            elif status == 2:  # penalty
                msgStr = createMessage(g, 'penalty')
                await disChannel.send(msgStr + " " + user.mention)
                return
            else:  # breakaway
                msgStr = createMessage(g, 'breakaway')
                await disChannel.send(msgStr + " " + user.mention)
                return
    else:
        # find player in database
        player = Database.getPlayersFromPID(message.author.id)
        if player is None:
            # cannot find player
            return

        # player info
        playerName = player[1]
        playerPos = player[2]
        playerType = player[3]
        playerTeam = player[4]
        playerDID = player[5]

        # get game
        g = Database.getGameFromTeam(playerTeam)
        if g is None:
            # no game for player
            return
        # game info
        gameID = g[0]
        gameHome = g[1]
        gameAway = g[2]
        gameChannelID = g[3]
        gamePeriod = g[4]
        gameMoves = g[5]
        status = g[6]
        gameCleanPasses = g[7]
        gameHomeScore = g[8]
        gameAwayScore = g[9]
        homePositionWaiting = g[10]
        awayPositionWaiting = g[11]
        possession = g[12]
        defNum = g[13]
        goalieHome = g[14]
        goalieAway = g[15]
        hGoaliePulled = g[16]
        aGoaliePulled = g[17]
        origPoss = possession

        # get "waiting on" info
        msgStr, teamWO, positionWO, typeWO = Utils.getWaitingOn(g)

        ### CHECKS ###
        # wrong channel dude
        if message.channel.id != gameChannelID:
            print("wrong channel dude")
            return
        # yo, get outta my dms bro. not waiting on you
        if typeWO == "DM":
            print("yo, get outta my dms bro. not waiting on you")
            return
        # is player on the team being waited on?
        if teamWO != "Both" and teamWO != playerTeam:
            print("is player on the team being waited on? {} != {}".format(playerTeam, teamWO))
            return
        # is player the position waited on?
        if positionWO != playerPos:
            print("is player the position waited on? {} != {}".format(playerPos, positionWO))
            return
        # number already submitted?
        if defNum == -1:
            print("number already submitted? no")
            return

        # passed check
        numList = re.findall('\d+', message.content)
        if numList.__len__() <= 0:
            await message.channel.send("Cannot find number in message.")
            return

        submittedNum = int(numList[0])
        if not (1 <= submittedNum <= 1000):
            await message.channel.send("Number must be between 1 and 1000 (inclusive).")
            return

        difference = Utils.getDifference(submittedNum, defNum)
        gameLogDefNum = defNum
        gNum = 0

        if status == 0:
            # check if pass/shot/deke
            playType = ""
            result = ""
            goalieStatus = "ingoal"
            if possession == "Home":
                if hGoaliePulled == 1:
                    goalieStatus = "pulled"
                if aGoaliePulled == 1:
                    goalieStatus = "open"
            else:
                if aGoaliePulled == 1:
                    goalieStatus = "pulled"
                if hGoaliePulled == 1:
                    goalieStatus = "open"
            msgContent = message.content.lower()
            if "pass" in msgContent and "shot" not in msgContent and "Deke" not in msgContent:
                playType = "pass"
                if goalieStatus == "pulled":
                    rangeTupleList = ranges[playType]["pulled"]
                else:
                    rangeTupleList = ranges[playType][playerType]
                result = ""
                for tup in rangeTupleList:
                    if tup[0] <= difference <= tup[1]:
                        result = tup[2]
                        break
            elif "shot" in msgContent and "pass" not in msgContent and "Deke" not in msgContent:
                playType = "shot"
                oppGoalie = None

                if playerTeam == gameHome:
                    oppGoalie = Database.getPlayerFromTeamAndPosition(gameAway, "Goalie")
                else:
                    oppGoalie = Database.getPlayerFromTeamAndPosition(gameHome, "Goalie")
                oppGoalieNums = goalieNums[oppGoalie[5]]
                gNum = oppGoalieNums.pop(0)
                goalieNums[oppGoalie[5]] = oppGoalieNums
                Database.updateGoalieCSV()
                gameLogDefNum = gNum
                if gameCleanPasses > 3:
                    cleanPassClamp = 3
                else:
                    cleanPassClamp = gameCleanPasses

                difference = Utils.getDifference(submittedNum, gNum)

                if goalieStatus == "open":
                    rangeTupleList = ranges[playType][cleanPassClamp]["open"]
                else:
                    rangeTupleList = ranges[playType][cleanPassClamp][playerType][goalieStatus]
                result = ""
                for tup in rangeTupleList:
                    if tup[0] <= difference <= tup[1]:
                        result = tup[2]
                        break
            elif "deke" in msgContent and "pass" not in msgContent and "shot" not in msgContent:
                playType = "deke"
                rangeTupleList = ranges[playType][playerType]
                result = ""
                for tup in rangeTupleList:
                    if tup[0] <= difference <= tup[1]:
                        result = tup[2]
                        break
            else:
                await message.channel.send("Could not find play type or too many play types found.")
                return

            resultStr = ""
            if result == 'breakaway':
                homePos = ''
                awayPos = ''
                if playType == "pass":
                    resultStr = "{} makes a great pass to their teammate, who gets behind the defense for a breakaway!".format(playerName)
                    if playerTeam == gameHome:
                        if playerPos == "Forward":
                            homePos = "Defense"
                        else:
                            homePos = "Forward"
                        awayPos = "Defense"
                    else:
                        if playerPos == "Forward":
                            awayPos = "Defense"
                        else:
                            awayPos = "Forward"
                        homePos = "Defense"
                elif playType == "deke":
                    resultStr = "{} dekes out the defender and finds themself with nobody between them and the goal!".format(playerName)
                    if playerTeam == gameHome:
                        if playerPos == "Forward":
                            homePos = "Forward"
                        else:
                            homePos = "Defense"
                        awayPos = "Defense"
                    else:
                        if playerPos == "Forward":
                            awayPos = "Forward"
                        else:
                            awayPos = "Defense"
                        homePos = "Defense"

                Database.updateGameVariable(gameID, 'moves', gameMoves-1)
                Database.updateGameVariable(gameID, 'status', 3)
                Database.updateGameVariable(gameID, 'cleanPasses', 0)

                Database.updateGameVariable(gameID, 'homePositionWaiting', homePos)
                Database.updateGameVariable(gameID, 'awayPositionWaiting', awayPos)
                Database.updateGameVariable(gameID, 'defenseNum', -1)
            elif result == 'clean':
                resultStr = "{} passes the puck cleanly to their teammate.".format(playerName)
                homePos = ''
                awayPos = ''
                if playerTeam == gameHome:
                    if playerPos == "Forward":
                        homePos = "Defense"
                    else:
                        homePos = "Forward"
                    awayPos = "Defense"
                else:
                    if playerPos == "Forward":
                        awayPos = "Defense"
                    else:
                        awayPos = "Forward"
                    homePos = "Defense"
                Database.updateGameVariable(gameID, 'moves', gameMoves - 1)
                Database.updateGameVariable(gameID, 'status', 0)
                Database.updateGameVariable(gameID, 'cleanPasses', gameCleanPasses+1)

                Database.updateGameVariable(gameID, 'homePositionWaiting', homePos)
                Database.updateGameVariable(gameID, 'awayPositionWaiting', awayPos)
                Database.updateGameVariable(gameID, 'defenseNum', -1)
            elif result == 'twoclean':
                resultStr = "In a reckless maneuver, {} heaves the puck down the ice. It's controlled just before it's an icing call, and the offense looks to be in a great position! (+2 CP)".format(playerName)
                homePos = ''
                awayPos = ''
                if playerTeam == gameHome:
                    if playerPos == "Forward":
                        homePos = "Defense"
                    else:
                        homePos = "Forward"
                    awayPos = "Defense"
                else:
                    if playerPos == "Forward":
                        awayPos = "Defense"
                    else:
                        awayPos = "Forward"
                    homePos = "Defense"
                Database.updateGameVariable(gameID, 'moves', gameMoves - 1)
                Database.updateGameVariable(gameID, 'status', 0)
                Database.updateGameVariable(gameID, 'cleanPasses', gameCleanPasses+2)

                Database.updateGameVariable(gameID, 'homePositionWaiting', homePos)
                Database.updateGameVariable(gameID, 'awayPositionWaiting', awayPos)
                Database.updateGameVariable(gameID, 'defenseNum', -1)
            elif result == 'sloppy':
                resultStr = "{} passes the puck sloppily to their teammate.".format(playerName)
                homePos = ''
                awayPos = ''
                if playerTeam == gameHome:
                    if playerPos == "Forward":
                        homePos = "Defense"
                    else:
                        homePos = "Forward"
                    awayPos = "Defense"
                else:
                    if playerPos == "Forward":
                        awayPos = "Defense"
                    else:
                        awayPos = "Forward"
                    homePos = "Defense"
                Database.updateGameVariable(gameID, 'moves', gameMoves - 1)
                Database.updateGameVariable(gameID, 'status', 0)

                Database.updateGameVariable(gameID, 'homePositionWaiting', homePos)
                Database.updateGameVariable(gameID, 'awayPositionWaiting', awayPos)
                Database.updateGameVariable(gameID, 'defenseNum', -1)
            elif result == 'offsides':
                resultStr = "{}'s pass goes offsides, and the puck will return to the faceoff circle.".format(playerName)

                Database.updateGameVariable(gameID, 'moves', gameMoves - 1)
                Database.updateGameVariable(gameID, 'status', 1)
                Database.updateGameVariable(gameID, 'cleanPasses', 0)

                Database.updateGameVariable(gameID, 'homePositionWaiting', "Forward")
                Database.updateGameVariable(gameID, 'awayPositionWaiting', "Forward")
                Database.updateGameVariable(gameID, 'defenseNum', -1)
            elif result == 'turnover':
                resultStr = "{}'s pass is intercepted by the other team!".format(playerName)

                if possession == "Home":
                    Database.updateGameVariable(gameID, 'possession', "Away")
                else:
                    Database.updateGameVariable(gameID, 'possession', "Home")

                Database.updateGameVariable(gameID, 'moves', gameMoves - 1)
                Database.updateGameVariable(gameID, 'status', 0)
                Database.updateGameVariable(gameID, 'cleanPasses', 0)

                Database.updateGameVariable(gameID, 'homePositionWaiting', "Defense")
                Database.updateGameVariable(gameID, 'awayPositionWaiting', "Defense")
                Database.updateGameVariable(gameID, 'defenseNum', -1)
            elif result == 'penalty':
                if playType == "pass":
                    resultStr = "{}'s pass misses their target, but their teammate is called for hooking! Penalty shot!".format(playerName)
                elif playType == "shot":
                    resultStr = "{} takes the shot, but their teammate gets called for goalie interference! Penalty shot!".format(playerName)
                elif playType == "deke":
                    resultStr = "{} gets laid out and the defense has it! There's nobody between him and the defense minder!".format(playerName)

                if possession == "Home":
                    Database.updateGameVariable(gameID, 'possession', "Away")
                    Database.updateGameVariable(gameID, 'homePositionWaiting', "Defense")
                    Database.updateGameVariable(gameID, 'awayPositionWaiting', random.choice(['Forward', 'Defense']))
                else:
                    Database.updateGameVariable(gameID, 'possession', "Home")
                    Database.updateGameVariable(gameID, 'homePositionWaiting', random.choice(['Forward', 'Defense']))
                    Database.updateGameVariable(gameID, 'awayPositionWaiting', "Defense")

                Database.updateGameVariable(gameID, 'moves', gameMoves - 1)
                Database.updateGameVariable(gameID, 'status', 2)
                Database.updateGameVariable(gameID, 'cleanPasses', 0)


                Database.updateGameVariable(gameID, 'defenseNum', -1)
            elif result == 'oppgoal':
                if playType == "shot":
                    resultStr = "{}'s shot is good, it finds the back of the net, and HE CELEBRATES! BUT WAIT, IT WAS ON HIS OWN GOAL!".format(playerName)
                elif playType == "pass":
                    resultStr = "{}'s pass is so bad that the ref awards the other team a goal.".format(playerName)
                elif playType == "deke":
                    resultStr = "{} tries to deke but he collides with his teammate! They are both down! It’s a two on O and the goalie slips trying to get back into position! They will walk it in for a goal!".format(playerName)

                if playerTeam == gameHome:
                    Database.updateGameVariable(gameID, 'possession', "Away")
                    Database.updateGameVariable(gameID, 'awayScore', gameAwayScore + 1)
                else:
                    Database.updateGameVariable(gameID, 'possession', "Home")
                    Database.updateGameVariable(gameID, 'homeScore', gameHomeScore + 1)

                Database.updateGameVariable(gameID, 'moves', gameMoves - 1)
                Database.updateGameVariable(gameID, 'status', 1)
                Database.updateGameVariable(gameID, 'cleanPasses', 0)


                Database.updateGameVariable(gameID, 'homePositionWaiting', "Forward")
                Database.updateGameVariable(gameID, 'awayPositionWaiting', "Forward")
                Database.updateGameVariable(gameID, 'defenseNum', -1)
            elif result == 'dekesuccess':
                resultStr = "{} successfully dekes out the defender.".format(playerName)

                homePos = ''
                awayPos = ''
                if playerTeam == gameHome:
                    if playerPos == "Forward":
                        homePos = "Forward"
                    else:
                        homePos = "Defense"
                    awayPos = "Defense"
                else:
                    if playerPos == "Forward":
                        awayPos = "Forward"
                    else:
                        awayPos = "Defense"
                    homePos = "Defense"
                Database.updateGameVariable(gameID, 'moves', gameMoves - 1)
                Database.updateGameVariable(gameID, 'cleanPasses', gameCleanPasses+1)
                Database.updateGameVariable(gameID, 'status', 0)

                Database.updateGameVariable(gameID, 'homePositionWaiting', homePos)
                Database.updateGameVariable(gameID, 'awayPositionWaiting', awayPos)
                Database.updateGameVariable(gameID, 'defenseNum', -1)
            elif result == 'twodeke':
                resultStr = "{} makes a move up the ice. He dekes to the left, and the defenseman is out of position! This could be a chance for the attackers!  (+2 CP)".format(playerName)

                homePos = ''
                awayPos = ''
                if playerTeam == gameHome:
                    if playerPos == "Forward":
                        homePos = "Forward"
                    else:
                        homePos = "Defense"
                    awayPos = "Defense"
                else:
                    if playerPos == "Forward":
                        awayPos = "Forward"
                    else:
                        awayPos = "Defense"
                    homePos = "Defense"
                Database.updateGameVariable(gameID, 'moves', gameMoves - 1)
                Database.updateGameVariable(gameID, 'cleanPasses', gameCleanPasses+2)
                Database.updateGameVariable(gameID, 'status', 0)

                Database.updateGameVariable(gameID, 'homePositionWaiting', homePos)
                Database.updateGameVariable(gameID, 'awayPositionWaiting', awayPos)
                Database.updateGameVariable(gameID, 'defenseNum', -1)
            elif result == 'dekefail':
                resultStr = "{} tries to deke out the defender, but the defenseman's stick manages to poke the puck out and take possession!".format(playerName)

                if possession == "Home":
                    Database.updateGameVariable(gameID, 'possession', "Away")
                else:
                    Database.updateGameVariable(gameID, 'possession', "Home")

                Database.updateGameVariable(gameID, 'moves', gameMoves - 1)
                Database.updateGameVariable(gameID, 'status', 0)
                Database.updateGameVariable(gameID, 'cleanPasses', 0)

                Database.updateGameVariable(gameID, 'homePositionWaiting', "Defense")
                Database.updateGameVariable(gameID, 'awayPositionWaiting', "Defense")
                Database.updateGameVariable(gameID, 'defenseNum', -1)
            elif result == 'goal':
                if playType == "shot":
                    resultStr = "{} takes a shot, and it finds the back of the net! GOAL!!!".format(playerName)
                elif playType == "pass":
                    resultStr = random.choice(["{} slips the puck up the ice. There's a commotion at the net and the pass deflects into the back of it! GOAL!".format(playerName),
                                               "{}'s pass is off the mark and pings off the boards. The goalie lost sight of the puck and it easily coasts into the goal! It's a GOAL!".format(playerName)])
                elif playType == "deke":
                    resultStr = "{} anticipates the defense and slaps the puck to the boards. Before {} can corral the puck back it's slipped into the back of the net! GOAL!".format(playerName, playerName)


                if playerTeam == gameHome:
                    Database.updateGameVariable(gameID, 'homeScore', gameHomeScore + 1)
                else:
                    Database.updateGameVariable(gameID, 'awayScore', gameAwayScore + 1)

                Database.updateGameVariable(gameID, 'moves', gameMoves - 1)
                Database.updateGameVariable(gameID, 'status', 1)
                Database.updateGameVariable(gameID, 'cleanPasses', 0)


                Database.updateGameVariable(gameID, 'homePositionWaiting', "Forward")
                Database.updateGameVariable(gameID, 'awayPositionWaiting', "Forward")
                Database.updateGameVariable(gameID, 'defenseNum', -1)
            elif result == 'rebound':
                resultStr = "The shot is stopped by the goalie, but the offense gets the rebound!"
                homePos, awayPos = "", ""

                if playerTeam == gameHome:
                    if playerPos == "Forward":
                        homePos = "Defense"
                    else:
                        homePos = "Forward"
                    awayPos = "Defense"
                else:
                    if playerPos == "Forward":
                        awayPos = "Defense"
                    else:
                        awayPos = "Forward"
                    homePos = "Defense"

                Database.updateGameVariable(gameID, 'moves', gameMoves - 1)
                Database.updateGameVariable(gameID, 'status', 0)
                Database.updateGameVariable(gameID, 'cleanPasses', 0)


                Database.updateGameVariable(gameID, 'homePositionWaiting', homePos)
                Database.updateGameVariable(gameID, 'awayPositionWaiting', awayPos)
                Database.updateGameVariable(gameID, 'defenseNum', -1)
            elif result == 'save':
                resultStr = "The shot is stopped by the goalie, and they hold on to it to bring up the faceoff."

                Database.updateGameVariable(gameID, 'moves', gameMoves - 1)
                Database.updateGameVariable(gameID, 'status', 1)
                Database.updateGameVariable(gameID, 'cleanPasses', 0)


                Database.updateGameVariable(gameID, 'homePositionWaiting', "Forward")
                Database.updateGameVariable(gameID, 'awayPositionWaiting', "Forward")
                Database.updateGameVariable(gameID, 'defenseNum', -1)
            elif result == 'block':
                resultStr = "The shot is blocked by the defense, who gains possession!"

                if playerTeam == gameHome:
                    Database.updateGameVariable(gameID, 'possession', "Away")
                else:
                    Database.updateGameVariable(gameID, 'possession', "Home")

                Database.updateGameVariable(gameID, 'moves', gameMoves - 1)
                Database.updateGameVariable(gameID, 'status', 0)
                Database.updateGameVariable(gameID, 'cleanPasses', 0)


                Database.updateGameVariable(gameID, 'homePositionWaiting', "Defense")
                Database.updateGameVariable(gameID, 'awayPositionWaiting', "Defense")
                Database.updateGameVariable(gameID, 'defenseNum', -1)

            if gNum != 0:
                responseMsg = bldResponse(g, submittedNum, playType, difference, resultStr, 'Goalie', gNum)
            else:
                responseMsg = bldResponse(g, submittedNum, playType, difference, resultStr, 'Defense', gNum)
            await message.channel.send(responseMsg)

            # add to gamelog
            offPlayer, defPlayer = "", ""
            if possession == "Home":
                offPlayer = Database.getPlayerFromTeamAndPosition(gameHome, homePositionWaiting)
                if playType != "shot":
                    defPlayer = Database.getPlayerFromTeamAndPosition(gameAway, awayPositionWaiting)
                else:
                    defPlayer = Database.getPlayerFromTeamAndPosition(gameAway, 'Goalie')
            else:
                if playType != "shot":
                    defPlayer = Database.getPlayerFromTeamAndPosition(gameHome, homePositionWaiting)
                else:
                    defPlayer = Database.getPlayerFromTeamAndPosition(gameHome, 'Goalie')
                offPlayer = Database.getPlayerFromTeamAndPosition(gameAway, awayPositionWaiting)

            insertRow = [WEEK, gameHome, gameAway, "normal", possession, offPlayer[1], submittedNum, defPlayer[1], gameLogDefNum, playType, difference, result, hGoaliePulled, aGoaliePulled, gamePeriod, gameMoves, gameHomeScore, gameAwayScore, gameCleanPasses]
            Database.addToGamelog(insertRow)
            Database.updateGameVariable(gameID, "last_message_time", str(datetime.datetime.now()))

            # SendNextMessage
            g = Database.getGameFromTeam(gameHome)
            gameID = g[0]
            gameHome = g[1]
            gameAway = g[2]
            gameChannelID = g[3]
            gamePeriod = g[4]
            gameMoves = g[5]
            status = g[6]
            gameHomeScore = g[8]
            gameAwayScore = g[9]

            # Power Play update!
            if result == "goal" or result == "oppgoal":
                channel = client.get_channel(POWERPLAYID)
                pStr = getPeriodStr(gamePeriod)
                await channel.send(
                    "**SCORE UPDATE**\n{} **{} {} |** {} **{} {}** | {} ({})".format(client.get_emoji(teamEmoji[gameHome]), gameHome,
                                                                                     gameHomeScore, client.get_emoji(teamEmoji[gameAway]),
                                                                                     gameAway, gameAwayScore, pStr,
                                                                                     gameMoves + 1))
                time.sleep(1)

            editStr = "{} {} - {} {} ({} moves | {})".format(gameHome, gameHomeScore, gameAwayScore, gameAway, gameMoves, getPeriodStr(gamePeriod))

            if gameMoves <= 0:
                Database.updateGameVariable(gameID, 'cleanPasses', 0)
                Database.updateGameVariable(gameID, 'hGoaliePulled', 0)
                Database.updateGameVariable(gameID, 'aGoaliePulled', 0)

                Database.updateGameVariable(gameID, 'period', gamePeriod + 1)
                gamePeriod = gamePeriod + 1
                if gamePeriod == 4:
                    if status == 2:
                        Database.updateGameVariable(gameID, 'moves', 1)
                    elif gameHomeScore == gameAwayScore:
                        # OT
                        print("OT")
                        Database.updateGameVariable(gameID, 'moves', 12)
                        Database.updateGameVariable(gameID, 'status', 1)
                        Database.updateGameVariable(gameID, 'homePositionWaiting', "Forward")
                        Database.updateGameVariable(gameID, 'awayPositionWaiting', "Forward")
                        await message.channel.send(
                            "That's the end of the period. Overtime! {} {} - {} {}.".format(client.get_emoji(teamEmoji[gameHome]),
                                                                                  gameHomeScore, gameAwayScore,
                                                                                  client.get_emoji(
                                                                                      teamEmoji[gameAway])))
                        time.sleep(1)

                    else:
                        # GameOVER
                        await message.channel.send(
                            "That's the end of the game. {} {} - {} {}.".format(client.get_emoji(teamEmoji[gameHome]),
                                                                                  gameHomeScore, gameAwayScore,
                                                                                  client.get_emoji(
                                                                                      teamEmoji[gameAway])))
                        time.sleep(1)
                        print("Over")
                        Database.deleteGame(gameID)
                        return
                elif gamePeriod == 5:
                    if gameHomeScore == gameAwayScore:
                        # Shootout
                        print("Shootout")
                    else:
                        # GameOVER
                        await message.channel.send(
                            "That's the end of the game. {} {} - {} {}.".format(client.get_emoji(teamEmoji[gameHome]),
                                                                                gameHomeScore, gameAwayScore,
                                                                                client.get_emoji(
                                                                                    teamEmoji[gameAway])))
                        print("Over")
                        Database.deleteGame(gameID)
                        return
                else:
                    # Next Period
                    Database.updateGameVariable(gameID, 'moves', PERIODLENGHT)
                    if status != 2:
                        Database.updateGameVariable(gameID, 'status', 1)
                        Database.updateGameVariable(gameID, 'homePositionWaiting', "Forward")
                        Database.updateGameVariable(gameID, 'awayPositionWaiting', "Forward")

                    await message.channel.send("That's the end of the period. {} {} - {} {}.".format(client.get_emoji(teamEmoji[gameHome]), gameHomeScore, gameAwayScore, client.get_emoji(teamEmoji[gameAway])))

            # check if game over or period over or goalie num missing

            g = Database.getGameFromTeam(gameHome)
            msgStr, teamWO, positionWO, typeWO = Utils.getWaitingOn(g)

            pWO = Database.getPlayerFromTeamAndPosition(teamWO, positionWO)
            user = client.get_user(pWO[5])

            homeGoal = Database.getPlayerFromTeamAndPosition(gameHome, "Goalie")
            awayGoal = Database.getPlayerFromTeamAndPosition(gameAway, "Goalie")

            goalieWaitH = False
            goalieWaitA = False
            if isinstance(goalieNums[homeGoal[5]], list) and goalieNums[homeGoal[5]].__len__() <= 0:
                Database.updateGameVariable(gameID, 'goalieHome', 1)
                goalieWaitH = True
            if isinstance(goalieNums[awayGoal[5]], list) and goalieNums[awayGoal[5]].__len__() <= 0:
                Database.updateGameVariable(gameID, 'goalieAway', 1)
                goalieWaitA = True

            if goalieWaitH is True or goalieWaitA is True:
                goalieMessage = createGoalieMessage(g)

                if goalieWaitH is True:
                    await client.get_user(homeGoal[5]).send(goalieMessage)
                if goalieWaitA is True:
                    await client.get_user(awayGoal[5]).send(goalieMessage)
                return

            if status == 0:
                if "pull goalie" in message.content.lower() and origPoss == possession:
                    if origPoss == "Home":
                        Database.updateGameVariable(gameID, 'hGoaliePulled', 1)
                    else:
                        Database.updateGameVariable(gameID, 'aGoaliePulled', 1)

                    await message.channel.send("Goalie has been pulled.")
                    time.sleep(1)

                await user.send(createMessage(g, 'defensive'))
            elif status == 1:
                Database.updateGameVariable(gameID, 'hGoaliePulled', 0)
                Database.updateGameVariable(gameID, 'aGoaliePulled', 0)
                await user.send(createMessage(g, 'faceoff'))
            elif status == 2:
                Database.updateGameVariable(gameID, 'hGoaliePulled', 0)
                Database.updateGameVariable(gameID, 'aGoaliePulled', 0)
                Database.updateGameVariable(gameID, 'defenseNum', 1)
                if possession == "Home":
                    Database.updateGameVariable(gameID, 'homePositionWaiting', "Forward")
                else:
                    Database.updateGameVariable(gameID, 'awayPositionWaiting', "Forward")
                g = Database.getGameFromTeam(gameHome)
                msgStr, teamWO, positionWO, typeWO = Utils.getWaitingOn(g)

                pWO = Database.getPlayerFromTeamAndPosition(teamWO, positionWO)
                user = client.get_user(pWO[5])
                disChannel = client.get_channel(gameChannelID)
                msgStr = createMessage(g, 'penalty')

                await disChannel.send(msgStr + " " + user.mention)
            elif status == 3:
                Database.updateGameVariable(gameID, 'hGoaliePulled', 0)
                Database.updateGameVariable(gameID, 'aGoaliePulled', 0)
                Database.updateGameVariable(gameID, 'defenseNum', 1)
                g = Database.getGameFromTeam(gameHome)
                msgStr, teamWO, positionWO, typeWO = Utils.getWaitingOn(g)

                pWO = Database.getPlayerFromTeamAndPosition(teamWO, positionWO)
                user = client.get_user(pWO[5])
                disChannel = client.get_channel(gameChannelID)
                msgStr = createMessage(g, 'breakaway')

                await disChannel.send(msgStr + " " + user.mention)

            await message.channel.edit(topic=editStr)
            time.sleep(1)
            return
        elif status == 1:
            Database.updateGameVariable(gameID, 'status', 0)
            Database.updateGameVariable(gameID, 'cleanPasses', 0)
            Database.updateGameVariable(gameID, 'defenseNum', -1)
            Database.updateGameVariable(gameID, 'homePositionWaiting', 'Defense')
            Database.updateGameVariable(gameID, 'awayPositionWaiting', 'Defense')

            faceoffWin = ""
            result = ""
            playType = "faceoff"

            if difference <= 15:
                # possession team win cleanly
                if possession == "Home":
                    faceoffWin = gameHome
                    result = "homefaceoffwinCP"
                    Database.updateGameVariable(gameID, 'possession', 'Home')
                else:
                    faceoffWin = gameAway
                    result = "awayfaceoffwinCP"
                    Database.updateGameVariable(gameID, 'possession', 'Away')
                Database.updateGameVariable(gameID, 'cleanPasses', 1)
                resultStr = "{} wins the faceoff cleanly, and they start a maneuver into the offensive zone!".format(faceoffWin)
            elif difference <= 250:
                # possession team win
                if possession == "Home":
                    faceoffWin = gameHome
                    result = "homefaceoffwin"
                    Database.updateGameVariable(gameID, 'possession', 'Home')
                else:
                    faceoffWin = gameAway
                    result = "awayfaceoffwin"
                    Database.updateGameVariable(gameID, 'possession', 'Away')

                resultStr = "{} wins the faceoff!".format(faceoffWin)
            elif difference >= 486:
                # possession team lose cleanly
                if possession == "Home":
                    faceoffWin = gameAway
                    result = "awayfaceoffwinCP"
                    Database.updateGameVariable(gameID, 'possession', 'Away')
                else:
                    faceoffWin = gameHome
                    result = "homefaceoffwinCP"
                    Database.updateGameVariable(gameID, 'possession', 'Home')
                Database.updateGameVariable(gameID, 'cleanPasses', 1)
                resultStr = "{} wins the faceoff cleanly, and they start a maneuver into the offensive zone!".format(faceoffWin)
            else:
                # possession team lose
                if possession == "Home":
                    faceoffWin = gameAway
                    result = "awayfaceoffwin"
                    Database.updateGameVariable(gameID, 'possession', 'Away')
                else:
                    faceoffWin = gameHome
                    result = "homefaceoffwin"
                    Database.updateGameVariable(gameID, 'possession', 'Home')
                resultStr = "{} wins the faceoff!".format(faceoffWin)

            responseMsg = bldResponse(g, submittedNum, 'faceoff', difference, resultStr, "Defense", -1)
            await message.channel.send(responseMsg)

            # add to gamelog
            offPlayer, defPlayer = "", ""
            if possession == "Home":
                offPlayer = Database.getPlayerFromTeamAndPosition(gameHome, homePositionWaiting)
                defPlayer = Database.getPlayerFromTeamAndPosition(gameAway, awayPositionWaiting)
            else:
                defPlayer = Database.getPlayerFromTeamAndPosition(gameHome, homePositionWaiting)
                offPlayer = Database.getPlayerFromTeamAndPosition(gameAway, awayPositionWaiting)
            insertRow = [WEEK, gameHome, gameAway, "faceoff", possession, offPlayer[1], submittedNum, defPlayer[1], defNum,
                         playType, difference, result, hGoaliePulled, aGoaliePulled, gamePeriod, gameMoves, gameHomeScore, gameAwayScore, gameCleanPasses]
            Database.addToGamelog(insertRow)
            Database.updateGameVariable(gameID, "last_message_time", str(datetime.datetime.now()))


            g = Database.getGameFromTeam(gameHome)
            status = g[6]

            msgStr, teamWO, positionWO, typeWO = Utils.getWaitingOn(g)

            pWO = Database.getPlayerFromTeamAndPosition(teamWO, positionWO)
            user = client.get_user(pWO[5])

            if status == 0:
                await user.send(createMessage(g, 'defensive'))
                return
            elif status == 1:
                await user.send(createMessage(g, 'faceoff'))
                return
            elif status == 2:
                await user.send(createMessage(g, 'penalty'))
                return
            elif status == 3:
                await user.send(createMessage(g, 'breakaway'))
                return
        elif status == 2:
            playType = "penalty"
            result = ""
            msgContent = message.content.lower()

            oppGoalie = None

            if playerTeam == gameHome:
                oppGoalie = Database.getPlayerFromTeamAndPosition(gameAway, "Goalie")
            else:
                oppGoalie = Database.getPlayerFromTeamAndPosition(gameHome, "Goalie")
            oppGoalieNums = goalieNums[oppGoalie[5]]
            gNum = oppGoalieNums.pop(0)
            goalieNums[oppGoalie[5]] = oppGoalieNums
            Database.updateGoalieCSV()
            gameLogDefNum = gNum

            difference = Utils.getDifference(submittedNum, gNum)
            rangeTupleList = ranges['penalty'][playerType]
            result = ""
            for tup in rangeTupleList:
                if tup[0] <= difference <= tup[1]:
                    result = tup[2]
                    break

            resultStr = ""

            if result == 'goal':
                resultStr = "{} takes a shot, and it finds the back of the net! GOAL!!!".format(playerName)

                if playerTeam == gameHome:
                    Database.updateGameVariable(gameID, 'homeScore', gameHomeScore + 1)
                else:
                    Database.updateGameVariable(gameID, 'awayScore', gameAwayScore + 1)

                Database.updateGameVariable(gameID, 'moves', gameMoves - 1)
                Database.updateGameVariable(gameID, 'status', 1)
                Database.updateGameVariable(gameID, 'cleanPasses', 0)

                Database.updateGameVariable(gameID, 'homePositionWaiting', "Forward")
                Database.updateGameVariable(gameID, 'awayPositionWaiting', "Forward")
                Database.updateGameVariable(gameID, 'defenseNum', -1)
            elif result == 'save':
                resultStr = "The shot is stopped by the goalie, and they hold on to it to bring up the faceoff."

                Database.updateGameVariable(gameID, 'moves', gameMoves - 1)
                Database.updateGameVariable(gameID, 'status', 1)
                Database.updateGameVariable(gameID, 'cleanPasses', 0)

                Database.updateGameVariable(gameID, 'homePositionWaiting', "Forward")
                Database.updateGameVariable(gameID, 'awayPositionWaiting', "Forward")
                Database.updateGameVariable(gameID, 'defenseNum', -1)

            responseMsg = bldResponse(g, submittedNum, playType, difference, resultStr, 'Goalie', gNum)
            await message.channel.send(responseMsg)

            # add to gamelog
            offPlayer, defPlayer = "", ""
            if possession == "Home":
                offPlayer = Database.getPlayerFromTeamAndPosition(gameHome, homePositionWaiting)
                defPlayer = Database.getPlayerFromTeamAndPosition(gameAway, 'Goalie')
            else:
                defPlayer = Database.getPlayerFromTeamAndPosition(gameHome, 'Goalie')
                offPlayer = Database.getPlayerFromTeamAndPosition(gameAway, awayPositionWaiting)

            insertRow = [WEEK, gameHome, gameAway, "penalty", possession, offPlayer[1], submittedNum, defPlayer[1], gameLogDefNum,
                         playType, difference, result, hGoaliePulled, aGoaliePulled, gamePeriod, gameMoves, gameHomeScore, gameAwayScore, gameCleanPasses]
            Database.addToGamelog(insertRow)
            Database.updateGameVariable(gameID, "last_message_time", str(datetime.datetime.now()))

            # SendNextMessage
            g = Database.getGameFromTeam(gameHome)
            gameID = g[0]
            gameHome = g[1]
            gameAway = g[2]
            gameChannelID = g[3]
            gamePeriod = g[4]
            gameMoves = g[5]
            status = g[6]
            gameHomeScore = g[8]
            gameAwayScore = g[9]

            # Power Play update!
            if result == "goal" or result == "oppgoal":
                channel = client.get_channel(POWERPLAYID)
                pStr = getPeriodStr(gamePeriod)
                await channel.send(
                    "**SCORE UPDATE**\n{} **{} {} |** {} **{} {}** | {} ({})".format(client.get_emoji(teamEmoji[gameHome]), gameHome,
                                                                                     gameHomeScore, client.get_emoji(teamEmoji[gameAway]),
                                                                                     gameAway, gameAwayScore, pStr,
                                                                                     gameMoves + 1))
                time.sleep(1)

            #await message.channel.edit(topic="{} {} - {} {} ({} moves | {})".format(gameHome, gameHomeScore, gameAwayScore, gameAway, gameMoves, getPeriodStr(gamePeriod)))

            if gameMoves <= 0:
                status = 1
                Database.updateGameVariable(gameID, 'cleanPasses', 0)

                Database.updateGameVariable(gameID, 'period', gamePeriod + 1)
                gamePeriod = gamePeriod + 1
                if gamePeriod == 4:
                    if gameHomeScore == gameAwayScore:
                        # OT
                        print("OT")
                        Database.updateGameVariable(gameID, 'moves', 12)
                        Database.updateGameVariable(gameID, 'status', 1)
                        Database.updateGameVariable(gameID, 'homePositionWaiting', "Forward")
                        Database.updateGameVariable(gameID, 'awayPositionWaiting', "Forward")
                    else:
                        # GameOVER
                        await message.channel.send(
                            "That's the end of the game. {} {} - {} {}.".format(client.get_emoji(teamEmoji[gameHome]),
                                                                                  gameHomeScore, gameAwayScore,
                                                                                  client.get_emoji(
                                                                                      teamEmoji[gameAway])))
                        print("Over")
                        Database.deleteGame(gameID)
                        return
                elif gamePeriod == 5:
                    if gameHomeScore == gameAwayScore:
                        # Shootout
                        print("Shootout")
                    else:
                        # GameOVER
                        await message.channel.send(
                            "That's the end of the game. {} {} - {} {}.".format(client.get_emoji(teamEmoji[gameHome]),
                                                                                gameHomeScore, gameAwayScore,
                                                                                client.get_emoji(
                                                                                    teamEmoji[gameAway])))
                        print("Over")
                        Database.deleteGame(gameID)
                        return
                else:
                    # Next Period
                    Database.updateGameVariable(gameID, 'moves', PERIODLENGHT)
                    Database.updateGameVariable(gameID, 'status', 1)
                    Database.updateGameVariable(gameID, 'homePositionWaiting', "Forward")
                    Database.updateGameVariable(gameID, 'awayPositionWaiting', "Forward")

                    await message.channel.send("That's the end of the period. {} {} - {} {}.".format(client.get_emoji(teamEmoji[gameHome]), gameHomeScore, gameAwayScore, client.get_emoji(teamEmoji[gameAway])))


            # check if game over or period over or goalie num missing

            msgStr, teamWO, positionWO, typeWO = Utils.getWaitingOn(g)

            pWO = Database.getPlayerFromTeamAndPosition(teamWO, positionWO)
            user = client.get_user(pWO[5])

            homeGoal = Database.getPlayerFromTeamAndPosition(gameHome, "Goalie")
            awayGoal = Database.getPlayerFromTeamAndPosition(gameAway, "Goalie")

            goalieWaitH = False
            goalieWaitA = False
            if isinstance(goalieNums[homeGoal[5]], list) and goalieNums[homeGoal[5]].__len__() <= 0:
                Database.updateGameVariable(gameID, 'goalieHome', 1)
                goalieWaitH = True
            if isinstance(goalieNums[awayGoal[5]], list) and goalieNums[awayGoal[5]].__len__() <= 0:
                Database.updateGameVariable(gameID, 'goalieAway', 1)
                goalieWaitA = True

            if goalieWaitH is True or goalieWaitA is True:
                goalieMessage = createGoalieMessage(g)

                if goalieWaitH is True:
                    await client.get_user(homeGoal[5]).send(goalieMessage)
                if goalieWaitA is True:
                    await client.get_user(awayGoal[5]).send(goalieMessage)
                return

            # status must = 1
            Database.updateGameVariable(gameID, 'hGoaliePulled', 0)
            Database.updateGameVariable(gameID, 'aGoaliePulled', 0)
            await user.send(createMessage(g, 'faceoff'))
            return
        elif status == 3:
            playType = "breakaway"
            result = ""
            msgContent = message.content.lower()

            oppGoalie = None

            if playerTeam == gameHome:
                oppGoalie = Database.getPlayerFromTeamAndPosition(gameAway, "Goalie")
            else:
                oppGoalie = Database.getPlayerFromTeamAndPosition(gameHome, "Goalie")
            oppGoalieNums = goalieNums[oppGoalie[5]]
            gNum = oppGoalieNums.pop(0)
            goalieNums[oppGoalie[5]] = oppGoalieNums
            Database.updateGoalieCSV()
            gameLogDefNum = gNum

            difference = Utils.getDifference(submittedNum, gNum)
            rangeTupleList = ranges['penalty'][playerType]
            result = ""
            for tup in rangeTupleList:
                if tup[0] <= difference <= tup[1]:
                    result = tup[2]
                    break

            resultStr = ""

            if result == 'goal':
                resultStr = "{} takes a shot, and it finds the back of the net! GOAL!!!".format(playerName)

                if playerTeam == gameHome:
                    Database.updateGameVariable(gameID, 'homeScore', gameHomeScore + 1)
                else:
                    Database.updateGameVariable(gameID, 'awayScore', gameAwayScore + 1)

                Database.updateGameVariable(gameID, 'moves', gameMoves - 1)
                Database.updateGameVariable(gameID, 'status', 1)
                Database.updateGameVariable(gameID, 'cleanPasses', 0)


                Database.updateGameVariable(gameID, 'homePositionWaiting', "Forward")
                Database.updateGameVariable(gameID, 'awayPositionWaiting', "Forward")
                Database.updateGameVariable(gameID, 'defenseNum', -1)
            elif result == 'save':
                resultStr = "The shot is stopped by the goalie, and they hold on to it to bring up the faceoff."

                Database.updateGameVariable(gameID, 'moves', gameMoves - 1)
                Database.updateGameVariable(gameID, 'status', 1)
                Database.updateGameVariable(gameID, 'cleanPasses', 0)


                Database.updateGameVariable(gameID, 'homePositionWaiting', "Forward")
                Database.updateGameVariable(gameID, 'awayPositionWaiting', "Forward")
                Database.updateGameVariable(gameID, 'defenseNum', -1)

            responseMsg = bldResponse(g, submittedNum, playType, difference, resultStr, 'Goalie', gNum)
            await message.channel.send(responseMsg)

            # add to gamelog
            offPlayer, defPlayer = "", ""
            if possession == "Home":
                offPlayer = Database.getPlayerFromTeamAndPosition(gameHome, homePositionWaiting)
                defPlayer = Database.getPlayerFromTeamAndPosition(gameAway, 'Goalie')
            else:
                defPlayer = Database.getPlayerFromTeamAndPosition(gameHome, 'Goalie')
                offPlayer = Database.getPlayerFromTeamAndPosition(gameAway, awayPositionWaiting)

            insertRow = [WEEK, gameHome, gameAway, "breakaway", possession, offPlayer[1], submittedNum, defPlayer[1], gameLogDefNum, playType, difference, result, hGoaliePulled, aGoaliePulled, gamePeriod, gameMoves, gameHomeScore, gameAwayScore, gameCleanPasses]
            Database.addToGamelog(insertRow)
            Database.updateGameVariable(gameID, "last_message_time", str(datetime.datetime.now()))

            # SendNextMessage
            g = Database.getGameFromTeam(gameHome)
            gameID = g[0]
            gameHome = g[1]
            gameAway = g[2]
            gameChannelID = g[3]
            gamePeriod = g[4]
            gameMoves = g[5]
            status = g[6]
            gameHomeScore = g[8]
            gameAwayScore = g[9]

            # Power Play update!
            if result == "goal" or result == "oppgoal":
                channel = client.get_channel(POWERPLAYID)
                pStr = getPeriodStr(gamePeriod)
                await channel.send(
                    "**SCORE UPDATE**\n{} **{} {} |** {} **{} {}** | {} ({})".format(client.get_emoji(teamEmoji[gameHome]), gameHome,
                                                                                     gameHomeScore, client.get_emoji(teamEmoji[gameAway]),
                                                                                     gameAway, gameAwayScore, pStr,
                                                                                     gameMoves + 1))
                time.sleep(1)
            #await message.channel.edit(topic="{} {} - {} {} ({} moves | {})".format(gameHome, gameHomeScore, gameAwayScore, gameAway, gameMoves, getPeriodStr(gamePeriod)))

            if gameMoves <= 0:
                status = 1
                Database.updateGameVariable(gameID, 'cleanPasses', 0)

                Database.updateGameVariable(gameID, 'period', gamePeriod + 1)
                gamePeriod = gamePeriod + 1
                if gamePeriod == 4:
                    if gameHomeScore == gameAwayScore:
                        # OT
                        print("OT")
                        Database.updateGameVariable(gameID, 'moves', 12)
                        Database.updateGameVariable(gameID, 'status', 1)
                        Database.updateGameVariable(gameID, 'homePositionWaiting', "Forward")
                        Database.updateGameVariable(gameID, 'awayPositionWaiting', "Forward")
                    else:
                        # GameOVER
                        await message.channel.send(
                            "That's the end of the game. {} {} - {} {}.".format(client.get_emoji(teamEmoji[gameHome]),
                                                                                gameHomeScore, gameAwayScore,
                                                                                client.get_emoji(
                                                                                    teamEmoji[gameAway])))
                        print("Over")
                        Database.deleteGame(gameID)
                        return
                elif gamePeriod == 5:
                    if gameHomeScore == gameAwayScore:
                        # Shootout
                        print("Shootout")
                    else:
                        # GameOVER
                        await message.channel.send(
                            "That's the end of the game. {} {} - {} {}.".format(client.get_emoji(teamEmoji[gameHome]),
                                                                                gameHomeScore, gameAwayScore,
                                                                                client.get_emoji(
                                                                                    teamEmoji[gameAway])))
                        print("Over")
                        Database.deleteGame(gameID)
                        return
                else:
                    # Next Period
                    Database.updateGameVariable(gameID, 'moves', PERIODLENGHT)
                    Database.updateGameVariable(gameID, 'status', 1)
                    Database.updateGameVariable(gameID, 'homePositionWaiting', "Forward")
                    Database.updateGameVariable(gameID, 'awayPositionWaiting', "Forward")

                    await message.channel.send(
                        "That's the end of the period. {} {} - {} {}.".format(client.get_emoji(teamEmoji[gameHome]),
                                                                              gameHomeScore, gameAwayScore,
                                                                              client.get_emoji(teamEmoji[gameAway])))

            # check if game over or period over or goalie num missing

            msgStr, teamWO, positionWO, typeWO = Utils.getWaitingOn(g)

            pWO = Database.getPlayerFromTeamAndPosition(teamWO, positionWO)
            user = client.get_user(pWO[5])

            homeGoal = Database.getPlayerFromTeamAndPosition(gameHome, "Goalie")
            awayGoal = Database.getPlayerFromTeamAndPosition(gameAway, "Goalie")

            goalieWaitH = False
            goalieWaitA = False
            if isinstance(goalieNums[homeGoal[5]], list) and goalieNums[homeGoal[5]].__len__() <= 0:
                Database.updateGameVariable(gameID, 'goalieHome', 1)
                goalieWaitH = True
            if isinstance(goalieNums[awayGoal[5]], list) and goalieNums[awayGoal[5]].__len__() <= 0:
                Database.updateGameVariable(gameID, 'goalieAway', 1)
                goalieWaitA = True

            if goalieWaitH is True or goalieWaitA is True:
                goalieMessage = createGoalieMessage(g)

                if goalieWaitH is True:
                    await client.get_user(homeGoal[5]).send(goalieMessage)
                if goalieWaitA is True:
                    await client.get_user(awayGoal[5]).send(goalieMessage)
                return

            # status must = 1
            Database.updateGameVariable(gameID, 'hGoaliePulled', 0)
            Database.updateGameVariable(gameID, 'aGoaliePulled', 0)
            await user.send(createMessage(g, 'faceoff'))
            return

# Creates message prompt.
def createMessage(gameInfo, type):
    time.sleep(1)
    period = gameInfo[4]
    cleanPasses = gameInfo[7]
    cleanPassStr = ""
    if type == "offensive":
        cleanPassStr = "{} clean pass(es).".format(cleanPasses)

    periodStr = ""
    if period == 1:
        periodStr = "1st"
    elif period == 2:
        periodStr = "2nd"
    elif period == 3:
        periodStr = "3rd"
    elif period == 4:
        periodStr = "OT"
    elif period == 5:
        periodStr = "SO"

    messageStr = """{} **{} {} |** {} **{} {}** | {}
{} moves remaining. {}

Call a {} number (1-1000).""".format(client.get_emoji(teamEmoji[gameInfo[1]]), gameInfo[1], gameInfo[8],
                                     client.get_emoji(teamEmoji[gameInfo[2]]), gameInfo[2], gameInfo[9], periodStr, gameInfo[5], cleanPassStr, type)
    return messageStr

# Creates goalie message prompt.
def createGoalieMessage(gameInfo):
    time.sleep(1)
    msg = """Hello! I need a list of numbers for {} @ {}. At any time you can replace your list by calling
`replace` in your list message or append a second list by simply listing out numbers. You may also call `!viewnumbers`
to view your list. Good luck!""".format(gameInfo[2], gameInfo[1])
    return msg

# Builds a result response.
def bldResponse(gameInfo, offense, playType, difference, resultStr, defNumOrGoalie, goalieNum):
    time.sleep(1)
    period = gameInfo[4]
    defNum = gameInfo[13]
    dNum = 0
    if defNumOrGoalie == "Goalie":
        dNum = goalieNum
    else:
        dNum = defNum

    periodStr = ""
    if period == 1:
        periodStr = "1st"
    elif period == 2:
        periodStr = "2nd"
    elif period == 3:
        periodStr = "3rd"
    elif period == 4:
        periodStr = "OT"
    elif period == 5:
        periodStr = "SO"

    messageStr = """{} **{} {} |** {} **{} {}** | {}
Offense: {} ({})
{}: {}
Difference: {}
    
{}""".format(client.get_emoji(teamEmoji[gameInfo[1]]), gameInfo[1], gameInfo[8],
                                         client.get_emoji(teamEmoji[gameInfo[2]]), gameInfo[2], gameInfo[9], periodStr,
                                         offense, playType, defNumOrGoalie, dNum, difference, resultStr)
    return messageStr

# Helper function to convert a period number to string.
def getPeriodStr(period):
    periodStr = ""
    if period == 1:
        periodStr = "1st"
    elif period == 2:
        periodStr = "2nd"
    elif period == 3:
        periodStr = "3rd"
    elif period == 4:
        periodStr = "OT"
    elif period == 5:
        periodStr = "SO"
    return periodStr

client.run(TOKEN)