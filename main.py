import os
import random
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_user(data, uid):
    uid = str(uid)
    if uid not in data:
        data[uid] = {
            "balance": 0,
            "history": [],
            "checkin": {
                "last": "",
                "streak": 0
            },
            "events": {
                "newbie": False,
                "invite": False,
                "task": False,
                "checkin": False
            },
            "giftcodes": []
        }
    return data[uid]

def add_money(user, amount, reason):
    user["balance"] += amount
    user["history"].insert(0, f"{'+' if amount>0 else ''}{amount:,}đ | {reason}")
    user["history"] = user["history"][:5]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("💰 Số dư", callback_data="balance")],
        [InlineKeyboardButton("🎯 Sự kiện", callback_data="event")],
        [InlineKeyboardButton("📋 Nhiệm vụ", callback_data="task")],
        [InlineKeyboardButton("📅 Điểm danh", callback_data="checkin")],
        [InlineKeyboardButton("🎁 Nhập Giftcode", callback_data="redeem")],
        [InlineKeyboardButton("☎ CSKH", callback_data="cskh")]
    ]
    await update.message.reply_text("🤖 *BOT KIẾM TIỀN TỰ ĐỘNG*\n\nChọn chức năng bên dưới:", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = load_data()
    user = get_user(data, q.from_user.id)

    if q.data == "balance":
        text = f"👤 ID: {q.from_user.id}\n💰 Số dư: {user['balance']:,}đ\n\n🕘 Lịch sử gần nhất:\n"
        for h in user["history"]:
            text += f"• {h}\n"
        await q.edit_message_text(text)

    elif q.data == "checkin":
        today = datetime.now().strftime("%Y-%m-%d")
        last = user["checkin"]["last"]

        if last == today:
            await q.edit_message_text("❌ Bạn đã điểm danh hôm nay rồi!")
        else:
            if last == (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"):
                user["checkin"]["streak"] += 1
            else:
                user["checkin"]["streak"] = 1

            reward = random.randint(1000, 10000)
            streak = user["checkin"]["streak"]

            if streak == 7:
                reward += 100000
            if streak == 30:
                reward += 3000000

            user["checkin"]["last"] = today
            add_money(user, reward, "Điểm danh")

            save_data(data)
            await q.edit_message_text(f"✅ Điểm danh thành công!\n🎁 Nhận: {reward:,}đ\n🔥 Chuỗi: {streak} ngày")

    elif q.data == "event":
        text = (
            "🎉 *TRUNG TÂM SỰ KIỆN*\n\n"
            "🎁 Tân thủ: Nhận 58k (1 lần)\n"
            "👥 Mời bạn: Mời ≥1 bạn nhận 99k\n"
            "📅 Điểm danh: Nhận 99k\n"
            "📋 Nhiệm vụ: Làm ≥1 nhiệm vụ nhận 88k\n\n"
            "👉 Nhấn nút bên dưới để nhận thưởng!"
        )
        kb = [[InlineKeyboardButton("🎁 Nhận thưởng", callback_data="event_claim")]]
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif q.data == "event_claim":
        reward = 58000
        add_money(user, reward, "Sự kiện tân thủ")
        save_data(data)
        await q.edit_message_text(f"🎉 Nhận thành công {reward:,}đ")

    elif q.data == "cskh":
        text = (
            "☎ *TRUNG TÂM CSKH*\n\n"
            "💳 Nạp tiền – chờ admin xử lý\n"
            "🏧 Rút tiền – duyệt thủ công\n"
            "🎁 Nhận Giftcode – mỗi ngày 1 lần\n"
            "👤 Liên hệ trực tiếp: @cskhmnm"
        )
        kb = [[InlineKeyboardButton("🎁 Nhận Giftcode", callback_data="getcode")]]
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif q.data == "getcode":
        today = datetime.now().strftime("%Y-%m-%d")
        if today in user["giftcodes"]:
            await q.edit_message_text("❌ Hôm nay bạn đã nhận giftcode!")
        else:
            code = f"MM{random.randint(100000,999999)}"
            user["giftcodes"].append(today)
            context.bot_data[code] = True
            save_data(data)
            await q.edit_message_text(f"🎁 Giftcode của bạn:\n`{code}`", parse_mode="Markdown")

    elif q.data == "redeem":
        await q.edit_message_text("🎁 Vui lòng nhập Giftcode:")
        context.user_data["redeem"] = True

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("redeem"):
        return

    code = update.message.text.strip()
    data = load_data()
    user = get_user(data, update.message.from_user.id)

    if context.bot_data.get(code):
        reward = random.randint(8000, 88000)
        add_money(user, reward, "Giftcode")
        del context.bot_data[code]
        save_data(data)
        await update.message.reply_text(f"🎉 Nhập thành công! Nhận {reward:,}đ")
    else:
        await update.message.reply_text("❌ Giftcode không hợp lệ!")

    context.user_data["redeem"] = False

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, redeem))
    app.run_polling()

if __name__ == "__main__":
    main()

