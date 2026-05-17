import asyncio
import aiohttp
import json
import re
from datetime import datetime

TOKEN = "8877423898:AAGh_tsQVdGSL0bX8w-I8_XHijHM74HCq5g"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# Raqamlar - Ucell saytidan
NUMBERS = {
    "simple": {
        "name": "Simple",
        "price": "Bepul",
        "numbers": [
            "+998 50 171 28 54", "+998 50 171 28 62", "+998 50 171 28 64",
            "+998 50 171 28 69", "+998 50 171 28 73", "+998 50 171 28 74",
            "+998 50 171 28 93", "+998 50 171 29 18", "+998 50 171 29 32",
            "+998 50 171 29 34", "+998 50 171 29 35", "+998 50 171 29 36",
            "+998 50 171 29 41", "+998 50 171 29 45", "+998 50 171 29 47",
            "+998 50 171 29 48"
        ]
    },
    "steel": {
        "name": "Steel",
        "price": "10 000 so'm",
        "numbers": [
            "+998 50 729 89 27", "+998 50 752 62 57", "+998 50 756 26 57",
            "+998 50 759 39 57", "+998 50 759 47 59", "+998 50 759 75 93",
            "+998 93 053 83 50", "+998 93 060 67 89", "+998 93 062 06 28",
            "+998 93 124 94 21", "+998 93 134 24 31", "+998 93 135 81 35",
            "+998 93 148 58 41", "+998 93 152 15 23", "+998 93 152 32 51",
            "+998 93 158 41 58"
        ]
    },
    "gold": {
        "name": "Gold",
        "price": "250 000 so'm",
        "numbers": [
            "+998 50 188 68 66", "+998 93 614 03 30", "+998 93 692 00 29",
            "+998 93 785 06 60", "+998 93 819 06 60", "+998 93 835 00 53",
            "+998 93 843 00 66", "+998 93 847 22 20", "+998 93 961 04 40",
            "+998 93 974 03 30", "+998 94 142 06 60", "+998 94 148 06 60",
            "+998 94 237 06 60", "+998 94 265 00 56", "+998 94 267 33 30",
            "+998 94 289 33 30"
        ]
    },
    "platinum": {
        "name": "Platinum",
        "price": "500 000 so'm",
        "numbers": [
            "+998 50 728 00 60", "+998 93 413 00 60", "+998 93 483 00 60",
            "+998 93 532 00 60", "+998 93 641 00 60", "+998 93 758 00 30",
            "+998 93 827 00 40", "+998 93 839 06 00", "+998 93 852 00 30",
            "+998 93 956 00 30", "+998 94 185 00 60", "+998 94 241 00 60",
            "+998 94 289 00 30", "+998 94 427 00 30", "+998 94 431 00 90",
            "+998 94 468 00 60"
        ]
    },
    "vip": {
        "name": "VIP",
        "price": "1 000 000 so'm",
        "numbers": [
            "+998 50 579 60 00", "+998 93 164 00 06", "+998 93 174 60 00",
            "+998 93 176 30 00", "+998 93 179 80 00", "+998 93 268 40 00",
            "+998 93 283 00 06", "+998 93 324 00 06", "+998 93 429 00 06",
            "+998 93 429 00 08", "+998 93 429 80 00", "+998 93 438 00 06",
            "+998 93 539 00 06", "+998 93 548 30 00", "+998 93 549 80 00",
            "+998 93 592 00 06"
        ]
    },
    "lux": {
        "name": "Lux",
        "price": "1 500 000 - 3 000 000 so'm",
        "numbers": [
            "+998 93 341 60 60", "+998 93 689 30 30", "+998 93 849 60 60",
            "+998 93 854 60 60", "+998 94 090 33 00", "+998 94 293 60 60",
            "+998 94 398 60 60", "+998 94 481 60 60", "+998 94 538 60 60",
            "+998 94 728 40 40", "+998 94 731 60 60", "+998 94 752 60 60",
            "+998 94 753 60 60", "+998 94 831 60 60", "+998 94 842 60 60",
            "+998 94 843 60 60"
        ]
    },
    "luxplus": {
        "name": "Lux+",
        "price": "2 500 000 - 5 000 000 so'm",
        "numbers": [
            "+998 50 220 60 60", "+998 50 330 06 06", "+998 50 330 60 60",
            "+998 50 330 80 80", "+998 50 330 90 90", "+998 50 404 90 90",
            "+998 50 440 20 20", "+998 50 500 55 95", "+998 93 060 80 00",
            "+998 93 080 60 60", "+998 93 660 40 40", "+998 93 880 30 30",
            "+998 94 002 60 60", "+998 94 006 80 80", "+998 94 008 30 30",
            "+998 94 009 20 20"
        ]
    },
    "special": {
        "name": "Special / Privilege",
        "price": "10 000 000 - 30 000 000 so'm",
        "numbers": [
            "+998 93 060 06 66", "+998 93 226 66 66", "+998 50 883 33 33"
        ]
    }
}

