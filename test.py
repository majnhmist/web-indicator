import os
from datetime import date
import telegram
from dotenv import load_dotenv
import time

if __name__ == '__main__':
    
    load_dotenv()
    TOKEN = os.getenv('TOKEN')
    today = date.today()
    bot = telegram.Bot(token=TOKEN)
    text = "hello manhmit"
    bot.send_message(chat_id='-4034907986',text=text,parse_mode='Markdown',disable_web_page_preview=True)
    update = bot.get_updates()
