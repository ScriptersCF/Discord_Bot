import discord, random, json, sqlite3, math, confusables, urllib.request, copy, asyncio, os, shutil
from datetime import datetime
from contextlib import contextmanager
import threading, _thread

client = discord.Client()
server = "306153640023031820"
testserver = "461643418725122086"

Filter = json.loads(open("filter.json").read())
SeriousFilter = json.loads(open("seriousfilter.json").read())
FunAndGames = "349255881977757696"
Logs = "332883332528603146"
Pending = "346605168596353024"
Donations = "473852097415086090"
Moderators = "306155459667165184"
Suggestions = "639942887152549899"
Winners = "640960718824275968" 
Logged = "370937658920271874"

Prefix = "!"
LastMessage = 0
PrevUserMessages = {}

ObtainableRoles = {
    "Regular": 2000,
    "10,000+ Club": 10000,
    "20,000+ Club": 20000,
    "50,000+ Club": 50000,
    "100,000+ Club": 100000,
    "250,000+ Club": 250000
}

PublicChannels = [
    "306153640023031820",
    "306156119519264770",
    "308549999250112512",
    "379023623245004810",
    "432542646322462740",
    "349255881977757696"
]

ChannelPoints = {
    "349255881977757696": 0,
    "306885827189800960": 3,
    "351182527316099072": 3,
    "372506961171841025": 2,
    "639153031619018752": 2,
    "306156119519264770": 2,
    "462394160629153812": 2
}

Colours = [
    "Maroon",
    "Wheat",
    "Lime",
    "Blue",
    "Hot Pink",
    "Green",
    "Yellow",
    "Cyan",
    "Purple",
    "Brown",
    "Blurple",
    "Orange",
    "Coral",
    "Navy Blue",
    "Fuchsia",
    "Black",
    "Gold",
    "Plum",
    "White",
    "Red"
]

ToLog = ""

"""class TimeoutException(Exception):
    def __init__(self, msg=''):
        self.msg = msg

@contextmanager
def time_limit(seconds, msg=''):
    timer = threading.Timer(seconds, lambda: _thread.interrupt_main())
    timer.start()
    try:
        yield
    except KeyboardInterrupt:
        return
    finally:
        # if the action ends in specified time, timer is canceled
        timer.cancel()"""

def BracketContents(Name):
    Log = False
    New = ""
    for i in Name:
        if i == "]":
            Log = False
        if Log:
            New += i
        if i == "[":
            Log = True
    return New

def RemoveBrackets(Name):
    return Name.replace(BracketContents(Name), "").replace("[", "").replace("]", "")

def CheckName(Name):
    if Name.count("[") == 1 and Name.count("]") == 1:
        return (Name.find("[") < Name.find("]")) and Name.find("[") > 0 and Name.find("]") == len(Name) - 1
    return False

def ListContainsPhrase(List, Phrase):
    for i in List:
        if Phrase in i:
            return True
    return False

def Execute(Type, Command):
    Database = sqlite3.connect("scores.sqlite")
    Cursor = Database.cursor()
    Cursor.execute(Command)
    if Type == "Get":
        AllData = Cursor.fetchall()
        Database.close()
        return AllData
    elif Type == "Set":
        Database.commit()
        Database.close()

async def SendLevelMsg(User, Channel, Title, Description):
    Embed = discord.Embed(
        title = Title,
        description = Description,
        color = 0x0094ff
    )
    Embed.set_thumbnail(url = User.avatar_url or "https://discordapp.com/assets/322c936a8c8be1b803cd94861bdfa868.png")
    await client.send_message(Channel, embed = Embed)

async def AddPoints(User, Amount, Channel):
    Data = Execute(
        "Get",
        "SELECT * FROM scores WHERE userId = \"" + User.id + "\""
    )
    if Data != []:
        NewPoints = Data[0][1] + Amount
        NewWkPoints = (Data[0][9] or 0) + (Amount if Amount < 5 else 1)
        NewLevel = 1 + (math.floor(0.3 * math.sqrt(NewPoints)))
        if NewLevel != Data[0][2]:
            #sql.run(`UPDATE scores SET points = ${row.points + amount} WHERE userId = ${member.id}`);
            Execute(
                "Set",
                "UPDATE scores SET level = " + str(NewLevel) + " WHERE userId = " + User.id
            )
            await SendLevelMsg(User, Channel, "Level up!", "Congratulations, <@" + User.id + ">!\nYou've just levelled up to **level " + str(NewLevel) + "!**")

        Execute("Set","UPDATE scores SET points = " + str(NewPoints) + " WHERE userId = " + User.id)
        Execute("Set","UPDATE scores SET wkPoints = " + str(NewWkPoints) + " WHERE userId = " + User.id)

        for i in ObtainableRoles:
            Role = discord.utils.get(server.roles, name=i)
            if NewPoints >= ObtainableRoles[i] and Role not in User.roles:
                await client.add_roles(User, Role)
                Msg = "Congratulations, <@" + User.id + ">!\nYou've just obtained the **" + i + "** role!"
                if "100,000" in i and not any("Custom //" in x.name for x in User.roles):
                    Msg += "\nYou can now use the `!changecolour` command!" 
                    await client.add_roles(User, discord.utils.get(server.roles, name = "Custom // Lime"))
                await SendLevelMsg(User, Channel, "Level up!", Msg)
        
        Role = discord.utils.get(server.roles, name = "Verified Lvl.2")
        if NewPoints >= 30 and Role not in User.roles and (User.joined_at.timestamp() + 259200) < datetime.utcnow().timestamp():
            await client.add_roles(User, Role)
            await SendLevelMsg(User, Channel, "Level up!", "Congratulations, <@" + User.id + ">!\nYou've just obtained the **Verified Lvl.2** role!")

async def GetLevel(User):
    RoleLevels = {
        "Owner": 8,
        "Administrator": 7,
        "Senior Moderator": 6,
        "Moderator": 5,
        "Trial Moderator": 4,
        "Regular": 3,
        "Verified Lvl.2": 2,
        "Verified": 1
    }
    Roles = ["Owner", "Administrator", "Senior Moderator", "Moderator", "Trial Moderator", "Regular", "Verified Lvl.2", "Verified"]
    UserRoles = [i.name for i in User.roles]
    for i in Roles:
        if i in UserRoles:
            return RoleLevels[i]
    return 0

async def ToggleRole(User, RoleName):
    Role = discord.utils.get(server.roles, name=RoleName)
    if Role in User.roles:
        await client.remove_roles(User, Role)
    else:
        await client.add_roles(User, Role)

async def SendEmbed(Channel, Title, Content):
    try:
        return await client.send_message(
            Channel,
            embed = discord.Embed(
                title = Title,
                description = Content,
                color = 0x0094ff
            )
        )
    except Exception as e:
        print("1",e)

async def Help(Message, Args):
    await SendEmbed(
        Message.author,
        "Help",
        """
**Commands**
`!help` - Displays general help for the Mr. SCF bot
`!gang help` - Displays help with gang usage
`g:help` - Displays help for Gamer bot used in <#349255881977757696>
`!stats @user OR <num>` - Displays the stats of a user
`!leaderboard` - Displays the top 10 users in the server
`!report @user reason` - Reports a user for breaking our rules
`!forhire` - Gives you the `For Hire` role
`!notforhire` - Gives you the `Not For Hire` role
`!scripter` - Gives you the `Scripter` role
`!learner` - Gives you the `Learner` role
`!roll 5d3` - Rolls 5 dice with a max of 3 per dice
`!rolldie` - Rolls a die
`!latex <equation>` - Displays a LaTeX equation

**Scripting**
[Look through our open-source games](https://discordapp.com/channels/306153640023031820/543874721603911690)
[Read the Lua PIL guide](https://cdn.discordapp.com/attachments/306156119519264770/575829412235313172/Programming_in_Lua_5.1.pdf)
[Take a look at the Roblox Wiki](https://developer.roblox.com)
[Check out our YouTube tutorials](https://www.youtube.com/scripterscf) *(Coming Soon)*

**Miscellaneous**
[View our rules](https://discordapp.com/channels/306153640023031820/306155109203836928)
[Support us on Roblox](https://www.roblox.com/games/960878638/Donate)
[Support us on Patreon](https://patreon.com/ScriptersCF)"""
    )

async def RollDie(Message, Args):
    await SendEmbed(
        Message.channel,
        "Results",
        "🎲 " + str(random.randint(1, 6))
    )

async def Roll(Message, Args):
    if Message.channel.id == FunAndGames:
        if Args == []:
            await RollDie(Message, Args)
            return
        Info = Args[0].split("d")
        RollNum = int(Info[0])
        RollMax = int(Info[1])
        if 1 <= RollNum <= 50 and 1 <= RollMax <= 500:
            Results = []
            for i in range(RollNum):
                Results += [random.randint(1, RollMax)]
            await SendEmbed(
                Message.channel,
                "Results",
                "🎲 Total: **" + str(sum(Results)) + "** (" + ", ".join(map(str, Results)) + ")"
            )
        else:
            await client.send_message(Message.channel, "Sorry, the values provided are too large!")

