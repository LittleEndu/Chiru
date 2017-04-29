"""
My Fun commands.
"""

import struct
import time
from ast import literal_eval
from io import BytesIO

import aiohttp
import websockets
from PIL import Image
from bs4 import BeautifulSoup as BS
from discord.ext import commands

from bot import Chiru
from override import Context


class Pxls(object):
    """
    For pxls stuff
    """

    def __init__(self, bot: Chiru):
        self.bot = bot
        self.templates = list()
        self.color_tuples = None
        self.running = False
        self.alertchannels = set()
        self.helpfuls = list()
        self.harmfuls = list()

    def get_nearest_pixel(self, tuplein, colortuples):
        try:
            return colortuples.index(tuplein)
        except:
            pass
        differences = []
        for color in colortuples:
            differences.append(sum([abs(color[i] - tuplein[i]) for i in range(3)]))
        minimum = 0
        for i in range(len(differences)):
            if differences[i] < differences[minimum]:
                minimum = i
        tdif = sum([abs(tuplein[i] - (0, 0, 0, 0)[i]) for i in range(3)])
        if tdif < differences[minimum]:
            return -1
        return minimum

    def one_dim_to_two_dim(self, listin, size):
        to_return = []
        xx = 0
        yy = 0
        ii = 0
        while yy < size[1]:
            to_append = []
            while xx < size[0]:
                to_append.append(listin[ii])
                ii += 1
                xx += 1
            to_return.append(to_append)
            xx = 0
            yy += 1
        return to_return

    def cleanhelpharm(self):
        delete_after = time.time() - 120
        for hh in self.helpfuls[:]:
            assert isinstance(hh, dict)
            if hh["time"] < delete_after:
                self.helpfuls.remove(hh)
        for hh in self.harmfuls[:]:
            assert isinstance(hh, dict)
            if hh["time"] < delete_after:
                self.harmfuls.remove(hh)

    @commands.command(pass_context=True)
    async def pxlsstatus(self, ctx: Context):
        """
        Shows status
        """
        if len(self.alertchannels) == 0:
            await self.bot.say("Currently not alerting any channels.\nYou should change that!")
        await self.bot.say(
            "Currently using {} template{}.".format(len(self.templates), "" if len(self.templates) == 1  else "s"))

        if self.running:
            self.cleanhelpharm()
            helpnr = len(self.helpfuls)
            harmnr = len(self.harmfuls)
            await self.bot.say("{} active helpful user{}".format(helpnr, "" if helpnr == 1 else "s") +
                               "\n{} active harmful user{}".format(harmnr, "" if harmnr == 1 else "s"))
        else:
            await self.bot.say("We aren't spectating the canvas.")

    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)
    async def pxlsdebug(self, ctx: Context):
        for tt in self.templates:
            assert isinstance(tt, dict)
            await self.bot.say("{}: {}".format(tt["name"], tt["score"]))

    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)
    async def startpxls(self, ctx: Context):
        """
        Starts spectating pixels
        """
        self.running = True
        await self.bot.say("Now spectating pxls")
        async with aiohttp.ClientSession() as session:
            async with session.get("https://pxls.space/info", headers={'Cookie': 'pxls-agegate=1'}) as response:
                soup = BS(await response.read(), "lxml")
                info = literal_eval(soup.find("p").string)
                palette = info["palette"]
                self.color_tuples = [struct.unpack('BBBB', bytes.fromhex(i[1:] + "FF")) for i in palette]
        async with websockets.connect("ws://pxls.space/ws", extra_headers={"Cookie": "pxls-agegate=1"}) as ws:
            while self.running:
                info = literal_eval(await ws.recv())
                if info["type"] == "pixel":
                    for tt in self.templates:
                        assert isinstance(tt, dict)
                        xx = info["pixels"][0]["x"] - tt["ox"]
                        yy = info["pixels"][0]["y"] - tt["oy"]
                        if xx >= 0 and yy >= 0 and xx < tt["size"][0] and yy < tt["size"][1]:
                            if info["pixels"][0]["color"] == tt["template"][yy][xx]:
                                self.helpfuls.append({**info, **{"time": time.time(), "name": tt["name"]}})
                                tt["score"] = tt["score"] * 0.5 + 1
                            else:
                                self.harmfuls.append({**info, **{"time": time.time(), "name": tt["name"]}})
                                tt["score"] = tt["score"] * 0.5 - 1
                            if tt["score"] < -0.5:
                                msg = "@everyone {} is under attack!!!".format(tt["name"])
                                tt["score"] = 8
                                for channel in self.alertchannels:
                                    await self.bot.send_message(self.bot.get_channel(channel), msg)
                for tt in self.templates:
                    assert isinstance(tt, dict)
                    tt["score"] *= 0.99

    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)
    async def stoppxls(self, ctx: Context):
        """
        Stops spectating pixels
        """
        self.running = False
        await self.bot.say("Stopped spectating pxls")

    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)
    async def addtemplate(self, ctx: Context, ox: int, oy: int, *, name: str):
        """
        Adds template
        """
        if len(ctx.message.attachments) == 0:
            await self.bot.say("Please attach a .png file")
            return
        if self.color_tuples is None:
            await self.bot.say("Can't add templates when not connected to web socket")

        with aiohttp.ClientSession() as session:
            async with session.get(url=ctx.message.attachments[0]["url"]) as response:
                im = Image.open(BytesIO(await response.read()))

        index_pixels = [self.get_nearest_pixel(pxl, self.color_tuples) for pxl in im.getdata()]
        template = self.one_dim_to_two_dim(index_pixels, im.size)
        self.templates.append({"name": name, "ox": ox, "oy": oy, "template": template, "size": im.size, "score": 0})
        await self.bot.say("Successfully added template")

    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)
    async def removetemplate(self, ctx: Context, name: str):
        """
        Removes template
        """
        for tt in self.templates[:]:
            assert isinstance(tt, dict)
            if tt["name"] == name:
                self.templates.remove(tt)
                await self.bot.say("Successfully removed template")

    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)
    async def startalerts(self, ctx: Context):
        """
        Starts atting everyone in this channel
        """
        self.alertchannels.add(ctx.channel.id)
        await self.bot.say("Will alert this channel")

    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)
    async def stopalerts(self, ctx: Context):
        """
        Stop atting everyone in this channel
        """
        try:
            self.alertchannels.remove(ctx.channel.id)
            await self.bot.say("Successfully removed channel from list")
        except:
            await self.bot.say("That channel isn't in the list")

    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)
    async def testalert(self, ctx: Context):
        """
        Does test alert
        """
        for channel in self.alertchannels:
            await self.bot.send_message(self.bot.get_channel(channel), "Test alert, please ignore")


def setup(bot: Chiru):
    bot.add_cog(Pxls(bot))
