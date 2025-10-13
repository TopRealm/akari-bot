from core.config import Config

from .rss_utils import fetch_latest_entry


YSARCHIVES_USER_AGENT = Config(
    "ysarchives_user_agent",
    "",
    cfg_type=str,
    table_name="module_weekly",
)


async def get_rss():
    """
    Get RSS feed from YsArchives
    """
    headers = {"User-Agent": YSARCHIVES_USER_AGENT} if YSARCHIVES_USER_AGENT else None

    return await fetch_latest_entry(
        "https://youshou.wiki/api.php?action=featuredfeed&feed=ysarchives-biweekly&feedformat=atom",
        "https://youshou.wiki",
        headers=headers,
    )
