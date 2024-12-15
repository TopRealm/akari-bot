from core.builtins import Bot
from core.logger import Logger
from core.queue import JobQueue
from core.scheduler import CronTrigger, Scheduler
from modules.weekly import get_weekly
from modules.weekly.teahouse import get_rss as get_teahouse_rss
from modules.weekly.ysarchives import get_rss as get_ysarchives_rss
from datetime import datetime


def is_odd_week():
    today = datetime.now()
    return today.isocalendar()[1] % 2 != 0

async def weekly_rss():
    Logger.info("Checking MCWZH weekly...")

    weekly_cn = await get_weekly(Bot.FetchTarget.name == "QQ")
    weekly_tw = await get_weekly(Bot.FetchTarget.name == "QQ", zh_tw=True)
    _weekly_cn = [i.to_dict() for i in weekly_cn]
    _weekly_tw = [i.to_dict() for i in weekly_tw]
    await JobQueue.trigger_hook_all(
        "weekly_rss", weekly_cn=_weekly_cn, weekly_tw=_weekly_tw
    )


@Scheduler.scheduled_job(trigger=CronTrigger.from_crontab("30 9 * * MON"))
async def weekly_rss():
    Logger.info("Checking teahouse weekly...")

    weekly = await get_teahouse_rss()
    await JobQueue.trigger_hook_all("teahouse_weekly_rss", weekly=weekly)


@Scheduler.scheduled_job(trigger=CronTrigger.from_crontab('0 9 * * MON'))
async def weekly_rss():
    Logger.info('Checking ysarchives biweekly...')

    if is_odd_week():
        weekly = await get_ysarchives_rss()
        await JobQueue.trigger_hook_all('ysarchives_weekly_rss', weekly=weekly)