async def ForHire(Message, Args):
    await ToggleRole(Message.author, "For Hire")

async def NotForHire(Message, Args):
    await ToggleRole(Message.author, "Not For Hire")

async def Scripter(Message, Args):
    await ToggleRole(Message.author, "Scripter")

async def Learner(Message, Args):
    await ToggleRole(Message.author, "Learner")

async def Increase(User, Type):
    Amount = Execute("Get", "SELECT " + Type + "s from scores WHERE userId = " + User.id)[0][0]
    if not Amount:
        Amount = 0
    Execute(
        "Set",
        "UPDATE scores SET " + Type + "s = " + str(Amount + 1) + " WHERE userId = " + User.id
    )

async def Punish(User, Type, End):
    if Execute("Get", "SELECT " + Type + "End FROM punishments WHERE userId = \"" + User.id + "\"") == []:
        Execute("Set", "INSERT INTO punishments (userId, " + Type + "End) VALUES (" + User.id + ", " + str(End) + ")")
    Execute("Set", "UPDATE punishments SET " + Type + "End = " + str(End) + " WHERE userId = " + User.id)

async def Mute(Message, Args):
    Targets = []
    Reason = "N/A"
    Time = 0
    Count = 0
    #print(1)
    for i in Args:
        if i[:2] == "<@":
            Targets += [Message.mentions[Count]]
        elif i.isdigit():
            Time = int(i)
        else:
            Reason = " ".join(Args[Count:])
            break
        Count += 1
    #print(2)
    Role = discord.utils.get(server.roles, name="Muted")
    #print(3)
    for i in Targets:
        #print(4)
        if await GetLevel(i) <= 4:
            #print(5)
            await client.add_roles(i, Role)
            await SendEmbed(
                i,
                "ScriptersCF",
                "You have been muted in the ScriptersCF Discord Server, for " + str(Time or "N/A") + """ minutes, for the following reason:
```""" + Reason + """```If you feel you have been moderated by mistake, please contact a staff member."""
            )
            await Increase(i, "mute")
            await Punish(i, "mute", [999999999999, Time * 60 + datetime.utcnow().timestamp()][Time > 0])
    print(6)
    await SendEmbed(
        client.get_channel(Logs),
        "Mute",
        "**Moderator**: <@" + Message.author.id + """>
**Targets**: """ + ", ".join(["<@" + i.id + ">" for i in Targets]) + """
**Length**: """ + str(Time or "N/A") + """ minutes
**Reason**: """ + Reason
    )

async def Unmute(Message, Args):
    Count = 0
    Targets = []
    for i in Args:
        if i[:2] == "<@":
            Targets += [Message.mentions[Count]]
            Count += 1
        else:
            break
    Role = discord.utils.get(server.roles, name="Muted")
    for i in Targets:
        try:
            await client.remove_roles(i, Role)
            await SendEmbed(
                i,
                "ScriptersCF",
                "You have been unmuted in the ScriptersCF Discord Server. Please review our <#306155109203836928> channel to ensure you aren't punished again."
            )
            Execute("Set", "UPDATE punishments SET muteEnd = NULL WHERE userId = " + i.id)
        except Exception as e:
            print("2",e)
    await SendEmbed(
        client.get_channel(Logs),
        "Unmute",
        "**Moderator**: <@" + Message.author.id + """>
**Targets**: """ + ", ".join(["<@" + i.id + ">" for i in Targets])
    )

async def Kick(Message, Args):
    Count = 0
    Targets = []
    Reason = "N/A"
    for i in Args:
        if i[:2] == "<@":
            Targets += [Message.mentions[Count]]
            Count += 1
        else:
            Reason = " ".join(Args[Count:])
            break
    for i in Targets:
        if await GetLevel(i) <= 4:
            await SendEmbed(
                i,
                "ScriptersCF",
                """You have been kicked from the ScriptersCF Discord Server for the following reason:
```""" + Reason + """```"""
            )
            await Increase(i, "kick")
            await client.kick(i)
    await SendEmbed(
        client.get_channel(Logs),
        "Kick",
        "**Moderator**: <@" + Message.author.id + """>
**Targets**: """ + ", ".join(["<@" + i.id + ">" for i in Targets]) + """
**Reason**: """ + Reason
    )

async def Ban(Message, Args):
    Count = 0
    Targets = []
    Reason = "N/A"
    for i in Args:
        if i[:2] == "<@":
            Targets += [Message.mentions[Count]]
            Count += 1
        else:
            Reason = " ".join(Args[Count:])
            break
    for i in Targets:
        if await GetLevel(i) <= 4:
            await SendEmbed(
                i,
                "ScriptersCF",
                """You have been banned from the ScriptersCF Discord Server for the following reason:
```""" + Reason + """```If you feel you have been banned by mistake, please appeal [here](https://forms.gle/Rzd4QvLJYyo3BkQg6)."""
            )
            await Increase(i, "ban")
            await client.ban(i)
    await SendEmbed(
        client.get_channel(Logs),
        "Ban",
        "**Moderator**: <@" + Message.author.id + """>
**Targets**: """ + ", ".join(["<@" + i.id + ">" for i in Targets]) + """
**Reason**: """ + Reason
    )

async def Report(Message, Args):
    Count = 0
    Targets = []
    Reason = "N/A"
    for i in Args:
        if i[:2] == "<@":
            Targets += [Message.mentions[Count]]
            Count += 1
        else:
            Reason = " ".join(Args[Count:])
            break
    await SendEmbed(
        Message.author,
        "ScriptersCF",
        """Thank you, your report has been submitted for review.
If there is an emergency, please tag the moderator role for a quick response.

Please note that false reports are not permitted and will result in punishment."""
    )
    await SendEmbed(
        client.get_channel(Logs),
        "Report",
        "**Reporter**: <@" + Message.author.id + """>
**Channel**: <#""" + Message.channel.id + """>
**Targets**: """ + ", ".join(["<@" + i.id + ">" for i in Targets]) + """
**Reason**: """ + Reason
    )
    await client.delete_message(Message)

async def Clear(Message, Args):
    Amount = int(Args[0]) + 1
    if 2 <= Amount <= 99:
        await client.purge_from(Message.channel, limit = Amount)
        await SendEmbed(
            client.get_channel(Logs),
            "Clear",
            "**Moderator**: <@" + Message.author.id + """>
**Channel**: <#""" + Message.channel.id + """>
**Amount**: """ + Args[0]
        )
    else:
        await SendEmbed(
            Message.channel,
            "Clear",
            "❗ Amount must be between 1 and 98"
        )

async def Lock(Message, Args):
    Reason = " ".join(Args) or "N/A"
    Overwrite = discord.PermissionOverwrite()
    Overwrite.send_messages = False
    Overwrite.read_messages = True
    await client.edit_channel_permissions(Message.channel, discord.utils.get(server.roles, name = "Verified"), Overwrite)
    await SendEmbed(
        client.get_channel(Logs),
        "Lock",
        "**Moderator**: <@" + Message.author.id + """>
**Channel**: <#""" + Message.channel.id + """>
**Reason**: """ + Reason
    )

async def Lockdown(Message, Args):
    Reason = " ".join(Args) or "N/A"
    Overwrite = discord.PermissionOverwrite()
    Overwrite.send_messages = False
    Overwrite.read_messages = True
    for i in PublicChannels:
        await client.edit_channel_permissions(client.get_channel(i), discord.utils.get(server.roles, name = "Verified"), Overwrite)
    await client.send_message(Message.channel, "<@&" + Moderators + "> **EMERGENCY LOCKDOWN ACTIVATED**")
    await SendEmbed(
        client.get_channel(Logs),
        "Lockdown",
        "**Moderator**: <@" + Message.author.id + """>
**Channel**: <#""" + Message.channel.id + """>
**Reason**: """ + Reason
    )

async def Unlock(Message, Args):
    Overwrite = discord.PermissionOverwrite()
    Overwrite.read_messages = True
    await client.edit_channel_permissions(Message.channel, discord.utils.get(server.roles, name = "Verified"), Overwrite)
    await SendEmbed(
        client.get_channel(Logs),
        "Unlock",
        "**Moderator**: <@" + Message.author.id + """>
**Channel**: <#""" + Message.channel.id + ">"
    )

async def Unlockdown(Message, Args):
    Overwrite = discord.PermissionOverwrite()
    Overwrite.read_messages = True
    for i in PublicChannels:
        await client.edit_channel_permissions(client.get_channel(i), discord.utils.get(server.roles, name = "Verified"), Overwrite)
    await SendEmbed(
        client.get_channel(Logs),
        "Unlockdown",
        "**Moderator**: <@" + Message.author.id + """>
**Channel**: <#""" + Message.channel.id + ">"
    )

