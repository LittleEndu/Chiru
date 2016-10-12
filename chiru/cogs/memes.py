"""
Meme responses
"""

import os
import re
import asyncio
import json
import discord
import aiohttp
from random import randint
from discord.ext import commands

from bot import Chiru
from override import Context


class Memes:
    """
    idk, it does meme stuff
    """

    def __init__(self, bot: Chiru):
        self.bot = bot
        self._members = set()
        self._message = ""
        self._mentiontimer = 0
        self._lastlisted = []
        self._undobutton = {}
        self._lastimage = None
        self._lastextension = ""
        self._loc = self.bot.config.get("memelocation", "")
        if not os.path.isdir(self._loc + "ignore"):
            os.makedirs(self._loc + "ignore")
        self._blacklist = dict()
        if os.path.isfile(self._loc + "ignore/memes.json"):
            with open(self._loc + "ignore/memes.json", encoding="UTF-8") as file:
                self._blacklist = json.load(file)

    @commands.command(pass_context=True, invoke_without_command=True)
    async def mememention(self, ctx: Context, *, member: str = ""):
        """
        Set a mention for next meme
        """
        if member != "":
            try:
                int(member)
                tempmember = ctx.server.get_member(member)
            except:
                tempmember = ctx.server.get_member_named(member)
            if tempmember != None:
                await self.bot.delete_message(ctx.message)
                self._members.add(tempmember)
                mytimer = 60
                self._mentiontimer += 60
                while self._mentiontimer > 0 and tempmember in self._members:
                    await asyncio.sleep(1)
                    if mytimer > 0:
                        self._mentiontimer -= 1
                        mytimer -= 1
                if tempmember in self._members:
                    self._members.remove(tempmember)
            else:
                toDel = await self.bot.say("Chiru: ``Can't find such member``")
                await asyncio.sleep(5)
                await self.bot.delete_message(ctx.message)
                await self.bot.delete_message(toDel)

        else:
            if self._members == set():
                await self.bot.say("Chiru: ``There's nobody set to be mentioned``")
            else:
                fmt = ""
                for m in self._members:
                    fmt += str(m.name) + ", "
                if len(self._members) == 1:
                    await self.bot.say("Chiru: ``" + fmt[:-2] + " is set to be mentioned``")
                else:
                    await self.bot.say("Chiru: ``" + fmt[:-2] + " are set to be mentioned``")

    @commands.command(pass_context=True)
    async def clearmention(self, ctx: Context):
        """
        Clears the mention
        """
        self._members = set()
        await self.bot.say("Chiru: ``Metions cleared`` :thumbsup:")

    @commands.command(pass_context=True)
    async def mememessage(self, ctx: Context, *, message: str):
        """
        Set a message for next meme
        """
        self._message = message
        await self.bot.delete_message(ctx.message)
        await asyncio.sleep(60)
        self._message = ""

    @commands.command(pass_context=True)
    async def clearmessage(self, ctx: Context):
        """
        Clears the message
        """
        self._message = ""
        await self.bot.say("Chiru: ``Message cleared``:thumbsup:")

    def getBestMatch(self, searchfor, loc):
        matches = {x: 0 for x in os.listdir(loc) if os.path.isfile(os.path.join(loc, x))}
        for j in searchfor:
            if all(not re.match(".*(" + re.escape(j) + ").*", i.lower()) for i in os.listdir(loc)):
                searchfor.remove(j)
        rq = len(searchfor) // 2
        for i in os.listdir(loc):
            if not os.path.isfile(os.path.join(loc, i)):
                continue
            for j in searchfor:
                if re.match(".*" + re.escape(j) + ".*", i.lower()):
                    matches[i] += 1
        bestmatch = []
        for m in matches:
            if matches[m] > rq:
                if bestmatch == []:
                    bestmatch = [m]
                elif matches[m] > matches[bestmatch[0]]:
                    bestmatch = [m]
                elif matches[m] == matches[bestmatch[0]]:
                    bestmatch += [m]
        return bestmatch

    @commands.command(pass_context=True)
    async def meme(self, ctx: Context, *, searchfor: str = ""):
        """
        Finds a image file and sends it. Usually sends something.

        Will send image that matches most search terms but only if over half are matched
        """
        if ctx.server.id in self._blacklist:
            if ctx.channel.id in self._blacklist[ctx.server.id]:
                toDel = await self.bot.say("Chiru: ``No memes in here please.``")
                msg = await self.bot.wait_for_message(timeout=10, author=ctx.author, channel=ctx.channel,
                                                      content="meme anyway")
                await self.bot.delete_message(toDel)
                if msg == None:
                    await self.bot.delete_message(ctx.message)
                    return
                else:
                    await self.bot.delete_message(msg)

        loc = self._loc
        if searchfor != "":
            searchfor = searchfor.replace("'", "").lower().split()
            bestmatch = self.getBestMatch(searchfor, loc)
        elif len(self._lastlisted) > 0:
            bestmatch = self._lastlisted
        else:
            toDel = await self.bot.say("Chiru: ``You need to use listmemes first if you don't search for anything``")
            await asyncio.sleep(5)
            await self.bot.delete_message(ctx.message)
            await self.bot.delete_message(toDel)
            return

        if len(bestmatch) > 0:
            self._lastlisted = []
            fmt = ""
            for m in self._members:
                fmt += str(m.mention) + " "
            try:
                await self.bot.send_file(ctx.channel, loc + bestmatch[randint(0, len(bestmatch) - 1)],
                                         content=fmt + " " + self._message)
                self._members = set()
                self._message = ""
                await self.bot.delete_message(ctx.message)
            except:
                toDel = await self.bot.say("Chiru: ``FORBIDDEN``")
                await asyncio.sleep(5)
                await self.bot.delete_message(ctx.message)
                await self.bot.delete_message(toDel)
        else:
            toDel = await self.bot.say("Chiru: ``No image matched the search term``")
            await asyncio.sleep(5)
            await self.bot.delete_message(ctx.message)
            await self.bot.delete_message(toDel)

    @commands.command(pass_context=True)
    async def listmemes(self, ctx: Context, *, searchfor: str = ""):
        """
        Will list all meme images. Optional string to search for.

        Memes listed all have a chance to appear when same string is used on meme command
        """
        loc = self._loc
        if searchfor != "":
            ##They serched for something so we'll use dictonary
            ss = searchfor
            fmt = ""
            searchfor = searchfor.replace("'", "").lower().split()
            bestmatch = self.getBestMatch(searchfor, loc)
            index = 0
            if len(bestmatch) > 0:
                self._lastlisted = bestmatch
                for m in bestmatch:
                    fmt += "``" + str(index + 1) + ". " + m + "``\t\t"
                    index += 1
                    if index % 20 == 0:
                        await self.bot.say(fmt)
                        fmt = ""
                await self.bot.say(fmt)
            else:
                await self.bot.say("Chiru: ``Didn't find any memes for " + ss + "``")
        else:
            ##They didn't search anything so we are good to list them all
            index = 0
            fmt = ""
            ss = searchfor
            for i in os.listdir(loc):
                fmt = fmt + "``" + str(index + 1) + ". " + i + "``\t\t"
                index += 1
                if index % 20 == 0:
                    await self.bot.say(fmt)
                    fmt = ""
                    await asyncio.sleep(0.1)
            await self.bot.say(fmt)

    @commands.command(pass_context=True)
    async def checkmemes(self, ctx: Context):
        """
        Checks if every meme can be used.
        """
        cantfind = []
        loc = self._loc
        for m in os.listdir(loc):
            if not os.path.isfile(os.path.join(loc, m)):
                continue
            for j in os.listdir(loc):
                if not os.path.isfile(os.path.join(loc, j)):
                    continue
                if m == j:
                    continue
                if all(re.match(".*(" + n.lower() + ").*", j.lower()) for n in m.replace(".", " ").split()):
                    cantfind += [m]
                    break
        if len(cantfind) > 0:
            fmt = "```These memes can't be found:\n"
            if len(cantfind) == 1:
                fmt = "``This meme can't be found: "
            for i in cantfind:
                fmt += i + "\n"
            fmt += "``"
            if len(fmt.split("\n")) > 2:
                fmt += "`"
            await self.bot.say(fmt)
        else:
            await self.bot.say("Chiru: ``All memes have uniqe enough filenames.``")
        toobig = []
        for m in os.listdir(loc):
            if os.stat(loc + m).st_size > 8000000:
                toobig += [m]
        if len(toobig) > 0:
            fmt = "``` These memes are too big:\n"
            if len(toobig) == 1:
                fmt = "``This meme is too big: "
            for i in toobig:
                fmt += i + "\n"
            fmt += "``"
            if len(fmt.split("\n")) > 2:
                fmt += "`"
            await self.bot.say(fmt)

    @commands.command(pass_context=True)
    async def cleanmemes(self, ctx: Context):
        """
        Removes repeat words from file names
        """
        loc = self._loc
        fmt = ""
        for i in os.listdir(loc):
            if not os.path.isfile(os.path.join(loc, i)):
                continue
            words = i.lower().split()
            ext = words[-1]
            words.remove(ext)
            ext = ext.split(".")
            words.append(ext[0])
            ext = "." + ext[-1]
            words.reverse()
            finalwords = words[:]  # bugfix: will now remove more than one word. It didn't before for some reason
            for w1 in words:
                oneskip = True
                for w2 in finalwords:  # bugfix: will now remove only one duplicate
                    if w1 == w2:
                        if oneskip:
                            oneskip = False
                            continue
                    if re.match(".*(" + re.escape(w1) + ").*", w2):
                        finalwords.remove(w1)
                        break
            name = ""
            finalwords.reverse()
            for w in finalwords:
                name += w.replace("'", "").lower() + " "
            name = name.strip() + ext.replace("'", "").lower()
            if i != name:
                os.rename(loc + i, loc + name)
                fmt += '"' + i + '" --> "' + name + '"\n'
        if fmt != "":
            bb = ""
            index = 0
            await self.bot.say("Chiru: ``Here are the memes I renamed``\n")
            for i in fmt.split("\n"):
                bb += i + "\n"
                index += 1
                if index % 10 == 0:
                    await self.bot.say("```" + bb + "```")
                    bb = ""
                    await asyncio.sleep(0.1)
            await self.bot.say("```" + bb + "```")
        else:
            await self.bot.say("Chiru: ``All memes are already clean``")

    @commands.group(pass_context=True, invoke_without_command=True)
    async def addmemeterm(self, ctx: Context, *, input: str):
        """
        Will add words to filenames

        Adds first word in input to every meme that matches the other words
        """
        if len(input.split()) < 2:
            await self.bot.say("Chiru: ``You need to atleast one word to search for``")
            return
        if input.split()[1] != "to":
            await self.bot.say('Chiru: ``Second word needs to be "to" as in "addmemeterm something to something else"')
        toAdd = input.replace("'", "").lower().split()[0]
        toSearch = input.replace("'", "").lower().split()[2:]
        loc = self._loc
        bestmatch = self.getBestMatch(toSearch, loc)
        self._undobutton = {}
        for b in bestmatch:
            self._undobutton[loc + b] = loc + toAdd + " " + b
            os.rename(loc + b, loc + toAdd + " " + b)
        fmt = ""
        index = 0
        if len(bestmatch) > 0:
            await self.bot.say("Chiru: ``Here are the new memes``")
            for m in bestmatch:
                fmt += "``" + str(index + 1) + ". " + toAdd + " " + m + "``\t\t"
                index += 1
                if index % 20 == 0:
                    await self.bot.say(fmt)
                    fmt = ""
            await self.bot.say(fmt)
        else:
            await self.bot.say(
                "Chiru: ``Didn't find any memes for " + str(input.replace("'", "").lower().split()[2:]) + "``")

    @addmemeterm.command(pass_context=True)
    async def undo(self, ctx: Context):
        """
        Undoes the damage
        """
        if len(self._undobutton) == 0:
            await self.bot.say("Chiru: ``There's nothing to undo``")
            return
        for i in self._undobutton:
            os.rename(self._undobutton[i], i)
        self._undobutton = {}
        await self.bot.say("Chiru: :ok_hand:")

    @commands.command(pass_context=True)
    async def banmemes(self, ctx: Context):
        """
        Will ban memes in the channel it's said in
        """
        if not ctx.server.id in self._blacklist:
            self._blacklist[ctx.server.id] = [ctx.channel.id]
        else:
            self._blacklist[ctx.server.id].append(ctx.channel.id)
        with open(self._loc + "ignore/memes.json", "w+", encoding="UTF-8") as file:
            json.dump(self._blacklist, file)
        await self.bot.delete_message(ctx.message)

    @commands.command(pass_context=True)
    async def allowmemes(self, ctx: Context):
        """
        Will allow memes in the channel it's said in
        """
        if ctx.server.id in self._blacklist:
            if ctx.channel.id in self._blacklist[ctx.server.id]:
                self._blacklist[ctx.server.id].remove(ctx.channel.id)
        with open(self._loc + "ignore/memes.json", "w+", encoding="UTF-8") as file:
            json.dump(self._blacklist, file)
        await self.bot.delete_message(ctx.message)

    @commands.group(pass_context=True, invoke_without_command=True)
    async def snagmeme(self, ctx: Context):
        """
        Searches the logs and saves the first image it finds
        """
        urls = []
        iterator = self.bot.logs_from(ctx.channel)
        reg = re.compile("(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?")
        async for m in iterator:
            assert isinstance(m, discord.Message)
            if len(m.attachments) > 0:
                if m.attachments[0]['url'].split(".")[-1] in ['jpg', 'png', 'gif']:
                    urls.append(m.attachments[0]['url'])
            elif reg.match(m.content):
                url = reg.match(m.content).group()
                if url.split(".")[-1] in ['jpg', 'png', 'gif']:
                    urls.append(url)

        if len(urls) == 0:
            await self.bot.say("Didn't find any image files sent trough discord.")
            return

        for u in urls:
            await self.bot.say("Do you want to save ``{}``?".format(u.split("/")[-1]))
            mmm = await self.bot.wait_for_message(timeout=10, author=ctx.author, channel=ctx.channel)
            if mmm.content[0].lower() == "n":
                continue
            elif mmm.content[0].lower() == "y":
                await self.bot.say("Saving ``{}``".format(u.split("/")[-1]))
                self._lastextension = u.split(".")[-1]
                with aiohttp.ClientSession() as session:
                    async with session.get(url=u) as response:
                        self._lastimage = await response.read()
                return
            else:
                return
        
        await self.bot.say("Wow. No more images found.")

    @snagmeme.command(pass_context=True)
    async def saveas(self, ctx: Context, *, name: str):
        """
        Used to save the image
        """

        with open(os.path.join(self._loc, "{}.{}".format(name, self._lastextension)), "wb") as file:
            file.write(self._lastimage)
            self._lastimage = None
            await self.bot.delete_message(ctx.message)
            await self.bot.say("Saved as {}".format(file.name.split("/")[-1]))

    @snagmeme.command(pass_context=True)
    async def reset(self, ctx: Context):
        """
        Resets the last saved image
        """
        self._lastimage = None
        await self.bot.delete_message(ctx.message)


def setup(bot: Chiru):
    bot.add_cog(Memes(bot))
