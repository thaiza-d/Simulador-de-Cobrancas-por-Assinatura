from slowapi import Limiter
from slowapi.util import get_remote_address
from apscheduler.schedulers.background import BackgroundScheduler

limiter = Limiter(key_func=get_remote_address)
scheduler = BackgroundScheduler()