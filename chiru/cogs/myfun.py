"""
My Fun commands.
"""
import functools
import re

import aiohttp
import discord
import google
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
    async def marco(self, ctx: Context):
        """
        Says "polo"
        """
        await self.bot.say("polo")

    @commands.command(pass_context=True)
    async def shrug(self, ctx: Context):
        """
        Makes a shrug
        """
        await self.bot.delete_message(ctx.message)
        await self.bot.say("¯\_(ツ)_/¯")

    @commands.command(pass_context=True)
    async def lenny(self, ctx: Context):
        """
        Makes a lenny face
        """
        await self.bot.delete_message(ctx.message)
        await self.bot.say("( ͡° ͜ʖ ͡°)")

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
