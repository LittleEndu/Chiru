"""
Bot file.
"""
import os
import shutil
import sys
import pip
import re

import aioredis as aioredis
import asyncio
import discord
import logbook
import logging

import time

import random
import yaml

import traceback

from discord.ext import commands
from discord.ext.commands import Bot, CommandError, CommandNotFound
from discord.ext.commands.view import StringView
from kyokai import Kyokai
from kyokai.asphalt import KyoukaiComponent
from kyokai.blueprints import Blueprint
from kyokai.context import HTTPRequestContext
import itsdangerous

from logbook.compat import redirect_logging
from logbook import StreamHandler

from chiru import db
from override import Context

# Define logging stuff.
redirect_logging()

StreamHandler(sys.stderr).push_application()

r = re.compile(r"_requirements:: (.*)?")

initial_extensions = [
    'chiru.cogs.owner',
]
logging.root.setLevel(logging.INFO)


def _get_command_prefix(bot: 'Chiru', message: discord.Message):
    if bot.config.get("self_bot"):
        return "self."
    elif bot.config.get("dev"):
        return "domo "
    else:
        return "chiru "


class Chiru(Bot):
    """
    Bot class.
    """

    def __init__(self, *args, **kwargs):
        self.logger = logbook.Logger("Chiru")
        self.logger.level = logbook.INFO

        # We still have to do this
        logging.root.setLevel(logging.INFO)

        # Set SQLAlchemy's logger to INFO
        logging.getLogger("sqlalchemy").setLevel(logging.INFO)

        try:
            cfg = sys.argv[1]
        except IndexError:
            cfg = "config.yml"

        self.logger.info("Loading from `{}`.".format(cfg))

        if not os.path.exists(cfg):
            shutil.copy("config.example.yml", cfg)

        with open(cfg) as f:
            self.config = yaml.load(f)

        if self.config.get("use_uvloop", False):
            import uvloop
            self.logger.info("Switching to uvloop.")
            policy = uvloop.EventLoopPolicy()
            self.logger.info("Created event loop policy `{}`.".format(policy))
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        else:
            self.logger.info("Using base selector event loop.")

        # Init now, so the loop is created here.
        super().__init__(*args, **kwargs)

        if self.config.get("self_bot"):
            self._skip_check = discord.User.__ne__

        self._redis = None

        # Create a new Kyoukai web server.
        self._webserver = Kyokai("chiru")
        self._webserver_started = False

        self._webserver.debug = self.config.get("dev", False)

        self._webserver.before_request(self.before_request)
        self._webserver.route("/")(self.root)

        try:
            self.http_signer = itsdangerous.Serializer(secret_key=self.config["oauth2"]["http_secret"])
        except KeyError:
            self.http_signer = None

        self.db = db.ChiruDatabase(self.config.get("db_url"))

        self.start_time = time.time()

        # Create the rotation background task.
        self.loop.create_task(self._rotate_game_text())

    async def _rotate_game_text(self):
        """
        Coroutine to rotate the game text.
        """
        await self.wait_until_ready()
        texts = self.config.get("game_texts", [])
        while True:
            await self.change_status(game=discord.Game(name=random.choice(texts)))
            await asyncio.sleep(15)

    @property
    def is_self_bot(self):
        return self.config.get("self_bot", False)

    async def root(self, r: HTTPRequestContext):
        return "Chiru OK!", 200, {"X-Bot": "Chiru"}

    async def before_request(self, r: HTTPRequestContext):
        r.request.extra["bot"] = self
        return r

    def register_blueprint(self, blueprint: Blueprint):
        """
        Add a blueprint to the built-in webserver.
        """
        self._webserver.register_blueprint(blueprint)

    # region Redis

    async def _connect_redis(self):
        """
        Connect to redis.
        """
        host = self.config.get("redis")["host"]
        port = self.config.get("redis")["port"]
        password = self.config.get("redis", {}).get("password")
        db = self.config.get("redis", {}).get("db", 0)
        self.logger.info("Connecting to redis://{}:{}/{}...".format(host, port, db))
        try:
            redis_pool = await aioredis.create_pool(
                (host, port),
                db=db, password=password
            )
        except ConnectionRefusedError:
            self.logger.error("Could not connect to redis server.")
            self.logger.error("Exiting.")
            await self.logout()
            return
        else:
            self.logger.info("Established Redis connection.")
        self._redis = redis_pool
        self.logger.info("Connected to redis.")

        return self._redis

    async def get_redis(self) -> aioredis.RedisPool:
        if self._redis is None:
            await self._connect_redis()

        return self._redis

    async def get_config(self, server: discord.Server, key: str):
        """
        Get a server config key.
        """
        async with (await self.get_redis()).get() as conn:
            assert isinstance(conn, aioredis.Redis)
            built = "cfg:{}:{}".format(server, key)
            x = await conn.get(built)
            if isinstance(x, bytes):
                return x.decode()
            return x

    async def get_key(self, key: str):
        async with (await self.get_redis()).get() as conn:
            assert isinstance(conn, aioredis.Redis)
            x = await conn.get(key)
            if isinstance(x, bytes):
                return x.decode()
            return x

    async def set_config(self, server: discord.Server, key: str, value, **kwargs):
        async with (await self.get_redis()).get() as conn:
            assert isinstance(conn, aioredis.Redis)
            built = "cfg:{}:{}".format(server, key)
            return await conn.set(built, value, **kwargs)

    # endregion

    async def on_ready(self):
        self.logger.info("Loaded Chiru, logged in as `{}`.".format(self.user.name))
        try:
            id = (await self.application_info()).id
            self.logger.info("Invite link: {}".format(discord.utils.oauth_url(id)))
        except discord.Forbidden:
            pass
        redis = await self.get_redis()
        if not redis:
            return

        extensions = initial_extensions + self.config.get("autoload", [])

        for cog in extensions:
            try:
                self.load_extension(cog)
            except Exception as e:
                self.logger.critical("Could not load extension `{}`".format(cog, e))
                self.logger.exception()
            else:
                self.logger.info("Loaded extension {}.".format(cog))

        if not self._webserver_started:
            try:
                self.logger.info("Starting built-in webserver.")
                component = KyoukaiComponent(self._webserver,
                                             self.config.get("webserver", {}).get("ip", "127.0.0.1"),
                                             self.config.get("port", {}).get("port", 5555),
                                             renderer="template_mako")
                self._webserver.component = component
                await self._webserver.start(component=component)
            except OSError as e:
                if e.errno == 98:
                    self.logger.warning("Cannot start built-in webserver; something is already listening.")
            else:
                self.logger.info("Started webserver successfully.")
                self._webserver_started = True

        new_time = time.time() - self.start_time

        self.logger.info("Ready in {} seconds.".format(new_time))
        self.logger.info("Bot has loaded and is ready for processing.")

    def __del__(self):
        self.loop.set_exception_handler(lambda *args, **kwargs: None)

    async def on_message(self, message):
        # Print logging output.

        if not isinstance(message.channel, discord.PrivateChannel):
            self.logger.info("Recieved message: {message.content} from {message.author.display_name}{bot}"
                             .format(message=message, bot=" [BOT]" if message.author.bot else ""))
            self.logger.info(" On channel: #{message.channel.name}".format(message=message))

        # Check for a valid server.
        if message.server is not None:
            self.logger.info(" On server: {} ({})".format(message.server.name, message.server.id))
        else:
            if self.config.get("self_bot"):
                return
            if not message.author.bot:
                # No DMs
                await self.send_message(message.channel, "I don't accept private messages.")
                return

        # Process commands
        try:
            await self.process_commands(message)
        except Exception as e:
            # Check the type of the error.
            if isinstance(e, (commands.errors.BadArgument, commands.errors.MissingRequiredArgument)):
                await self.send_message(message.channel, ":x: Bad argument: {}".format(' '.join(e.args)))
                return
            elif isinstance(e, (commands.errors.CheckFailure)):
                await self.send_message(message.channel, ":x: Check failed. You probably don't have permission to do "
                                                         "this.")
                return
            else:
                if isinstance(e, commands.errors.CommandInvokeError):
                    lines = traceback.format_exception(type(e), e.__cause__, e.__cause__.__traceback__)
                else:
                    lines = traceback.format_exception(type(e), e, e.__traceback__)
                await self.send_message(message.channel, ":no_entry: An error has occurred. This has been logged.")
                self.logger.error(''.join(lines))

    async def send_message(self, destination, content, *, tts=False):
        content = "\u200b{}".format(content)
        return await super().send_message(destination, content, tts=tts)

    async def process_commands(self, message):
        """
        Override of process_commands to use our own context.
        """
        _internal_channel = message.channel
        _internal_author = message.author

        view = StringView(message.content)
        if self._skip_check(message.author, self.user):
            return

        prefix = self._get_prefix(message)
        invoked_prefix = prefix

        if not isinstance(prefix, (tuple, list)):
            if not view.skip_string(prefix):
                return
        else:
            invoked_prefix = discord.utils.find(view.skip_string, prefix)
            if invoked_prefix is None:
                return

        invoker = view.get_word()
        tmp = {
            'bot': self,
            'invoked_with': invoker,
            'message': message,
            'view': view,
            'prefix': invoked_prefix
        }
        ctx = Context(**tmp)
        del tmp

        if invoker in self.commands:
            command = self.commands[invoker]
            self.dispatch('command', command, ctx)
            await command.invoke(ctx)
            self.dispatch('command_completion', command, ctx)
        elif invoker:
            exc = CommandNotFound('Command "{}" is not found'.format(invoker))
            self.dispatch('command_error', exc, ctx)

    def main(self):
        self.run(self.config["oauth2_token"], bot=not self.config.get("self_bot", False))


if __name__ == "__main__":
    client = Chiru(command_prefix=_get_command_prefix, description="AAAA")
    client.main()
