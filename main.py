import os, sqlite3, time, random, string
from telebot import TeleBot, types

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = TeleBot(TOKEN, parse_mode="HTML")
DB="bot.db"

def db(): return sqlite3.connect(DB, check_same_thread=False)

def init():
    c=db();cur=c.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 0,
        state TEXT DEFAULT '',
        bank TEXT DEFAULT '',
        streak INTEGER DEFAULT 0,
        last_check INTEGER DEFAULT 0,
        invited INTEGER DEFAULT 0,
        invited_today INTEGER DEFAULT 0,
        last_invite INTEGER DEFAULT 0
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER, amount INTEGER, note TEXT, t INTEGER
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS pending(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER, type TEXT, amount INTEGER, info TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS giftcodes(
        code TEXT PRIMARY KEY, used INTEGER DEFAULT 0
    )""")
    c.commit();c.close()

init()

def user(uid):
    c=db();cur=c.cursor()
    cur.execute("SELECT * FROM users WHERE id=?",(uid,))
    r=cur.fetchone()
    if not r:
        cur.execute("INSERT INTO users(id) VALUES(?)",(uid,))
        c.commit()
        cur.execute("SELECT * FROM users WHERE id=?",(uid,))
        r=cur.fetchone()
    c.close(); return r

def set_state(uid,s):
    c=db();cur=c.cursor()
    cur.execute("UPDATE users SET state=? WHERE id=?",(s,uid))
    c.commit();c.close()

def add(uid,amt,note):
    c=db();cur=c.cursor()
    cur.execute("UPDATE users SET balance=balance+? WHERE id=?",(amt,uid))
    cur.execute("INSERT INTO logs(uid,amount,note,t) VALUES(?,?,?,?)",
                (uid,amt,note,int(time.time())))
    c.commit();c.close()

def sub(uid,amt,note): add(uid,-amt,note)

def menu():
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=3)
    kb.add("💰 Nạp","💸 Rút","📅 Điểm danh")
    kb.add("👥 Mời","🎯 Nhiệm vụ","🏆 Đua top")
    kb.add("🎉 Sự kiện","💳 Số dư","🛎 CSKH")
    kb.add("🎁 Giftcode")
    return kb

@bot.message_handler(commands=["start"])
def start(m):
    user(m.from_user.id)
    bot.send_message(m.chat.id,"🤖 BOT TÀI CHÍNH VIP\n\n👇 Chọn chức năng:",reply_markup=menu())

def locked(uid):
    return user(uid)[2]!=""

# ===== NẠP =====
@bot.message_handler(func=lambda m:m.text=="💰 Nạp")
def nap(m):
    uid=m.from_user.id
    if locked(uid): return
    set_state(uid,"nap_amount")
    bot.send_message(m.chat.id,"💰 Nhập số tiền cần nạp (k):")

# ===== RÚT =====
@bot.message_handler(func=lambda m:m.text=="💸 Rút")
def rut(m):
    uid=m.from_user.id
    if locked(uid): return
    set_state(uid,"rut_bank")
    bot.send_message(m.chat.id,"🏦 Nhập NH - STK - CTK:")

# ===== ĐIỂM DANH =====
@bot.message_handler(func=lambda m:m.text=="📅 Điểm danh")
def checkin(m):
    uid=m.from_user.id
    u=user(uid)
    today=int(time.time()//86400)
    if u[5]==today: return bot.send_message(m.chat.id,"❌ Hôm nay đã điểm danh")
    streak=u[4]+1 if u[5]==today-1 else 1
    reward=random.randint(1,10)*1000
    c=db();cur=c.cursor()
    cur.execute("UPDATE users SET streak=?,last_check=? WHERE id=?",(streak,today,uid))
    c.commit();c.close()
    add(uid,reward,"Điểm danh")
    if streak==7: add(uid,100000,"Chuỗi 7 ngày")
    if streak==30: add(uid,3000000,"Chuỗi 30 ngày")
    bot.send_message(m.chat.id,f"🎁 +{reward:,} | Chuỗi {streak} ngày")

# ===== SỐ DƯ =====
@bot.message_handler(func=lambda m:m.text=="💳 Số dư")
def bal(m):
    u=user(m.from_user.id)
    c=db();cur=c.cursor()
    cur.execute("SELECT amount,note FROM logs WHERE uid=? ORDER BY id DESC LIMIT 5",(m.from_user.id,))
    logs="\n".join([f"{a:+,} | {n}" for a,n in cur.fetchall()])
    c.close()
    bot.send_message(m.chat.id,f"💳 SỐ DƯ: {u[1]:,}\n\n{logs if logs else 'Chưa có giao dịch'}")

# ===== CSKH =====
@bot.message_handler(func=lambda m:m.text=="🛎 CSKH")
def cskh(m):
    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💰 Nạp",callback_data="cskh_nap"),
           types.InlineKeyboardButton("💸 Rút",callback_data="cskh_rut"))
    kb.add(types.InlineKeyboardButton("🎁 Gift",callback_data="cskh_gift"),
           types.InlineKeyboardButton("📞 Liên hệ",url="https://t.me/cskhmnm"))
    bot.send_message(m.chat.id,"🛎 CSKH – Chọn mục:",reply_markup=kb)

@bot.callback_query_handler(func=lambda c:c.data.startswith("cskh"))
def cskh_cb(c):
    if c.data=="cskh_nap":
        bot.send_message(c.message.chat.id,"⏳ Nạp tiền đang chờ admin xử lý")
    if c.data=="cskh_rut":
        bot.send_message(c.message.chat.id,"⏳ Rút tiền đang chờ admin xử lý")
    if c.data=="cskh_gift":
        code="".join(random.choices(string.ascii_uppercase+string.digits,k=10))
        cdb=db();cur=cdb.cursor()
        cur.execute("INSERT OR IGNORE INTO giftcodes(code) VALUES(?)",(code,))
        cdb.commit();cdb.close()
        bot.send_message(c.message.chat.id,f"🎁 Giftcode hôm nay: <b>{code}</b>")

# ===== GIFTCODE =====
@bot.message_handler(func=lambda m:m.text=="🎁 Giftcode")
def gift(m):
    set_state(m.from_user.id,"gift")
    bot.send_message(m.chat.id,"🎁 Nhập giftcode:")

# ===== MESSAGE HANDLER =====
@bot.message_handler(func=lambda m:True)
def handler(m):
    uid=m.from_user.id
    st=user(uid)[2]

    if st=="nap_amount":
        if not m.text.isdigit(): return
        amt=int(m.text)*1000
        c=db();cur=c.cursor()
        cur.execute("INSERT INTO pending(uid,type,amount,info) VALUES(?,?,?,?)",
                    (uid,"nap",amt,""))
        pid=cur.lastrowid; c.commit();c.close()
        kb=types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✅ Đã xong",callback_data=f"ok_{pid}"),
               types.InlineKeyboardButton("❌ Hủy",callback_data=f"cancel_{pid}"))
        bot.send_message(m.chat.id,
            f"🏦 CHUYỂN: {amt:,} VND\nCTK: TRAN KIM SON\nSTK: 10425048114935233\n\nBấm xác nhận:",
            reply_markup=kb)
        set_state(uid,"")

    elif st=="rut_bank":
        c=db();cur=c.cursor()
        cur.execute("UPDATE users SET bank=? WHERE id=?",(m.text,uid))
        c.commit();c.close()
        set_state(uid,"rut_amount")
        bot.send_message(m.chat.id,"💸 Nhập số tiền rút (min 200k):")

    elif st=="rut_amount":
        if not m.text.isdigit(): return
        amt=int(m.text)*1000
        if amt<200000 or user(uid)[1]<amt:
            set_state(uid,"")
            return bot.send_message(m.chat.id,"❌ Không hợp lệ")
        c=db();cur=c.cursor()
        cur.execute("INSERT INTO pending(uid,type,amount,info) VALUES(?,?,?,?)",
                    (uid,"rut",amt,user(uid)[3]))
        pid=cur.lastrowid; c.commit();c.close()
        bot.send_message(m.chat.id,"⏳ Đang chờ duyệt")
        bot.send_message(ADMIN_ID,f"💸 DUYỆT RÚT ID {pid}")
        set_state(uid,"")

    elif st=="gift":
        c=db();cur=c.cursor()
        cur.execute("SELECT used FROM giftcodes WHERE code=?",(m.text,))
        r=cur.fetchone()
        if not r or r[0]==1:
            bot.send_message(m.chat.id,"❌ Sai")
        else:
            reward=random.randint(8000,88000)
            cur.execute("UPDATE giftcodes SET used=1 WHERE code=?",(m.text,))
            c.commit();c.close()
            add(uid,reward,"Giftcode")
            bot.send_message(m.chat.id,f"🎉 +{reward:,}")
        set_state(uid,"")

# ===== CALLBACK =====
@bot.callback_query_handler(func=lambda c:True)
def cb(c):
    if c.data.startswith("ok_"):
        pid=int(c.data.split("_")[1])
        bot.send_message(ADMIN_ID,f"💰 DUYỆT NẠP ID {pid}")
    if c.data.startswith("cancel_"):
        bot.answer_callback_query(c.id,"Đã hủy")

# ===== ADMIN =====
@bot.message_handler(commands=["duyet"])
def duyet(m):
    if m.from_user.id!=ADMIN_ID: return
    try:
        _,pid=m.text.split()
        pid=int(pid)
    except:
        return
    c=db();cur=c.cursor()
    cur.execute("SELECT uid,type,amount FROM pending WHERE id=?",(pid,))
    r=cur.fetchone()
    if not r: return bot.send_message(m.chat.id,"❌ Không tồn tại")
    uid,typ,amt=r
    if typ=="nap":
        add(uid,amt,"Nạp")
        bot.send_message(uid,f"🎉 Nạp {amt:,} thành công")
    if typ=="rut":
        sub(uid,amt,"Rút")
        bot.send_message(uid,f"🎉 Rút {amt:,} thành công")
    cur.execute("DELETE FROM pending WHERE id=?",(pid,))
    c.commit();c.close()

print("BOT ONLINE")
bot.infinity_polling()