async def SHBan(Message, Args):
    Targets = []
    Reason = "N/A"
    Time = 0
    Count = 0
    for i in Args:
        if i[:2] == "<@":
            Targets += [Message.mentions[Count]]
        elif i.isdigit():
            Time = int(i)
        else:
            Reason = " ".join(Args[Count:])
            break
        Count += 1
    Role = discord.utils.get(server.roles, name="S&H_Ban")
    for i in Targets:
        if await GetLevel(i) <= 4:
            await SendEmbed(
                i,
                "ScriptersCF",
                "You have been banned from selling and hiring in the ScriptersCF Discord Server, for " + str(Time or "N/A") + """ days, for the following reason:
```""" + Reason + """```If you feel you have been moderated by mistake, please contact a staff member."""
            )
            await client.add_roles(i, Role)
            await Increase(i, "shBan")
            await Punish(i, "shBan", [999999999999, Time * 60 * 60 * 24 + datetime.utcnow().timestamp()][Time > 0])
    await SendEmbed(
        client.get_channel(Logs),
        "S&H Ban",
        "**Moderator**: <@" + Message.author.id + """>
**Targets**: """ + ", ".join(["<@" + i.id + ">" for i in Targets]) + """
**Length**: """ + str(Time or "N/A") + """ days
**Reason**: """ + Reason
    )

async def UnSHBan(Message, Args):
    Count = 0
    Targets = []
    for i in Args:
        if i[:2] == "<@":
            Targets += [Message.mentions[Count]]
            Count += 1
        else:
            break
    Role = discord.utils.get(server.roles, name="S&H_Ban")
    for i in Targets:
        try:
            await SendEmbed(
                i,
                "ScriptersCF",
                "You have been unbanned from selling and hiring in the ScriptersCF Discord Server. Please review our <#306155109203836928> channel to ensure you aren't punished again."
            )
            await client.remove_roles(i, Role)
            Execute("Set", "UPDATE punishments SET shBanEnd = NULL WHERE userId = " + i.id)
        except Exception as e:
            print("3",e)
    await SendEmbed(
        client.get_channel(Logs),
        "S&H Unban",
        "**Moderator**: <@" + Message.author.id + """>
**Targets**: """ + ", ".join(["<@" + i.id + ">" for i in Targets])
    )

async def ABan(Message, Args):
    Targets = []
    Reason = "N/A"
    Time = 0
    Count = 0
    for i in Args:
        if i[:2] == "<@":
            Targets += [Message.mentions[Count]]
        elif i.isdigit():
            Time = int(i)
        else:
            Reason = " ".join(Args[Count:])
            break
        Count += 1
    Role = discord.utils.get(server.roles, name="Academics_Ban")
    for i in Targets:
        if await GetLevel(i) <= 4:
            await SendEmbed(
                i,
                "ScriptersCF",
                "You have been banned from the academic channels in the ScriptersCF Discord Server, for " + str(Time or "N/A") + """ days, for the following reason:
```""" + Reason + """```If you feel you have been moderated by mistake, please contact a staff member."""
            )
            await client.add_roles(i, Role)
            await Increase(i, "aBan")
            await Punish(i, "aBan", [999999999999, Time * 60 * 60 * 24 + datetime.utcnow().timestamp()][Time > 0])
    await SendEmbed(
        client.get_channel(Logs),
        "Academics Ban",
        "**Moderator**: <@" + Message.author.id + """>
**Targets**: """ + ", ".join(["<@" + i.id + ">" for i in Targets]) + """
**Length**: """ + str(Time or "N/A") + """ days
**Reason**: """ + Reason
    )

async def UnABan(Message, Args):
    Count = 0
    Targets = []
    for i in Args:
        if i[:2] == "<@":
            Targets += [Message.mentions[Count]]
            Count += 1
        else:
            break
    Role = discord.utils.get(server.roles, name="Academics_Ban")
    for i in Targets:
        try:
            await SendEmbed(
                i,
                "ScriptersCF",
                "You have been unbanned from the academic channels in the ScriptersCF Discord Server. Please review our <#306155109203836928> channel to ensure you aren't punished again."
            )
            await client.remove_roles(i, Role)
            Execute("Set", "UPDATE punishments SET aBanEnd = NULL WHERE userId = " + i.id)
        except Exception as e:
            print("4",e)
    await SendEmbed(
        client.get_channel(Logs),
        "Academics Unban",
        "**Moderator**: <@" + Message.author.id + """>
**Targets**: """ + ", ".join(["<@" + i.id + ">" for i in Targets])
    )

async def GetRank(User):
    Count = 0
    for i in Execute("Get", "SELECT * FROM scores ORDER BY points DESC"):
        Count += 1
        if i[0] == User.id:
            return Count

async def GetUserFromRank(Rank):
    Count = 0
    for i in Execute("Get", "SELECT * FROM scores ORDER BY points DESC"):
        Count += 1
        if Count == Rank:
            return server.get_member(i[0])

async def Stats(Message, Args):
    User = Message.author
    try:
        if Args[0][:2] == "<@":
            User = Message.mentions[0]
        elif Args[0].isdigit():
            User = await GetUserFromRank(int(Args[0]))
    except Exception as e:
        print("5",e)
    Data = Execute(
        "Get",
        "SELECT * FROM scores WHERE userId = \"" + User.id + "\""
    )
    await SendLevelMsg(
        User,
        Message.channel,
        "Stats",
        "**User**: <@" + User.id + """>
**Level**: """ + str(Data[0][2]) + """
**Points**: """ + str(Data[0][1]) + """
**Rank**: """ + str(await GetRank(User)) + """
**Joined**: """ + User.joined_at.strftime('%d %b %Y') + "\n**Staff Member** ✔️\n" * (await GetLevel(User) >= 4)
    )

async def Leaderboard(Message, Args):
    Count = 0
    Results = []
    for i in Execute("Get", "SELECT * FROM scores ORDER BY points DESC")[:10]:
        Count += 1
        Pos = (["","st","nd","rd"] + ["th"] * 7)[Count]
        Results += ["**" + str(Count) + Pos + "**: <@" + i[0] + "> - " + str(i[1]) + " points"]
    Embed = discord.Embed(
        title = "Leaderboard",
        description = "\n".join(Results),
        color = 0x0094ff
    )
    Embed.set_thumbnail(url = server.icon_url)
    await client.send_message(Message.channel, embed = Embed)

async def AddPointsCMD(Message, Args):
    await AddPoints(Message.mentions[0], int(Args[1]), Message.channel)

def GetRobloxUsername(ID):
    try:
        Data = json.loads(
            urllib.request.urlopen(
                urllib.request.Request(
                    "https://verify.eryn.io/api/user/" + ID, 
                    data=None, 
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36'
                    }
                )
            ).read().decode("utf-8")
        )
        return "[" + Data["robloxUsername"] + "](https://roblox.com/users/" + str(Data["robloxId"]) + ")"
    except Exception as e:
        print("6",e)
        return "N/A"

async def Info(Message, Args):
    User = Message.mentions[0]
    Data = []
    try:
        Data = Execute("Get", "SELECT mutes, kicks, bans, aBans, shBans FROM scores WHERE userId = " + User.id)[0]
    except Exception as e:
        print("7",e)
        Data = [None, None, None, None, None]
    await SendLevelMsg(
        User,
        Message.channel,
        "Info",
        "**User**: <@" + User.id + """>
**Roblox**: """ + GetRobloxUsername(User.id) + """
**Mutes**: """ + str(Data[0] or "0") + """
**Kicks**: """ + str(Data[1] or "0") + """
**Bans**: """ + str(Data[2] or "0") + """
**Ac. Bans**: """ + str(Data[3] or "0") + """
**S&H Bans**: """ + str(Data[4] or "0")
    )

def FilterGangName(Name):
    Possible = [x * x.isalpha() for x in Name.lower().split()]
    """with time_limit(1, "sleep"):
        Possible = ["".join([x * (x.isalpha() or x == ".") for x in i.lower()]) for i in confusables.normalize(Name, prioritize_alpha = True)]
        Possible += confusables.normalize("".join([x * x.isalpha() for x in Name]))"""
    for i in SeriousFilter + Filter:
        if ListContainsPhrase(Possible, i):
            return False
    return [False, Name][all(1 <= ord(i) <= 128 and i not in "\'\"\\" for i in Name) or Name == "🦋"]

def CheckGangName(Name):
    IsAlpha = FilterGangName(Name)
    Gang = []
    if IsAlpha:
        Gang = Execute("Get", "SELECT * FROM gangs WHERE cname = \"" + Name.lower() + "\"")
    return [False, Name][IsAlpha and 1 <= len(Name) <= 16 and Gang == []]

