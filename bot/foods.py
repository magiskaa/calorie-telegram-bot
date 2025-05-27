from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.save_and_load import save, save_foods, user_data, food_data

active_food_type = None

GET_FOOD = 1

async def add_new_food_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [InlineKeyboardButton(type.capitalize(), callback_data=f"new_{type}") for i, type in enumerate(food_data)]
    buttons.append(InlineKeyboardButton("❌Peruuta", callback_data="new_cancel"))
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Valitse:", reply_markup=reply_markup)

async def new_food_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "new_cancel":
        await query.edit_message_text("Peruutettu")
        return ConversationHandler.END
    elif data.startswith("new_"):
        global active_food_type
        active_food_type = str(data.split("_")[1])

        await query.edit_message_text(f"{active_food_type.capitalize()} valittu. Kirjoita ruuan nimi, kalorit ja kalorit per 100g:")
        return GET_FOOD
    
async def get_food(update: Update, context: ContextTypes.DEFAULT_TYPE):
    food = update.message.text.strip()
    name, calories, per_100 = food.split()

    global active_food_type
    food_data[active_food_type][name] = {
        "calories": int(calories),
        "per_100": int(per_100)
    }
    save_foods()

    await update.message.reply_text(
        f"Lisätty kategoriaan {active_food_type}:\n"
        f"Nimi: {name}\n"
        f"Kalorit: {calories}\n"
        f"Per 100g: {per_100}"
    )
    return ConversationHandler.END
