import sys

from khl import Message, MessageTypes

from bots.kook.client import bot
from bots.kook.info import client_name
from bots.kook.message import MessageSession, FetchTarget
from config import Config
from core.bot import load_prompt, init_async
from core.builtins import PrivateAssets, Url, EnableDirtyWordCheck
from core.parser.message import parser
from core.types import MsgInfo, Session
from core.utils.info import Info

PrivateAssets.set('assets/private/kook')
EnableDirtyWordCheck.status = Config('enable_dirty_check', False)
Url.disable_mm = not Config('enable_urlmanager', False)
Url.md_format = True


@bot.on_message((MessageTypes.TEXT, MessageTypes.IMG))
async def msg_handler(message: Message):
    if message.channel_type.name == "GROUP":

        target_id = f'KOOK|Group|{message.target_id}'
    else:
        target_id = f'KOOK|{message.channel_type.name.title()}|{message.author_id}'

    reply_id = None
    if 'quote' in message.extra:
        reply_id = message.extra['quote']['rong_id']

    msg = MessageSession(MsgInfo(target_id=target_id,
                                 sender_id=f'KOOK|User|{message.author_id}',
                                 target_from=f'KOOK|{message.channel_type.name.title()}',
                                 sender_from='KOOK|User', sender_name=message.author.nickname,
                                 client_name=client_name,
                                 message_id=message.id,
                                 reply_id=reply_id),
                         Session(message=message, target=message.target_id, sender=message.author_id))
    await parser(msg)


@bot.on_startup
async def _(b: bot):
    await init_async()
    await load_prompt(FetchTarget)


Info.client_name = client_name
if 'subprocess' in sys.argv:
    Info.subprocess = True

bot.run()