async def Create(Message, Args):
    User = Message.author
    CurrentGang = Execute("Get", "SELECT gang FROM scores WHERE userId = " + User.id)[0][0]
    if CurrentGang:
        await SendEmbed(Message.channel, "Gang", "You must leave your current gang to create a new one.")
        return
    if Args:
        Name = CheckGangName(Args[0])
        if Name:
            Question = await SendEmbed(Message.channel, "Gang", "Is this gang name ok?\n```" + Name + "```")
            await client.add_reaction(Question, "👍")
            await client.add_reaction(Question, "👎")
            Reaction = await client.wait_for_reaction(["👍", "👎"], message = Question, timeout = 60, user = User)
            if Reaction:
                if Reaction.reaction.emoji == "👍":
                    Execute("Set", "DELETE FROM gangs WHERE owner = \"" + User.id + "\"")
                    Execute("Set", "INSERT INTO gangs (name, cname, owner, admins, members, motto, icon, invites) VALUES (\"" + Name + "\", \"" + Name.lower() + "\", \"" + User.id + "\", \"[]\", \"[]\", \"Hello world\", \"http://images.clipartpanda.com/member-clipart-member-clipart-k0434250.jpg\", \"[]\")")
                    Execute("Set", "UPDATE scores SET gang = \"" + Name + "\" WHERE userId = \"" + User.id + "\"")
                    try:await client.change_nickname(User, (User.nick or User.name) + " []")
                    except Exception as e:print("7",e)
                    await SendEmbed(Message.channel, "Gang", "Your gang has been created! Type `!gang help` for information on how to use the commands.")
        else:
            await SendEmbed(
                Message.channel,
                "Gang",
                """Sorry, you can't have that name!
- Your gang name must be appropriate
- You are not allowed to use special characters
- You cannot have the same name as another gang
- The gang name must be 16 characters or less"""
            )
    else:
        await SendEmbed(
            Message.channel,
            "Gang",
            "Please specify the name of your gang.\nEx: `!gang create JoshGang`"
        )

async def GetGangPoints(Members):
    Scores = []
    Amount = len(Members)
    for i in Members:
        Scores += [(Execute("Get", "SELECT wkPoints FROM scores WHERE userId = \"" + i + "\"")[0][0] or 0)]
    return int((sum(Scores) / Amount) * (1 * Amount - (5 / 3) * math.log(math.exp(0.575 * Amount) + math.exp(171 / 50)) + 5.75))
    """Count = 0
    Total = 0
    for i in sorted(Scores, reverse = True):
        Fraction = Count / Amount
        Total += i / (5-(Fraction * 4))
        Count += 1
    return int((Total / (len(Members) ** (1 / 3.5))) * 2)"""

async def GangLeaderboard(Message, Args):
    Results = []
    Gangs = {}
    if len(Args) > 0:
        Name = CheckGangName(Args[0])
        if Name:
            Data = Execute("Get", "SELECT userId, wkPoints FROM scores WHERE gang = \"" + Name + "\"")
            for i in Data:
                Gangs["<@" + i[0] + ">"] = i[1]
    else:
        Data = Execute("Get", "SELECT * FROM gangs")
        Count = 0
        for i in Data:
            if i[0] != "htij": # for decryption challenge #1
                Gangs[i[0]] = await GetGangPoints(json.loads(i[1].replace("\'", "\"")) + [i[2]] + json.loads(i[3].replace("\'", "\"")))
    for i in sorted(Gangs, key = Gangs.get, reverse = True)[:10]:
        Count += 1
        Pos = (["","st","nd","rd"] + ["th"] * 7)[Count]
        Results += ["**" + str(Count) + Pos + "**: " + i + " - " + str(Gangs[i]) + " points"]
    Embed = discord.Embed(
        title = "Gang Leaderboard",
        description = "\n".join(Results + ["*Algorithm may be subject to change.*"]),
        color = 0x0094ff
    )
    if Results:
        Embed.set_thumbnail(url = server.icon_url)
        await client.send_message(Message.channel, embed = Embed)

async def GangInfo(Message, Args):
    if Args:
        Name = FilterGangName(" ".join(Args))
        if Name:
            Data = Execute("Get", "SELECT * FROM gangs WHERE cname = \"" + Name.lower() + "\"")[0]
            Members = json.loads(Data[1].replace("\'", "\""))
            Admins = json.loads(Data[3].replace("\'", "\""))
            Owner = Data[2]
            Embed = discord.Embed(
                title = "Gang Information",
                description = "**" + Data[0] + """**
*\"""" + Data[5] + """\"*

**Owner**: <@""" + Owner + """>
**Admins**: """ + (", ".join(["<@"+i+">" for i in Admins]) or "N/A") + """
**Members**: """ + (", ".join(["<@"+i+">" for i in Members]) or "N/A") + """
**Points**: """ + str(await GetGangPoints(Members + Admins + [Owner])),
                color = 0x0094ff
            )
            Embed.set_thumbnail(url = Data[6])
            try:
                await client.send_message(Message.channel, embed = Embed)
            except Exception as e:
                print("8",e)
                Embed.set_thumbnail(url = "")
                await client.send_message(Message.channel, embed = Embed)
        else:
            await SendEmbed(Message.channel, "Gang", "Sorry, that gang doesn't exist!")
    else:
        await SendEmbed(Message.channel, "Gang", "Please specify the gang name\nEx: `!gang info JoshGang`")

async def UpdateMemberGangs(Members, NewGang):
    for i in Members:
        try:
            Execute("Set", "UPDATE scores SET gang = \"" + NewGang + "\" WHERE userId = \"" + i + "\"")
            Member = server.get_member(i)
            await client.change_nickname(Member, Member.name)
        except Exception as e:
            print("9",e)

async def GetGangRole(User, Gang):
    GangData = Execute("Get", "SELECT * FROM gangs WHERE cname = \"" + Gang.lower() + "\"")
    if GangData[0][2] == User.id:
        return 3 # Owner
    elif User.id in json.loads(GangData[0][3].replace("\'", "\"")):
        return 2 # Admin
    else:
        return 1 # Member

async def GangRename(Message, Args):
    try:
        Args[1]
        if await GetLevel(Message.author) >= 6:
            GangData = Execute("Get", "SELECT * FROM gangs WHERE cname = \"" + Args[0].lower() + "\"")
            if GangData:
                Name = CheckGangName(Args[1])
                if Name:
                    Execute("Set", "UPDATE gangs SET name = \"" + Name + "\", cname = \"" + Name.lower() + "\" WHERE cname = \"" + Args[0].lower() + "\"")
                    await UpdateMemberGangs(json.loads(GangData[0][1].replace("\'", "\"")) + json.loads(GangData[0][3].replace("\'", "\"")) + [GangData[0][2]], Name)
                    await SendEmbed(Message.channel, "Gang", "Renamed gang!")
            else:
                await SendEmbed(Message.channel, "Gang", "Gang not found!")
        else:
            await SendEmbed(Message.channel, "Gang", "Sorry, your gang name cannot contain spaces.")
    except Exception as e:
        print("10",e)
        try:
            UserGang = Execute("Get", "SELECT gang FROM scores WHERE userId = \"" + Message.author.id + "\"")[0][0]
            GangData = Execute("Get", "SELECT * FROM gangs WHERE cname = \"" + UserGang.lower() + "\"")
            Role = await GetGangRole(Message.author, UserGang)
            if Role == 3:
                Name = CheckGangName(Args[0])
                if Name:
                    Question = await SendEmbed(Message.channel, "Gang", "Is this gang name ok?\n```" + Name + "```")
                    await client.add_reaction(Question, "👍")
                    await client.add_reaction(Question, "👎")
                    Reaction = await client.wait_for_reaction(["👍", "👎"], message = Question, timeout = 60, user = Message.author)
                    if Reaction:
                        if Reaction.reaction.emoji == "👍":
                            Execute("Set", "UPDATE gangs SET name = \"" + Name + "\", cname = \"" + Name.lower() + "\" WHERE cname = \"" + UserGang.lower() + "\"")
                            await UpdateMemberGangs(json.loads(GangData[0][1].replace("\'", "\"")) + json.loads(GangData[0][3].replace("\'", "\"")) + [GangData[0][2]], Name)
                            await SendEmbed(Message.channel, "Gang", "Renamed gang!")
                else:
                    print("name not acceptable!")
            else:
                await SendEmbed(Message.channel, "Gang", "Sorry, you don't have permission to do that!")
        except Exception as e:
            print("11",e)

