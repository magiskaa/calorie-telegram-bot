from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.save_and_load import save, save_foods, user_data, food_data

active_food_type = None
active_food = None
active_detail = None

GET_FOOD = 1

EDIT_DETAIL = 1

# Add new foods
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

        await query.edit_message_text(
            f"{active_food_type.capitalize()} valittu. "
            "Kirjoita ruuan nimi, kalorit, kalorit per 100g ja proteiinin määrä:"
        )
        return GET_FOOD
    
async def get_food(update: Update, context: ContextTypes.DEFAULT_TYPE):
    food = update.message.text.strip()
    name, calories, per_100, protein = food.split()

    global active_food_type
    food_data[active_food_type][name] = {
        "calories": int(calories),
        "per_100": int(per_100),
        "protein": int(protein)
    }
    save_foods()

    await update.message.reply_text(
        f"Lisätty kategoriaan {active_food_type}:\n"
        f"Nimi: {name}\n"
        f"Kalorit: {calories}kcal\n"
        f"Per 100g: {per_100}kcal\n"
        f"Proteiinia: {protein}g"
    )
    return ConversationHandler.END

# Edit existing foods
async def edit_menu_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [InlineKeyboardButton(type.capitalize(), callback_data=f"edittype_{type}") for i, type in enumerate(food_data)]
    buttons.append(InlineKeyboardButton("❌Peruuta", callback_data="edittype_cancel"))
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Valitse:", reply_markup=reply_markup)

async def edit_menu_food(update: Update, context: ContextTypes.DEFAULT_TYPE, type: str):
    query = update.callback_query
    await query.answer()
    data = query.data

    buttons = [InlineKeyboardButton(food.capitalize(), callback_data=f"editfood_{food}") for i, food in enumerate(food_data[type])]
    buttons.append(InlineKeyboardButton("❌Peruuta", callback_data="editfood_cancel"))
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Valitse:", reply_markup=reply_markup)

async def edit_menu_details(update: Update, context: ContextTypes.DEFAULT_TYPE, type: str, food: str):
    query = update.callback_query
    await query.answer()
    data = query.data

    buttons = [InlineKeyboardButton(detail.capitalize(), callback_data=f"editdetail_{detail}") for i, detail in enumerate(food_data[type][food])]
    buttons.append(InlineKeyboardButton("❌Peruuta", callback_data="editdetail_cancel"))
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Valitse:", reply_markup=reply_markup)

async def edit_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    global active_food_type, active_food, active_detail

    # Cancel buttons
    if data in ("edittype_cancel", "editfood_cancel", "editdetail_cancel"):
        await query.edit_message_text("Peruutettu")
        return ConversationHandler.END

    # Edit type
    if data.startswith("edittype_"):
        active_food_type = str(data.split("_")[1])
        await edit_menu_food(update, context, active_food_type)
        return

    # Edit food
    if data.startswith("editfood_"):
        active_food = str(data.split("_")[1])
        await edit_menu_details(update, context, active_food_type, active_food)
        return

    # Edit detail
    if data.startswith("editdetail_"):
        active_detail = str(data.split("_")[1])
        await query.edit_message_text("Kirjoita uusi arvo:")
        return EDIT_DETAIL

async def edit_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_value = int(update.message.text.strip())
        if new_value <= 0:
            raise ValueError("Arvo ei voi olla nolla tai negatiivinen.")
        
        global active_food_type, active_food, active_detail

        old_value = food_data[active_food_type][active_food][active_detail]
        food_data[active_food_type][active_food][active_detail] = new_value
        save_foods()

        if active_detail == "protein":
            text = "g"
        else:
            text = "kcal"

        await update.message.reply_text(f"{active_food.capitalize()} | {active_detail}: {old_value}{text} -> {new_value}{text}")
        return ConversationHandler.END
    except ValueError as e:
        if "Arvo ei" in str(e):
            await update.message.reply_text(f"Virheellinen syöte. {e}")
        else:
            await update.message.reply_text(f"Virheellinen syöte. Kirjoita uusi arvo:")
