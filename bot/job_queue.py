from telegram.ext import CallbackContext
from datetime import datetime, timedelta
from bot.save_and_load import save, user_data
from config.config import ADMIN_ID

async def daily_reset(context: CallbackContext):
    date = datetime.now() - timedelta(days=1)
    date_str = date.strftime("%d.%m.%Y")

    profile = user_data[str(ADMIN_ID)]

    history = user_data["history"]

    oldest = date - timedelta(days=28)
    oldest_str = oldest.strftime("%d.%m.%Y")
    if oldest_str in history:
        history.pop(oldest_str)
        
    history[date_str] = {
        "calories": profile["calories"],
        "calorie_goal": profile["calorie_goal"],
        "protein": profile["protein"]
    }

    days = 0
    sum_c = 0
    sum_p = 0
    for i, day in enumerate(history):
        days += 1
        sum_c += history[day]["calories"]
        sum_p += history[day]["protein"]
    
    profile["month_avg_c"] = int(sum_c / days)
    profile["month_avg_p"] = round(float(sum_p / days), 1)

    profile["calories"] = 0
    profile["protein"] = 0
    profile["foods"] = []

    save()