# Foydalanuvchi holatlari
user_states = {}
orders = {}

async def send_message(chat_id, text, reply_markup=None):
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    
    async with aiohttp.ClientSession() as session:
        await session.post(f"{BASE_URL}/sendMessage", json=data)

def main_menu():
    return {
        "keyboard": [
            [{"text": "🔍 Raqam qidirish"}],
            [{"text": "📋 Kategoriya bo'yicha ko'rish"}],
            [{"text": "📝 Buyurtma berish"}, {"text": "📞 Biz bilan bog'laning"}]
        ],
        "resize_keyboard": True
    }

def category_menu():
    return {
        "keyboard": [
            [{"text": "⚪ Simple (Bepul)"}, {"text": "🔵 Steel (10 000 so'm)"}],
            [{"text": "🟡 Gold (250 000 so'm)"}, {"text": "⚫ Platinum (500 000 so'm)"}],
            [{"text": "💜 VIP (1 000 000 so'm)"}, {"text": "✨ Lux (3 000 000 so'm)"}],
            [{"text": "💎 Lux+ (5 000 000 so'm)"}, {"text": "👑 Special/Privilege"}],
            [{"text": "🔙 Orqaga"}]
        ],
        "resize_keyboard": True
    }

def search_result_in_numbers(query):
    """Barcha raqamlar ichidan qidirish"""
    query_clean = re.sub(r'[^\d]', '', query)
    found = []
    for cat_key, cat_data in NUMBERS.items():
        for number in cat_data["numbers"]:
            num_clean = re.sub(r'[^\d]', '', number)
            if query_clean in num_clean:
                found.append({
                    "number": number,
                    "category": cat_data["name"],
                    "price": cat_data["price"]
                })
    return found

async def handle_start(chat_id, user_name):
    welcome = (
        f"👋 Assalomu alaykum, <b>{user_name}</b>!\n\n"
        "🟡 <b>Ucell Chiroyli Raqamlar Boti</b>ga xush kelibsiz!\n\n"
        "Bu bot orqali siz:\n"
        "✅ Mavjud chiroyli raqamlarni ko'rishingiz\n"
        "🔍 Kerakli raqamni qidirishingiz\n"
        "📝 Raqamga buyurtma berishingiz mumkin\n\n"
        "Quyidagi menyudan tanlang 👇"
    )
    await send_message(chat_id, welcome, main_menu())

async def handle_category(chat_id, cat_key):
    cat = NUMBERS[cat_key]
    numbers_list = "\n".join([f"  • {n}" for n in cat["numbers"]])
    text = (
        f"📱 <b>{cat['name']} toifasi</b>\n"
        f"💰 Narxi: <b>{cat['price']}</b>\n\n"
        f"Mavjud raqamlar:\n{numbers_list}\n\n"
        f"<i>Biror raqamni olmoqchimisiz? 📝 Buyurtma berish tugmasini bosing!</i>"
    )
    await send_message(chat_id, text, main_menu())

