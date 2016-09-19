"""
Fun commands.
"""
import functools
import re

import aiohttp
import discord
import google
from dateutil.parser import parse
from discord.ext import commands
from io import BytesIO

from bot import Chiru
from chiru import util
from override import Context


class Fun(object):
    """
    aaa
    """

    def __init__(self, bot: Chiru):
        self.bot = bot

    @commands.command(pass_context=True)
    async def stats(self, ctx: Context):
        """
        Show stats about the bot.
        """
        # Calculate unique members
        members = sum(1 for x in self.bot.get_all_members())
        uniques = len({x.id for x in self.bot.get_all_members()})
        await self.bot.say(
            "Currently connected to `{}` servers, with `{}` channels and `{}` users (`{}` unique).{}".format(
                len(self.bot.servers), len([x for x in self.bot.get_all_channels()]),
                members, uniques, "\nRunning in self-bot mode." if self.bot.config.get("self_bot") else ""
            )
        )

    @commands.command(pass_context=True)
    async def servers(self, ctx: Context, max_servers: int = 5):
        """
        Show the biggest servers.
        """
        servers = [s for s in self.bot.servers]
        servers = sorted(servers, key=lambda x: x.member_count, reverse=True)

        fmt = "**Top servers**:\n"

        for x in range(0, max_servers):
            if x >= len(servers):
                break

            fmt += "**{0}.** `{1.name}` -> `{1.member_count}` members\n".format(x + 1, servers[x])

        await self.bot.say(fmt)

    @commands.command(pass_context=True)
    async def whois(self, ctx: Context, *, member: discord.Member):
        """
        Show detailed information about a user.
        """
        fmt = """WHOIS for user {m}:

```xl
Username: {member.name}#{member.discriminator}
Display name: {member.display_name}
User ID: {member.id}

Created: {cr}
Joined: {jr}

Colour: {member.colour}
Roles: {roles}

Avatar URL: <{member.avatar_url}>

Mutual servers: {mut}```"""
        await self.bot.say(fmt.format(m=str(member), member=member,
                                      cr=member.created_at, jr=member.joined_at,
                                      mut=self._calculate_mutual_servers(member),
                                      roles=', '.join(util.safe_roles(member.roles)))
                           )

    def _calculate_mutual_servers(self, member: discord.Member):
        # Calculates mutual servers.
        count = 0
        for serv in self.bot.servers:
            assert isinstance(serv, discord.Server)
            if serv.get_member(member.id):
                count += 1
        return count

    def _search_google(self, fn, query):
        """
        Callback for searching google.

        Used inside an executor.
        """
        search = fn(query)
        # Get the first item off of the search.
        result = next(search)
        return result

    @commands.group(pass_context=True, invoke_without_command=True)
    async def search(self, ctx: Context, *, searchstr: str):
        """
        Searches the web for something.

        Use `search images` for google images search.
        """
        result = await self.bot.loop.run_in_executor(
            None, functools.partial(self._search_google, google.search, searchstr)
        )
        await self.bot.say(result)

    @search.command(pass_context=True)
    async def images(self, ctx: Context, *, searchstr: str):
        """
        Search google images.
        """
        result = await self.bot.loop.run_in_executor(
            None, functools.partial(self._search_google, google.search_images, searchstr)
        )
        await self.bot.say(result)

    @commands.command(pass_context=True)
    async def info(self, ctx: Context):
        """
        Show information about the bot.
        """
        await self.bot.say("I'm Chiru - yet another bot.\n"
                           "I was written by Fuyu, the best programmer in the world.\n"
                           "https://github.com/LittleEndu/Chiru")

    @commands.command(pass_context=True, )
    async def upscale(self, ctx: Context, *, url: str):
        """
        Upscales an image using waifu2x.

        This takes a link to an image, and returns a link to the upscaled image.
        """
        sess = aiohttp.ClientSession()
        await self.bot.say(":hourglass: Upscaling image...")

        params = {
            "url": url,
            "scale": "2",  # yikes
            "noise": "-1",
            "style": "art"
        }

        async with sess.post("http://waifu2x.udp.jp/api", data=params) as r:
            assert isinstance(r, aiohttp.ClientResponse)
            if r.status != 200:
                await self.bot.say("Waifu2x returned an error - cannot upscale.")
                return
            file_content = await r.read()

        await self.bot.send_file(ctx.channel, BytesIO(file_content), filename="upscaled.png")

        sess.close()

    @commands.command(pass_context=True)
    async def fullwidth(self, ctx: Context, *, text: str):
        """
        Fullwidth some text.
        """
        final_c = ""
        for char in text:
            if not ord(char) in range(33, 127):
                final_c += char
                continue
            # Add 65248 to the ord() value to get the fullwidth counterpart.
            final_c += chr(ord(char) + 65248)

        if self.bot.is_self_bot:
            await self.bot.delete_message(ctx.message)

        await self.bot.say(final_c)

    @commands.command(pass_context=True)
    async def discrims(self, ctx: Context):
        """
        List how many discrims out of 10000 I can see.
        """
        can_see = {int(x.discriminator) for x in self.bot.get_all_members()}
        base = 9999
        num_cant_see = 0

        missing = []

        for x in range(1, base + 1):
            if x not in can_see:
                num_cant_see += 1
                if len(can_see) > 9990:
                    missing.append(x)

        await self.bot.say("I see `{}` discriminators out of a possible `{}`, or {}%. I am missing {}.".format(
            base - num_cant_see, base, round(((base - num_cant_see) / base) * 100, 3), num_cant_see
        ))
        if missing:
            await self.bot.say("Almost at 10000! Missing: `{}`".format(", ".join(map(str, missing))))

    @commands.command(pass_context=True)
    async def find(self, ctx: Context, regex: str, limit: int = 100, date: str = None):
        """
        Search the last <limit> messages for messages matching the regex <regex>, starting from <date>.

        Note that the maximum limit is 100, but you can use <date> to search for messages earlier than that.

        This will return, at most, 100 messages, which will then be sent in a private message in chunks of 10 (so 50
        messages at maximum).
        """
        if date is not None:
            try:
                date = parse(date)
            except ValueError:
                await self.bot.say(":x: Date could not be parsed.")
                return None

        regexp = re.compile(regex)

        messages = []
        # Make sure the limit is not above 100, to prevent endpoint spam.
        if limit > 100:
            limit = 100

        iterator = self.bot.logs_from(ctx.channel, limit=limit, before=date)
        async for message in iterator:
            assert isinstance(message, discord.Message)
            if message.author == ctx.server.me:
                continue
            if len(messages) >= 100:
                break
            if not message.content:
                continue

            if regexp.match(message.content):
                messages.append(message)

        if len(messages) == 0:
            await self.bot.say("\N{WHITE EXCLAMATION MARK ORNAMENT} Search results: Found `0` messages.")
            return

        header = "\N{HEAVY EXCLAMATION MARK SYMBOL} Search results: Found `{}` messages\n".format(len(messages))
        fmt = "{}\n".format(header)

        messages = list(reversed(messages))

        # yikes

        if len(messages) <= 10:
            # Just say them in the normal channel.
            for num, message in enumerate(messages):
                fmt += "**{}:** `[{}] {}: {}`\n".format(num + 1, message.timestamp,
                                                        message.author.name.replace("`", "´"),
                                                        message.clean_content.replace("`", "´"),
                                                        )

            if len(fmt) > 1500:
                fmt = util.chunk(fmt)
                if not self.bot.is_self_bot:
                    await self.bot.say("Private messaging you the search results.")
                    chan = ctx.author
                else:
                    await self.bot.say("Self-bot mode; sending messages to channel you specified.")
                    chan = self.bot.get_channel(self.bot.config["self_vars"].get("find_channel"))
            else:
                chan = ctx.channel
                fmt = [fmt]

            for f in fmt:
                await self.bot.send_message(chan, f)
        else:
            if not self.bot.is_self_bot:
                await self.bot.say("Private messaging you the search results.")
                chan = ctx.author
            else:
                await self.bot.say("Self-bot mode; sending messages to channel you specified.")
                chan = self.bot.get_channel(self.bot.config["self_vars"].get("find_channel"))
            sp = [messages[i:i + 10] for i in range(0, len(messages), 10)]
            # yikes, counters
            counter = 0
            for group in sp:
                msg_block = ""
                for message in group:
                    counter += 1
                    msg_block += "**{}:** `[{}] {}: {}`\n".format(counter, message.timestamp,
                                                                  message.author.name.replace("`", "´"),
                                                                  message.clean_content.replace("`", "´"))
                await self.bot.send_message(chan, msg_block)

    @commands.command(pass_context=True)
    async def serverinfo(self, ctx: Context):
        """
        Mandatory server info command.
        """
        fmt = """Server information:
```xl
Server name: {server.name}
ID: {server.id}
Server region: {server.region.name}

Owner: {server.owner.display_name}#{server.owner.discriminator}

Channels: {channels} channels ({secret} secret!)
Roles: {roles} roles
Admins: {admins} admins
```"""
        channels = len(ctx.server.channels)
        secret_channels = sum(1 for chan in ctx.server.channels if
                              chan.overwrites_for(ctx.server.default_role).read_messages is False
                              and chan.type == discord.ChannelType.text
                              )
        roles = len(ctx.server.roles)
        admins = sum(
            1 for member in ctx.server.members if ctx.server.default_channel.permissions_for(member).administrator
        )

        await self.bot.say(fmt.format(server=ctx.server, channels=channels, secret=secret_channels,
                                      roles=roles, admins=admins))


def setup(bot: Chiru):
    bot.add_cog(Fun(bot))
