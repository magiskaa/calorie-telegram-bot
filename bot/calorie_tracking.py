from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.save_and_load import save, save_foods, user_data, food_data


async def get_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [InlineKeyboardButton(type.capitalize(), callback_data=f"type_{type}") for i, type in enumerate(food_data)]
    buttons.append(InlineKeyboardButton("Peruuta", callback_data="type_cancel"))
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Valitse:", reply_markup=reply_markup)

async def type_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "type_cancel":
        await query.edit_message_text("Peruutettu")
        return ConversationHandler.END
    elif data.startswith("type_"):
        type = str(data.split("_")[1])
        await get_food(update, context, type)

async def get_food(update: Update, context: ContextTypes.DEFAULT_TYPE, type: str):
    query = update.callback_query
    await query.answer()
    data = query.data

    buttons = [InlineKeyboardButton(food.capitalize(), callback_data=f"food_{i}") for i, food in enumerate(food_data[type])]
    buttons.append(InlineKeyboardButton("Peruuta", callback_data="food_cancel"))
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Valitse:", reply_markup=reply_markup)

async def food_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "food_cancel":
        await query.edit_message_text("Peruutettu")
        return ConversationHandler.END
    elif data.startswith("food_"):
        index = int(data.split("_")[1])
        if index < 0:
            await query.edit_message_text("Virheellinen valinta.")
            return ConversationHandler.END
        else:
            await query.edit_message_text("Lisätty")
