from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Duyệt nạp", callback_data="admin_deposit"),
        InlineKeyboardButton("💸 Duyệt rút", callback_data="admin_withdraw"),
        InlineKeyboardButton("🏦 Ngân hàng", callback_data="admin_bank"),
        InlineKeyboardButton("🎁 Giftcode", callback_data="admin_gift")
    )
    return kb
