import Database

def processStartGame(message, commandInfo):
    gameChannelID = message.channel.id
    if Database.checkIfChannelOccupied(gameChannelID):
        return "Channel is occupied."
    else:
        Database.addGame(commandInfo[0].title(), commandInfo[1].title(), gameChannelID)

    return "I hear ya. Game started."
