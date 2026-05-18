import asyncio
import aiohttp
import json
import re
from datetime import datetime

TOKEN = "8877423898:AAGh_tsQVdGSL0bX8w-I8_XHijHM74HCq5g"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
ADMIN_ID = 5546613019

# =====================
# RAQAMLAR BAZASI
# =====================
NUMBERS_DB = {
    "simple":   {"name": "⚪ Simple",   "price_uz": "Bepul",                      "price_ru": "Бесплатно",         "numbers": []},
    "steel":    {"name": "🔵 Steel",    "price_uz": "10 000 so'm",                "price_ru": "10 000 сум",        "numbers": []},
    "gold":     {"name": "🟡 Gold",     "price_uz": "250 000 so'm",               "price_ru": "250 000 сум",       "numbers": []},
    "platinum": {"name": "⚫ Platinum", "price_uz": "500 000 so'm",               "price_ru": "500 000 сум",       "numbers": []},
    "vip":      {"name": "💜 VIP",      "price_uz": "1 000 000 so'm",             "price_ru": "1 000 000 сум",     "numbers": []},
    "lux":      {"name": "✨ Lux",      "price_uz": "1 500 000 - 3 000 000 so'm", "price_ru": "1.5M - 3M сум",    "numbers": []},
    "luxplus":  {"name": "💎 Lux+",     "price_uz": "2 500 000 - 5 000 000 so'm", "price_ru": "2.5M - 5M сум",    "numbers": []},
    "special":  {"name": "👑 Special",  "price_uz": "10 000 000+ so'm",           "price_ru": "10 000 000+ сум",   "numbers": []},
}

# Zaxira raqamlar (sayt yuklanmasa ishlatiladi)
FALLBACK_NUMBERS = {
    "simple":   ["+998 50 171 28 54","+998 50 171 28 62","+998 50 171 28 64","+998 50 171 28 69","+998 50 171 28 73","+998 50 171 29 18","+998 50 171 29 32","+998 50 171 29 34","+998 50 171 29 41","+998 50 171 29 45"],
    "steel":    ["+998 50 729 89 27","+998 50 752 62 57","+998 50 756 26 57","+998 93 053 83 50","+998 93 060 67 89","+998 93 124 94 21","+998 93 134 24 31","+998 93 148 58 41","+998 93 152 15 23","+998 93 158 41 58"],
    "gold":     ["+998 50 188 68 66","+998 93 614 03 30","+998 93 692 00 29","+998 93 785 06 60","+998 93 835 00 53","+998 93 843 00 66","+998 93 847 22 20","+998 93 961 04 40","+998 94 142 06 60","+998 94 267 33 30"],
    "platinum": ["+998 50 728 00 60","+998 93 413 00 60","+998 93 483 00 60","+998 93 532 00 60","+998 93 641 00 60","+998 93 758 00 30","+998 93 827 00 40","+998 93 852 00 30","+998 94 185 00 60","+998 94 431 00 90"],
    "vip":      ["+998 50 579 60 00","+998 93 164 00 06","+998 93 174 60 00","+998 93 179 80 00","+998 93 268 40 00","+998 93 283 00 06","+998 93 324 00 06","+998 93 429 00 06","+998 93 539 00 06","+998 93 592 00 06"],
    "lux":      ["+998 93 341 60 60","+998 93 689 30 30","+998 93 849 60 60","+998 94 090 33 00","+998 94 293 60 60","+998 94 398 60 60","+998 94 728 40 40","+998 94 731 60 60","+998 94 842 60 60","+998 94 843 60 60"],
    "luxplus":  ["+998 50 220 60 60","+998 50 330 06 06","+998 50 330 60 60","+998 50 330 80 80","+998 93 060 80 00","+998 93 080 60 60","+998 93 660 40 40","+998 93 880 30 30","+998 94 002 60 60","+998 94 006 80 80"],
    "special":  ["+998 93 060 06 66","+998 93 226 66 66","+998 50 883 33 33"],
}

last_update_time = None
user_states = {}
user_langs = {}  # foydalanuvchi tili

# =====================
# STATISTIKA BAZASI
# =====================
import os

