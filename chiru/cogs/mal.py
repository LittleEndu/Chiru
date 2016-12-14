import asyncio
import discord
import spice_api as spice
import spice_api.constants as cc
from discord.ext import commands
from urllib.parse import quote

from bot import Chiru
from chiru import util
from override import Context


class Mal:
    """
    For connection with MyAnimeList

    Uses Spice_api
    """

    def __init__(self, bot: Chiru):
        self.bot = bot
        self.usr = self.bot.config.get("mal_username", "")
        self.pw = self.bot.config.get("mal_password", "12345")
        self.creds = spice.init_auth(self.usr, self.pw)

    @commands.command(pass_context=True)
    async def findanime(self, ctx: Context, *, searchfor: str = ""):
        """
        Searches MyAnimeList for the query.

        Returns link of the first anime.
        """
        results = spice.search(searchfor, spice.get_medium("anime"), self.creds)
        if len(results)>0:
            await self.bot.say("{}{}/{}".format(cc.ANIME_SCRAPE_BASE, str(results[0].id),
                                            quote(results[0].title.replace(" ", "_"), safe="")))
        else:
            await self.bot.say("Didn't find any anime for '{}'".format(searchfor))

def setup(bot: Chiru):
    bot.add_cog(Mal(bot))
