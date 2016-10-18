"""
My Fun commands.
"""
import functools
import re

import aiohttp
import discord
import asyncio
from random import randint
from discord.ext import commands

from bot import Chiru
from chiru import util
from override import Context


class MyFun(object):
    """
    aaa
    """

    def __init__(self, bot: Chiru):
        self.bot = bot

    @commands.command(pass_context=True)
    async def instadel(self, ctx: Context, *, msg: str = ""):
        """
        Deletes the message
        """
        try:
            time = int(msg.split()[0])
        except:
            time = 0
        await asyncio.sleep(time)
        try:
            await self.bot.delete_message(ctx.message)
        except:
            self.bot.logger.error("Message deleted manually")

    # @commands.command(pass_context=True)
    # async def wall(self, ctx: Context):
    #     """
    #     Makes a wall to hide stuff
    #     """
    #     fmt = ".\n"
    #     for i in range(50):
    #         fmt += ".\n"
    #     await self.bot.say(fmt)


    @commands.command(pass_context=True)
    async def marco(self, ctx: Context):
        """
        Says "polo"
        """
        await self.bot.say("polo")

    @commands.command(pass_context=True)
    async def soon(self, ctx: Context, *, message: str = ""):
        """
        Makes a soon tm
        """
        await self.bot.delete_message(ctx.message)
        await self.bot.say("soon\u2122" + message)

    @commands.command(pass_context=True)
    async def give(self, ctx: Context, *, message: str = ""):
        """
        Makes a soon tm
        """
        await self.bot.delete_message(ctx.message)
        await self.bot.say("༼ つ ◕\\_◕ ༽つ " + message + " ༼ つ ◕\\_◕ ༽つ")

    @commands.command(pass_context=True)
    async def shrug(self, ctx: Context, *, message: str = ""):
        """
        Makes a shrug
        """
        await self.bot.delete_message(ctx.message)
        await self.bot.say("¯\_(ツ)_/¯ " + message)

    @commands.command(pass_context=True)
    async def lenny(self, ctx: Context, *, message: str = ""):
        """
        Makes a lenny face
        """
        await self.bot.delete_message(ctx.message)
        await self.bot.say("( ͡° ͜ʖ ͡°) " + message)

    @commands.command(pass_context=True)
    async def snagavatar(self, ctx: Context, member: discord.Member):
        """
        Finds the avatar url of some member
        """
        await self.bot.say(
            "Chiru: ``Here you go. Avatar url for {member.name}#{member.discriminator}: <{member.avatar_url}>``".format(
                member=member))

    @commands.command(pass_context=True)
    async def justdeleteme(self, ctx: Context, count: int):
        """
        Deletes 'count' number of message you have sent in the channel

        But only if they are in the first 1000 messages
        """
        count += 1
        iterator = self.bot.logs_from(ctx.channel, limit=1000)
        async for m in iterator:
            if isinstance(m, discord.Message):
                if (m.author == ctx.author):
                    await self.bot.delete_message(m)
                    count -= 1
                    if count <= 0:
                        return

    @commands.command(pass_context=True)
    async def loadingbar(self, ctx: Context, length: int = 10, message: str = "Loading", fail: bool = False,
                         hide: bool = False, after: str = ""):
        """
        Displays a loading bar, actually doesn't load anything.
        """
        await self.bot.delete_message(ctx.message)
        if hide:
            title = ""
        else:
            title = "Attempting to "
        loading_bar = await self.bot.say(
            "{}{}: ``{}``".format(title if fail else "", message if fail else message,
                                  "_" * length))
        for i in range(length):
            await self.bot.edit_message(loading_bar,
                                        "{}{}: ``{}{}``".format(title if fail else "",
                                                                message if fail else message, "\u2588" * i,
                                                                "_" * (length - i)))
            await asyncio.sleep(1)
            if fail and i > length // 3 and randint(1, length // 3) == 1:
                break
        if not fail:
            message = message[0].lower() + message[1:]
        if hide:
            message = " ".join([after] + message.split()[1:])
        await self.bot.edit_message(loading_bar, "Failed to {}".format(message) if fail else "Done {}.".format(
            message))


def setup(bot: Chiru):
    bot.add_cog(MyFun(bot))