STATS_FILE = "bot_stats.json"

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "users": {},        # {chat_id: {name, username, first_seen, last_seen, lang, actions}}
        "orders": [],       # buyurtmalar ro'yxati
        "searches": [],     # qidiruvlar
        "total_starts": 0,
    }

def save_stats(stats):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def track_user(chat_id, user_name, username=""):
    stats = load_stats()
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    uid = str(chat_id)
    if uid not in stats["users"]:
        stats["users"][uid] = {
            "name": user_name,
            "username": username,
            "first_seen": now,
            "last_seen": now,
            "lang": "uz",
            "actions": 0
        }
        stats["total_starts"] += 1
    else:
        stats["users"][uid]["last_seen"] = now
        stats["users"][uid]["name"] = user_name
    stats["users"][uid]["actions"] = stats["users"][uid].get("actions", 0) + 1
    save_stats(stats)

def track_order(chat_id, user_name, order_id, number, phone):
    stats = load_stats()
    stats["orders"].append({
        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "order_id": order_id,
        "user_id": str(chat_id),
        "user_name": user_name,
        "number": number,
        "phone": phone
    })
    save_stats(stats)

def track_search(chat_id, query, results_count):
    stats = load_stats()
    stats["searches"].append({
        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "user_id": str(chat_id),
        "query": query,
        "results": results_count
    })
    save_stats(stats)

# =====================
# SAYTDAN RAQAM OLISH
# =====================
async def fetch_numbers_from_site():
    """
    Ucell sayt JavaScript bilan ishlaydi — oddiy HTTP so'rov bilan
    raqamlarni olib bo'lmaydi. Shuning uchun har doim FALLBACK ishlatamiz.
    Raqamlarni qo'lda yangilash uchun FALLBACK_NUMBERS ni tahrirlang.
    """
    global last_update_time

    print("📋 Zaxira raqamlar bazaga yuklanmoqda...")
    for key in NUMBERS_DB:
        NUMBERS_DB[key]["numbers"] = list(FALLBACK_NUMBERS.get(key, []))

    last_update_time = datetime.now()
    total = sum(len(v["numbers"]) for v in NUMBERS_DB.values())
    print(f"✅ Bazaga {total} ta raqam yuklandi: {last_update_time.strftime('%d.%m.%Y %H:%M')}")

async def auto_update_loop():
    """Har 6 soatda avtomatik yangilash"""
    while True:
        await fetch_numbers_from_site()
        await asyncio.sleep(6 * 60 * 60)

# =====================
# NIQOB QIDIRISH
# =====================
def match_mask(number_clean, mask_clean):
    """
    Niqob qidirish: * — istalgan raqam
    Masalan: 9300**00 yoki 93***000
    """
    if len(mask_clean) != len(number_clean):
        # Uzunlik mos kelmasa, substring qidirish
        if '*' not in mask_clean:
            return mask_clean in number_clean
        return False

    for m, n in zip(mask_clean, number_clean):
        if m == '*':
            continue
        if m != n:
            return False
    return True

def search_numbers(query, lang="uz"):
    query_clean = re.sub(r'[^\d*]', '', query)
    found = []

    for cat_key, cat_data in NUMBERS_DB.items():
        for number in cat_data["numbers"]:
            num_clean = re.sub(r'[^\d]', '', number)
            matched = False

            if '*' in query_clean:
                matched = match_mask(num_clean, query_clean)
            else:
                matched = query_clean in num_clean

            if matched:
                price = cat_data["price_uz"] if lang == "uz" else cat_data["price_ru"]
                found.append({
                    "number": number,
                    "category": cat_data["name"],
                    "price": price
                })
    return found

# =====================
# TELEGRAM FUNKSIYALAR
# =====================
async def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    async with aiohttp.ClientSession() as session:
        await session.post(f"{BASE_URL}/sendMessage", json=data)

async def forward_photo(chat_id, file_id, caption=""):
    data = {"chat_id": chat_id, "photo": file_id, "caption": caption, "parse_mode": "HTML"}
    async with aiohttp.ClientSession() as session:
        await session.post(f"{BASE_URL}/sendPhoto", json=data)

async def forward_document(chat_id, file_id, caption=""):
    data = {"chat_id": chat_id, "document": file_id, "caption": caption, "parse_mode": "HTML"}
    async with aiohttp.ClientSession() as session:
        await session.post(f"{BASE_URL}/sendDocument", json=data)

