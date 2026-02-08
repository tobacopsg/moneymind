import logging
from aiogram import Bot, Dispatcher, executor, types
from config import BOT_TOKEN, ADMIN_ID
from database import cursor, conn
from keyboards.user_kb import main_menu
from keyboards.admin_kb import admin_menu

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    cursor.execute("INSERT OR IGNORE INTO users(id) VALUES(?)", (m.from_user.id,))
    conn.commit()

    if m.from_user.id == ADMIN_ID:
        await m.answer("🎛 PANEL ADMIN", reply_markup=admin_menu())
    else:
        await m.answer(
            "🎉 Chào mừng bạn đến hệ thống kiếm tiền tự động\n\n"
            "Vui lòng sử dụng menu bên dưới để thao tác.",
            reply_markup=main_menu()
        )


@dp.callback_query_handler(lambda c: c.data == "deposit")
async def deposit(cb: types.CallbackQuery):
    cursor.execute("SELECT bank_name,stk,owner FROM bank WHERE id=1")
    bank = cursor.fetchone()
    await cb.message.answer(
        f"🏦 THÔNG TIN NẠP TIỀN\n\n"
        f"Ngân hàng: {bank[0]}\n"
        f"STK: {bank[1]}\n"
        f"Chủ TK: {bank[2]}\n\n"
        f"Chuyển khoản xong gửi bill cho admin."
    )


@dp.callback_query_handler(lambda c: c.data == "withdraw")
async def withdraw(cb: types.CallbackQuery):
    await cb.message.answer("💸 Nhập: Số tiền | Ngân hàng | STK | Chủ TK")


@dp.callback_query_handler(lambda c: c.data == "tasks")
async def tasks(cb: types.CallbackQuery):
    await cb.message.answer(
        "🎯 NHIỆM VỤ HẰNG NGÀY\n\n"
        "• Nạp tiền → thưởng 30%\n"
        "• Mời 3 người → +50.000đ\n"
        "• Rút ≥50k → +15.000đ"
    )


@dp.callback_query_handler(lambda c: c.data == "events")
async def events(cb: types.CallbackQuery):
    await cb.message.answer(
        "🎉 SỰ KIỆN HIỆN TẠI\n\n"
        "Đang cập nhật...\n\n"
        "Bấm tham gia để ghi danh."
    )


@dp.callback_query_handler(lambda c: c.data == "ranking")
async def ranking(cb: types.CallbackQuery):
    await cb.message.answer("🏆 BXH đang cập nhật")


@dp.callback_query_handler(lambda c: c.data == "invite")
async def invite(cb: types.CallbackQuery):
    link = f"https://t.me/{(await bot.get_me()).username}?start={cb.from_user.id}"
    await cb.message.answer(f"👥 Link mời bạn:\n{link}")


@dp.callback_query_handler(lambda c: c.data == "support")
async def support(cb: types.CallbackQuery):
    await cb.message.answer("📞 CSKH: @admin")


@dp.message_handler(commands=["admin"])
async def admin(m: types.Message):
    if m.from_user.id == ADMIN_ID:
        await m.answer("🎛 PANEL ADMIN", reply_markup=admin_menu())


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
