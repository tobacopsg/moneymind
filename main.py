import logging, sqlite3, random, string
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 123456789

logging.basicConfig(level=logging.INFO)
bot = Bot(TOKEN)
dp = Dispatcher(bot)

db = sqlite3.connect("bot.db")
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    ref INTEGER DEFAULT 0,
    invite INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
    deposit INTEGER DEFAULT 0,
    invite INTEGER DEFAULT 0,
    withdraw INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS giftcode (
    code TEXT PRIMARY KEY,
    value INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS pending (
    id INTEGER,
    type TEXT,
    amount INTEGER
)
""")

db.commit()

def menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💰 Nạp", callback_data="deposit"),
        InlineKeyboardButton("🏧 Rút", callback_data="withdraw"),
        InlineKeyboardButton("🎯 Nhiệm vụ", callback_data="task"),
        InlineKeyboardButton("🎉 Sự kiện", callback_data="event"),
        InlineKeyboardButton("👥 Mời bạn", callback_data="invite"),
        InlineKeyboardButton("🏆 BXH", callback_data="top"),
        InlineKeyboardButton("🎁 Giftcode", callback_data="gift")
    )
    return kb

@dp.message_handler(commands=['start'])
async def start(m: types.Message):
    uid = m.from_user.id
    ref = m.get_args()
    cur.execute("INSERT OR IGNORE INTO users(id, ref) VALUES(?,?)",(uid, ref if ref else 0))
    cur.execute("INSERT OR IGNORE INTO tasks(id) VALUES(?)",(uid,))
    if ref and int(ref)!=uid:
        cur.execute("UPDATE users SET invite = invite+1 WHERE id=?",(ref,))
    db.commit()
    await m.answer("🤖 BOT KIẾM TIỀN", reply_markup=menu())

@dp.callback_query_handler(text="deposit")
async def deposit(c: types.CallbackQuery):
    await c.message.answer("💰 Nhập số tiền cần nạp:")
    await c.answer()

@dp.callback_query_handler(text="withdraw")
async def withdraw(c: types.CallbackQuery):
    await c.message.answer("🏧 Nhập số tiền cần rút:")
    await c.answer()

@dp.callback_query_handler(text="invite")
async def invite(c: types.CallbackQuery):
    link = f"https://t.me/{(await bot.get_me()).username}?start={c.from_user.id}"
    await c.message.answer(f"👥 Link mời bạn:\n{link}")
    await c.answer()

@dp.callback_query_handler(text="event")
async def event(c: types.CallbackQuery):
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🔥 Tham gia", callback_data="join_event")
    )
    await c.message.answer("🎉 SỰ KIỆN HOT:\n- Mời 3 người = 99k\n- Top nạp thưởng lớn", reply_markup=kb)
    await c.answer()

@dp.callback_query_handler(text="join_event")
async def join_event(c: types.CallbackQuery):
    await c.message.answer("✅ Đã tham gia sự kiện!")
    await c.answer()

@dp.callback_query_handler(text="task")
async def task(c: types.CallbackQuery):
    cur.execute("SELECT * FROM tasks WHERE id=?",(c.from_user.id,))
    t = cur.fetchone()
    text = f"""
🎯 NHIỆM VỤ NGÀY
Nạp: {t[1]}/1 (+30%)
Mời: {t[2]}/3 (+50k)
Rút: {t[3]}/1 (+15k)
"""
    await c.message.answer(text)
    await c.answer()

@dp.callback_query_handler(text="top")
async def top(c: types.CallbackQuery):
    cur.execute("SELECT id,invite FROM users ORDER BY invite DESC LIMIT 10")
    data = cur.fetchall()
    text="🏆 TOP MỜI\n"
    for i,u in enumerate(data,1):
        text+=f"{i}. {u[0]} | {u[1]}\n"
    await c.message.answer(text)
    await c.answer()

@dp.callback_query_handler(text="gift")
async def gift(c: types.CallbackQuery):
    await c.message.answer("🎁 Nhập giftcode:")
    await c.answer()

@dp.message_handler(commands=['admin'])
async def admin(m: types.Message):
    if m.from_user.id!=ADMIN_ID: return
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✔ Duyệt nạp", callback_data="ad_deposit"),
        InlineKeyboardButton("✔ Duyệt rút", callback_data="ad_withdraw"),
        InlineKeyboardButton("🎁 Tạo code", callback_data="ad_code"),
        InlineKeyboardButton("🏦 Ngân hàng", callback_data="bank")
    )
    await m.answer("👑 ADMIN PANEL", reply_markup=kb)

@dp.callback_query_handler(text="ad_code")
async def create_code(c: types.CallbackQuery):
    code=''.join(random.choices(string.ascii_uppercase+string.digits,k=8))
    cur.execute("INSERT INTO giftcode VALUES(?,?)",(code,50000))
    db.commit()
    await c.message.answer(f"🎁 Code: {code} | 50k")

@dp.message_handler()
async def input_handler(m: types.Message):
    uid = m.from_user.id
    txt = m.text.strip()
    if txt.isdigit():
        amount=int(txt)
        cur.execute("INSERT INTO pending VALUES(?,?,?)",(uid,'deposit',amount))
        db.commit()
        await m.answer("⏳ Chờ admin duyệt nạp")
        await bot.send_message(ADMIN_ID,f"📥 NẠP\nUser: {uid}\nSố tiền: {amount}")
        return
    cur.execute("SELECT value FROM giftcode WHERE code=?",(txt,))
    g=cur.fetchone()
    if g:
        cur.execute("UPDATE users SET balance=balance+? WHERE id=?",(g[0],uid))
        cur.execute("DELETE FROM giftcode WHERE code=?",(txt,))
        db.commit()
        await m.answer(f"✅ Nhận {g[0]} VND")

if __name__=="__main__":
    executor.start_polling(dp)
