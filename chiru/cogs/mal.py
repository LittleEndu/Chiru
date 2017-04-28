from urllib.parse import quote

import aiohttp
import async_timeout
from bs4 import BeautifulSoup as BS
from discord.ext import commands

from bot import Chiru
from override import Context


class Mal:
    """
    For connection with MyAnimeList
    """

    def __init__(self, bot: Chiru):
        self.bot = bot

    def scrape_searchresults(self, soup: BS, is_anime=True):
        return soup.find("div", attrs={"class": "js-categories-seasonal js-block-list list"}) \
            .find_all("a", attrs={"class": "hoverinfo_trigger fw-b{}".format(" fl-l" if is_anime else "")})

    @commands.command(pass_context=True)
    async def findanime(self, ctx: Context, *, searchfor: str = ""):
        """
        Searches MyAnimeList for the query.

        Returns link of the first anime.
        """
        link = "https://myanimelist.net/anime.php?q={}"
        animedeafult = "https://myanimelist.net/anime/"
        search_query = quote(searchfor.replace(" ", "+"), safe="")
        async with aiohttp.ClientSession() as session:
            with async_timeout.timeout(10):
                async with session.get(link.format(search_query)) as response:
                    soup = BS(await response.read(), "lxml")
                    results = [(i.get("href"), i.string) for i in self.scrape_searchresults(soup, True)]

        if len(results) > 0:
            await self.bot.say(results[0][0])
        else:
            await self.bot.say("Didn't find any anime for '{}'".format(searchfor))


def setup(bot: Chiru):
    bot.add_cog(Mal(bot))
