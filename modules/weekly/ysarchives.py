import feedparser

from core.utils.html2text import html2text
from core.utils.http import get_url


async def get_rss():
    """
    Get RSS feed from YsArchives
    """
    url = await get_url('https://youshou.wiki/api.php?action=featuredfeed&feed=ysarchives-biweekly&feedformat=atom',
                        status_code=200, fmt='text')
    feed = feedparser.parse(url)['entries'][-1]
    title = feed['title']
    summary = html2text(feed['summary'], baseurl='https://youshou.wiki')
    return title + '\n' + summary