# =====================
# MENYULAR
# =====================
def lang_menu():
    return {
        "keyboard": [
            [{"text": "🇺🇿 O'zbekcha"}, {"text": "🇷🇺 Русский"}]
        ],
        "resize_keyboard": True
    }

def main_menu(lang="uz"):
    if lang == "uz":
        return {
            "keyboard": [
                [{"text": "🔍 Raqam qidirish"}, {"text": "🎭 Niqob bo'yicha qidirish"}],
                [{"text": "📋 Kategoriyalar"}, {"text": "🔄 Bazani yangilash"}],
                [{"text": "📝 Buyurtma berish"}, {"text": "📞 Aloqa"}]
            ],
            "resize_keyboard": True
        }
    else:
        return {
            "keyboard": [
                [{"text": "🔍 Поиск номера"}, {"text": "🎭 Поиск по маске"}],
                [{"text": "📋 Категории"}, {"text": "🔄 Обновить базу"}],
                [{"text": "📝 Заказать номер"}, {"text": "📞 Контакты"}]
            ],
            "resize_keyboard": True
        }

def category_menu(lang="uz"):
    if lang == "uz":
        return {
            "keyboard": [
                [{"text": "⚪ Simple — Bepul"}, {"text": "🔵 Steel — 10 000"}],
                [{"text": "🟡 Gold — 250 000"}, {"text": "⚫ Platinum — 500 000"}],
                [{"text": "💜 VIP — 1 000 000"}, {"text": "✨ Lux — 3 000 000"}],
                [{"text": "💎 Lux+ — 5 000 000"}, {"text": "👑 Special — 10M+"}],
                [{"text": "🔙 Orqaga"}]
            ],
            "resize_keyboard": True
        }
    else:
        return {
            "keyboard": [
                [{"text": "⚪ Simple — Бесплатно"}, {"text": "🔵 Steel — 10 000"}],
                [{"text": "🟡 Gold — 250 000"}, {"text": "⚫ Platinum — 500 000"}],
                [{"text": "💜 VIP — 1 000 000"}, {"text": "✨ Lux — 3 000 000"}],
                [{"text": "💎 Lux+ — 5 000 000"}, {"text": "👑 Special — 10M+"}],
                [{"text": "🔙 Назад"}]
            ],
            "resize_keyboard": True
        }

def cancel_kb(lang="uz"):
    btn = "❌ Bekor qilish" if lang == "uz" else "❌ Отмена"
    return {"keyboard": [[{"text": btn}]], "resize_keyboard": True}

# =====================
# HANDLERLAR
# =====================
async def handle_start(chat_id, user_name):
    text = (
        f"👋 Assalomu alaykum / Здравствуйте, <b>{user_name}</b>!\n\n"
        "🌐 Tilni tanlang / Выберите язык:"
    )
    await send_message(chat_id, text, lang_menu())

async def handle_welcome(chat_id, user_name, lang="uz"):
    update_info = ""
    if last_update_time:
        update_info = f"\n🕐 База yangilandi: {last_update_time.strftime('%d.%m.%Y %H:%M')}" if lang == "uz" else f"\n🕐 База обновлена: {last_update_time.strftime('%d.%m.%Y %H:%M')}"

    total = sum(len(v["numbers"]) for v in NUMBERS_DB.values())

    if lang == "uz":
        text = (
            f"━━━━━━━━━━━━━━━━━\n"
            f"🟡 <b>UCELL CHIROYLI RAQAMLAR</b>\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"👋 Xush kelibsiz, <b>{user_name}</b>!\n\n"
            f"📱 Bazada: <b>{total} ta raqam</b> mavjud\n"
            f"{update_info}\n\n"
            f"🔍 Raqam qidiring yoki kategoriyani tanlang 👇"
        )
    else:
        text = (
            f"━━━━━━━━━━━━━━━━━\n"
            f"🟡 <b>UCELL КРАСИВЫЕ НОМЕРА</b>\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"👋 Добро пожаловать, <b>{user_name}</b>!\n\n"
            f"📱 В базе: <b>{total} номеров</b>\n"
            f"{update_info}\n\n"
            f"🔍 Ищите номер или выберите категорию 👇"
        )
    await send_message(chat_id, text, main_menu(lang))

