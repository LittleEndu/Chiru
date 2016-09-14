"""
Meme responses
"""

import discord
import os
import re
import asyncio
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

    @commands.command(pass_context=True)
    async def meme(self, ctx: Context, *, searchfor: str):
        """
        Finds a image file and sends it. Usually sends something.

        Will send image that matches most search terms but only if over half are matched
        """
        loc = self.bot.config.get("memelocation", "")
        matches = {x: 0 for x in os.listdir(loc)}
        searchfor = searchfor.replace("'", "").lower().split()
        for j in searchfor:
            if all(not re.match(".*(" + re.escape(j) + ").*", i.lower()) for i in os.listdir(loc)):
                searchfor.remove(j)
        rq = len(searchfor) // 2
        for i in os.listdir(loc):
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
        if len(bestmatch) > 0:
            await self.bot.send_file(ctx.channel, loc + bestmatch[randint(0, len(bestmatch) - 1)])
            await self.bot.delete_message(ctx.message)

        else:
            toDel = await self.bot.say("Chiru: ``No image matched the search term``")
            await asyncio.sleep(5)
            await self.bot.delete_message(ctx.message)
            await self.bot.delete_message(toDel)

    @commands.command(pass_context=True)
    async def maymay(self, ctx: Context, *, searchfor: str):
        """
        Finds a image file and sends it. Might not send anything.
        
        It used to always return something but now it doesn't if it finds more than one match.
        """
        matches = []
        searchfor = searchfor.replace("'", "").lower().split()
        loc = self.bot.config.get("memelocation", "")
        for j in searchfor:
            if all(not re.match(".*(" + re.escape(j) + ").*", i.lower()) for i in os.listdir(loc)):
                searchfor.remove(j)
        if len(searchfor) > 0:
            for i in os.listdir(loc):
                if all(re.match(".*(" + re.escape(j) + ").*", i.lower()) for j in searchfor):
                    matches += [i]
        if len(matches) == 1:
            await self.bot.send_file(ctx.channel, loc + matches[0])
            await self.bot.delete_message(ctx.message)
        else:
            toDel = await self.bot.say(
                "Chiru: ``Found {} pictures. You should refine your search``".format(len(matches)))
            fmt = "```Here are the memes I found for: " + ctx.message.content + "\n"
            if len(matches) > 0:
                if len(matches) < 11:
                    for i in matches:
                        fmt += i + "\n"
                fmt = fmt + "```"
                await self.bot.send_message(self.bot.get_channel(self.bot.config["self_vars"].get("find_channel")), fmt)
                await asyncio.sleep(5)
            await self.bot.delete_message(ctx.message)
            await self.bot.delete_message(toDel)

    @commands.command(pass_context=True)
    async def listmemes(self, ctx: Context, *, searchfor: str = ""):
        """
        Will list all meme images. Optional string to search for.
        """
        counter = 0
        loc = self.bot.config.get("memelocation", "")
        fmt = ""
        searchfor = searchfor.replace("'", "").replace("-", "").lower().strip().split()
        for i in os.listdir(loc):
            if all(re.match(".*(" + re.escape(j) + ").*", i.lower()) for j in searchfor):
                fmt = fmt + "``" + i + "``\t\t"
                counter += 1
                if counter % 10 == 0:
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
        loc = self.bot.config.get("memelocation", "")
        for m in os.listdir(loc):
            for j in os.listdir(loc):
                if m == j:
                    continue
                if all(re.match(".*(" + n.lower() + ").*", j.lower()) for n in m.replace(".", " ").split()):
                    cantfind += [m]
                    break
        if len(cantfind) > 0:
            fmt = "```These memes can't be found:\n"
            if len(cantfind) == 1:
                fmt = "```This meme can't be found: "
            for i in cantfind:
                fmt += i + "\n"
            fmt = fmt + "```"
            await self.bot.say(fmt)
        else:
            await self.bot.say("Chiru: ``All memes have uniqe enough filenames.``")

    @commands.command(pass_context=True)
    async def cleanmemes(self, ctx: Context):
        """
        Removes repeat words from file names
        """
        loc = self.bot.config.get("memelocation", "")
        fmt = ""
        for i in os.listdir(loc):
            words = i.lower().split()
            ext = words[-1]
            words.remove(ext)
            ext = ext.split(".")
            words.append(ext[0])
            ext = "."+ext[1]
            for w1 in words:
                for w2 in words:
                    if w1 == w2:
                        continue
                    if re.match(".*(" + re.escape(w1) + ").*", w2):
                        words.remove(w1)
                        break
            name = ""
            for w in words:
                name += w + " "
            name = name.strip() + ext
            if i != name:
                os.rename(loc + i, loc + name)
                fmt += '"' + i + '" --> "' + name + '"\n'
        if fmt != "":
            await self.bot.say("Chiru: ``Here are the memes I renamed``\n"
                         "```" + fmt + "```")


def setup(bot: Chiru):
    bot.add_cog(Memes(bot))
