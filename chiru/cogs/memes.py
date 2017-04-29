"""
Meme responses
"""

import asyncio
import json
import operator
import os
import re
from random import randint

import aiohttp
import discord
from discord.ext import commands

from bot import Chiru
from chiru.checks import is_owner
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
        self._overwrite = {}
        try:
            with open(self._loc + "ignore/overwrite.json", encoding="UTF-8") as filein:
                self._overwrite = json.load(filein)
        except:
            pass

    @commands.command(pass_context=True, invoke_without_command=True)
    @commands.check(is_owner)
    async def addoverwritememe(self, ctx: Context, *, searchfor: str):
        """
        Adds a search overwrite for a listed meme
        """
        toDel = []
        searchfor = self.normalize(searchfor).split()
        bestmatch = self.getBestMatch(searchfor, self._loc)
        meme = bestmatch[0]
        toDel += [await self.bot.say("With what do you want ``{}`` to be overwritten in search?".format(meme))]
        overwrite = await self.bot.wait_for_message(channel=ctx.channel, author=ctx.author)
        toDel += [overwrite]
        if overwrite.content[0].lower() in ['c', 'r'] and len(overwrite.content) == 1:
            await self.bot.say("Oki, canceling.")
            await asyncio.sleep(5)
            for m in toDel:
                try:
                    await self.bot.delete_message(m)
                except:
                    continue
            return
        self._overwrite[overwrite.content] = meme
        with open(self._loc + "ignore/overwrite.json", "w", encoding="UTF-8") as fileout:
            json.dump(self._overwrite, fileout)
        toDel += [await self.bot.say("Successfully added the overwrite.")]
        await asyncio.sleep(5)
        for m in toDel:
            try:
                await self.bot.delete_message(m)
            except:
                continue

    @commands.command(pass_context=True, invoke_without_command=True)
    @commands.check(is_owner)
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
            if tempmember is not None:
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
            elif len(ctx.message.mentions) > 0:
                members = ctx.message.mentions
                await self.bot.delete_message(ctx.message)
                for m in members:
                    if isinstance(m, discord.Member):
                        self._members.add(m)
                mytimer = 60
                self._mentiontimer += 60
                while self._mentiontimer > 0 and mytimer > 0:
                    await asyncio.sleep(1)
                    if mytimer > 0:
                        self._mentiontimer -= 1
                        mytimer -= 1
                for m in members:
                    try:
                        self._members.remove(m)
                    except:
                        continue
                ctx.author.mention

            else:
                toDel = await self.bot.say("``Can't find such member``")
                await asyncio.sleep(5)
                await self.bot.delete_message(ctx.message)
                await self.bot.delete_message(toDel)

        else:
            if self._members == set():
                await self.bot.say("``There's nobody set to be mentioned``")
            else:
                fmt = ", ".join([i.name for i in self._members])
                if len(self._members) == 1:
                    await self.bot.say("``{} is set to be mentioned``".format(fmt))
                else:
                    await self.bot.say("``{} are set to be mentioned``".format(fmt))

    @commands.command(pass_context=True)
    @commands.check(is_owner)
    async def clearmention(self, ctx: Context):
        """
        Clears the mention
        """
        self._members = set()
        await self.bot.say("``Metions cleared`` :thumbsup:")

    @commands.command(pass_context=True)
    @commands.check(is_owner)
    async def mememessage(self, ctx: Context, *, message: str):
        """
        Set a message for next meme
        """
        self._message = message
        await self.bot.delete_message(ctx.message)
        await asyncio.sleep(60)
        self._message = ""

    @commands.command(pass_context=True)
    @commands.check(is_owner)
    async def clearmessage(self, ctx: Context):
        """
        Clears the message
        """
        self._message = ""
        await self.bot.say("``Message cleared``:thumbsup:")

    def getBestMatch(self, searchfor, loc, extra=1, overwrite=""):
        if overwrite in self._overwrite:
            best_match = [self._overwrite[overwrite]]
            return best_match
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
        mylist = ['*', '/', '+', '-']
        problem = ""
        answer = 0
        while True:
            try:
                problem = "{}{}{}{}{}".format(randint(1, 9), mylist[randint(2, 3)], randint(1, 9),
                                              mylist[randint(0, 3)], randint(1, 9))
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
        loc = self._loc
        if searchfor != "":
            bestmatch = self.getBestMatch(self.normalize(searchfor).split(), loc, overwrite=searchfor)
        elif len(self._lastlisted) > 0:
            bestmatch = self._lastlisted
        else:
            toDel = await self.bot.say("``You need to use listmemes first if you don't search for anything``")
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
            except:
                message = await self.bot.send_file(self.bot.get_channel("209734653853040640"),
                                                   loc + bestmatch[randint(0, len(bestmatch) - 1)])
                url = message.attachments[0]['url']
                await self.bot.say("{}\n{} {}".format(url, fmt, self._message))
                self._members = set()
                self._message = ""

            await asyncio.sleep(10)
            await self.bot.delete_message(ctx.message)
        else:
            toDel = await self.bot.say("``No image matched the search term``")
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
                    next = "``{}. {}``\t\t".format(str(index + 1), m)
                    if len(fmt + next) < 2000:
                        fmt += next
                    else:
                        await self.bot.say(fmt)
                        fmt = next
                    index += 1
                await self.bot.say(fmt)
            else:
                await self.bot.say("``Didn't find any memes for {}``".format(ss))
        else:
            ##They didn't search anything so we are good to list them all
            index = 0
            fmt = ""
            ss = searchfor
            for i in os.listdir(loc):
                next = "``{}. {}``\t\t".format(str(index + 1), i)
                if len(fmt + next) < 2000:
                    fmt += next
                else:
                    await self.bot.say(fmt)
                    fmt = next
                index += 1
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
    @commands.check(is_owner)
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
                str_ext = m.split(".")
                str_temp = m[:-len(str_ext[-1]) - 1]
                str_m = str_temp.split() + [str_ext[-1]]
                if all(re.match(".*({}).*".format(re.escape(n.lower())), j.lower()) for n in str_m):
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
            await self.bot.say("``All memes have unique enough filenames.``")
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
    @commands.check(is_owner)
    async def cleanmemes(self, ctx: Context):
        """
        Removes repeat words from file names
        """
        loc = self._loc
        fmt = ""
        for i in os.listdir(loc):
            if not os.path.isfile(os.path.join(loc, i)):
                continue
            words = self.normalize(i)
            ext = words.split(".")[-1]
            words = words[:-len(ext) - 1].split()
            words.append(ext)
            ext = ".{}".format(ext)
            words.reverse()
            finalwords = words[:]  # bugfix: will now remove more than one word. It didn't before for some reason
            # self.bot.logger.info("Going into for loop with {} and {}".format(i, str(words)))
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
            if ext[1:] in finalwords:
                finalwords.remove(ext[1:])
            name = " ".join([self.normalize(w) for w in finalwords]) + self.normalize(ext)
            if i != name:
                try:
                    os.rename(loc + i, loc + name)
                    fmt += '"' + i + '" --> "' + name + '"\n'
                except:
                    continue
        if fmt != "":
            bb = ""
            index = 0
            await self.bot.say("``Here are the memes I renamed``\n")
            for i in fmt.split("\n")[:-1]:
                next = "``{}``\n".format(i)
                if len(bb + next) < 2000:
                    bb += next
                else:
                    await self.bot.say(bb)
                    bb = next
                index += 1
            if bb != "":
                await self.bot.say(bb)
        else:
            await self.bot.say("``All memes are already clean``")

    @commands.command(pass_context=True)
    @commands.check(is_owner)
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
    @commands.check(is_owner)
    async def addmemeterm(self, ctx: Context, *, string_in: str):
        """
        Will add words to filenames

        Adds first word in input to every meme that matches the other words
        """
        if len(string_in.split()) < 2:
            await self.bot.say("``You need to atleast one word to search for``")
            return
        if string_in.split()[1] != "to":
            await self.bot.say('``Second word needs to be "to" as in "addmemeterm this to something else"``')
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
            await self.bot.say("``Here are the new memes``")
            for m in bestmatch:
                next = "``{}. {} {}``\t\t".format(str(index + 1), toAdd, m)
                if len(fmt + next) < 2000:
                    fmt += next
                else:
                    await self.bot.say(fmt)
                    fmt = next
                index += 1
            await self.bot.say(fmt)
        else:
            await self.bot.say(
                "``Didn't find any memes for {}``".format("".join(self.normalize(string_in).split()[2:])))

    @addmemeterm.command(pass_context=True)
    @commands.check(is_owner)
    async def undo(self, ctx: Context):
        """
        Undoes the damage
        """
        if len(self._undobutton) == 0:
            await self.bot.say("``There's nothing to undo``")
            return
        for i in self._undobutton:
            os.rename(self._undobutton[i], i)
        self._undobutton = {}
        await self.bot.say(":ok_hand:")

    @commands.group(pass_context=True, invoke_without_command=True)
    @commands.check(is_owner)
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
        reg = re.compile(
            "(https?:\\/\\/)?(www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{2,256}\\.[a-z]{2,6}\\/+[-a-zA-Z0-9@:%_\\+.~#?&//=]*")
        async for m in iterator:
            if isinstance(m, discord.Message):
                if len(m.attachments) > 0:
                    if m.attachments[0]['url'].split(".")[-1].lower() in extensions:
                        urls.append(m.attachments[0]['url'])
                elif len([i for i in reg.finditer(m.content)]) > 0:
                    for url in [i.group() for i in reg.finditer(m.content)]:
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
                try:
                    if len(name.content[7:].split()) > 1:
                        with open(os.path.join(self._loc,
                                               "{}.{}".format(self.normalize(name.content[7:]),
                                                              self._lastextension)),
                                  "wb") as file:
                            file.write(self._lastimage)
                            self._lastimage = None
                            await self.bot.delete_message(name)
                            self._savedel += [await self.bot.say("Saved as ``{}``".format(file.name.split("/")[-1]))]
                            self._savedel += name
                            delNow = self._savedel[:]
                            self._savedel = []
                            await asyncio.sleep(5)
                            for m in delNow:
                                try:
                                    await self.bot.delete_message(m)
                                except:
                                    continue
                        return
                except:
                    await self.bot.say("Something weird happened...")
                    pass
        return

    @snagmeme.command(pass_context=True)
    @commands.check(is_owner)
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