async def handle_search(chat_id, query):
    results = search_result_in_numbers(query)
    if results:
        text = f"🔍 <b>'{query}' bo'yicha natijalar:</b>\n\n"
        for r in results[:10]:
            text += f"📱 <b>{r['number']}</b>\n   Toifa: {r['category']} | Narx: {r['price']}\n\n"
        if len(results) > 10:
            text += f"<i>...va yana {len(results)-10} ta raqam topildi</i>\n\n"
        text += "Raqam yoqib qoldimi? <b>📝 Buyurtma berish</b> tugmasini bosing!"
    else:
        text = (
            f"❌ <b>'{query}'</b> bo'yicha raqam topilmadi.\n\n"
            "😊 Lekin xavotir olmang! Biz siz uchun kerakli raqamni <b>maxsus buyurtma</b> orqali ham olishimiz mumkin.\n\n"
            "📝 <b>Buyurtma berish</b> tugmasini bosib, kerakli raqamingizni yozib qoldiring — biz siz bilan bog'lanamiz!"
        )
    await send_message(chat_id, text, main_menu())

async def handle_order_start(chat_id):
    user_states[chat_id] = {"step": "order_number"}
    text = (
        "📝 <b>Buyurtma berish</b>\n\n"
        "Kerakli raqamingizni yozing:\n"
        "<i>(Masalan: +998 93 123 45 67 yoki qismi: 123 45 67)</i>"
    )
    cancel_kb = {
        "keyboard": [[{"text": "❌ Bekor qilish"}]],
        "resize_keyboard": True
    }
    await send_message(chat_id, text, cancel_kb)

async def handle_order_name(chat_id):
    user_states[chat_id]["step"] = "order_name"
    text = "👤 Ismingizni kiriting:"
    await send_message(chat_id, text)

async def handle_order_phone(chat_id):
    user_states[chat_id]["step"] = "order_phone"
    text = "📞 Telefon raqamingizni kiriting (bog'lanish uchun):"
    phone_kb = {
        "keyboard": [[{"text": "📱 Raqamimni ulashish", "request_contact": True}], [{"text": "❌ Bekor qilish"}]],
        "resize_keyboard": True
    }
    await send_message(chat_id, text, phone_kb)

async def handle_order_complete(chat_id, user_name):
    order = user_states[chat_id].get("order", {})
    order_id = f"ORD{datetime.now().strftime('%H%M%S')}"
    
    text = (
        f"✅ <b>Buyurtmangiz qabul qilindi!</b>\n\n"
        f"🆔 Buyurtma raqami: <b>{order_id}</b>\n"
        f"📱 Kerakli raqam: <b>{order.get('number', '-')}</b>\n"
        f"👤 Ism: <b>{order.get('name', '-')}</b>\n"
        f"📞 Telefon: <b>{order.get('phone', '-')}</b>\n\n"
        f"⏰ Tez orada siz bilan bog'lanamiz!\n"
        f"<i>Ish vaqti: 09:00 - 18:00</i>"
    )
    
    user_states.pop(chat_id, None)
    await send_message(chat_id, text, main_menu())

