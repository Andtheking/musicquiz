import os

from requests import get
from utils.jsonUtils import fromJSON

class Config:
    def __init__(self):
        self.TOKEN = os.getenv("TELEGRAM_TOKEN")  # TOKEN DEL BOT
        self.CANALE_LOG = os.getenv("TELEGRAM_LOG_CHANNEL") or None
        self.BOT_INFO = get(f'https://api.telegram.org/bot{self.TOKEN}/getMe')
        self.BOT_USERNAME = fromJSON(self.BOT_INFO.text)['result']['username']
        
config = Config()