async def GangInvite(Message, Args):
    UserGang = Execute("Get", "SELECT gang FROM scores WHERE userId = \"" + Message.author.id + "\"")[0][0]
    Role = await GetGangRole(Message.author, UserGang)
    if Role >= 2:
        Invited = []
        AllInvites = json.loads(Execute("Get", "SELECT invites FROM gangs WHERE cname = \"" + UserGang.lower() + "\"")[0][0].replace("\'", "\""))
        for i in Message.mentions:
            #print("SELECT gang FROM scores WHERE userId = \"" + i.id + "\"")
            try:
                if Execute("Get", "SELECT gang FROM scores WHERE userId = \"" + i.id + "\"")[0][0] != UserGang and i.id not in AllInvites:
                    await SendEmbed(i, "ScriptersCF", "<@" + Message.author.id + """> has invited you to their gang!
If you would like to join, type `!gang join """ + UserGang + "` in the server.")
                    Invited += [i.id]
            except Exception as e:
                print("13",e)
        if Invited != []:
            Execute("Set", "UPDATE gangs SET invites = \"" + json.dumps(AllInvites + Invited).replace("\"", "\'") + "\" WHERE cname = \"" + UserGang.lower() + "\"")
            await SendEmbed(Message.channel, "Gang", "Those users have been invited to your gang!")
    else:
        await SendEmbed(Message.channel, "Gang", "Sorry, you don't have permission to invite users to your gang!")

async def GangJoin(Message, Args):
    Name = FilterGangName(Args[0])
    User = Message.author
    if Name:
        CurrentGang = Execute("Get", "SELECT gang FROM scores WHERE userId = " + User.id)[0][0]
        if CurrentGang:
            await SendEmbed(Message.channel, "Gang", "You must leave your current gang to create a new one.")
            return
        Invites = json.loads(Execute("Get", "SELECT invites FROM gangs WHERE cname = \"" + Name.lower() + "\"")[0][0].replace("\'", "\""))
        RealName = Execute("Get", "SELECT name FROM gangs where cname = \"" + Name.lower() + "\"")[0][0]
        if User.id in Invites:
            Invites.remove(User.id)
            Members = json.loads(Execute("Get", "SELECT members from gangs WHERE cname = \"" + Name.lower() + "\"")[0][0].replace("\'", "\""))
            Members += [User.id]
            Execute("Set", "UPDATE gangs SET invites = \"" + json.dumps(Invites).replace("\"", "\'") + "\", members = \"" + json.dumps(Members).replace("\"", "\'") + "\" WHERE cname = \"" + Name.lower() + "\"")
            Execute("Set", "UPDATE scores SET gang = \"" + RealName + "\" WHERE userId = \"" + User.id + "\"")
            try:await client.change_nickname(User, (User.nick or User.name) + " []")
            except Exception as e:print("14",e)
            await SendEmbed(Message.channel, "Gang", "You are now a member of **" + RealName + "**!")
        else:
            await SendEmbed(Message.channel, "Gang", "Sorry, you don't have an invitation to join that gang!")

async def GangKick(Message, Args):
    Target = Message.mentions[0]
    UserGang = Execute("Get", "SELECT gang FROM scores WHERE userId = \"" + Message.author.id + "\"")[0][0]
    TargetGang = Execute("Get", "SELECT gang FROM scores WHERE userId = \"" + Target.id + "\"")[0][0]
    TargetRank = await GetGangRole(Target, TargetGang) 
    if UserGang == TargetGang and await GetGangRole(Message.author, UserGang) > TargetRank:
        TargetRank = "admins" if TargetRank == 2 else "members"
        Members = json.loads(Execute("Get", "SELECT " + TargetRank + " from gangs WHERE cname = \"" + UserGang.lower() + "\"")[0][0].replace("\'", "\""))
        Members.remove(Target.id)
        Execute("Set", "UPDATE gangs SET " + TargetRank + " = \"" + json.dumps(Members).replace("\"", "\'") + "\" WHERE cname = \"" + UserGang.lower() + "\"")
        Execute("Set", "UPDATE scores SET gang = NULL WHERE userId = \"" + Target.id + "\"")
        try:await client.change_nickname(Target, (Target.nick or Target.name) + "]")
        except Exception as e:print("15",e)
        await SendEmbed(Message.channel, "Gang", "The user has been kicked from your gang.")
    else:
        await SendEmbed(Message.channel, "Gang", "Sorry, you don't have permission to do that!")

async def GangLeave(Message, Args):
    UserGang = Execute("Get", "SELECT gang FROM scores WHERE userId = \"" + Message.author.id + "\"")[0][0]
    Possible = {3:"owner", 2:"admins", 1:"members"}
    TargetRank = Possible[await GetGangRole(Message.author, UserGang)]
    if TargetRank == "owner":
        Execute("Set", "DELETE FROM gangs WHERE cname = \"" + UserGang.lower() + "\"")
        Execute("Set", "UPDATE scores SET gang = NULL WHERE gang = \"" + UserGang + "\"")
    else:
        Members = []
        Members = json.loads(Execute("Get", "SELECT " + TargetRank + " from gangs WHERE cname = \"" + UserGang.lower() + "\"")[0][0].replace("\'", "\""))
        Members.remove(Message.author.id)
        Execute("Set", "UPDATE gangs SET " + TargetRank + " = \"" + json.dumps(Members).replace("\"", "\'") + "\" WHERE cname = \"" + UserGang.lower() + "\"")
        Execute("Set", "UPDATE scores SET gang = NULL WHERE userId = \"" + Message.author.id + "\"")
    try:await client.change_nickname(Message.author, (Message.author.nick or Message.author.name) + "]")
    except Exception as e:print("16",e)
    await SendEmbed(Message.channel, "Gang", "You have left the gang.")

async def GangPromote(Message, Args):
    Target = Message.mentions[0]
    UserGang = Execute("Get", "SELECT gang FROM scores WHERE userId = \"" + Message.author.id + "\"")[0][0]
    if await GetGangRole(Message.author, UserGang) == 3 and await GetGangRole(Target, UserGang) == 1:
        Members = json.loads(Execute("Get", "SELECT members from gangs WHERE cname = \"" + UserGang.lower() + "\"")[0][0].replace("\'", "\""))
        Members.remove(Target.id)
        Execute("Set", "UPDATE gangs SET members = \"" + json.dumps(Members).replace("\"", "\'") + "\" WHERE cname = \"" + UserGang.lower() + "\"")
        Admins = json.loads(Execute("Get", "SELECT admins from gangs WHERE cname = \"" + UserGang.lower() + "\"")[0][0].replace("\'", "\""))
        Admins += [Target.id]
        Execute("Set", "UPDATE gangs SET admins = \"" + json.dumps(Admins).replace("\"", "\'") + "\" WHERE cname = \"" + UserGang.lower() + "\"")
        await SendEmbed(Message.channel, "Gang", "I have promoted that user!")
    else:
        await SendEmbed(Message.channel, "Gang", "I could not promote that user.")

async def GangDemote(Message, Args):
    Target = Message.mentions[0]
    UserGang = Execute("Get", "SELECT gang FROM scores WHERE userId = \"" + Message.author.id + "\"")[0][0]
    if await GetGangRole(Message.author, UserGang) == 3 and await GetGangRole(Target, UserGang) == 2:
        Members = json.loads(Execute("Get", "SELECT members from gangs WHERE cname = \"" + UserGang.lower() + "\"")[0][0].replace("\'", "\""))
        Members += [Target.id]
        Execute("Set", "UPDATE gangs SET members = \"" + json.dumps(Members).replace("\"", "\'") + "\" WHERE cname = \"" + UserGang.lower() + "\"")
        Admins = json.loads(Execute("Get", "SELECT admins from gangs WHERE cname = \"" + UserGang.lower() + "\"")[0][0].replace("\'", "\""))
        Admins.remove(Target.id)
        Execute("Set", "UPDATE gangs SET admins = \"" + json.dumps(Admins).replace("\"", "\'") + "\" WHERE cname = \"" + UserGang.lower() + "\"")
        await SendEmbed(Message.channel, "Gang", "I have demoted that user!")
    else:
        await SendEmbed(Message.channel, "Gang", "I could not demote that user.")

async def GangMotto(Message, Args):
    UserGang = Execute("Get", "SELECT gang FROM scores WHERE userId = \"" + Message.author.id + "\"")[0][0]
    if await GetGangRole(Message.author, UserGang) >= 2:
        Name = FilterGangName(" ".join(Args))
        try:
            Name = Name if len(Name) <= 160 else False
        except Exception as e:
            print("17",e)
        if Name:
            Execute("Set", "UPDATE gangs SET motto = \"" + Name + "\" WHERE cname = \"" + UserGang.lower() + "\"")
            await SendEmbed(Message.channel, "Gang", "Your motto has been set!")
        else:
            await SendEmbed(Message.channel, "Gang", "Sorry, I couldn't set the motto! Make sure that it is less than 160 characters and doesn't contain special characters.")
    else:
        await SendEmbed(Message.channel, "Gang", "Sorry, you don't have permission to do that!")

