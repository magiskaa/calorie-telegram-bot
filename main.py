import html
import json
import logging
import traceback
from datetime import datetime, time
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, ConversationHandler, CallbackQueryHandler, filters
from config.config import BOT_TOKEN, ADMIN_ID
from bot.save_and_load import save, user_data
from bot.job_queue import daily_reset
from bot.calorie_tracking import (
    get_type_menu, type_button_handler, food_button_handler, add_per_100, per_100_button_handler, get_per_100, show_calories, 
    set_goal, get_goal, add_custom_amount, get_custom_amount, GET_GOAL, GET_INPUT, GET_PER_100
)
from bot.foods import (
    add_new_food_menu, new_food_button_handler, get_food, edit_menu_type, edit_detail, edit_button_handler, 
    food_list, todays_foods, GET_FOOD, EDIT_DETAIL
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in user_data:
        await update.message.reply_text("Olet jo aloittanut botin käytön. Voit jatkaa komennolla: /add.")
        return

    user_data[user_id] = {
        "name": update.message.from_user.first_name,
        "calories": 0,
        "calorie_goal": 2500,
        "protein": 0,
        "month_avg_c": 0,
        "month_avg_p": 0,
        "foods": []
    }
    save()

    await update.message.reply_text(
        "Heipat! Pidän kirjaa tämän päivän kaloreistasi.\n"
        "Voit aloittaa komennolla: /add."
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Peruutettu")
    return ConversationHandler.END    
    
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    profile = user_data[user_id]

    profile["calories"] = 0
    profile["protein"] = 0
    profile["foods"] = []
    save()

    await update.message.reply_text("Kalorit resetattu.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling an update: ", exc_info=context.error)

    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        "An exception was raised while handling an update:\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    await context.bot.send_message(chat_id=ADMIN_ID, text=message, parse_mode=ParseMode.HTML)


def main():
    try:
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("reset", reset))
        app.add_handler(CommandHandler("cancel", cancel))

        app.add_handler(CommandHandler("add", get_type_menu))
        app.add_handler(CallbackQueryHandler(type_button_handler, pattern="^type_"))
        app.add_handler(CallbackQueryHandler(food_button_handler, pattern="^food_"))

        app.add_handler(CommandHandler("show", show_calories))

        app.add_handler(CommandHandler("food_list", food_list))

        app.add_handler(CommandHandler("todays_foods", todays_foods))

        goal_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("goal", set_goal)],
            states={
                GET_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_goal)]
            },
            fallbacks=[CommandHandler("cancel", cancel)]
        )
        app.add_handler(goal_conv_handler)

        custom_amount_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("custom", add_custom_amount)],
            states={
                GET_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_custom_amount)]
            },
            fallbacks=[CommandHandler("cancel", cancel)]
        )
        app.add_handler(custom_amount_conv_handler)

        new_food_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("add_food", add_new_food_menu), CallbackQueryHandler(new_food_button_handler, pattern="^new_")],
            states={
                GET_FOOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_food)]
            },
            fallbacks=[CommandHandler("cancel", cancel)]
        )
        app.add_handler(new_food_conv_handler)

        edit_food_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("edit_food", edit_menu_type), CallbackQueryHandler(edit_button_handler, pattern="^edit")],
            states={
                EDIT_DETAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_detail)]
            },
            fallbacks=[CommandHandler("cancel", cancel)]
        )
        app.add_handler(edit_food_conv_handler)

        add_per_100_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("per_100", add_per_100), CallbackQueryHandler(per_100_button_handler, pattern="^per100_")],
            states={
                GET_PER_100: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_per_100)]
            },
            fallbacks=[CommandHandler("cancel", cancel)]
        )
        app.add_handler(add_per_100_conv_handler)

        job_queue = app.job_queue
        job_queue.run_daily(daily_reset, time(hour=2, minute=0))

        app.add_error_handler(error_handler)

        app.run_polling()
    except Exception as e:
        print(f"Error in main: {e}")


if __name__ == "__main__":
    main()
    
    