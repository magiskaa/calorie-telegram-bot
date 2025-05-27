from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.save_and_load import save, user_data, food_data

active_food_type = None

GET_GOAL = 1

GET_INPUT = 1

# Add calories
async def get_type_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [InlineKeyboardButton(type.capitalize(), callback_data=f"type_{type}") for i, type in enumerate(food_data)]
    buttons.append(InlineKeyboardButton("❌Peruuta", callback_data="type_cancel"))
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
        global active_food_type
        active_food_type = str(data.split("_")[1])
        await get_food_menu(update, context, active_food_type)

async def get_food_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, type: str):
    query = update.callback_query
    await query.answer()
    data = query.data

    buttons = [InlineKeyboardButton(food.capitalize(), callback_data=f"food_{food}") for i, food in enumerate(food_data[type])]
    buttons.append(InlineKeyboardButton("❌Peruuta", callback_data="food_cancel"))
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
        global active_food_type
        chosen_food = str(data.split("_")[1])
        food = food_data[active_food_type][chosen_food]
        calories = food["calories"]
        protein = food["protein"]

        user_id = str(query.from_user.id)
        profile = user_data[user_id]
        profile["calories"] += calories
        profile["protein"] += protein

        profile["foods"].append({
            "food_type": active_food_type,
            "name": chosen_food,
            "calories": calories,
            "protein": protein
        })
        save()

        await query.edit_message_text(
            f"Lisätty *{chosen_food}*: *{food['calories']}kcal*.\n\n"
            f"Syöty: *{profile['calories']}kcal*\n"
            f"Jäljellä: *{profile['calorie_goal'] - profile['calories']}kcal*\n"
            f"Proteiini: *{profile['protein']}g*", 
            parse_mode="Markdown"
        )

# Add a food which has per_100 set
async def add_per_100(update: Update, context: ContextTypes.DEFAULT_TYPE):
    per_100 = []
    for i, type in enumerate(food_data):
        for i, food in enumerate(food_data[type]):
            if food_data[type][food]["per_100"] == 0:
                continue
            else:
                per_100.append(food)

    buttons = [InlineKeyboardButton(food.capitalize(), callback_data=f"type_{food}") for i, food in enumerate(per_100)]
    buttons.append(InlineKeyboardButton("❌Peruuta", callback_data="type_cancel"))
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Valitse:", reply_markup=reply_markup)

# Add a custom amount of calories
async def free_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Kirjoita kalorit:")
    return GET_INPUT

async def get_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        calories = int(update.message.text.strip())
        if calories <= 0:
            raise ValueError("Kalorit eivät voi olla nolla tai negatiivinen.")
        
        user_id = str(update.message.from_user.id)
        profile = user_data[user_id]

        profile["calories"] += calories
        save()

        await update.message.reply_text(
            f"Lisätty: *{calories}kcal*.\n\n"
            f"Syöty: *{profile['calories']}kcal*\n"
            f"Jäljellä: *{profile['calorie_goal'] - profile['calories']}kcal*\n"
            f"Proteiini: *{profile['protein']}g*", 
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    except ValueError as e:
        if "Kalorit ei" in str(e):
            await update.message.reply_text(f"Virheellinen syöte. {e}")
        else:
            await update.message.reply_text("Virheellinen syöte. Syötä kalorit:")
        return GET_INPUT

# Show todays consumed and remaining calories
async def show_calories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    profile = user_data[user_id]

    await update.message.reply_text(
        f"Syöty: *{profile['calories']}kcal*\n"
        f"Jäljellä: *{profile['calorie_goal'] - profile['calories']}kcal*\n"
        f"Proteiini: *{profile['protein']}g*", 
        parse_mode="Markdown"
    )

# Set daily calorie goal
async def set_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Kirjoita uusi päivittäinen kaloritavoite:")
    return GET_GOAL

async def get_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        goal = int(update.message.text.strip())
        if goal <= 0:
            raise ValueError("Tavoite ei voi olla nolla tai negatiivinen.")
        
        user_id = str(update.message.from_user.id)
        profile = user_data[user_id]

        old_goal = profile["calorie_goal"]
        profile["calorie_goal"] = goal
        save()

        await update.message.reply_text(f"Tavoite päivitetty: {old_goal}kcal -> {goal}kcal.")
        return ConversationHandler.END
    except ValueError as e:
        if "Tavoite ei" in str(e):
            await update.message.reply_text(f"Virheellinen syöte. {e}")
        else:
            await update.message.reply_text(f"Virheellinen syöte. Kirjoita uusi päivittäinen kaloritavoite:")
        return GET_GOAL