async def handle_category(chat_id, cat_key, lang="uz"):
    cat = NUMBERS_DB[cat_key]
    numbers = cat["numbers"]
    price = cat["price_uz"] if lang == "uz" else cat["price_ru"]

    if not numbers:
        msg = "❌ Hozircha bu toifada raqamlar mavjud emas." if lang == "uz" else "❌ В этой категории пока нет номеров."
        await send_message(chat_id, msg, main_menu(lang))
        return

    nums_text = "\n".join([f"  ✦ <code>{n}</code>" for n in numbers[:20]])
    more = f"\n\n<i>...va yana {len(numbers)-20} ta</i>" if len(numbers) > 20 else ""

    if lang == "uz":
        text = (
            f"━━━━━━━━━━━━━━━━━\n"
            f"{cat['name']} <b>toifasi</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💰 Narxi: <b>{price}</b>\n"
            f"📊 Mavjud: <b>{len(numbers)} ta raqam</b>\n\n"
            f"{nums_text}{more}\n\n"
            f"📝 Raqam yoqdimi? Buyurtma bering!"
        )
    else:
        text = (
            f"━━━━━━━━━━━━━━━━━\n"
            f"{cat['name']} <b>категория</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💰 Цена: <b>{price}</b>\n"
            f"📊 Доступно: <b>{len(numbers)} номеров</b>\n\n"
            f"{nums_text}{more}\n\n"
            f"📝 Понравился номер? Оформите заказ!"
        )
    await send_message(chat_id, text, main_menu(lang))

async def handle_search_results(chat_id, query, lang="uz"):
    results = search_numbers(query, lang)
    if results:
        if lang == "uz":
            text = f"🔍 <b>'{query}' bo'yicha natijalar:</b>\n━━━━━━━━━━━━━━━━━\n\n"
            for r in results[:15]:
                text += f"📱 <code>{r['number']}</code>\n   {r['category']} | 💰 {r['price']}\n\n"
            if len(results) > 15:
                text += f"<i>...va yana {len(results)-15} ta raqam</i>\n\n"
            text += "✅ Yoqgan raqamga <b>📝 Buyurtma berish</b> tugmasini bosing!"
        else:
            text = f"🔍 <b>Результаты по '{query}':</b>\n━━━━━━━━━━━━━━━━━\n\n"
            for r in results[:15]:
                text += f"📱 <code>{r['number']}</code>\n   {r['category']} | 💰 {r['price']}\n\n"
            if len(results) > 15:
                text += f"<i>...и ещё {len(results)-15} номеров</i>\n\n"
            text += "✅ Нравится номер? Нажмите <b>📝 Заказать номер</b>!"
    else:
        if lang == "uz":
            text = (
                f"━━━━━━━━━━━━━━━━━\n"
                f"❌ <b>'{query}'</b> bo'yicha topilmadi\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"😊 Xavotir olmang! Biz kerakli raqamni <b>maxsus buyurtma</b> orqali ham topib beramiz.\n\n"
                f"📝 <b>Buyurtma berish</b> tugmasini bosing!"
            )
        else:
            text = (
                f"━━━━━━━━━━━━━━━━━\n"
                f"❌ По запросу <b>'{query}'</b> ничего не найдено\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"😊 Не переживайте! Мы можем найти нужный номер через <b>специальный заказ</b>.\n\n"
                f"📝 Нажмите <b>Заказать номер</b>!"
            )
    await send_message(chat_id, text, main_menu(lang))

async def handle_mask_info(chat_id, lang="uz"):
    if lang == "uz":
        text = (
            "🎭 <b>Niqob bo'yicha qidirish</b>\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "<b>Qanday ishlatiladi?</b>\n"
            "• <code>*</code> — istalgan raqam o'rniga\n\n"
            "<b>Misollar:</b>\n"
            "• <code>93***0000</code> — oxiri 0000 bo'lgan\n"
            "• <code>**444**</code> — o'rtasida 444 bo'lgan\n"
            "• <code>500**00</code> — boshi 500, oxiri 00\n"
            "• <code>0000</code> — ichida 0000 bo'lgan\n\n"
            "✏️ Niqobingizni yozing:"
        )
    else:
        text = (
            "🎭 <b>Поиск по маске</b>\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "<b>Как использовать?</b>\n"
            "• <code>*</code> — вместо любой цифры\n\n"
            "<b>Примеры:</b>\n"
            "• <code>93***0000</code> — оканчивается на 0000\n"
            "• <code>**444**</code> — содержит 444 в середине\n"
            "• <code>500**00</code> — начало 500, конец 00\n"
            "• <code>0000</code> — содержит 0000\n\n"
            "✏️ Введите вашу маску:"
        )
    user_states[chat_id]["step"] = "mask_search"
    await send_message(chat_id, text, cancel_kb(lang))

