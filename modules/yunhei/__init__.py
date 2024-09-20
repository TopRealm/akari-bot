from core.component import module
from core.builtins import Bot
from modules.yunhei import user
from core.scheduler import CronTrigger

yunhei = module('yunhei', developers=['NSun200512'], desc='有兽云黑',doc=True)

@yunhei.command('add <qqnum> <reason> <level> {向黑名单添加成员}')
async def _(msg:Bot.MessageSession, qqnum:str, reason:str, level:str):
    await user.add(msg,qqnum,reason,level)
@yunhei.command('cx [<qqnum>] {查询单个黑名单成员或扫描群内的成员}')
async def _(msg:Bot.MessageSession,qqnum:str="all"):
    await user.check(msg,qqnum)
@yunhei.command('admin add <qqnum> <name> {添加云黑功能管理员}',required_superuser = True)
async def _(msg:Bot.MessageSession,qqnum:str,name:str):
    await user.admin_add(msg,qqnum,name)
@yunhei.command('admin del <qqnum> {删除云黑功能管理员}',required_superuser = True)
async def _(msg:Bot.MessageSession,qqnum:str):
    await user.admin_del(msg,qqnum)
@yunhei.command('admin list {查看云黑功能管理员列表}',required_superuser = True)
async def _(msg:Bot.MessageSession):
    await user.admin_list(msg)