import re
import os

file_path = "bot/telegram_bot.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add get_main_menu_en
en_menu = '''def get_main_menu_en() -> InlineKeyboardMarkup:
    """English main menu"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🧹 Order Service", callback_data="order_start"),
            InlineKeyboardButton("💰 Prices", callback_data="show_prices")
        ],
        [
            InlineKeyboardButton("📞 Contact", callback_data="contact"),
            InlineKeyboardButton("ℹ️ About Us", callback_data="about")
        ],
        [
            InlineKeyboardButton("⭐ Reviews", callback_data="reviews"),
            InlineKeyboardButton("🎁 Promotions", callback_data="promos")
        ]
    ])

'''
content = content.replace(
    "def get_services_keyboard", en_menu + "def get_services_keyboard"
)

# get_services_keyboard
svc_en = """    if lang == 'en':
        buttons = [
            [InlineKeyboardButton("🏠 Home/Office Cleaning", callback_data="svc_regular_cleaning")],
            [InlineKeyboardButton("🔨 Post-renovation", callback_data="svc_renovation_cleaning")],
            [InlineKeyboardButton("🛋 Sofa Cleaning", callback_data="svc_sofa_cleaning")],
            [InlineKeyboardButton("🪑 Chair Cleaning", callback_data="svc_chair_cleaning")],
            [InlineKeyboardButton("🧶 Carpet Cleaning", callback_data="svc_carpet_cleaning")],
            [InlineKeyboardButton("🏢 Facade Cleaning", callback_data="svc_facade_cleaning")],
            [InlineKeyboardButton("🪟 Window Cleaning", callback_data="svc_window_cleaning")],
            [InlineKeyboardButton("🔲 Tile Cleaning", callback_data="svc_tile_cleaning")],
            [InlineKeyboardButton("📦 Move-out Cleaning", callback_data="svc_move_out_cleaning")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ]
    elif lang == 'ru':"""
content = content.replace(
    "    if lang == 'ru':", svc_en, 1
)  # Only first occurrence in get_services_keyboard

# get_confirm_keyboard
conf_en = """    if lang == 'en':
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Yes, confirm", callback_data="confirm_order"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_order")
            ]
        ])
    elif lang == 'ru':"""
content = content.replace("    if lang == 'ru':", conf_en, 1)

# menu selection in start_command and others
menu_logic = """    if lang == 'uz':
        menu = get_main_menu_uz()
    elif lang == 'ru':
        menu = get_main_menu_ru()
    else:
        menu = get_main_menu_en()"""
content = re.sub(
    r"menu = get_main_menu_uz\(\) if lang == 'uz' else get_main_menu_ru\(\)",
    menu_logic,
    content,
)

# help_command
help_en = '''    if lang == 'en':
        text = """🤖 *Tozalash Servis Bot Help*

/start — Main Menu
/prices — Price List
/order — Make an Order
/contact — Contact Info
/status — Order Status
/help — Help

💬 Or just type any question — AI will answer!"""
    elif lang == 'ru':'''
content = content.replace("    if lang == 'ru':", help_en, 1)

# prices_command
prices_en = '''    if lang == 'en':
        text = """💰 *Our Prices:*

🏠 *Home/Office Cleaning*
└ 500,000 UZS per worker

🔨 *Post-renovation Cleaning*
└ 600,000 UZS per worker

🛋 *Sofa Cleaning*
└ 80,000 UZS/seat (min. 5 seats)

🪑 *Chair Cleaning*
└ 50,000 UZS/item (min. 5 items)

🧶 *Carpet Cleaning*
└ 27,000 UZS/sq.m (min. 10 sq.m)

🏢 *Facade Cleaning*
└ 22,000 UZS/sq.m

🔲 *Tile Cleaning*
└ 15,000 UZS/sq.m

📞 For more info: {phone}""".format(phone=BUSINESS_PHONE)
    elif lang == 'ru':'''
content = content.replace("    if lang == 'ru':", prices_en, 1)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated successfully")
