import os
import ast
import time
import dotenv
import discord
import logging
import sentry_sdk
from pathlib import Path
from os.path import join
from bot_files.lib import format_dt
from discord.ext import commands
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.threading import ThreadingIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.modules import ModulesIntegration

from bot_files.lib import Tokens, Embed, PostStats

log = logging.getLogger(__name__)


dotenv_file = os.path.join(Path(__file__).resolve().parent.parent / ".env")
def token_get(tokenname):
    if os.path.isfile(dotenv_file):
        dotenv.load_dotenv(dotenv_file)
    return os.environ.get(tokenname, 'False').strip('\n')



class MinatoNamikazeBot(commands.AutoShardedBot):
    def __init__(self):
        allowed_mentions = discord.AllowedMentions(
            roles=True, 
            everyone=True, 
            users=True
        )
        intents = discord.Intents(
            guilds=True,
            members=True,
            bans=True,
            emojis=True,
            voice_states=True,
            messages=True,
            reactions=True,
        ).all()
        self._cache = {}

        self.version = str(token_get('BOT_VER'))
        self.local = ast.literal_eval(token_get('LOCAL').capitalize())

        self.start_time = discord.utils.utcnow()
        self.github = token_get('GITHUB')
        self.DEFAULT_GIF_LIST_PATH = Path(__file__).resolve(
            strict=True).parent / join('botmain', 'bot', 'discord_bot_images')


        self.minato_dir = Path(__file__).resolve(strict=True).parent / join('bot_files','discord_bot_images')
        self.minato_gif = [f for f in os.listdir(join(self.minato_dir, 'minato'))]
        self.uptime = format_dt(self.start_time,'R')
        
        super().__init__(
            command_prefix=self.get_prefix,
            description = "Konichiwa, myself Minato Namikaze, Konohagakure Yondaime Hokage, I try my best to do every work as a Hokage!",
            chunk_guilds_at_startup=False,
            heartbeat_timeout=150.0,
            allowed_mentions=allowed_mentions,
            intents=intents,
            enable_debug_events=True,
        )
    
    def get_prefix(self, bot, message):
        """A callable Prefix for our bot. This could be edited to allow per server prefixes."""

        prefixes = [')', 'm!', 'minato', 'minato ']

        if not message.guild:
            return 'm!'

        return commands.when_mentioned_or(*prefixes)(bot, message)
    
    def run(self):
        try:
            
            sentry_sdk.init(
                Tokens.sentry_link.value,
                traces_sample_rate=1.0,
                integrations=[AioHttpIntegration(), ThreadingIntegration(), LoggingIntegration(), ModulesIntegration()]
            )
            log.info('Sentry Setup Done')
            
            if self.local:
                log.info('Attempting to start RICH PRESENCE')
                from pypresence import Presence
                try:
                    client_id = '779559821162315787'
                    RPC = Presence(client_id)
                    RPC.connect()
                    RPC.update(
                        state="火 Minato Namikaze 火",
                        large_image="fzglchm",
                        small_image="m57xri9",
                        details="Konichiwa, myself Minato Namikaze, \n Konohagakure Yondaime Hokage, \n\n I try my best to do every work as a Hokage",
                        large_text="Minato Namikaze | 波風ミナト",
                        small_text="Minato Namikaze",
                        buttons=[{"label": "Invite", "url": "https://discord.com/oauth2/authorize?client_id=779559821162315787&permissions=8&scope=bot%20applications.commands"},
                                {"label": "Website",
                                    "url": 'https://minato-namikaze.readthedocs.io/en/latest/'}
                                ]
                    )
                    log.info('RICH PRESENCE started')
                except Exception as e:
                    log.warning('There was some error in attempt to start the rich presence for the bot. Read below')
                    log.warning(e)
                    pass
    
            log.info('Bot will now start')
            super().run(Tokens.token.value, reconnect=True)
        except discord.PrivilegedIntentsRequired:
            log.critical(
                "[Login Failure] You need to enable the server members intent on the Discord Developers Portal."
            )
        except discord.errors.LoginFailure:
            log.critical("[Login Failure] The token initialsed in environment(or .env file) is invalid.")
        except KeyboardInterrupt:
            log.critical('The bot is shutting down since force shutdown was initiated.')
        except Exception as e:
            log.critical('An exception occured, %s', e)
    
    
    async def on_ready(self):
        cog_dir = Path(__file__).resolve(strict=True).parent / \
            join('bot_files','cogs')
        for filename in os.listdir(cog_dir):
            if os.path.isdir(cog_dir / filename):
                for i in os.listdir(cog_dir / filename):
                    if i.endswith('.py'):
                        self.load_extension(f'bot_files.cogs.{filename.strip(" ")}.{i[:-3]}')
            else:
                if filename.endswith('.py'):
                    self.load_extension(f'bot_files.cogs.{filename[:-3]}')
        
        difference = int(round(time.time() - self.start_time.timestamp()))
        stats = self.get_channel(819128718152695878) if not self.local else self.get_channel(869238107118112810)
        e = Embed(
            title=f"Bot Loaded!",
            description=f"Bot ready by **{time.ctime()}**, loaded all cogs perfectly! Time to load is {difference} secs :)", 
        )
        e.set_thumbnail(url=self.user.avatar.url)

        guild = self.get_guild(747480356625711204) if not self.local else self.get_channel(869238107118112810)
        try:
            self._cache[guild.id] = {}
            for invite in await guild.invites():
                self._cache[guild.id][invite.code] = invite
        except:
            pass
        log.critical('Started The Bot')

        try:
            await stats.send(embed=e)
        except:
            pass
        await self.change_presence(
            status=discord.Status.idle,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name='over Naruto'
            )
        )
        
        await PostStats(self).post_guild_stats_all()
        log.critical('Status Posted')
        
        if not self.local:
            await self.change_presence(
                status=discord.Status.dnd,
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name='over Naruto'
                )
            )
            await PostStats(self).post_commands()
            log.critical('Commands Status Posted')
            
            await self.change_presence(
                status=discord.Status.idle,
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name='over Naruto'
                )
            )

if __name__ == "__main__":
    MinatoNamikazeBot().run()
