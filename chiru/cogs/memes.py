"""
Meme responses
"""

import os
import re
import asyncio
import json
import discord
import aiohttp
import operator
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
        self._savedel = []
        self._lastimage = None
        self._lastextension = ""
        self._loc = self.bot.config.get("memelocation", "")
        if not os.path.isdir(os.path.join(self._loc, "ignore")):
            os.makedirs(os.path.join(self._loc, "ignore"))
        self._blacklist = dict()
        if os.path.isfile(os.path.join(self._loc, "ignore/memes.json")):
            with open(os.path.join(self._loc, "ignore/memes.json"), encoding="UTF-8") as file:
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
                fmt = ", ".join(self._members)
                if len(self._members) == 1:
                    await self.bot.say("Chiru: ``{} is set to be mentioned``".format(fmt))
                else:
                    await self.bot.say("Chiru: ``{} are set to be mentioned``".format(fmt))

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

    def getBestMatch(self, searchfor, loc, extra=1):
        matches = {x: 0.0 for x in os.listdir(loc) if os.path.isfile(os.path.join(loc, x))}
        for j in searchfor:
            if all(not re.match(".*({}).*".format(re.escape(j)), i.lower()) for i in os.listdir(loc)):
                searchfor.remove(j)
        rq = len(searchfor) // 2
        for i in os.listdir(loc):
            if not os.path.isfile(os.path.join(loc, i)):
                continue
            for j in searchfor:
                if re.match(".*{}.*".format(re.escape(j)), i.lower()):
                    matches[i] += 1 + (1 / (len(i.split()) + 1)) * extra
        best_match = []
        for m in matches:
            if matches[m] > rq:
                if best_match == []:
                    best_match = [m]
                elif matches[m] > matches[best_match[0]]:
                    best_match = [m]
                elif matches[m] == matches[best_match[0]]:
                    best_match += [m]
        return best_match

    def normalize(self, string: str):
        return string.replace("'", "").replace("fuck", "fck").lower()

    def get_random_problem(self):
        mylist = ['*','/','+','-']
        problem = ""
        answer = 0
        while True:
            try:
                problem = "{}{}{}{}{}".format(randint(1,9),mylist[randint(2,3)],randint(1,9),mylist[randint(0,3)],randint(1,9))
                answer = int(eval(problem))
                break
            except ZeroDivisionError:
                continue
        return problem, answer

    @commands.command(pass_context=True)
    async def meme(self, ctx: Context, *, searchfor: str = ""):
        """
        Finds a image file and sends it. Usually sends something.

        Will send image that matches most search terms but only if over half are matched
        """
        if ctx.server.id in self._blacklist:
            if ctx.channel.id in self._blacklist[ctx.server.id]:
                problem, answer = self.get_random_problem()
                toDel = await self.bot.say("Chiru: ``Solve this problem to continue: {}``".format(problem))
                msg = await self.bot.wait_for_message(author=ctx.author, channel=ctx.channel)
                await self.bot.delete_message(toDel)
                if msg is not None and msg.content=="{}".format(str(answer)):
                    await self.bot.delete_message(msg)
                else:
                    await self.bot.say("Chiru: ``Wrong!!! {}={}``".format(problem,str(answer)))
                    await self.bot.delete_message(msg)
                    await self.bot.delete_message(toDel)
                    await self.bot.delete_message(ctx.message)
                    return



        loc = self._loc
        if searchfor != "":
            searchfor = self.normalize(searchfor).split()
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
            fmt = " ".join([m.mention for m in self._members])
            try:
                await self.bot.send_file(ctx.channel, loc + bestmatch[randint(0, len(bestmatch) - 1)],
                                         content="{} {}".format(fmt, self._message))
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
            searchfor = self.normalize(searchfor).split()
            bestmatch = self.getBestMatch(searchfor, loc, extra=0)
            index = 0
            if len(bestmatch) > 0:
                self._lastlisted = bestmatch
                for m in bestmatch:
                    fmt += "``{}. {}``\t\t".format(str(index + 1), m)
                    index += 1
                    if index % 20 == 0:
                        await self.bot.say(fmt)
                        fmt = ""
                await self.bot.say(fmt)
            else:
                await self.bot.say("Chiru: ``Didn't find any memes for {}``".format(ss))
        else:
            ##They didn't search anything so we are good to list them all
            index = 0
            fmt = ""
            ss = searchfor
            for i in os.listdir(loc):
                fmt += "``{}. {}``\t\t".format(str(index + 1), i)
                index += 1
                if index % 20 == 0:
                    await self.bot.say(fmt)
                    fmt = ""
                    await asyncio.sleep(0.1)
            await self.bot.say(fmt)

    @commands.command(pass_context=True)
    async def findmeme(self, ctx: Context, *, searchfor: str):
        """
        Kinda like listmeme but this is what meme command sees
        """
        loc = self._loc
        bestmatch = self.getBestMatch(self.normalize(searchfor).split(), loc)
        fmt = ""
        index = 0
        for m in bestmatch:
            fmt += "``{}``\t\t".format(m)
            index += 1
            if index % 20 == 0:
                await self.bot.say(fmt)
                fmt = ""
        await self.bot.say(fmt)

    @commands.command(pass_context=True)
    async def checkmemes(self, ctx: Context):
        """
        Checks if every meme can be used.
        """
        loading_bar = await self.bot.say("Loading: ``__________``")
        cantfind = []
        loc = self._loc
        ll = len(os.listdir(loc))
        index = 0
        step = ll // 10
        next = step
        current = 0
        for m in os.listdir(loc):
            index += 1
            if index > next:
                current += 1
                next += step
                await self.bot.edit_message(loading_bar,
                                            "Loading: ``{}{}``".format("\u2588" * current, "_" * (10 - current)))
            if not os.path.isfile(os.path.join(loc, m)):
                continue
            for j in os.listdir(loc):
                if not os.path.isfile(os.path.join(loc, j)):
                    continue
                if m == j:
                    continue
                if all(re.match(".*({}).*".format(n.lower()), j.lower()) for n in m.replace(".", " ").split()):
                    cantfind += [m]
                    break
        await self.bot.delete_message(loading_bar)
        if len(cantfind) > 0:
            fmt = "```These memes can't be found:\n"
            if len(cantfind) == 1:
                fmt = "``This meme can't be found: "
            for i in cantfind:
                fmt += "{}\n".format(i)
            fmt += "``"
            if len(fmt.split("\n")) > 2:
                fmt += "`"
            await self.bot.say(fmt[:1500])
        else:
            await self.bot.say("Chiru: ``All memes have unique enough filenames.``")
        toobig = []
        for m in os.listdir(loc):
            if os.stat(loc + m).st_size > 8000000:
                toobig += [m]
        if len(toobig) > 0:
            fmt = "``` These memes are too big:\n"
            if len(toobig) == 1:
                fmt = "``This meme is too big: "
            for i in toobig:
                fmt += "{}\n".format(i)
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
            words = self.normalize(i).split()
            ext = words[-1]
            words.remove(ext)
            ext = ext.split(".")
            words.append(ext[0])
            ext = ".{}".format(ext[-1])
            words.reverse()
            finalwords = words[:]  # bugfix: will now remove more than one word. It didn't before for some reason
            for w1 in words:
                oneskip = True
                for w2 in finalwords:  # bugfix: will now remove only one duplicate
                    if w1 == w2:
                        if oneskip:
                            oneskip = False
                            continue
                    if re.match(".*({}).*".format(re.escape(w1)), w2):
                        finalwords.remove(w1)
                        break
            finalwords.reverse()
            name = " ".join([self.normalize(w) for w in finalwords]) + self.normalize(ext)
            if i != name:
                os.rename(loc + i, loc + name)
                fmt += '"' + i + '" --> "' + name + '"\n'
        if fmt != "":
            bb = ""
            index = 0
            await self.bot.say("Chiru: ``Here are the memes I renamed``\n")
            for i in fmt.split("\n"):
                bb += "``{}``\n".format(i)
                index += 1
                if index % 10 == 0:
                    await self.bot.say(bb)
                    bb = ""
                    await asyncio.sleep(0.5)
            if bb != "":
                await self.bot.say(bb)
        else:
            await self.bot.say("Chiru: ``All memes are already clean``")

    @commands.command(pass_context=True)
    async def bigmemes(self, ctx: Context, count: int = 10):
        """
        Return count biggest memes
        """
        files = dict()
        for m in os.listdir(self._loc):
            if not os.path.isfile(self._loc + m):
                continue
            files[str(m)] = os.stat(self._loc + m).st_size
        bigfiles = sorted(files.items(), key=operator.itemgetter(1))
        bigfiles.reverse()
        fmt = "\n".join(
            ["``{} = {}``".format(str(i[0]), "{} MB".format("%.2f" % (i[1] / 1000000))) for i in bigfiles[:count]])
        await self.bot.say(fmt)

    @commands.group(pass_context=True, invoke_without_command=True)
    async def addmemeterm(self, ctx: Context, *, string_in: str):
        """
        Will add words to filenames

        Adds first word in input to every meme that matches the other words
        """
        if len(string_in.split()) < 2:
            await self.bot.say("Chiru: ``You need to atleast one word to search for``")
            return
        if string_in.split()[1] != "to":
            await self.bot.say('Chiru: ``Second word needs to be "to" as in "addmemeterm this to something else"``')
            return
        toAdd = self.normalize(string_in).split()[0]
        toSearch = self.normalize(string_in).split()[2:]
        loc = self._loc
        bestmatch = self.getBestMatch(toSearch, loc, extra=0)
        self._undobutton = {}
        for b in bestmatch:
            self._undobutton[loc + b] = "{}{} {}".format(loc, toAdd, b)
            os.rename(loc + b, "{}{} {}".format(loc, toAdd, b))
        fmt = ""
        index = 0
        if len(bestmatch) > 0:
            await self.bot.say("Chiru: ``Here are the new memes``")
            for m in bestmatch:
                fmt += "``{}. {} {}``\t\t".format(str(index + 1), toAdd, m)
                index += 1
                if index % 20 == 0:
                    await self.bot.say(fmt)
                    fmt = ""
            await self.bot.say(fmt)
        else:
            await self.bot.say(
                "Chiru: ``Didn't find any memes for {}``".format("".join(self.normalize(string_in).split()[2:])))

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
        with open(os.path.join(self._loc, "ignore/memes.json"), "w+", encoding="UTF-8") as file:
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
        with open(os.path.join(self._loc, "ignore/memes.json"), "w+", encoding="UTF-8") as file:
            json.dump(self._blacklist, file)
        await self.bot.delete_message(ctx.message)

    @commands.group(pass_context=True, invoke_without_command=True)
    async def snagmeme(self, ctx: Context, channel=None):
        """
        Searches the logs and saves the first image it finds
        """
        self._savedel += [ctx.message]
        urls = []
        extensions = ['jpeg', 'jpg', 'png', 'gif']
        if channel == None:
            iterator = self.bot.logs_from(ctx.channel)
        else:
            iterator = self.bot.logs_from(self.bot.get_channel(channel))
        reg = re.compile("(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?")
        async for m in iterator:
            if isinstance(m, discord.Message):
                if len(m.attachments) > 0:
                    if m.attachments[0]['url'].split(".")[-1].lower() in extensions:
                        urls.append(m.attachments[0]['url'])
                elif reg.match(m.content):
                    url = reg.match(m.content).group()
                    if url.split(".")[-1].lower() in extensions:
                        urls.append(url)

        if len(urls) == 0:
            await self.bot.say("Didn't find any images.")
            return

        fmt = "Choose what image:\n"
        forurls = urls[:10]
        forurls.reverse()
        fmt += "".join(["{}. ``{}``\n".format(str(i), forurls[i].split("/")[-1]) for i in range(len(forurls))])
        self._savedel += [await self.bot.say(fmt)]

        index = 0
        fails = 0
        while True:
            answer = await self.bot.wait_for_message(channel=ctx.channel, author=ctx.author)
            if answer.content[0].lower() in ['c', 'r']:
                self._savedel += [answer, await self.bot.say("Oki, canceling!")]
                delNow = self._savedel[:]
                self._savedel = []
                await asyncio.sleep(2)
                for m in delNow:
                    try:
                        await self.bot.delete_message(m)
                    except:
                        continue
                return
            try:
                index = int(answer.content)
                forurls[index]
                await self.bot.delete_message(answer)
                break
            except:
                fails += 1
                if fails > 3:
                    self._savedel += [await self.bot.say("Canceling...")]
                    delNow = self._savedel[:]
                    self._savedel = []
                    await asyncio.sleep(5)
                    for m in delNow:
                        try:
                            await self.bot.delete_message(m)
                        except:
                            continue
                    return

        self._savedel += [
            await self.bot.say("Saving ``{}``\nWaiting for file name...".format(forurls[index].split("/")[-1]))]
        self._lastextension = forurls[index].split(".")[-1]
        with aiohttp.ClientSession() as session:
            async with session.get(url=forurls[index]) as response:
                self._lastimage = await response.read()

        while True:
            name = await self.bot.wait_for_message(channel=ctx.channel, author=ctx.author)
            if name.content[:7].lower() == "saveas ":
                if len(name.content.split()) > 1:
                    with open(os.path.join(self._loc,
                                           "{}.{}".format(self.normalize(name.content[7:]),
                                                          self._lastextension)),
                              "wb") as file:
                        file.write(self._lastimage)
                        self._lastimage = None
                        await self.bot.delete_message(name)
                        self._savedel += [await self.bot.say("Saved as ``{}``".format(file.name.split("/")[-1]))]
                        delNow = self._savedel[:]
                        self._savedel = []
                        await asyncio.sleep(5)
                        for m in delNow:
                            try:
                                await self.bot.delete_message(m)
                            except:
                                continue
                    return
        return

    @snagmeme.command(pass_context=True)
    async def reset(self, ctx: Context):
        """
        Resets the last saved image
        """
        self._lastimage = None
        self._savedel += [ctx.message]
        delNow = self._savedel[:]
        self._savedel = []
        for m in delNow:
            try:
                await self.bot.delete_message(m)
            except:
                continue


def setup(bot: Chiru):
    bot.add_cog(Memes(bot))
