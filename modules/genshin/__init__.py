import asyncio
import genshin as genshin_py
from core.component import module
from core.builtins import Bot
from core.utils.cooldown import CoolDown
from core.config import Config


genshin_module = module('genshin_info', alias='yuanshen', desc='原神角色信息查询。', developers=['ZoruaFox'])

username = Config('hoyolab_username')
password = Config('hoyolab_password')
# login with username and password
cookies = genshin_py.Client.login_with_password('{username}', '{password}')
client = genshin_py.Client(cookies, lang="zh-cn")

@genshin_module.handle('uid <number> {{I18N:genshin.help.uid}}')
async def _(msg: Bot.MessageSession):
    data = await client.get_genshin_user(msg.parsed_msg['<number>'])
    player_level = {data.player.level}
    await msg.send_message(
        f"玩家昵称：{data.player.nickname}\n"
        f"玩家签名: {data.player.signature}\n"
        f"冒险等阶：{data.player.level}\n"
        f"本期深境螺旋: {data.player.abyss_floor} 层 {data.player.abyss_room} 间\n"
        f"缓存过期时间：{data.ttl} s"
        )