async def GangIcon(Message, Args, Attachments):
    UserGang = Execute("Get", "SELECT gang FROM scores WHERE userId = \"" + Message.author.id + "\"")[0][0]
    Link = FilterGangName(" ".join(Args) or Attachments[0]["proxy_url"])
    if await GetGangRole(Message.author, UserGang) >= 2:
        if Link:
            if Link.startswith("http://") or Link.startswith("https://"):
                Execute("Set", "UPDATE gangs SET icon = \"" + Link + "\" WHERE cname = \"" + UserGang.lower() + "\"")
                await SendEmbed(Message.channel, "Gang", "I've set your gang icon!")
                return
    await SendEmbed(Message.channel, "Gang", "Sorry, I couldn't set the icon. Make sure you have permission and you posted a link/attachment.")

async def GangHelp(Message, Args):
    await SendEmbed(
        Message.author,
        "Gang Help",
        """`!gang info <gangname>` - Displays information about the specified gang
`!gang leaderboard` - Displays each gang ordered by accumulated points
`!gang leave` - Leaves your current gang
`!gang create <name>` - Creates a gang **[Regular+]**
`!gang rename <name>` - Renames a gang **[Gang Owner+]**
`!gang invite @user` - Invites a user to your gang **[Gang Admin+]**
`!gang kick @user` - Kicks a gang member from your gang **[Gang Admin+]**
`!gang promote @user` - Promotes a gang member to admin **[Gang Owner+]**
`!gang demote @user` - Demotes a gang admin to member **[Gang Owner+]**
`!gang motto <motto>` - Sets the gang's motto **[Gang Admin+]**
`!gang icon <link>` - Sets the gang's icon **[Gang Admin+]**"""
    )

async def Gang(Message, Args):
    Type = Args[0].lower()
    if Type == "create":
        if await GetLevel(Message.author) >= 3:
            await Create(Message, Args[1:])
        else:
            await SendEmbed(
                Message.channel,
                "Gang",
                "You must be **Regular+** to create a gang!"
            )
    elif Type == "info": await GangInfo(Message, Args[1:])
    elif Type == "leaderboard": await GangLeaderboard(Message, Args[1:])
    elif Type == "rename": await GangRename(Message, Args[1:])
    elif Type == "invite": await GangInvite(Message, Args[1:])
    elif Type == "join": await GangJoin(Message, Args[1:])
    elif Type == "kick": await GangKick(Message, Args[1:])
    elif Type == "leave": await GangLeave(Message, Args[1:])
    elif Type == "promote": await GangPromote(Message, Args[1:])
    elif Type == "demote": await GangDemote(Message, Args[1:])
    elif Type == "motto": await GangMotto(Message, Args[1:])
    elif Type == "icon": await GangIcon(Message, Args[1:], Message.attachments)
    else: await GangHelp(Message, Args[1:])

async def UserCanChangeColour(User):
    for i in User.roles:
        if "Custom //" in i.name:
            return i
    return False

async def ChangeRoleColour(Message, Args):
    Colour = ""
    try: Colour = ("_".join(Args)).replace("_", " ").title()
    except Exception as e:print("18",e)
    User = Message.author
    Role = await UserCanChangeColour(User)
    if Role:
        if Colour:
            try:
                NewRole = discord.utils.get(server.roles, name = "Custom // " + Colour)
                if NewRole != Role and NewRole in server.roles:
                    #await client.add_roles(User, NewRole)
                    #await client.remove_roles(User, Role, NewRole)
                    #await client.add_roles(User, NewRole)
                    for i in User.roles:
                        if i.name.startswith("Custom //") and i != NewRole:
                            await client.remove_roles(User, i)
                    await client.add_roles(User, NewRole)
                    await SendEmbed(Message.channel, "Role Colour", "I've changed your role colour!")
                else:
                    await SendEmbed(Message.channel, "Role Colour", "Sorry, that is not a valid colour!")
            except Exception as e:
                print("19",e)
                await SendEmbed(Message.channel, "Role Colour", "Sorry, that is not a valid colour!")
        else:
            Content = "**Available Colours**:\n"
            for i in Colours:
                Content += str(discord.utils.get(testserver.emojis, name = i.replace(" ", "_").lower())) + " " + i + "\n"
            Content += "Type `!changecolour <colourname>` in the server to change your coloured role."
            await SendEmbed(
                User,
                "Role Colour",
                Content
            )

def GenerateImage(latex, name):
    Dir = ""
    latex_file = Dir + name + '.tex'
    dvi_file = Dir + name + '.dvi'
    png_file = Dir + name + '1.png'

    with open("template.tex", 'r') as textemplatefile:
        textemplate = textemplatefile.read()

        with open(latex_file, 'w') as tex:
            backgroundcolour = "36393E"
            textcolour = "DBDBDB"
            latex = textemplate.replace('__DATA__', latex).replace('__BGCOLOUR__', backgroundcolour).replace('__TEXTCOLOUR__', textcolour)
            print("a")
            tex.write(latex)
            tex.flush()
            tex.close()

    imagedpi = "300"
    latexsuccess = os.system('latex -quiet -interaction=nonstopmode ' + latex_file + " --admin")
    if latexsuccess == 0:
        os.system('dvipng -q* -D {0} -T tight '.format(imagedpi) + dvi_file)
        return png_file, latex_file, dvi_file
    else:
        return '', latex_file, dvi_file

async def LaTeX(Message, Args):
    await SendEmbed(Message.channel, "LaTeX", "Sorry, LaTeX has been temporarily disabled due to a bug. We are looking at resolving it as soon as possible.")
    return
    latex = " ".join(Args)
    num = str(random.randint(0, 2 ** 31))
    fn, ltx, dvi = GenerateImage(latex, num)
    if fn and os.path.getsize(fn) > 0:
        await client.send_file(Message.channel, fn)
    else:
        await SendEmbed(Message.channel, "LaTeX", "Sorry, something went wrong! Make sure your equation is correct.")

async def ResetGangs(Message, Args):
    Execute("Set", "UPDATE scores SET wkPoints = 0")

async def Send(Message, Args):
    await client.send_message(client.get_channel("306153640023031820"), Message.content[5:])

"""
Level 0: Everyone
Level 1: Verified
Level 2: Verified Level 2
Level 3: Regular
Level 4: Trial Moderator
Level 5: Moderator
Level 6: Senior Moderator
Level 7: Administrator
Level 8: Owner
"""
Commands = {
    "send": {
        "level": 8,
        "run": Send
    },
    "resetgangs": {
        "level": 7,
        "run": ResetGangs
    },
    "help": {
        "level": 1,
        "run": Help
    },
    "roll": {
        "level": 1,
        "run": Roll
    },
    "rolldie": {
        "level": 1,
        "run": RollDie
    },
    "forhire": {
        "level": 1,
        "run": ForHire
    },
    "notforhire": {
        "level": 1,
        "run": NotForHire
    },
    "learner": {
        "level": 1,
        "run": Learner
    },
    "scripter": {
        "level": 1,
        "run": Scripter
    },
    "mute": {
        "level": 4,
        "run": Mute
    },
    "unmute": {
        "level": 5,
        "run": Unmute
    },
    "kick": {
        "level": 5,
        "run": Kick
    },
    "ban": {
        "level": 6,
        "run": Ban
    },
    "report": {
        "level": 1,
        "run": Report
    },
    "clear": {
        "level": 4,
        "run": Clear
    },
    "lock": {
        "level": 5,
        "run": Lock
    },
    "unlock": {
        "level": 5,
        "run": Unlock
    },
    "shban": {
        "level": 5,
        "run": SHBan
    },
    "unshban": {
        "level": 5,
        "run": UnSHBan
    },
    "shunban": {
        "level": 5,
        "run": UnSHBan
    },
    "aban": {
        "level": 5,
        "run": ABan
    },
    "unaban": {
        "level": 5,
        "run": UnABan
    },
    "aunban": {
        "level": 5,
        "run": UnABan
    },
    "stats": {
        "level": 1,
        "run": Stats
    },
    "addpoints": {
        "level": 7,
        "run": AddPointsCMD
    },
    "leaderboard" : {
        "level": 1,
        "run": Leaderboard
    },
    "lockdown": {
        "level": 5,
        "run": Lockdown
    },
    "unlockdown": {
        "level": 5,
        "run": Unlockdown
    },
    "gang": {
        "level": 1,
        "run": Gang
    },
    "info": {
        "level": 4,
        "run": Info
    },
    "changecolour": {
        "level": 1,
        "run": ChangeRoleColour
    },
    "changecolor": { 
        "level": 1,
        "run": ChangeRoleColour
    },
    "tex": {
        "level": 1,
        "run": LaTeX
    },
    "latex": {
        "level": 1,
        "run": LaTeX
    }
}
"""
Mute, Unmute, Lock, Unlock
    "uptime": {
        "level": 5,
        "run": Uptime
    },
"""

