import os, sqlite3, time, random, string
from telebot import TeleBot, types

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = TeleBot(TOKEN, parse_mode="HTML")
DB = "bot.db"

# ===== DATABASE =====
def db():
    return sqlite3.connect(DB, check_same_thread=False)

def init():
    c = db(); cur = c.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 0,
        invited INTEGER DEFAULT 0,
        invited_today INTEGER DEFAULT 0,
        last_invite_day INTEGER DEFAULT 0,
        checkin_day INTEGER DEFAULT 0,
        streak INTEGER DEFAULT 0
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER, amount INTEGER, note TEXT, t INTEGER
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS deposits(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER, amount INTEGER, status TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS withdraws(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER, amount INTEGER, bank TEXT, status TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS giftcodes(
        code TEXT PRIMARY KEY, used INTEGER DEFAULT 0
    )""")
    c.commit(); c.close()

init()

def user(uid):
    c=db(); cur=c.cursor()
    cur.execute("SELECT * FROM users WHERE id=?",(uid,))
    r=cur.fetchone()
    if not r:
        cur.execute("INSERT INTO users(id) VALUES(?)",(uid,))
        c.commit()
        cur.execute("SELECT * FROM users WHERE id=?",(uid,))
        r=cur.fetchone()
    c.close()
    return r

def add(uid, amount, note=""):
    c=db(); cur=c.cursor()
    cur.execute("UPDATE users SET balance=balance+? WHERE id=?",(amount,uid))
    cur.execute("INSERT INTO logs(uid,amount,note,t) VALUES(?,?,?,?)",
                (uid,amount,note,int(time.time())))
    c.commit(); c.close()

def sub(uid, amount, note=""):
    add(uid, -amount, note)

# ===== MENU =====
def menu():
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=3)
    kb.add("💰 Nạp tiền","💸 Rút tiền","📅 Điểm danh")
    kb.add("👥 Mời bạn","🎯 Nhiệm vụ","🏆 Đua top")
    kb.add("🎉 Sự kiện","💳 Số dư","🛎 CSKH")
    kb.add("🎁 Nhập giftcode")
    return kb

@bot.message_handler(commands=["start"])
def start(m):
    user(m.from_user.id)
    bot.send_message(m.chat.id,
    "🤖 <b>BOT TÀI CHÍNH CAO CẤP</b>\n"
    "⚡ Giao diện VIP – xử lý cực nhanh\n"
    "💎 Khuyến mãi cực lớn mỗi ngày\n\n"
    "👇 Chọn chức năng:",
    reply_markup=menu())

# ===== NẠP =====
@bot.message_handler(func=lambda m:m.text=="💰 Nạp tiền")
def deposit(m):
    msg=bot.send_message(m.chat.id,"💰 Nhập số tiền cần nạp (k):")
    bot.register_next_step_handler(msg,dep_amount)

def dep_amount(m):
    if not m.text.isdigit(): return
    amount=int(m.text)*1000
    c=db(); cur=c.cursor()
    cur.execute("INSERT INTO deposits(uid,amount,status) VALUES(?,?,?)",
                (m.from_user.id,amount,"pending"))
    did=cur.lastrowid; c.commit(); c.close()

    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Đã hoàn tất",callback_data=f"dok_{did}"),
           types.InlineKeyboardButton("❌ Hủy",callback_data=f"dcancel_{did}"))

    bot.send_message(m.chat.id,
    f"🏦 <b>THÔNG TIN NẠP</b>\n"
    f"Ngân hàng: Kiên Long Bank\n"
    f"CTK: TRAN KIM SON\n"
    f"STK: 10425048114935233\n\n"
    f"Số tiền: <b>{amount:,} VND</b>\n"
    f"Nội dung: MM{m.from_user.id}\n\n"
    f"Sau khi chuyển → bấm <b>Đã hoàn tất</b>",
    reply_markup=kb)

@bot.callback_query_handler(func=lambda c:c.data.startswith("dok_"))
def done_dep(c):
    did=int(c.data.split("_")[1])
    bot.send_message(ADMIN_ID,f"💰 DUYỆT NẠP ID {did}")

@bot.callback_query_handler(func=lambda c:c.data.startswith("dcancel_"))
def cancel_dep(c):
    bot.answer_callback_query(c.id,"Đã hủy")

# ===== ADMIN DUYỆT =====
@bot.message_handler(commands=["duyet"])
def admin_approve(m):
    if m.from_user.id!=ADMIN_ID: return
    try:
        _,typ,_id=m.text.split()
    except:
        return bot.send_message(m.chat.id,"/duyet nap 12  |  /duyet rut 12")

    c=db(); cur=c.cursor()
    if typ=="nap":
        cur.execute("SELECT uid,amount FROM deposits WHERE id=? AND status='pending'",(_id,))
        r=cur.fetchone()
        if not r: return bot.send_message(m.chat.id,"❌ Không tồn tại")
        uid,amt=r
        cur.execute("UPDATE deposits SET status='done' WHERE id=?",(_id,))
        add(uid,amt,"Nạp tiền")
        bot.send_message(uid,f"🎉 Nạp <b>{amt:,}</b> thành công!")
    if typ=="rut":
        cur.execute("SELECT uid,amount FROM withdraws WHERE id=? AND status='pending'",(_id,))
        r=cur.fetchone()
        if not r: return bot.send_message(m.chat.id,"❌ Không tồn tại")
        uid,amt=r
        cur.execute("UPDATE withdraws SET status='done' WHERE id=?",(_id,))
        sub(uid,amt,"Rút tiền")
        bot.send_message(uid,f"🎉 Rút <b>{amt:,}</b> thành công!")
    c.commit(); c.close()

# ===== RÚT =====
@bot.message_handler(func=lambda m:m.text=="💸 Rút tiền")
def withdraw(m):
    msg=bot.send_message(m.chat.id,"💸 Nhập số tiền cần rút (k, min 200k):")
    bot.register_next_step_handler(msg,w_amount)

def w_amount(m):
    if not m.text.isdigit(): return
    amt=int(m.text)*1000
    if amt<200000: return bot.send_message(m.chat.id,"❌ Tối thiểu 200k")
    if user(m.from_user.id)[1]<amt:
        return bot.send_message(m.chat.id,"❌ Số dư không đủ")
    msg=bot.send_message(m.chat.id,"🏦 Nhập thông tin NH - STK - CTK:")
    bot.register_next_step_handler(msg,w_bank,amt)

def w_bank(m,amt):
    c=db(); cur=c.cursor()
    cur.execute("INSERT INTO withdraws(uid,amount,bank,status) VALUES(?,?,?,?)",
                (m.from_user.id,amt,m.text,"pending"))
    wid=cur.lastrowid; c.commit(); c.close()
    bot.send_message(m.chat.id,"⏳ Đang chờ duyệt")
    bot.send_message(ADMIN_ID,f"💸 DUYỆT RÚT ID {wid}")

# ===== ĐIỂM DANH =====
@bot.message_handler(func=lambda m:m.text=="📅 Điểm danh")
def checkin(m):
    uid=m.from_user.id
    c=db(); cur=c.cursor()
    cur.execute("SELECT checkin_day,streak FROM users WHERE id=?",(uid,))
    last,streak=cur.fetchone()
    today=int(time.time()//86400)
    if last==today: return bot.send_message(m.chat.id,"❌ Hôm nay đã điểm danh")
    if last==today-1: streak+=1
    else: streak=1
    reward=random.randint(1,10)*1000
    cur.execute("UPDATE users SET checkin_day=?,streak=? WHERE id=?",(today,streak,uid))
    add(uid,reward,"Điểm danh")
    if streak==7: add(uid,100000,"Chuỗi 7 ngày")
    if streak==30: add(uid,3000000,"Chuỗi 30 ngày")
    c.commit(); c.close()
    bot.send_message(m.chat.id,f"🎁 Nhận {reward:,} | Chuỗi {streak} ngày")

# ===== MỜI BẠN =====
@bot.message_handler(func=lambda m:m.text=="👥 Mời bạn")
def invite(m):
    link=f"https://t.me/{bot.get_me().username}?start={m.from_user.id}"
    bot.send_message(m.chat.id,
    f"👥 Link mời:\n{link}\n\n"
    f"🎁 1 bạn đủ điều kiện → 99k\n"
    f"🏆 20 bạn → 1000k | 50 bạn → 3000k")

# ===== SỐ DƯ =====
@bot.message_handler(func=lambda m:m.text=="💳 Số dư")
def balance(m):
    u=user(m.from_user.id)
    c=db(); cur=c.cursor()
    cur.execute("SELECT amount,note FROM logs WHERE uid=? ORDER BY id DESC LIMIT 5",(m.from_user.id,))
    logs="\n".join([f"{'+' if i[0]>0 else ''}{i[0]:,} | {i[1]}" for i in cur.fetchall()])
    c.close()
    bot.send_message(m.chat.id,
    f"💳 <b>SỐ DƯ:</b> {u[1]:,} VND\n\n"
    f"📜 <b>5 Giao dịch gần nhất:</b>\n{logs if logs else 'Chưa có'}")

# ===== CSKH =====
@bot.message_handler(func=lambda m:m.text=="🛎 CSKH")
def cskh(m):
    bot.send_message(m.chat.id,
    "🛎 <b>TRUNG TÂM CSKH</b>\n\n"
    "• Nạp tiền: chờ duyệt\n"
    "• Rút tiền: chờ duyệt\n"
    "• Lỗi nhận thưởng\n"
    "• Nhận giftcode\n\n"
    "📞 Liên hệ: @cskhmnm")

# ===== GIFT =====
@bot.message_handler(func=lambda m:m.text=="🎁 Nhập giftcode")
def gift(m):
    msg=bot.send_message(m.chat.id,"🎁 Nhập giftcode:")
    bot.register_next_step_handler(msg,gift_ok)

def gift_ok(m):
    c=db(); cur=c.cursor()
    cur.execute("SELECT used FROM giftcodes WHERE code=?",(m.text,))
    r=cur.fetchone()
    if not r or r[0]==1:
        return bot.send_message(m.chat.id,"❌ Giftcode không hợp lệ")
    reward=random.randint(8000,88000)
    cur.execute("UPDATE giftcodes SET used=1 WHERE code=?",(m.text,))
    add(m.from_user.id,reward,"Giftcode")
    c.commit(); c.close()
    bot.send_message(m.chat.id,f"🎉 Nhận {reward:,} VND")

# ===== TẠO GIFTCODE ADMIN =====
@bot.message_handler(commands=["gift"])
def gen_gift(m):
    if m.from_user.id!=ADMIN_ID: return
    code="".join(random.choices(string.ascii_uppercase+string.digits,k=10))
    c=db(); cur=c.cursor()
    cur.execute("INSERT INTO giftcodes(code) VALUES(?)",(code,))
    c.commit(); c.close()
    bot.send_message(m.chat.id,f"🎁 Giftcode: <b>{code}</b>")

print("BOT ONLINE...")
bot.infinity_polling()
