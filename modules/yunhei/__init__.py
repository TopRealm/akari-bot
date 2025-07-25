from core.component import module
from core.builtins.bot import Bot
from modules.yunhei import user


yunhei = module(
    'yunhei',
    alias={'yunhei cx': 'yunhei check', 'yunhei tj': 'yunhei add'},
    developers=['NSun200512', 'RegadPoleCN'],
    desc='{yunhei.help.desc}')


@yunhei.command('add <qqnum> <reason> <level> {{I18N:yunhei.help.add}}')
async def _(msg: Bot.MessageSession, qqnum: str, reason: str, level: str):
    await user.add(msg, qqnum, reason, level)


@yunhei.command('check [<qqnum>] {{I18N:yunhei.help.check}}')
async def _(msg: Bot.MessageSession, qqnum: str = "all"):
    await user.check(msg, qqnum)


@yunhei.command('admin add <qqnum> [<name>] {{I18N:yunhei.help.addadmin}}', required_superuser=True)
async def _(msg: Bot.MessageSession, qqnum: str, name: str = None):
    await user.admin_add(msg, qqnum, name)


@yunhei.command('admin del <qqnum> {{I18N:yunhei.help.deladmin}}', required_superuser=True)
async def _(msg: Bot.MessageSession, qqnum: str):
    await user.admin_del(msg, qqnum)


@yunhei.command('admin list {{I18N:yunhei.help.listadmin}}')
async def _(msg: Bot.MessageSession):
    await user.admin_list(msg)
