from core.component import module
from core.builtins import Bot
from modules.yunhei import user

yunhei = module('yunhei', developers=['NSun200512'], desc='{{yunhei.help.desc}}',doc=True)

@yunhei.command('add <qqnum> <reason> <level> {{yunhei.help.add}}')
async def _(msg:Bot.MessageSession, qqnum:str, reason:str, level:str):
    await user.add(msg,qqnum,reason,level)
@yunhei.command('cx [<qqnum>] {{yunhei.help.check}}')
async def _(msg:Bot.MessageSession,qqnum:str="all"):
    await user.check(msg,qqnum)
@yunhei.command('admin add <qqnum> <name> {{yunhei.help.addadmin}}',required_superuser = True)
async def _(msg:Bot.MessageSession,qqnum:str,name:str):
    await user.admin_add(msg,qqnum,name)
@yunhei.command('admin del <qqnum> {{yunhei.help.deladmin}}',required_superuser = True)
async def _(msg:Bot.MessageSession,qqnum:str):
    await user.admin_del(msg,qqnum)
@yunhei.command('admin list {{yunhei.help.listadmin}}')
async def _(msg:Bot.MessageSession):
    await user.admin_list(msg)