async def Donation(message):
    try:
        Data = json.loads(message.content.split("\n")[0])
        User = server.get_member_named(Data["user"])
        if User:
            d = discord.utils.get(server.roles, name="Donator")
            dp = discord.utils.get(server.roles, name="Donator+")
            Message = "Thank you for your donation, we really appreciate the support!"
            if Data["amount"] >= 1000:
                if not any(i.name == "Donator+" for i in User.roles):
                    await client.add_roles(User, d, dp)
                    Message += "\nYou have been awarded the **Donator+** role."
            elif Data["amount"] >= 100:
                if not any(i.name == "Donator" for i in User.roles):
                    await client.add_roles(User, d)
                    Message += "\nYou have been awarded the **Donator** role."
            elif not any(i.name == "Donator" for i in User.roles):
                Message += "\nUnfortunately, we require a donation of at least 100R$ for the Donator role."
            if Data["amount"] >= 10000:
                Message += "\nPlease contact an administrator to discuss your perks."
            elif Data["amount"] >= 3500:
                if not any("Custom //" in i.name for i in User.roles):
                    await client.add_roles(User, discord.utils.get(server.roles, name = "Custom // Lime"))
                    Message += "\nYou now have access to custom name colours! Type `!changecolour` in the server for more information."
            await SendEmbed(
                User,
                "ScriptersCF",
                Message
            )
            return True
    except Exception as e:
        print("20",e)

def ListContainsWord(List, Phrase):
    for i in List:
        if Phrase in i.split():
            return True
    return False

async def FilterMessage(message):
    Possible = [x * x.isalpha() for x in message.content.lower().split()]
    """with time_limit(1, "sleep"):
        if sum(i.isdigit() for i in message.content) <= 10:
            Possible = ["".join([x * (x.isalpha() or x in ". ") for x in i.lower()]) for i in confusables.normalize(message.content, prioritize_alpha = True)]
            Possible += confusables.normalize("".join([x * (x.isalpha() or x==" ") for x in message.content]))"""
    #Possible = [i.lower() for i in confusables.normalize(message.content, prioritize_alpha = True) if i.isalpha() or i == "."]
    #print(Possible)
    Replacement = message.content
    Changed = False
    """for i in SeriousFilter:
        #if i in ''.join([x for x in Possible.lower() if x.isalpha()]):
        if ListContainsWord(Possible, i):
            await client.delete_message(message)
            Role = discord.utils.get(server.roles, name = "Muted")
            await client.add_roles(message.author, Role)
            await Increase(message.author, "mute")
            await Punish(message.author, "mute", 30 * 60 + datetime.utcnow().timestamp())
            await SendEmbed(
                message.author,
                "ScriptersCF",
                "Use of the n-word in our server is strictly prohibited. You have been muted for 30 minutes."
            )
            await SendEmbed(
                client.get_channel(Logs),
                "Automated Mute",
                "**Targets**: <@" + message.author.id + \""">
**Length**: 30 minutes
**Reason**: n-word usage\"""
            )
            return True"""
    
    for i in Filter:
        #if i in ''.join([x for x in Possible.lower() if x.isalpha() or x == "."]):
        if ListContainsPhrase(Possible, i):
            Replacement = Replacement.replace(i, "**" + i + "**")
            Changed = True
    if Changed:
        await client.delete_message(message)
        await SendEmbed(
            message.author,
            "ScriptersCF",
            """Your message has been censored by our bot. Below is the message you posted so you can modify it:

""" + Replacement + """

Please remove the inappropriate language before reposting your message. Note that bypassing the filter will result in punishment."""
        )
        return True

async def CheckPunishments():
    for i in Execute("Get", "SELECT * FROM punishments"):
        Options = {
            "Muted": ["mute", 1],
            "Academics_Ban": ["academics ban", 2],
            "S&H_Ban": ["selling & hiring ban", 3]
        }
        Columns = {
            1: "muteEnd",
            2: "aBanEnd",
            3: "shBanEnd"
        }
        for x in Options:
            try:
                if i[Options[x][1]] != None:
                    #print(float(i[Options[x][1]]), LastMessage)
                    if float(i[Options[x][1]]) <= LastMessage:
                        Role = discord.utils.get(server.roles, name=x)
                        #print(str(i[0]), str(Role))
                        User = server.get_member(i[0])
                        if not User: return
                        await client.remove_roles(User, Role)
                        await SendEmbed(User, "ScriptersCF", "Your " + Options[x][0] + " has expired in the ScriptersCF Discord Server. Please review our <#306155109203836928> channel to ensure you aren't punished again.")
                        await SendEmbed(client.get_channel(Logs), Options[x][0].title() + " Expired", "**Targets**: <@" + User.id + ">")
                        Execute("Set", "UPDATE punishments SET " + Columns[Options[x][1]] + " = NULL WHERE userId = " + i[0])
            except Exception as e:
                print("aaa"+str(e))

def ListContentsEqual(List):
    Comparison = List[0][1].content
    for i in List:
        if i[1].content != Comparison:
            return False
    return True

def FilterSpamCheck():
    global PrevUserMessages
    Replica = copy.deepcopy(PrevUserMessages)
    Now = datetime.utcnow().timestamp()
    for i in Replica:
        if (Now - PrevUserMessages[i][-1][0]) > 60:
            del PrevUserMessages[i]

async def CheckForSpam(Message):
    message = Message.content.lower()
    Length = len(message)
    if Length >= 30:
        for i in "abcdefghijklmnopqrstuvwxyz":
            Percentage = (message.count(i) / Length)
            if Percentage >= 0.3:
                await client.delete_message(Message)
                await SendEmbed(
                    Message.author,
                    "ScriptersCF",
                    """Your message has been detected as spam by our bot. Below is the message you posted so you can modify it:

""" + Message.content + """

Please remove the excessive use of the same character before reposting your message."""
                )
                break
    
    Author = Message.author
    if Author not in PrevUserMessages.keys():
        PrevUserMessages[Author] = []
    Time = datetime.utcnow().timestamp()
    PrevUserMessages[Author] += [[Time, Message]]
    #print(PrevUserMessages)
    if len(PrevUserMessages[Author]) >= 7:
        PrevUserMessages[Author].pop(0)
        if (Time - PrevUserMessages[Author][0][0]) <= 3 or ((Time - PrevUserMessages[Author][0][0]) <= 60 and ListContentsEqual(PrevUserMessages[Author])):
            await client.add_roles(Author, discord.utils.get(server.roles, name = "Muted"))
            Messages = []
            for i in PrevUserMessages[Author]:
                Messages += [i[1]]
            await client.delete_messages(Messages)
            await Punish(Author, "mute", Time + 30 * 60)
            await Increase(Author, "mute")
            await SendEmbed(
                client.get_channel(Logs),
                "Automated Mute",
                "**Targets**: <@" + Author.id + """>
**Length**: 30 minutes
**Reason**: Spam"""
            )
            await SendEmbed(
                Author,
                "ScriptersCF",
                "You have been automatically muted for 30 minutes for spamming. If you believe this is a mistake, please contact a staff member."
            )

def LaTeXClear():
    for i in os.listdir("."):
        if i.endswith(".dvi") or i.endswith(".log") or i.endswith(".aux") or i.endswith(".png") or (i.endswith(".tex") and i != "template.tex"):
            os.remove(i)

async def IsDM(Message):
    try:
        Message.channel.server
        return False
    except Exception as e:
        print("22",e)
        return True

def UserHasWon():
    try:
        open("winner.txt", "r+").close()
        return False
    except Exception as e:
        print("23",e)
        File = open("winner.txt", "w")
        File.write("WON")
        File.close()
        return True

async def CheckForBestGang():
    0