async def handle_order_start(chat_id, lang="uz"):
    user_states[chat_id] = {"step": "order_number", "lang": lang}
    if lang == "uz":
        text = (
            "📝 <b>Buyurtma berish</b>\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "1️⃣ Kerakli raqamingizni yozing:\n"
            "<i>(+998 93 123 45 67 yoki qismi: 0000)</i>"
        )
    else:
        text = (
            "📝 <b>Оформить заказ</b>\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "1️⃣ Напишите нужный номер:\n"
            "<i>(+998 93 123 45 67 или часть: 0000)</i>"
        )
    await send_message(chat_id, text, cancel_kb(lang))

async def handle_order_name(chat_id, lang="uz"):
    user_states[chat_id]["step"] = "order_name"
    text = "2️⃣ Ismingizni kiriting:" if lang == "uz" else "2️⃣ Введите ваше имя:"
    await send_message(chat_id, text)

async def handle_order_phone(chat_id, lang="uz"):
    user_states[chat_id]["step"] = "order_phone"
    if lang == "uz":
        text = "3️⃣ Telefon raqamingizni kiriting:"
        btn = "📱 Raqamimni ulashish"
    else:
        text = "3️⃣ Введите ваш номер телефона:"
        btn = "📱 Поделиться номером"
    kb = {
        "keyboard": [[{"text": btn, "request_contact": True}], [{"text": "❌ Bekor qilish" if lang == "uz" else "❌ Отмена"}]],
        "resize_keyboard": True
    }
    await send_message(chat_id, text, kb)

async def handle_order_document(chat_id, lang="uz"):
    user_states[chat_id]["step"] = "order_document"
    if lang == "uz":
        text = (
            "4️⃣ <b>Hujjat rasmini yuboring</b>\n\n"
            "📄 Pasport yoki haydovchilik guvohnomangiz rasmini yuboring\n"
            "<i>(Rasm yoki PDF ko'rinishida)</i>"
        )
    else:
        text = (
            "4️⃣ <b>Отправьте фото документа</b>\n\n"
            "📄 Отправьте фото паспорта или водительского удостоверения\n"
            "<i>(Фото или PDF)</i>"
        )
    await send_message(chat_id, text, cancel_kb(lang))

async def handle_admin_stats(chat_id):
    stats = load_stats()
    total_users = len(stats["users"])
    total_orders = len(stats["orders"])
    total_searches = len(stats["searches"])
    total_starts = stats.get("total_starts", total_users)

    # Bugungi faollik
    today = datetime.now().strftime("%d.%m.%Y")
    today_users = sum(1 for u in stats["users"].values() if u.get("last_seen", "").startswith(today))
    today_orders = sum(1 for o in stats["orders"] if o.get("date", "").startswith(today))
    today_searches = sum(1 for s in stats["searches"] if s.get("date", "").startswith(today))

    # Oxirgi 5 ta buyurtma
    last_orders = stats["orders"][-5:] if stats["orders"] else []
    orders_text = ""
    for o in reversed(last_orders):
        orders_text += f"\n  📦 {o['order_id']} — {o['user_name']} — {o['number']}"

    text = (
        f"📊 <b>BOT STATISTIKASI</b>\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"👥 <b>Foydalanuvchilar:</b>\n"
        f"  • Jami: <b>{total_users}</b> ta\n"
        f"  • Bugun faol: <b>{today_users}</b> ta\n"
        f"  • /start bosganlari: <b>{total_starts}</b>\n\n"
        f"🔍 <b>Qidiruvlar:</b>\n"
        f"  • Jami: <b>{total_searches}</b> ta\n"
        f"  • Bugun: <b>{today_searches}</b> ta\n\n"
        f"📝 <b>Buyurtmalar:</b>\n"
        f"  • Jami: <b>{total_orders}</b> ta\n"
        f"  • Bugun: <b>{today_orders}</b> ta\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        f"<b>Oxirgi buyurtmalar:</b>{orders_text if orders_text else ' —'}\n\n"
        f"📋 /users — foydalanuvchilar ro'yxati"
    )
    await send_message(chat_id, text)

