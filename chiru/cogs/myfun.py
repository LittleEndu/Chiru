"""
My Fun commands.
"""
import functools
import re

import aiohttp
import discord
import google
import asyncio
from dateutil.parser import parse
from datetime import datetime
from discord.ext import commands
from io import BytesIO

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


def setup(bot: Chiru):
    bot.add_cog(MyFun(bot))