async def process_update(update):
    if "message" not in update:
        return
    
    msg = update["message"]
    chat_id = msg["chat"]["id"]
    user_name = msg["from"].get("first_name", "Foydalanuvchi")
    
    # Contact ulashilgan bo'lsa
    if "contact" in msg:
        phone = msg["contact"]["phone_number"]
        if chat_id in user_states and user_states[chat_id].get("step") == "order_phone":
            if "order" not in user_states[chat_id]:
                user_states[chat_id]["order"] = {}
            user_states[chat_id]["order"]["phone"] = phone
            await handle_order_complete(chat_id, user_name)
        return
    
    if "text" not in msg:
        return
    
    text = msg["text"]
    state = user_states.get(chat_id, {})
    
    # Buyurtma jarayoni
    if state.get("step") == "order_number":
        if text == "❌ Bekor qilish":
            user_states.pop(chat_id, None)
            await send_message(chat_id, "❌ Bekor qilindi.", main_menu())
            return
        if "order" not in user_states[chat_id]:
            user_states[chat_id]["order"] = {}
        user_states[chat_id]["order"]["number"] = text
        await handle_order_name(chat_id)
        return
    
    elif state.get("step") == "order_name":
        if text == "❌ Bekor qilish":
            user_states.pop(chat_id, None)
            await send_message(chat_id, "❌ Bekor qilindi.", main_menu())
            return
        if "order" not in user_states[chat_id]:
            user_states[chat_id]["order"] = {}
        user_states[chat_id]["order"]["name"] = text
        await handle_order_phone(chat_id)
        return
    
    elif state.get("step") == "order_phone":
        if text == "❌ Bekor qilish":
            user_states.pop(chat_id, None)
            await send_message(chat_id, "❌ Bekor qilindi.", main_menu())
            return
        if "order" not in user_states[chat_id]:
            user_states[chat_id]["order"] = {}
        user_states[chat_id]["order"]["phone"] = text
        await handle_order_complete(chat_id, user_name)
        return
    
    elif state.get("step") == "searching":
        user_states.pop(chat_id, None)
        await handle_search(chat_id, text)
        return
    
    # Asosiy menyu
    if text in ["/start", "🔙 Orqaga"]:
        await handle_start(chat_id, user_name)
    
    elif text == "🔍 Raqam qidirish":
        user_states[chat_id] = {"step": "searching"}
        search_kb = {"keyboard": [[{"text": "❌ Bekor qilish"}]], "resize_keyboard": True}
        await send_message(chat_id, "🔍 Qidirmoqchi bo'lgan raqam yoki uning qismini yozing:\n<i>Masalan: 444, 00 00, 93 123</i>", search_kb)
    
    elif text == "📋 Kategoriya bo'yicha ko'rish":
        await send_message(chat_id, "📋 Toifani tanlang:", category_menu())
    
    elif text == "📝 Buyurtma berish":
        await handle_order_start(chat_id)
    
    elif text == "📞 Biz bilan bog'laning":
        contact_text = (
            "📞 <b>Biz bilan bog'laning:</b>\n\n"
            "☎️ Telefon: +998 93 180 00 00\n"
            "🕐 Ish vaqti: 09:00 - 18:00\n"
            "📱 Ucell Call Center: 8123\n\n"
            "Yoki <b>📝 Buyurtma berish</b> orqali so'rov qoldiring!"
        )
        await send_message(chat_id, contact_text, main_menu())
    
    # Kategoriyalar
    elif "Simple" in text:
        await handle_category(chat_id, "simple")
    elif "Steel" in text:
        await handle_category(chat_id, "steel")
    elif "Gold" in text:
        await handle_category(chat_id, "gold")
    elif "Platinum" in text:
        await handle_category(chat_id, "platinum")
    elif "VIP" in text:
        await handle_category(chat_id, "vip")
    elif "Lux+" in text or "Lux+" in text:
        await handle_category(chat_id, "luxplus")
    elif "Lux" in text:
        await handle_category(chat_id, "lux")
    elif "Special" in text or "Privilege" in text:
        await handle_category(chat_id, "special")
    
    else:
        await send_message(chat_id, "❓ Menyudan birini tanlang 👇", main_menu())

async def main():
    print("✅ Ucell bot ishga tushdi!")
    offset = 0
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                params = {"timeout": 30, "offset": offset}
                async with session.get(f"{BASE_URL}/getUpdates", params=params) as resp:
                    data = await resp.json()
                
                if data.get("ok") and data.get("result"):
                    for update in data["result"]:
                        offset = update["update_id"] + 1
                        await process_update(update)
            
            except Exception as e:
                print(f"Xato: {e}")
                await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(main())
