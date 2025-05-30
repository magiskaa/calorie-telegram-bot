from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.save_and_load import save_foods, food_data, user_data

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
        food_type = str(data.split("_", 1)[1])
        context.user_data["active_food_type"] = food_type

        await query.edit_message_text(
            f"{food_type.capitalize()} valittu. "
            "Kirjoita ruuan nimi, kalorit, kalorit per 100g, proteiinin määrä ja proteiini per 100g:"
        )
        return GET_FOOD
    
async def get_food(update: Update, context: ContextTypes.DEFAULT_TYPE):
    food = update.message.text.strip()
    name, calories, per_100, protein, protein_per_100 = food.split()

    food_type = context.user_data["active_food_type"]
    food_data[food_type][name] = {
        "calories": int(calories),
        "calories_per_100": int(per_100),
        "protein": float(protein),
        "protein_per_100": float(protein_per_100)
    }
    save_foods()

    await update.message.reply_text(
        f"Lisätty kategoriaan *{food_type.capitalize()}*:\n\n"
        f"Nimi: *{name.capitalize()}*\n"
        f"Kalorit: *{calories}kcal*\n"
        f"Per 100g: *{per_100}kcal*\n"
        f"Proteiinia: *{protein}g*\n"
        f"Per 100g: *{protein_per_100}g*",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# Edit existing foods
async def edit_menu_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [InlineKeyboardButton(type.capitalize(), callback_data=f"edittype_{type}") for i, type in enumerate(food_data)]
    buttons.append(InlineKeyboardButton("❌Peruuta", callback_data="edittype_cancel"))
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Valitse:", reply_markup=reply_markup)

async def edit_menu_food(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    type = context.user_data["active_food_type"]

    buttons = [InlineKeyboardButton(food.capitalize(), callback_data=f"editfood_{food}") for i, food in enumerate(food_data[type])]
    buttons.append(InlineKeyboardButton("❌Peruuta", callback_data="editfood_cancel"))
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Valitse:", reply_markup=reply_markup)

async def edit_menu_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    type = context.user_data["active_food_type"]
    food = context.user_data["active_food"]

    buttons = [InlineKeyboardButton(detail.capitalize(), callback_data=f"editdetail_{detail}") for i, detail in enumerate(food_data[type][food])]
    buttons.append(InlineKeyboardButton("Name", callback_data="editdetail_name"))
    buttons.append(InlineKeyboardButton("❌Peruuta", callback_data="editdetail_cancel"))
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Valitse:", reply_markup=reply_markup)

async def edit_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Cancel buttons
    if data in ("edittype_cancel", "editfood_cancel", "editdetail_cancel"):
        await query.edit_message_text("Peruutettu")
        return ConversationHandler.END

    # Edit type
    if data.startswith("edittype_"):
        food_type = str(data.split("_", 1)[1])
        context.user_data["active_food_type"] = food_type
        await edit_menu_food(update, context)
        return

    # Edit food
    if data.startswith("editfood_"):
        food = str(data.split("_", 1)[1])
        context.user_data["active_food"] = food
        await edit_menu_details(update, context)
        return

    # Edit detail
    if data.startswith("editdetail_"):
        detail = str(data.split("_", 1)[1])
        context.user_data["active_detail"] = detail
        await query.edit_message_text(f"Kirjoita uusi arvo ({detail}):")
        return EDIT_DETAIL

async def edit_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        type = context.user_data["active_food_type"]
        food = context.user_data["active_food"]
        detail = context.user_data["active_detail"]

        if detail == "name":
            new_value = str(update.message.text.strip())
            old_value = food
            food_data[type][new_value] = food_data[type].pop(old_value)
            save_foods()
            await update.message.reply_text(f"{food.capitalize()} | {detail}: {old_value} -> {new_value}")
            return ConversationHandler.END
        elif detail == "protein" or detail == "protein_per_100":
            new_value = round(float(update.message.text.strip()), 1)
            text = "g"
        else:
            new_value = int(update.message.text.strip())
            text = "kcal"
        
        if new_value <= 0:
            raise ValueError("Arvo ei voi olla nolla tai negatiivinen.")

        old_value = food_data[type][food][detail]
        food_data[type][food][detail] = new_value
        save_foods()

        await update.message.reply_text(f"{food.capitalize()} | {detail}: {old_value}{text} -> {new_value}{text}")
        return ConversationHandler.END
    except ValueError as e:
        if "Arvo ei" in str(e):
            await update.message.reply_text(f"Virheellinen syöte. {e}")
        else:
            await update.message.reply_text(f"Virheellinen syöte. Kirjoita uusi arvo:")
        return EDIT_DETAIL

# Show all available foods
async def food_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ""
    for i, type in enumerate(food_data):
        message += f"{type.capitalize()}:\n"
        for i, food in enumerate(food_data[type]):
            message += (
                f"   - {food.capitalize()}:\n"
                f"      ~ {food_data[type][food]['calories']}kcal, {food_data[type][food]['calories_per_100']}kcal, "
                f"{food_data[type][food]['protein']}g, {food_data[type][food]['protein_per_100']}g\n"
            )
    
    await update.message.reply_text(message)

# Show all todays foods
async def todays_foods(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    message = ""
    foods = user_data[user_id]["foods"]
    for i, food in enumerate(foods):
        message += (
            f"{foods[i]['name'].capitalize()}:\n"
            f"   - {foods[i]['calories']}kcal, {foods[i]['protein']}g\n"
        )
        
    await update.message.reply_text(message)