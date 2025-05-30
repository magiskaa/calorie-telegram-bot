from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.save_and_load import save, user_data, food_data

GET_GOAL = 1

GET_INPUT = 1

GET_PER_100 = 1

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
        food_type = str(data.split("_")[1])
        context.user_data["active_food_type"] = food_type
        await get_food_menu(update, context)

async def get_food_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    food_type = context.user_data["active_food_type"]

    buttons = [InlineKeyboardButton(food.capitalize(), callback_data=f"food_{food}") for i, food in enumerate(food_data[food_type])]
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
        food_type = context.user_data["active_food_type"]
        chosen_food = str(data.split("_")[1])
        food_details = food_data[food_type][chosen_food]
        calories = food_details["calories"]
        protein = food_details["protein"]

        user_id = str(query.from_user.id)
        profile = user_data[user_id]
        profile["calories"] += calories
        profile["protein"] += protein

        profile["foods"].append({
            "name": chosen_food,
            "calories": calories,
            "protein": protein
        })
        save()

        await query.edit_message_text(
            f"Lisätty: *{chosen_food.capitalize()}*\n\n"
            f"Kaloreita: *{calories}kcal*\n"
            f"Proteiinia: *{protein}*g\n\n"
            f"Syöty: *{profile['calories']}kcal*\n"
            f"Jäljellä: *{profile['calorie_goal'] - profile['calories']}kcal*\n"
            f"Proteiini: *{profile['protein']}g*", 
            parse_mode="Markdown"
        )

# Add a food which has per_100 set
async def add_per_100(update: Update, context: ContextTypes.DEFAULT_TYPE):
    per_100_list = [
        (type, food)
        for type in food_data
        for food in food_data[type]
        if food_data[type][food]["calories_per_100"] > 0
    ]
    context.user_data["per_100_list"] = per_100_list

    buttons = [InlineKeyboardButton(food.capitalize(), callback_data=f"per100_{type}_{food}") for type, food in per_100_list]
    buttons.append(InlineKeyboardButton("❌Peruuta", callback_data="per100_cancel"))
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Valitse:", reply_markup=reply_markup)

async def per_100_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "per100_cancel":
        await query.edit_message_text("Peruutettu")
        return ConversationHandler.END
    elif data.startswith("per100_"):
        _, type, food = data.split("_")
        context.user_data["per_100_selected"] = (type, food)
        await query.edit_message_text(f"Paljonko söit: *{food.capitalize()}*", parse_mode="Markdown")
        return GET_PER_100

async def get_per_100(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip())
        if amount <= 0:
            raise ValueError("Määrä ei voi olla nolla tai negatiivinen.")
        
        type, food = context.user_data["per_100_selected"]

        food_details = food_data[type][food]

        calories_per_100 = food_details["calories_per_100"]
        protein_per_100 = food_details["protein_per_100"]

        total_calories = int(calories_per_100 * amount)
        total_protein = round(float(protein_per_100 * amount), 1)

        user_id = str(update.message.from_user.id)
        profile = user_data[user_id]

        profile["calories"] += total_calories
        profile["protein"] += total_protein

        profile["foods"].append({
            "name": food,
            "calories": total_calories,
            "protein": total_protein
        })
        save()

        await update.message.reply_text(
            f"Lisätty: *{food.capitalize()}*\n\n"
            f"Kaloreita: *{total_calories}kcal*\n"
            f"Proteiinia: *{total_protein}g*\n\n"
            f"Syöty: *{profile['calories']}kcal*\n"
            f"Jäljellä: *{profile['calorie_goal'] - profile['calories']}kcal*\n"
            f"Proteiini: *{profile['protein']}g*", 
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    except ValueError as e:
        if "Määrä ei" in str(e):
            await update.message.reply_text(f"Virheellinen syöte. {e}")
        else:
            await update.message.reply_text(f"Virheellinen syöte. Paljonko söit: *{food.capitalize()}*", parse_mode="Markdown")
        return GET_PER_100

# Add a custom amount of calories
async def add_custom_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Kirjoita kalorit ja proteiini:")
    return GET_INPUT

async def get_custom_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message.text.strip()
        calories, protein = message.split()
        if calories <= 0:
            raise ValueError("Kalorit eivät voi olla nolla tai negatiivinen.")
        if protein < 0:
            raise ValueError("Proteiini ei voi olla negatiivinen.")

        user_id = str(update.message.from_user.id)
        profile = user_data[user_id]

        profile["calories"] += calories
        profile["protein"] += protein
        save()

        await update.message.reply_text(
            f"Lisätty: *Custom*\n\n"
            f"Kaloreita: *{calories}kcal*\n"
            f"Proteiinia: *{protein}g*\n\n"
            f"Syöty: *{profile['calories']}kcal*\n"
            f"Jäljellä: *{profile['calorie_goal'] - profile['calories']}kcal*\n"
            f"Proteiini: *{profile['protein']}g*", 
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    except ValueError as e:
        if "Kalorit ei" in str(e) or "Proteiini ei" in str(e):
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
        f"Proteiini: *{profile['protein']}g*\n\n"
        f"Kalori KA: *{profile['month_avg_c']}kcal*\n"
        f"Proteiini KA: *{profile['month_avg_p']}g*", 
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