@client.event
async def on_message(message):
    global LastMessage, ToLog
    if message.author.id == client.user.id or message.channel.id == Logged.id:
        return
    
    CurrentTime2 = str(datetime.utcnow())

    cmsg = "\n**" + CurrentTime2 + " | " + message.author.name + " | <#" + message.channel.id + "> |** " + message.content
    if len(ToLog + cmsg) <= 2000:
        ToLog += cmsg
    else:
        await client.send_message(Logged, ToLog.replace("@", "(@)"))
        ToLog = cmsg
    
    if message.content.startswith("print") and any(i in message.content for i in ['"youdidit"', "'youdidit'", "[[youdidit]]"]):
        Author = message.author
        if not await IsDM(message):
            await client.delete_message(message)
        Sent = await SendEmbed(Author, "ScriptersCF", "Executing script...")
        await asyncio.sleep(2)
        await client.edit_message(Sent, embed = discord.Embed(
            title = "ScriptersCF",
            description = """```lua
> "youdidit"```
**Congratulations!** 🥳🎉
You have completed section 1 of our decryption challenge!
Keep an eye out for information regarding section 2!

""" + ["Unfortunately, you were not the first person to complete the challenge. But don't worry, you can still win section 2!", "**You are the first person to complete the challenge!** You will be contacted about your prize shortly."][UserHasWon()] + """

Have some feedback? We'd love to hear it! DM <@276080091749154816> and let him know your thoughts on the challenge so far!""",
            color = 0x0094ff
        ))
        await client.send_message(client.get_channel(Winners), "<@" + message.author.id + ">, " + message.author.name + " has finished!")

    if message.channel.id == Pending:
        if message.content == "!agree":
            Role = discord.utils.get(server.roles, name="Verified")
            if Execute("Get", "SELECT * FROM scores WHERE userId = \"" + message.author.id + "\"") == []:
                Execute(
                    "Set",
                    "INSERT INTO scores (userId, points, level) VALUES (\"" + message.author.id + "\", 1, 1)"
                )
            await client.add_roles(message.author, Role)
        else:
            await client.delete_message(message)
            return
    
    if message.channel.id == Donations:
        if await Donation(message):
            return
    
    if message.channel.id == Suggestions:
        try:
            await client.add_reaction(message, "👍")
            await client.add_reaction(message, "👎")
        except Exception as e:
            print("24",e)
    
    try:
        if await GetLevel(message.author) <= 4:
            if await FilterMessage(message) or await CheckForSpam(message):
                return
    except Exception as e:
        print("25",e)

    try:
        Seg = message.content.split()
        #Keyword = "".join([x*x.isalpha() for x in Seg[0]])

        """with time_limit(1, "sleep"):
            if "!" in Seg[0] and confusables.is_confusable(Keyword, "report"):
                await Commands["report"]["run"](message, Seg[1:])
                return"""

        Command = Seg[0].lower()[1:] if message.content[0] == Prefix else None
        if Command in Commands:
            if await GetLevel(message.author) >= Commands[Command]["level"]:
                await Commands[Command]["run"](message, Seg[1:])
    except Exception as e:
        print("26",e)
    
    try:
        if len(message.content) >= 10:
            if message.channel.id in ChannelPoints.keys():
                await AddPoints(message.author, ChannelPoints[message.channel.id], message.channel)
            else:
                await AddPoints(message.author, 1, message.channel)
    except Exception as e:
        print("27",e)
    
    CurrentTime = datetime.utcnow().timestamp()

    if (CurrentTime - LastMessage) > 15:
        LastMessage = CurrentTime
        try:await client.send_message(Logged, ToLog.replace("@", "(@)"))
        except Exception as e:print("28",e)
        ToLog = ""
        #client.messages.append(client.get_message(client.get_channel(ColourChannel), ColourMessage))
        await CheckPunishments()
        FilterSpamCheck()
        await CheckForBestGang()
        LaTeXClear()

@client.event
async def on_message_edit(before, after):
    try:
        if before.author.id == client.user.id or before.channel.id == Logged.id: return
        if await GetLevel(after.author) <= 4 and after.author.id != client.user.id:
            if await FilterMessage(after):
                return
    except Exception as e:
        print("29",e)

@client.event
async def on_member_update(before, after):
    try:
        if await GetLevel(after) <= 4:
            Name = after.nick or after.name
            Possible = [x * x.isalpha() for x in Name.lower().split()]
            """with time_limit(1, "sleep"):
                Possible = ["".join([x * (x.isalpha() or x == ".") for x in i.lower()]) for i in confusables.normalize(Name, prioritize_alpha = True)]
                Possible += confusables.normalize("".join([x * x.isalpha() for x in Name]))"""
            for i in SeriousFilter + Filter:
                if ListContainsPhrase(Possible, i):
                    await client.change_nickname(after, "Unnamed")
                    await SendEmbed(
                        after,
                        "ScriptersCF",
                        "Sorry, that nickname has been flagged as inappropriate! Please try another one."
                    )
                    return
    except Exception as e:
        print("30",e)
    
    try:
        if await GetLevel(after) <= 7:
            Gang = Execute("Get", "SELECT gang from scores WHERE userId = \"" + after.id + "\"")
            Gang = Gang[0][0] if Gang else ""
            Name = after.nick or after.name
            NewName = Name
            GangLength = 0
            if Gang:
                GangLength = len(Gang) + 2
            if CheckName(Name):
                if BracketContents(Name) != Gang:
                    if Gang:
                        NewName = RemoveBrackets(Name) + " [" + Gang + "]"
                    else:
                        NewName = RemoveBrackets(Name)
            else:
                if Gang:
                    NewName = RemoveBrackets(Name) + " [" + Gang + "]"
                else:
                    NewName = RemoveBrackets(Name)
            if len(NewName) > 32:
                Seg = NewName.split("[")[0]
                NewName = Seg[:28 - GangLength] + "..."
            if NewName != Name:
                await client.change_nickname(after, NewName)
    except Exception as e:
        print("31",e)
    
    Booster = discord.utils.get(server.roles, name = "Nitro Booster")

    if Booster in after.roles and Booster not in before.roles:
        await client.add_roles(after, discord.utils.get(server.roles, name = "Custom // Lime"))
        await SendEmbed(
            after,
            "ScriptersCF",
            """Thank you for your donation, we really appreciate the support!
You have been awarded **Nitro Booster**.
You now have access to custom name colours! Type `!changecolour` for more information.

Boosted us twice? Please DM <@276080091749154816> for access to the private contests channel."""
        )
    elif Booster in before.roles and Booster not in after.roles:
        if discord.utils.get(server.roles, name = "Donator+") in after.roles:
            await SendEmbed(
                after,
                "ScriptersCF",
                "Unfortunately, your **Nitro Booster** role has been removed."
            )
        else:
            Role = await UserCanChangeColour(after)
            await client.remove_roles(after, Role)
            await SendEmbed(
                after,
                "ScriptersCF",
                "Unfortunately, your **Nitro Booster** role and custom name colour permissions have been removed."
            )

@client.event
async def on_ready():
    global server, testserver, Logged
    server = client.get_server(server)
    testserver = client.get_server(testserver)
    Logged = client.get_channel(Logged)
    await client.change_presence(game = discord.Game(name = "!help"))

async def Appeal(user):
    await SendEmbed(
        user,
        "Appeal",
            """Please explain in one message the reason for your ban and why we should unban you. You must respond in the next 30 minutes, otherwise your message won't be read.

Please note that if you leave the appeal server, your appeal won't be sent."""
    )
    Response = await client.wait_for_message(channel = user, timeout = 60 * 30)
    if Response:
        await SendEmbed(
            user,
            "Appeal",
                """Thank you for your appeal. It may take up to one week before you receive a response.

If you leave the appeal server, you will not receive a response."""
        )

@client.event
async def on_member_join(user):
    if user.server.id == "637696905077456911":
        await Appeal(user)
        return
    
    if Execute("Get", "SELECT * FROM scores WHERE userId = \"" + user.id + "\"") != []:
        Mutes = Execute("Get", "SELECT muteEnd FROM punishments WHERE userId = \"" + user.id + "\"")
        if Mutes == []:
            await SendEmbed(user, "ScriptersCF", "Welcome back! 👋")
        else:
            MuteEnd = float(Mutes[0][0])
            Time = datetime.utcnow().timestamp()
            if Time < MuteEnd:
                await SendEmbed(user, "ScriptersCF", "You have been caught attempting to evade your mute. As a result, we have added 30 minutes to your mute length.\n\nIf you believe this is a mistake, please contact a staff member.")
                Execute("Set", "UPDATE punishments SET muteEnd = " + str(MuteEnd + 30 * 60) + " WHERE userId = \"" + user.id + "\"")
                await Increase(user, "mute")
                await client.add_roles(user, discord.utils.get(server.roles, name = "Muted"))
                await SendEmbed(
                    client.get_channel(Logs),
                    "Automated Mute Extension",
                    "**Targets**: <@" + user.id + """>
**Length**: 30 minutes
**Reason**: Attempted mute evasion"""
                )
            else:
                await SendEmbed(user, "ScriptersCF", "Welcome back! 👋\n\nPlease read our [rules](https://discordapp.com/channels/306153640023031820/306155109203836928) to ensure you don't get muted again.")
        return

    await SendEmbed(
        user,
        "ScriptersCF",
        """Welcome to the ScriptersCF Discord Server! 👋

We're a friendly community passionate about scripting and helping others!

To access our server, please read our [rules](https://discordapp.com/channels/306153640023031820/306155109203836928) and then type `!agree` in the <#346605168596353024> channel.

If you're looking for help with a script you've written in Lua, check out our <#306156119519264770> channel!

If you want to sell and hire or access our academic channels, you will need to engage in discussion for a few days before automatically obtaining access.

If you have any questions, feel free to ask in the <#306153640023031820> channel.

Type `!help` for information on how to use the commands and some useful links.

We hope you enjoy your stay! :)"""
    )

client.run("TOKEN_HERE")