async def handle_admin_users(chat_id):
    stats = load_stats()
    users = stats["users"]
    if not users:
        await send_message(chat_id, "❌ Hali foydalanuvchi yo'q.")
        return

    # Oxirgi 20 ta foydalanuvchi (last_seen bo'yicha)
    sorted_users = sorted(users.items(), key=lambda x: x[1].get("last_seen", ""), reverse=True)[:20]

    text = f"👥 <b>SO'NGGI FOYDALANUVCHILAR</b> (jami: {len(users)})\n━━━━━━━━━━━━━━━━━\n\n"
    for uid, u in sorted_users:
        uname = f"@{u['username']}" if u.get('username') else "—"
        text += (
            f"👤 <b>{u['name']}</b> ({uname})\n"
            f"   🆔 {uid}\n"
            f"   📅 Kirdi: {u.get('first_seen', '—')}\n"
            f"   🕐 Oxirgi: {u.get('last_seen', '—')}\n"
            f"   📊 Harakatlar: {u.get('actions', 0)}\n\n"
        )
    await send_message(chat_id, text)

async def handle_order_complete(chat_id, user_name):
    state = user_states.get(chat_id, {})
    order = state.get("order", {})
    lang = state.get("lang", "uz")
    order_id = f"ORD{datetime.now().strftime('%d%H%M%S')}"

    if lang == "uz":
        text = (
            f"━━━━━━━━━━━━━━━━━\n"
            f"✅ <b>BUYURTMA QABUL QILINDI!</b>\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"🆔 Buyurtma: <b>{order_id}</b>\n"
            f"📱 Raqam: <b>{order.get('number', '-')}</b>\n"
            f"👤 Ism: <b>{order.get('name', '-')}</b>\n"
            f"📞 Telefon: <b>{order.get('phone', '-')}</b>\n\n"
            f"⏰ Tez orada bog'lanamiz!\n"
            f"🕐 Ish vaqti: 09:00 — 18:00"
        )
    else:
        text = (
            f"━━━━━━━━━━━━━━━━━\n"
            f"✅ <b>ЗАКАЗ ПРИНЯТ!</b>\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"🆔 Заказ: <b>{order_id}</b>\n"
            f"📱 Номер: <b>{order.get('number', '-')}</b>\n"
            f"👤 Имя: <b>{order.get('name', '-')}</b>\n"
            f"📞 Телефон: <b>{order.get('phone', '-')}</b>\n\n"
            f"⏰ Свяжемся с вами в ближайшее время!\n"
            f"🕐 Время работы: 09:00 — 18:00"
        )

    admin_text = (
        f"🔔 <b>YANGI BUYURTMA!</b>\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🆔 {order_id}\n"
        f"📱 Raqam: <b>{order.get('number', '-')}</b>\n"
        f"👤 Ism: <b>{order.get('name', '-')}</b>\n"
        f"📞 Tel: <b>{order.get('phone', '-')}</b>\n"
        f"🌐 Til: {'O\'zbekcha' if lang == 'uz' else 'Русский'}\n"
        f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    doc_file_id = order.get("document_file_id")
    doc_type = order.get("document_type", "photo")

    user_states.pop(chat_id, None)
    await send_message(chat_id, text, main_menu(lang))
    await send_message(ADMIN_ID, admin_text)
    track_order(chat_id, user_name, order_id, order.get('number', '-'), order.get('phone', '-'))

    if doc_file_id:
        caption = f"📄 Hujjat — {order_id}\n👤 {order.get('name', '-')}"
        if doc_type == "document":
            await forward_document(ADMIN_ID, doc_file_id, caption)
        else:
            await forward_photo(ADMIN_ID, doc_file_id, caption)

# =====================
# ASOSIY UPDATE
# =====================
async def process_update(update):
    if "message" not in update:
        return

    msg = update["message"]
    chat_id = msg["chat"]["id"]
    user_name = msg["from"].get("first_name", "Foydalanuvchi")
    username = msg["from"].get("username", "")
    state = user_states.get(chat_id, {})
    lang = user_langs.get(chat_id, "uz")

    # Statistika: foydalanuvchini kuzatish
    track_user(chat_id, user_name, username)

    cancel_text = "❌ Bekor qilish" if lang == "uz" else "❌ Отмена"
    back_text = "🔙 Orqaga" if lang == "uz" else "🔙 Назад"

    # Rasm
    if "photo" in msg:
        if state.get("step") == "order_document":
            file_id = msg["photo"][-1]["file_id"]
            if "order" not in user_states[chat_id]:
                user_states[chat_id]["order"] = {}
            user_states[chat_id]["order"]["document_file_id"] = file_id
            user_states[chat_id]["order"]["document_type"] = "photo"
            await handle_order_complete(chat_id, user_name)
        return

    # Fayl/PDF
    if "document" in msg:
        if state.get("step") == "order_document":
            file_id = msg["document"]["file_id"]
            if "order" not in user_states[chat_id]:
                user_states[chat_id]["order"] = {}
            user_states[chat_id]["order"]["document_file_id"] = file_id
            user_states[chat_id]["order"]["document_type"] = "document"
            await handle_order_complete(chat_id, user_name)
        return

    # Contact
    if "contact" in msg:
        phone = msg["contact"]["phone_number"]
        if state.get("step") == "order_phone":
            if "order" not in user_states[chat_id]:
                user_states[chat_id]["order"] = {}
            user_states[chat_id]["order"]["phone"] = phone
            await handle_order_document(chat_id, lang)
        return

    if "text" not in msg:
        return

    text = msg["text"]

    # Til tanlash
    if text == "🇺🇿 O'zbekcha":
        user_langs[chat_id] = "uz"
        await handle_welcome(chat_id, user_name, "uz")
        return
    elif text == "🇷🇺 Русский":
        user_langs[chat_id] = "ru"
        await handle_welcome(chat_id, user_name, "ru")
        return

    # Bekor qilish
    if text in ["❌ Bekor qilish", "❌ Отмена"]:
        user_states.pop(chat_id, None)
        msg_text = "❌ Bekor qilindi." if lang == "uz" else "❌ Отменено."
        await send_message(chat_id, msg_text, main_menu(lang))
        return

    # Buyurtma jarayoni
    if state.get("step") == "order_number":
        if "order" not in user_states[chat_id]:
            user_states[chat_id]["order"] = {}
        user_states[chat_id]["order"]["number"] = text
        await handle_order_name(chat_id, lang)
        return

    elif state.get("step") == "order_name":
        if "order" not in user_states[chat_id]:
            user_states[chat_id]["order"] = {}
        user_states[chat_id]["order"]["name"] = text
        await handle_order_phone(chat_id, lang)
        return

    elif state.get("step") == "order_phone":
        if "order" not in user_states[chat_id]:
            user_states[chat_id]["order"] = {}
        user_states[chat_id]["order"]["phone"] = text
        await handle_order_document(chat_id, lang)
        return

    elif state.get("step") == "order_document":
        msg_text = "📄 Iltimos, rasm yoki PDF fayl yuboring!" if lang == "uz" else "📄 Пожалуйста, отправьте фото или PDF!"
        await send_message(chat_id, msg_text)
        return

    elif state.get("step") == "searching":
        user_states.pop(chat_id, None)
        results = search_numbers(text, lang)
        track_search(chat_id, text, len(results))
        await handle_search_results(chat_id, text, lang)
        return

    elif state.get("step") == "mask_search":
        user_states.pop(chat_id, None)
        results = search_numbers(text, lang)
        track_search(chat_id, text, len(results))
        await handle_search_results(chat_id, text, lang)
        return

    # Start
    if text == "/start":
        await handle_start(chat_id, user_name)
        return

    # Admin statistika
    if text == "/stats" and chat_id == ADMIN_ID:
        await handle_admin_stats(chat_id)
        return

    if text == "/users" and chat_id == ADMIN_ID:
        await handle_admin_users(chat_id)
        return

    # Orqaga
    if text in ["🔙 Orqaga", "🔙 Назад"]:
        await handle_welcome(chat_id, user_name, lang)
        return

    # Qidirish
    if text in ["🔍 Raqam qidirish", "🔍 Поиск номера"]:
        user_states[chat_id] = {"step": "searching", "lang": lang}
        prompt = "🔍 Qidirmoqchi bo'lgan raqamni yozing:\n<i>Masalan: 0000, 444, 93123</i>" if lang == "uz" else "🔍 Введите номер для поиска:\n<i>Например: 0000, 444, 93123</i>"
        await send_message(chat_id, prompt, cancel_kb(lang))
        return

    # Niqob qidirish
    if text in ["🎭 Niqob bo'yicha qidirish", "🎭 Поиск по маске"]:
        user_states[chat_id] = {"step": "mask_search", "lang": lang}
        await handle_mask_info(chat_id, lang)
        return

    # Kategoriyalar
    if text in ["📋 Kategoriyalar", "📋 Категории"]:
        await send_message(chat_id, "📋 Toifani tanlang:" if lang == "uz" else "📋 Выберите категорию:", category_menu(lang))
        return

    # Bazani yangilash
    if text in ["🔄 Bazani yangilash", "🔄 Обновить базу"]:
        msg_text = "⏳ Yangilanmoqda..." if lang == "uz" else "⏳ Обновляется..."
        await send_message(chat_id, msg_text)
        await fetch_numbers_from_site()
        total = sum(len(v["numbers"]) for v in NUMBERS_DB.values())
        done = f"✅ Yangilandi! Jami: {total} ta raqam" if lang == "uz" else f"✅ Обновлено! Всего: {total} номеров"
        await send_message(chat_id, done, main_menu(lang))
        return

    # Buyurtma
    if text in ["📝 Buyurtma berish", "📝 Заказать номер"]:
        await handle_order_start(chat_id, lang)
        return

    # Aloqa
    if text in ["📞 Aloqa", "📞 Контакты"]:
        if lang == "uz":
            contact = (
                "📞 <b>Biz bilan bog'laning:</b>\n"
                "━━━━━━━━━━━━━━━━━\n\n"
                "☎️ +998 93 180 00 00\n"
                "📱 Call Center: 8123\n"
                "🕐 09:00 — 18:00"
            )
        else:
            contact = (
                "📞 <b>Свяжитесь с нами:</b>\n"
                "━━━━━━━━━━━━━━━━━\n\n"
                "☎️ +998 93 180 00 00\n"
                "📱 Call Center: 8123\n"
                "🕐 09:00 — 18:00"
            )
        await send_message(chat_id, contact, main_menu(lang))
        return

    # Kategoriya tugmalari — aniq moslik (Lux+ va Lux aralashmasligi uchun)
    if "Simple" in text:
        await handle_category(chat_id, "simple", lang); return
    if "Steel" in text:
        await handle_category(chat_id, "steel", lang); return
    if "Gold" in text:
        await handle_category(chat_id, "gold", lang); return
    if "Platinum" in text:
        await handle_category(chat_id, "platinum", lang); return
    if "VIP" in text or "Vip" in text:
        await handle_category(chat_id, "vip", lang); return
    if "Lux+" in text or "5 000 000" in text:
        await handle_category(chat_id, "luxplus", lang); return
    if "Lux" in text and "+" not in text:
        await handle_category(chat_id, "lux", lang); return
    if "Special" in text or "10M+" in text:
        await handle_category(chat_id, "special", lang); return

    # Noma'lum
    prompt = "❓ Menyudan tanlang 👇" if lang == "uz" else "❓ Выберите из меню 👇"
    await send_message(chat_id, prompt, main_menu(lang))

# =====================
# ASOSIY LOOP
# =====================
async def main():
    print("🚀 Ucell bot v2.0 ishga tushdi!")
    await fetch_numbers_from_site()

    asyncio.create_task(auto_update_loop())

    offset = 0
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                params = {"timeout": 30, "offset": offset}
                async with session.get(f"{BASE_URL}/getUpdates", params=params) as resp:
                    data = await resp.json()
                if data.get("ok") and data.get("result"):
                    for upd in data["result"]:
                        offset = upd["update_id"] + 1
                        asyncio.create_task(process_update(upd))
            except Exception as e:
                print(f"Xato: {e}")
                await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(main())
