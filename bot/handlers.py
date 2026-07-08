from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from bot import storage, tasks
from bot.config import ADMIN_ID, REWARD_SHORTEN, REWARD_VISIT, MIN_WITHDRAW, POINTS_PER_VND

# ConversationHandler states
WAITING_URL = 1
WAITING_BANK = 2
WAITING_APPROVE = 3

# ─── /start ───────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    storage.get_user(user.id)  # init nếu chưa có
    
    keyboard = [
        [InlineKeyboardButton("📋 Nhiệm vụ", callback_data="menu_tasks"),
         InlineKeyboardButton("💰 Số dư", callback_data="menu_balance")],
        [InlineKeyboardButton("💸 Rút tiền", callback_data="menu_withdraw"),
         InlineKeyboardButton("📊 Lịch sử", callback_data="menu_history")]
    ]
    await update.message.reply_text(
        f"👋 Chào {user.first_name}!\n\n"
        f"🤖 <b>Link4m Earn Bot</b>\n"
        f"Làm nhiệm vụ → Nhận điểm → Rút tiền\n\n"
        f"📌 {REWARD_SHORTEN} điểm/link rút gọn\n"
        f"📌 {REWARD_VISIT} điểm/quảng cáo\n"
        f"📌 {MIN_WITHDRAW} điểm = {MIN_WITHDRAW // POINTS_PER_VND * 1000:,}đ",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ─── MENU CALLBACK ─────────────────────────────────────────
async def menu_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu_tasks":
        keyboard = [
            [InlineKeyboardButton(f"🔗 Rút gọn link (+{REWARD_SHORTEN}đ)", callback_data="task_shorten")],
            [InlineKeyboardButton(f"👁 Xem quảng cáo (+{REWARD_VISIT}đ)", callback_data="task_ads")],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="menu_back")]
        ]
        await query.edit_message_text(
            "📋 <b>Chọn nhiệm vụ:</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data == "menu_balance":
        user_data = storage.get_user(query.from_user.id)
        vnd = user_data['points'] // POINTS_PER_VND * 1000
        await query.edit_message_text(
            f"💰 <b>Số dư của bạn</b>\n\n"
            f"🪙 Điểm hiện tại: <b>{user_data['points']:,}</b>\n"
            f"💵 Quy đổi: <b>{vnd:,}đ</b>\n\n"
            f"📈 Tổng đã kiếm: {user_data['total_earned']:,} điểm\n"
            f"✅ Nhiệm vụ đã làm: {user_data['tasks_done']}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Quay lại", callback_data="menu_back")
            ]])
        )

    elif data == "menu_withdraw":
        user_data = storage.get_user(query.from_user.id)
        if user_data['points'] < MIN_WITHDRAW:
            needed = MIN_WITHDRAW - user_data['points']
            await query.edit_message_text(
                f"❌ Chưa đủ điểm để rút!\n\n"
                f"Cần thêm <b>{needed:,} điểm</b> nữa\n"
                f"(Tối thiểu: {MIN_WITHDRAW:,} điểm)",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Quay lại", callback_data="menu_back")
                ]])
            )
        else:
            ctx.user_data["withdraw_points"] = user_data['points']
            await query.edit_message_text(
                f"💸 <b>Rút tiền</b>\n\n"
                f"Số điểm có thể rút: <b>{user_data['points']:,}</b>\n"
                f"Tương đương: <b>{user_data['points'] // POINTS_PER_VND * 1000:,}đ</b>\n\n"
                f"Nhập thông tin ngân hàng theo định dạng:\n"
                f"<code>STK - Ngân hàng - Tên chủ TK</code>\n"
                f"Ví dụ: <code>0123456789 - VCB - Nguyen Van A</code>",
                parse_mode="HTML"
            )
            ctx.user_data["state"] = WAITING_BANK
            ctx.user_data["withdraw_uid"] = query.from_user.id

    elif data == "menu_history":
        user_data = storage.get_user(query.from_user.id)
        history = user_data.get("withdraw_history", [])[-5:]
        if not history:
            text = "📊 Chưa có lịch sử rút tiền."
        else:
            lines = []
            for h in reversed(history):
                status_icon = "✅" if h["status"] == "approved" else ("❌" if h["status"] == "rejected" else "⏳")
                lines.append(f"{status_icon} {h['id']}: {h['points']:,} điểm — {h['time']}")
            text = "📊 <b>Lịch sử rút tiền (5 gần nhất):</b>\n\n" + "\n".join(lines)
        
        await query.edit_message_text(
            text, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Quay lại", callback_data="menu_back")
            ]])
        )

    elif data == "menu_back":
        keyboard = [
            [InlineKeyboardButton("📋 Nhiệm vụ", callback_data="menu_tasks"),
             InlineKeyboardButton("💰 Số dư", callback_data="menu_balance")],
            [InlineKeyboardButton("💸 Rút tiền", callback_data="menu_withdraw"),
             InlineKeyboardButton("📊 Lịch sử", callback_data="menu_history")]
        ]
        await query.edit_message_text(
            "🤖 <b>Link4m Earn Bot</b> — Chọn chức năng:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data == "task_shorten":
        await query.edit_message_text(
            f"🔗 <b>Nhiệm vụ: Rút gọn link</b>\n\n"
            f"Gửi link bất kỳ muốn rút gọn.\n"
            f"Bot sẽ tạo link4m và cộng <b>{REWARD_SHORTEN} điểm</b> cho bạn.\n\n"
            f"📤 Gửi link ngay:",
            parse_mode="HTML"
        )
        ctx.user_data["state"] = WAITING_URL
        ctx.user_data["task_uid"] = query.from_user.id

    elif data == "task_ads":
        ad_list = tasks.get_ad_tasks()
        keyboard = [
            [InlineKeyboardButton(ad["title"], url=ad["url"]),
             InlineKeyboardButton("✅ Đã xem", callback_data=f"confirm_ad_{ad['id']}")]
            for ad in ad_list
        ]
        keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data="menu_tasks")])
        await query.edit_message_text(
            f"👁 <b>Nhiệm vụ: Xem quảng cáo</b>\n\n"
            f"Click link → chờ 15 giây → nhấn ✅ Đã xem\n"
            f"Mỗi link: <b>+{REWARD_VISIT} điểm</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("confirm_ad_"):
        ad_id = data.replace("confirm_ad_", "")
        uid = query.from_user.id
        
        # Check chống spam: lưu vào user_data session
        seen = ctx.user_data.get("seen_ads", set())
        if ad_id in seen:
            await query.answer("⚠️ Bạn đã xem quảng cáo này rồi!", show_alert=True)
            return
        seen.add(ad_id)
        ctx.user_data["seen_ads"] = seen
        
        storage.add_points(uid, REWARD_VISIT)
        user_data = storage.get_user(uid)
        await query.answer(f"✅ +{REWARD_VISIT} điểm! Tổng: {user_data['points']:,}", show_alert=True)

    # ─── ADMIN: duyệt rút tiền ──────────────────────────
    elif data.startswith("approve_") or data.startswith("reject_"):
        if query.from_user.id != ADMIN_ID:
            await query.answer("⛔ Không có quyền!", show_alert=True)
            return
        
        parts = data.split("_")
        action = parts[0]           # approve / reject
        req_id = parts[1]           # WDxxxxxxxxxx
        target_uid = int(parts[2])  # user id
        
        user_data = storage.get_user(target_uid)
        history = user_data.get("withdraw_history", [])
        
        for req in history:
            if req["id"] == req_id:
                req["status"] = "approved" if action == "approve" else "rejected"
                if action == "reject":
                    # Hoàn điểm
                    storage.update_user(target_uid, {
                        "points": user_data["points"] + req["points"],
                        "pending_withdraw": max(0, user_data.get("pending_withdraw", 0) - req["points"]),
                        "withdraw_history": history
                    })
                else:
                    storage.update_user(target_uid, {
                        "pending_withdraw": max(0, user_data.get("pending_withdraw", 0) - req["points"]),
                        "withdraw_history": history
                    })
                break
        
        status_text = "✅ ĐÃ DUYỆT" if action == "approve" else "❌ TỪ CHỐI"
        await query.edit_message_text(
            query.message.text + f"\n\n<b>{status_text}</b> bởi admin",
            parse_mode="HTML"
        )
        
        # Notify user
        try:
            msg = (f"✅ Yêu cầu rút tiền #{req_id} đã được <b>duyệt</b>! Vui lòng chờ chuyển khoản."
                   if action == "approve"
                   else f"❌ Yêu cầu rút tiền #{req_id} bị <b>từ chối</b>. Điểm đã được hoàn lại.")
            await ctx.bot.send_message(target_uid, msg, parse_mode="HTML")
        except Exception:
            pass

# ─── TEXT HANDLER (URL + Bank info) ───────────────────────
async def text_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    state = ctx.user_data.get("state")
    
    if state == WAITING_URL:
        url = update.message.text.strip()
        if not url.startswith("http"):
            await update.message.reply_text("⚠️ Link không hợp lệ. Phải bắt đầu bằng http/https")
            return
        
        await update.message.reply_text("⏳ Đang rút gọn link...")
        result = await tasks.shorten_link(url)
        
        if result.get("status") == "success":
            short_url = result["shortenedUrl"]
            uid = ctx.user_data.get("task_uid", update.effective_user.id)
            storage.add_points(uid, REWARD_SHORTEN)
            user_data = storage.get_user(uid)
            
            await update.message.reply_text(
                f"✅ <b>Rút gọn thành công!</b>\n\n"
                f"🔗 Link gốc: <code>{url[:50]}...</code>\n"
                f"✂️ Link rút gọn: {short_url}\n\n"
                f"🪙 +{REWARD_SHORTEN} điểm! Tổng: <b>{user_data['points']:,}</b>",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(f"❌ Lỗi: {result.get('message', 'Unknown error')}")
        
        ctx.user_data["state"] = None

    elif state == WAITING_BANK:
        bank_info = update.message.text.strip()
        uid = ctx.user_data.get("withdraw_uid", update.effective_user.id)
        user_data = storage.get_user(uid)
        points_to_withdraw = user_data["points"]
        vnd = points_to_withdraw // POINTS_PER_VND * 1000
        
        req_id = storage.create_withdraw_request(uid, points_to_withdraw, bank_info)
        
        # Notify admin
        keyboard = [[
            InlineKeyboardButton("✅ Duyệt", callback_data=f"approve_{req_id}_{uid}"),
            InlineKeyboardButton("❌ Từ chối", callback_data=f"reject_{req_id}_{uid}")
        ]]
        await ctx.bot.send_message(
            ADMIN_ID,
            f"💸 <b>YÊU CẦU RÚT TIỀN MỚI</b>\n\n"
            f"👤 User: {update.effective_user.full_name} (ID: {uid})\n"
            f"🪙 Điểm: {points_to_withdraw:,}\n"
            f"💵 Số tiền: {vnd:,}đ\n"
            f"🏦 Thông tin: <code>{bank_info}</code>\n"
            f"📋 Mã yêu cầu: {req_id}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        await update.message.reply_text(
            f"✅ <b>Đã gửi yêu cầu rút tiền!</b>\n\n"
            f"💵 Số tiền: <b>{vnd:,}đ</b>\n"
            f"📋 Mã: {req_id}\n\n"
            f"Admin sẽ xử lý trong vòng 24h.",
            parse_mode="HTML"
        )
        ctx.user_data["state"] = None

# ─── ADMIN COMMANDS ────────────────────────────────────────
async def admin_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    all_users = storage.get_all_users()
    total_points = sum(u["points"] for u in all_users.values())
    total_users = len(all_users)
    total_tasks = sum(u["tasks_done"] for u in all_users.values())
    
    await update.message.reply_text(
        f"📊 <b>Thống kê hệ thống</b>\n\n"
        f"👥 Tổng users: {total_users}\n"
        f"🪙 Tổng điểm đang lưu: {total_points:,}\n"
        f"✅ Tổng nhiệm vụ đã làm: {total_tasks}",
        parse_mode="HTML"
    )

def build_application(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CallbackQueryHandler(menu_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    return app
