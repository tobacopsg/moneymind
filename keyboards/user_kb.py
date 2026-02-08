from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💰 Nạp tiền", callback_data="deposit"),
        InlineKeyboardButton("💸 Rút tiền", callback_data="withdraw"),
        InlineKeyboardButton("🎯 Nhiệm vụ", callback_data="tasks"),
        InlineKeyboardButton("🎉 Sự kiện", callback_data="events"),
        InlineKeyboardButton("🏆 Đua top", callback_data="ranking"),
        InlineKeyboardButton("👥 Mời bạn", callback_data="invite"),
        InlineKeyboardButton("🎁 Giftcode", callback_data="giftcode"),
        InlineKeyboardButton("📞 CSKH", callback_data="support")
    )
    return kb
