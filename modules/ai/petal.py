from decimal import Decimal
from math import ceil

from core.builtins import Bot
from core.config import Config

PREDICT_TOKEN = 1000


def precount_petal(msg: Bot.MessageSession, price: float, predict_token: int = PREDICT_TOKEN) -> bool:
    if Config("enable_petal", False):
        petal = int(ceil(predict_token * Decimal(price)))
        return msg.petal >= petal
    return True


def count_token_petal(msg: Bot.MessageSession, price: float, tokens: int) -> int:
    if Config("enable_petal", False):
        petal = int(ceil(tokens * Decimal(price)))
        msg.info.modify_petal(-petal)
        return petal
    return 0
