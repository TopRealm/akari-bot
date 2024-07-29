from core.builtins import Bot
from core.logger import Logger
from core.queue import JobQueue
from core.scheduler import CronTrigger, Scheduler
from modules.weekly import get_weekly
from modules.weekly.teahouse import get_rss as get_teahouse_rss
from modules.weekly.ysarchives import get_rss as get_ysarchives_rss
from datetime import datetime, timedelta
from apscheduler.triggers.interval import IntervalTrigger

# 尝试更新装饰器触发逻辑
def calculate_this_sunday():
    today = datetime.now()
    days_until_sunday = (6 - today.weekday()) % 7
    return today + timedelta(days=days_until_sunday)

this_sunday = calculate_this_sunday().replace(hour=19, minute=10)


@Scheduler.scheduled_job(trigger=IntervalTrigger(weeks=2), next_run_time = this_sunday)
async def weekly_rss():
    Logger.info('Checking ysarchives biweekly...')

    weekly = await get_ysarchives_rss()
    await JobQueue.trigger_hook_all('ysarchives_weekly_rss', weekly=weekly)


@Scheduler.scheduled_job(CronTrigger.from_crontab('0 9 * * MON'))
async def weekly_rss():
    Logger.info('Checking MCWZH weekly...')

    weekly_cn = await get_weekly(True if Bot.FetchTarget.name == 'QQ' else False)
    weekly_tw = await get_weekly(True if Bot.FetchTarget.name == 'QQ' else False, zh_tw=True)
    _weekly_cn = [i.to_dict() for i in weekly_cn]
    _weekly_tw = [i.to_dict() for i in weekly_tw]
    await JobQueue.trigger_hook_all('weekly_rss', weekly_cn=_weekly_cn, weekly_tw=_weekly_tw)


@Scheduler.scheduled_job(trigger=CronTrigger.from_crontab('30 9 * * MON'))
async def weekly_rss():
    Logger.info('Checking teahouse weekly...')

    weekly = await get_teahouse_rss()
    await JobQueue.trigger_hook_all('teahouse_weekly_rss', weekly=weekly)


# @Scheduler.scheduled_job(trigger=CronTrigger.from_crontab('10 19 * * SUN'))
# async def weekly_rss():
#     Logger.info('Checking ysarchives biweekly...')

#     weekly = await get_ysarchives_rss()
#     await JobQueue.trigger_hook_all('ysarchives_weekly_rss', weekly=weekly)
