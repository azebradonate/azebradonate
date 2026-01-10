import os
import asyncio
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import json
import aiohttp
import asyncpg
import time
from telegram import LabeledPrice
from telegram.ext import PreCheckoutQueryHandler


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
MY_CARD = os.getenv('MY_CARD')
DATABASE_URL = os.getenv('DATABASE_URL')
PORT = int(os.environ.get("PORT", 8443))


INSTAGRAM_LINK = "https://www.instagram.com/azebramc?igsh=b21vanB1YWNsMGJq&utm_source=qr"
TIKTOK_LINK = "https://www.tiktok.com/@azebramc?_t=ZS-8y3mxvYaFD6&_r=1"
TELEGRAM_BOT_LINK = "https://t.me/GetaiAnswers_bot"

# Referral thresholds (cumulative donated by referred player -> percent awarded to referrer)
REF_THRESHOLDS = [
    (500, 10),
    (450, 9),
    (400, 8),
    (350, 7),
    (300, 6),
    (250, 5),
    (200, 4),
    (150, 3),
    (100, 2),
    (30, 1),
]
MAX_OWNER_BONUS = 10  # global cap for owner's total bonus (sum of percentages from referrals)

# Language data (english, azerbaijani, russian)
LANGUAGES = {
    'en': {
        'donate_title': '💰 Azebra Server Donation',
        'donate_description': 'Support our Azebra server and lets climb to the top together! \n\nYour donations help us maintain and improve the server quality.',
        'donate_balance': '💳 Balance Top-up (Token)',
        'privileges': '👑 Get Privileges',
        'promotions': '🎁 Promotions',
        'amount_question': '💰 How much do you want to donate?\n\n💡 Note: to pay with a card you need to select at least 150 tokens\n\n⚠ Minimum donation: 20 tokens',
        'nickname_question': '👤 Enter your in-game nickname:\n\n⚠ Important: If your nickname has capital letters, write it here exactly the same way.\nNo refunds for incorrect nicknames!',
        'card_question': '💳 Enter your 16-digit card number:\n\n🔒 In case of cancellation, refund will be sent to this card\n✅ 100% refund guaranteed!\n\n 😎 If you want to skip, write from 1 to 8 x 2 times',
        'payment_info': '💳 Payment Information:\n\nSend money to this card: {}\n\nAmount to pay: {} AZN\n\n📸 After payment, send a screenshot of the receipt (not PDF!)',
        'confirm_buttons': 'Choose an action:',
        'send_request': '✅ Send Request',
        'cancel': '❌ Cancel',
        'request_sent': '⏳ Request sent! You will receive a response within 10 min - 1 day.',
        'request_cancelled': '❌ Request cancelled.',
        'admin_notification': '🔔 New donation request:\n\n👤 Nickname: {}\n💰 Amount: {} tokens\n💳 User card: {}\n📸 Receipt:',
        'accept': '✅ Accept',
        'reject': '❌ Reject',
        'reject_with_reason': '📝 Reject with reason',
        'request_accepted': '✅ Your donation request has been accepted! Donation will be added to your account soon.',
        'request_accepted_with_info': '✅ Your donation request has been accepted!\nDonation will be added to your account soon.',
        'request_rejected': '❌ Your donation request has been rejected. Please contact support for more information.',
        'request_rejected_with_reason': '❌ Your donation request has been rejected.\n\nReason: {}',
        'admin_enter_reason': 'Please enter the reason for rejection:',
        'lang_changed': '🌍 Language changed to English',
        'coming_soon': '🚧 Coming soon...',
        'no_promotions': '🎁 No promotions available yet',
        'invalid_amount': '❌ Please enter a valid number (minimum 20 tokens)',
        'invalid_card': '❌ Please enter a valid 16-digit card number',
        'invalid_photo': '❌ Please send a photo of the receipt',
        'bot_alive': '🤖 Bot is alive!',
        'subscribe_required': '📢 Before proceeding, please subscribe to our social media:\n\n📱 Instagram: {}\n🎵 TikTok: {}\n🤖 Telegram Bot: {}\n\nAfter subscribing, click Continue.',
        'continue_btn': '✅ Continue',
        'command_generated': '🎮 Command for console:\n\n`points give {} {}`\n\nClick the message to copy!',
        'subscription_check': '✅ Thank you for subscribing! You can now proceed.',
        'profile_title': '📋 Your profile',
        'profile_link': '🔗 Your invite link: {}',
        'profile_invited': '👥 Invited: {}',
        'profile_bonus': '🏷 Bonus percent: {}%',
        'profile_list_header': '🧾 Invited players and their contribution:',
        'profile_no_invited': 'You have not invited anyone yet.',
        'profile_hint': 'ℹ To get a donation bonus, invite players!\n➡ The invited player must purchase a donation of at least\n      30 tokens for a 1%, 100 tokens for 2%,\n      150 tokens for 3%, 200 tokens for 4%,\n      250 tokens for 5%, 300 tokens for 6%,\n      350 tokens for 7%, 400 tokens for 8%,\n      450 tokens for 9%, and 500 tokens for 10%.\n\n➡ The invited player\'s donations are cumulative,\n      they don\'t need to donate the full amount at once.\n\n➡ Example: If you have a 10% donation bonus, the next time\n      you buy a donation, you will receive 10% more.',
        'choose_saved_nick': 'You have a saved nickname: `{}`. Choose:',
        'use_saved_nick': '🗁 Use saved nickname',
        'enter_other_nick': '✏️ Enter another nickname (no bonus)',
        'nickname_saved': '✅ Your nickname `{}` has been saved and will be shown in your profile.',
        'reset_btn': 'Reset data',
        'reset_warning': '⚠️ This will delete your saved nickname, bonuses and donation history.',
        'reset_confirm_prompt': 'To confirm data deletion type: resetallthedata',
        'nickname_label': '\n👤 Nickname',
        'stars_payment': '⭐ Pay with Telegram Stars',
        'stars_invoice_title': 'Azebra Server Donation',
        'stars_invoice_description': 'Donation for {} tokens',
        'payment_timeout': '⏰ Payment canceled due to timeout (5 minutes)',
        'payment_success': '✅ Payment successful! Your donation will be processed shortly.',
        'card12': '💳 Card Payment (takes longer)',
        'cancel_payment': '❌ Cancel payment',
        'active_payment_block': '⚠️ You have an active payment. Cancel it before using /donate.',
        'payment_confirm': '⚠️ After this step, returning will take a long time.\nYou must pay the invoice to continue.\nIf you agree, type: ihavetopay',
        'payment_confirm_success': '✅ Confirmation accepted. Proceeding to payment.',
        'payment_confirm_fail': '❌ Incorrect input. Please type exactly: ihavetopay',

        'reset_success': '✅ Your data has been reset.'
    },
    'az': {
        'donate_title': '💰 Azebra Server Bağışlaması',
        'donate_description': 'Azebra serverimizi dəstəkləyin və gəlin birlikdə zirvəyə qalxaq! \n\nBağışlamanız serverin keyfiyyətini qorumaq və təkmilləşdirmək üçün bizə kömək edir.',
        'donate_balance': '💳 Balans artırma (token)',
        'privileges': '👑 Priviligiyalar',
        'promotions': '🎁 Aksiyalar',
        'amount_question': '💰 Nə qədər donasiya etmək istəyirsiniz?\n\n💡 Qeyd: kartla ödəmək üçün ən azı 150 token seçmək lazımdır\n\n⚠ Minimum ba bağışlama: 20 token',
        'nickname_question': '👤 Oyun nikneymi daxil edin:\n\n⚠ Vacib: Əgər nikneyminizdə böyük hərflər varsa, burada da eyni şəkildə yazın.\nSəhv nikneym üçün geri qaytarma yoxdur!',
        'card_question': '💳 16 rəqəmli kart nömrənizi daxil edin:\n\n🔒 Ləğv halında, geri qaytarma bu karta göndəriləcək\n✅ 100% geri qaytarma təmin edilir!\n\n 😎 Əgər oliqarxsınızsa, 2 dəfə x 8-ə qədər yazın.',
        'payment_info': '💳 Ödəniş məlumatları:\n\nBu karta ödənişi göndərin: {}\n\nÖdəniləcək məbləğ: {} AZN\n\n📸 Ödənişdən sonra qəbzi ekran görüntüsü kimi göndərin (PDF qəbul edilmir!)',
        'confirm_buttons': 'Əməliyyat seçin:',
        'send_request': '✅ Sorğu göndər',
        'cancel': '❌ Ləğv et',
        'request_sent': '⏳ Sorğu göndərildi! 10 dəq - 1 gün ərzində cavab alacaqsınız.',
        'request_cancelled': '❌ Sorğu ləğv edildi.',
        'admin_notification': '🔔 Yeni bağışlama sorğusu:\n\n👤 Nikneym: {}\n💰 Məbləğ: {} token\n💳 İstifadəçi kartı: {}\n📸 Çek:',
        'accept': '✅ Qəbul et',
        'reject': '❌ Rədd et',
        'reject_with_reason': '📝 Səbəblə rədd et',
        'request_accepted': '✅ Bağışlama sorğunuz qəbul edildi! Bağışlama tezliklə hesabınıza əlavə olunacaq.',
        'request_accepted_with_info': '✅ Bağışlama sorğunuz qəbul edildi!\nBağışlama tezliklə hesabınıza əlavə olunacaq.',
        'request_rejected': '❌ Bağışlama sorğunuz rədd edildi. Əlavə məlumat üçün dəstək ilə əlaqə saxlayın.',
        'request_rejected_with_reason': '❌ Bağışlama sorğunuz rədd edildi.\n\nSəbəb: {}',
        'admin_enter_reason': 'Rədd etmək səbəbini daxil edin:',
        'lang_changed': '🌐 Dil Azərbaycan dilinə dəyişdirildi',
        'coming_soon': '🚧 Tezliklə...',
        'no_promotions': '🎁 Hələ heç bir aksiya yoxdur',
        'invalid_amount': '❌ Zəhmət olmasa düzgün rəqəm daxil edin (minimum 20 token)',
        'invalid_card': '❌ Zəhmət olmasa 16 rəqəmli kart nömrəsi daxil edin',
        'invalid_photo': '❌ Zəhmət olmasa qəbzin şəklini göndərin',
        'bot_alive': '🤖 Bot işləyir!',
        'subscribe_required': '📢 Davam etməzdən əvvəl sosial mediaya abunə olun:\n\n📱 Instagram: {}\n🎵 TikTok: {}\n🤖 Telegram Bot: {}\n\nAbunə olduqdan sonra Davam et düyməsinə basın.',
        'continue_btn': '✅ Davam et',
        'command_generated': '🎮 Konsol əmri:\n\n`points give {} {}`\n\nKopyalamaq üçün mesaja basın!',
        'subscription_check': '✅ Abunə olduğunuz üçün təşəkkürlər! İndi davam edə bilərsiniz.',
        'profile_title': '📋 Profiliniz',
        'profile_link': '🔗 Dəvət linki: {}',
        'profile_invited': '👥 Dəvət edilmiş: {}',
        'profile_bonus': '🏷 Bonus faizi: {}%',
        'profile_list_header': '🧾 Dəvət edilmiş oyunçular və onların töhfəsi:',
        'profile_no_invited': 'Hələ heç kimi dəvət etməmisiniz.',
        'profile_hint': 'ℹ Bağışlama bonusu qazanmaq üçün oyunçuları dəvət et!\n➡ Dəvət etdiyin oyunçu ən azı\n      30 token - 1%, 100 token - 2%,\n      150 token - 3%, 200 token - 4%,\n      250 token - 5%, 300 token - 6%,\n      350 token - 7%, 400 token - 8%,\n      450 token - 9% və 500 token - 10%.\n\n➡ Dəvət etdiyin oyunçunun bağışlamaları toplanır,\n      bonus üçün məbləği bir dəfəlik ödəmək vacib deyil.\n\n➡ Misal: Əgər sənin donat bonusun 10%-dirsə, növbəti dəfə\n      donat alanda 10% artıq alacaqsan.',
        'choose_saved_nick': 'Saxlanmış oyunçu adı var: `{}`. Seçin:',
        'use_saved_nick': '🗁 Saxlanmış oyunçu adını istifadə et',
        'enter_other_nick': '✏️ Başqa oyunçu adı daxil et (bonus yoxdur)',
        'nickname_saved': '✅ Oyunçu adı `{}` saxlanıldı və profilinizdə görünəcək.',
        'reset_btn': 'Məlumatları sıfırla',
        'reset_warning': '⚠️ Bu, saxlanmış oyunçu adını, bonusları və donat tarixçəsini siləcək.',
        'reset_confirm_prompt': 'Məlumatların silinməsini təsdiqləmək üçün yazın: resetallthedata',
        'nickname_label': '\n👤 Oyunçu adı',
        'stars_payment': '⭐ Telegram Ulduzu ilə ödə',
        'stars_invoice_title': 'Azebra Server Bağışlamaı',
        'stars_invoice_description': '{} token bağışlama',
        'payment_timeout': '⏰ Ödəniş vaxtı bitdi (5 dəqiqə)',
        'payment_success': '✅ Ödəniş uğurlu! Bağışlama tezliklə işlənəcək.',
        'card12': '💳 Kartla ödəniş (uzun çəkir) ',
        'cancel_payment': '❌ Ödənişi ləğv et',
        'active_payment_block': '⚠️ Aktiv ödənişiniz var. /donate istifadə etməzdən əvvəl onu ləğv edin.',
        'payment_confirm': '⚠️ Bu addımdan sonra geri qayıtmaq çox vaxt aparacaq.\nDavam etmək üçün ödənişi etməlisiniz.\nƏgər razısınızsa, yazın: ihavetopay',
        'payment_confirm_success': '✅ Təsdiq qəbul edildi. Ödəniş mərhələsinə keçirik.',
        'payment_confirm_fail': '❌ Yanlış yazdınız. Zəhmət olmasa dəqiq yazın: ihavetopay',
        'reset_success': '✅ Məlumatlarınız sıfırlandı.'
    },
    'ru': {
        'donate_title': '💰 Донат на сервер Azebra',
        'donate_description': 'Поддержите наш Azebra сервер и давайте вместе поднимемся на вершину! \n\nВаши донаты помогают поддерживать и улучшать качество сервера.',
        'donate_balance': '💳 Пополнение баланса (токен)',
        'privileges': '👑 Привилегии',
        'promotions': '🎁 Акции',
        'amount_question': '💰 Сколько вы хотите задонатить?\n\n💡 Примечание: для оплаты с картой вам нужно выбрать минимум 150 токенов\n\n⚠ Минимальный донат: 20 токенов',
        'nickname_question': '👤 Введите ваш игровой ник:\n\n⚠ Важно: если в нике есть заглавные буквы, напишите их так же.\nВозврат средств за неверный ник не предусмотрен!',
        'card_question': '💳 Введите номер вашей карты (16 цифр):\n\n🔒 В случае отмены, возврат будет отправлен на эту карту\n✅ 100% гарантия возврата!\n\n 😎 Если хотите пропустить, напишите от 1 до 8 дважды',
        'payment_info': '💳 Информация об оплате:\n\nОтправьте деньги на эту карту: {}\n\nК оплате: {} AZN\n\n📸 После оплаты отправьте скриншот чека (не PDF!)',
        'confirm_buttons': 'Выберите действие:',
        'send_request': '✅ Отправить запрос',
        'cancel': '❌ Отменить',
        'request_sent': '⏳ Запрос отправлен! Вы получите ответ в течение 10 мин - 1 дня.',
        'request_cancelled': '❌ Запрос отменён.',
        'admin_notification': '🔔 Новый запрос на донат:\n\n👤 Ник: {}\n💰 Сумма: {} токенов\n💳 Карта пользователя: {}\n📸 Чек:',
        'accept': '✅ Принять',
        'reject': '❌ Отклонить',
        'reject_with_reason': '📝 Отклонить с причиной',
        'request_accepted': '✅ Ваша заявка на донат принята! Донат будет скоро добавлен на ваш счёт.',
        'request_accepted_with_info': '✅ Ваша заявка на донат принята!\nДонат будет скоро добавлен на ваш счёт.',
        'request_rejected': '❌ Ваша заявка на донат отклонена. Свяжитесь с поддержкой для деталей.',
        'request_rejected_with_reason': '❌ Ваша заявка на донат отклонена.\n\nПричина: {}',
        'admin_enter_reason': 'Пожалуйста, введите причину отклонения:',
        'lang_changed': '🌐 Язык сменён на русский',
        'coming_soon': '🚧 Скоро...',
        'no_promotions': '🎁 Пока нет акций',
        'invalid_amount': '❌ Пожалуйста, введите корректное число (минимум 20 токенов)',
        'invalid_card': '❌ Пожалуйста, введите корректный 16-значный номер карты',
        'invalid_photo': '❌ Пожалуйста, отправьте фотографию чека',
        'bot_alive': '🤖 Бот жив!',
        'subscribe_required': '📢 Перед продолжением подпишитесь на наши соцсети:\n\n📱 Instagram: {}\n🎵 TikTok: {}\n🤖 Telegram Bot: {}\n\nПосле подписки нажмите Продолжить.',
        'continue_btn': '✅ Продолжить',
        'command_generated': '🎮 Команда для консоли:\n\n`points give {} {}`\n\nНажмите сообщение, чтобы скопировать!',
        'subscription_check': '✅ Спасибо за подписку! Теперь можно продолжить.',
        'profile_title': '📋 Ваш профиль',
        'profile_link': '🔗 Ваша реферальная ссылка: {}',
        'profile_invited': '👥 Приглашено: {}',
        'profile_bonus': '🏷 Процент бонуса: {}%',
        'profile_list_header': '🧾 Приглашённые игроки и их вклад:',
        'profile_no_invited': 'Вы ещё никого не пригласили.',
        'profile_hint': 'ℹ Чтобы получить бонус на донат, приглашайте игроков!\n➡ Приглашённый игрок должен купить донат минимум\n      30 токенов — 1%, 100 токенов — 2%,\n      150 токенов — 3%, 200 токенов — 4%,\n      250 токенов — 5%, 300 токенов — 6%,\n      350 токенов — 7%, 400 токенов — 8%,\n      450 токенов — 9% и 500 токенов — 10%.\n\n➡ Донаты приглашённых суммируются.',
        'choose_saved_nick': 'У вас сохранён ник: `{}`. Выберите:',
        'use_saved_nick': '🗁 Использовать сохранённый ник',
        'enter_other_nick': '✏️ Ввести другой ник (без бонуса)',
        'nickname_saved': '✅ Ваш ник `{}` был сохранён и будет отображаться в профиле.',
        'reset_btn': 'Сбросить данные',
        'reset_warning': '⚠️ Это удалит ваш сохранённый ник, бонусы и историю донатов.',
        'reset_confirm_prompt': 'Чтобы подтвердить удаление данных, напишите: resetallthedata',
        'nickname_label': '\n👤 Игровое имя',
        'stars_payment': '⭐ Оплатить звездами Telegram',
        'stars_invoice_title': 'Донат на сервер Azebra',
        'stars_invoice_description': 'Донат на {} токенов',
        'payment_timeout': '⏰ Оплата отменена из-за истечения времени (5 минут)',
        'payment_success': '✅ Оплата успешна! Ваш донат скоро будет обработан.',
        'card12': '💳 Оплата картой (долгое ожидание)',
        'cancel_payment': '❌ Отменить оплату',
        'active_payment_block': '⚠️ У вас есть активная оплата. Сначала отмените её перед использованием /donate.',
        'payment_confirm': '⚠️ После этого шага вернуться займет много времени.\nЧтобы продолжить, нужно оплатить счёт.\nЕсли вы согласны, напишите: ihavetopay',
        'payment_confirm_success': '✅ Подтверждение принято. Переходим к оплате.',
        'payment_confirm_fail': '❌ Неверный ввод. Напишите точно: ihavetopay',

        'reset_success': '✅ Ваши данные успешно сброшены.'
    }
}

# In-memory user session (keeps compatibility with original code flow)
user_data = {}
user_languages = {}
admin_rejection_data = {}

#Utility helpers for language
def get_text(user_id, key):
    lang = user_languages.get(user_id, 'en')
    return LANGUAGES.get(lang, LANGUAGES['en'])[key]

#Database helpers
async def init_db_pool():
    if not DATABASE_URL:
        logger.warning('DATABASE_URL not set. Skipping DB initialization. Referral features will not persist.')
        return None
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as conn:
        # Create tables if they don't exist
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY,
                language TEXT DEFAULT 'en',
                referrer_id BIGINT,
                created_at TIMESTAMP DEFAULT now()
            );
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS donations (
                id bigserial PRIMARY KEY,
                user_id BIGINT NOT NULL,
                amount numeric NOT NULL,
                accepted boolean DEFAULT false,
                created_at TIMESTAMP DEFAULT now()
            );
        ''')
        # Add new columns if missing (safe to run)
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS game_nick TEXT;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS bonus_active BOOLEAN DEFAULT TRUE;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS locked BOOLEAN DEFAULT FALSE;")


        # Counters table for admin numbering (stars and card)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS counters (
                type TEXT PRIMARY KEY,
                value INT NOT NULL DEFAULT 0
            );
        ''')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS pending_requests (
                user_id BIGINT PRIMARY KEY,
                nickname TEXT,
                amount NUMERIC,
                pay_type TEXT,       -- 'card' или 'stars'
                receipt TEXT,        -- file_id квитанции (для card)
                created_at TIMESTAMP DEFAULT now()
            );
        ''')
        
        await conn.execute("INSERT INTO counters (type, value) VALUES ('stars', 0) ON CONFLICT (type) DO NOTHING;")
        await conn.execute("INSERT INTO counters (type, value) VALUES ('card', 0) ON CONFLICT (type) DO NOTHING;")


    return pool

async def ensure_user(pool, user_id, language='en', referrer_id=None):
    if not pool:
        return
    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO users (id, language, referrer_id)
            VALUES ($1, $2, $3)
            ON CONFLICT (id) DO UPDATE SET language=EXCLUDED.language
        ''', user_id, language, referrer_id)

async def set_referrer_if_missing(pool, user_id, referrer_id):
    if not pool:
        return
    async with pool.acquire() as conn:
        # only set if user exists without referrer
        await conn.execute('''
            UPDATE users SET referrer_id = $2 WHERE id = $1 AND (referrer_id IS NULL OR referrer_id = 0)
        ''', user_id, referrer_id)

async def add_donation_record(pool, user_id, amount, accepted=False):
    if not pool:
        return
    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO donations (user_id, amount, accepted) VALUES ($1, $2, $3)
        ''', user_id, amount, accepted)

async def get_total_accepted_by_user(pool, user_id):
    if not pool:
        return 0
    async with pool.acquire() as conn:
        row = await conn.fetchval('SELECT COALESCE(SUM(amount),0) FROM donations WHERE user_id=$1 AND accepted=true', user_id)
        return float(row)

async def get_invited_list(pool, referrer_id):
    if not pool:
        return []
    async with pool.acquire() as conn:
        rows = await conn.fetch('SELECT id, referrer_id FROM users WHERE referrer_id=$1', referrer_id)
        return [r['id'] for r in rows]

# New DB helpers for nickname & reset
async def set_game_nick(pool, user_id, nick):
    if not pool:
        return
    async with pool.acquire() as conn:
        await conn.execute('UPDATE users SET game_nick=$2, bonus_active=true WHERE id=$1', user_id, nick)

async def get_game_nick(pool, user_id):
    if not pool:
        return None
    async with pool.acquire() as conn:
        row = await conn.fetchrow('SELECT game_nick FROM users WHERE id=$1', user_id)
        return row['game_nick'] if row else None

async def reset_user_data(pool, user_id):
    if not pool:
        return
    async with pool.acquire() as conn:
        # reset
        await conn.execute('UPDATE users SET game_nick=NULL, bonus_active=false, referrer_id=NULL WHERE id=$1', user_id)
        await conn.execute('DELETE FROM donations WHERE user_id=$1', user_id)

        await conn.execute('UPDATE users SET referrer_id=NULL WHERE referrer_id=$1', user_id)

async def add_pending_request(pool, user_id, nickname, amount, pay_type, receipt=None):
    if not pool:
        return
    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO pending_requests (user_id, nickname, amount, pay_type, receipt)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (user_id) DO UPDATE 
            SET nickname=$2, amount=$3, pay_type=$4, receipt=$5, created_at=now()
        ''', user_id, nickname, amount, pay_type, receipt)

async def remove_pending_request(pool, user_id):
    if not pool:
        return
    async with pool.acquire() as conn:
        await conn.execute('DELETE FROM pending_requests WHERE user_id=$1', user_id)

# calculate percent for a single referred user's cumulative donations
def percent_for_cumulative(amount):
    pct = 0
    for threshold, p in REF_THRESHOLDS:
        if amount >= threshold:
            pct = max(pct, p)
    return pct

async def unlock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Only admin can use this command.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /unlock <user_id>")
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user_id.")
        return

    if target_id in user_data:
        user_data[target_id]['locked'] = False
    pool = context.bot_data.get('db_pool')
    if pool:
        async with pool.acquire() as conn:
            await conn.execute("UPDATE users SET locked=FALSE WHERE id=$1", target_id)
    await update.message.reply_text(f"✅ User {target_id} is now unlocked for /donate")
    await remove_pending_request(pool, target_id)


# sum up owner's total bonus (sum of percent_for_cumulative for each invited user), cap to MAX_OWNER_BONUS
async def compute_owner_bonus(pool, owner_id):
    invited = await get_invited_list(pool, owner_id)
    total = 0
    for uid in invited:
        cum = await get_total_accepted_by_user(pool, uid)
        total += percent_for_cumulative(cum)
    return total 

async def get_next_counter(pool, counter_type: str) -> int:
    """Atomically increment and return next counter value between 1 and 100 (wraps to 1 after 100)."""
    if not pool:
        return 1
    async with pool.acquire() as conn:
        # Atomically increment (wrap to 1 after reaching 100) and return new value
        row = await conn.fetchrow("""
            UPDATE counters
            SET value = CASE WHEN value >= 100 THEN 1 ELSE value + 1 END
            WHERE type = $1
            RETURNING value
        """, counter_type)
        if row and row.get('value') is not None:
            return int(row['value'])
        else:
            # If row doesn't exist for some reason, create it and return 1
            await conn.execute("INSERT INTO counters (type, value) VALUES ($1, 1) ON CONFLICT (type) DO UPDATE SET value = 1", counter_type)
            return 1

#Bot handlers 

LANGUAGES['en'].update({
    #'rules_text': '📜 Rules: Follow server guidelines and respect others. (Sample text)',
    'need_rules': '⚠️ To purchase a donation you must first accept the bot rules\nUse /rules (click to view).',
    'accept_rules_btn': '✅ Accept Rules',
    'rules_accepted': '✅ You have accepted the rules. Now you can use /donate.',
    'rules_reset': '♻️ Rules acceptance has been reset for all users.'
})
LANGUAGES['az'].update({
    #'rules_text': '📜 Qaydalar: Server qaydalarına əməl edin və başqalarına hörmət edin. (Nümunə mətn)',
    'need_rules': '⚠️ Bağışlama etmək üçün əvvəlcə botun qaydalarını qəbul etməlisiniz\n/rules istifadə edin (baxmaq üçün klikləyin).',
    'accept_rules_btn': '✅ Qaydaları qəbul et',
    'rules_accepted': '✅ Siz qaydaları qəbul etdiniz. İndi /donate istifadə edə bilərsiniz.',
    'rules_reset': '♻️ Bütün istifadəçilər üçün qaydaların qəbulu sıfırlandı.'
})
LANGUAGES['ru'].update({
    #'rules_text': '📜 Правила: Соблюдайте правила сервера и уважайте других. (Пример текста)',
    'need_rules': '⚠️ Для покупки доната нужно принять правила бота\nИспользуйте /rules (нажмите для просмотра).',
    'accept_rules_btn': '✅ Принять правила',
    'rules_accepted': '✅ Вы приняли правила. Теперь вы можете использовать /donate.',
    'rules_reset': '♻️ Принятие правил сброшено для всех пользователей.'
})

# DB modification
async def init_db_pool_with_rules():
    pool = await init_db_pool()
    if pool:
        async with pool.acquire() as conn:
            await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS rules_accepted BOOLEAN DEFAULT FALSE;")
    return pool

#/rules 
async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет пользователю обновленные правила сервера AZEBRA Minecraft."""
    
    
    rules_text = """
*1. Ümumi Şərtlər*

1.1. Bağışlama xidməti yalnız AZEBRA Minecraft serverində təqdim olunan əlavə imkanların əldə edilməsi üçün nəzərdə tutulub.
1.2. Bağışlama xidməti tamamilə könüllü əsasda həyata keçirilir. Heç bir şəxs Sizi ödəniş etməyə məcbur etmir.

---

*2. İstifadəçi Öhdəlikləri*

2.1. Siz bu qaydarı qəbul etdikdən sonra bu qaydalarla tam razılaşmış hesab edilirsiniz və onların icrasına görə məsuliyyət daşıyırsınız.
2.2. Siz ödəniş zamanı daxil etdiyiniz bütün məlumatların (o cümlədən Minecraft oyunundaki oyunçu adı) düzgünlüyünə tam məsuliyyət daşıyırsınız.
2.3. Əgər oyunçu adı və ya digər məlumatlar səhv daxil edilərsə, ödəniş geri qaytarılmır.

---

*3. Geri Qaytarılma Şərtləri*

3.1. Bağışlama ödənişləri ümumiyyətlə geri qaytarılmır.
3.2. İstisna hallarda geri qaytarılma yalnız aşağıdakı şərtlərlə mümkündür:
    •	Əgər ödəniş sistem tərəfindən avtomatik rədd edilibsə və bu hal rəsmi dəstək tərəfindən təsdiqlənibsə;
    •	Əgər texniki nasazlıq səbəbindən ödəniş düzgün icra edilməyibsə və bu dəstək xidməti tərəfindən təsdiqlənibsə.
3.3. Geri qaytarılma yalnız AZEBRA Telegram bot daxilində təqdim edilən rəsmi dəstək linki vasitəsilə həyata keçirilir. Siz yalnız bu dəstək xidməti ilə əlaqə saxlayaraq geri qaytarılma prosesini başlada bilərsiniz. Başqa üsullarla geri qaytarılma qətiyyən mümkün deyil.

---

*4. Hüquqi Qeyd*

4.1. Siz bu qaydarı qəbul etməklə təsdiq edirsiniz ki, ödəniş tamamilə öz könüllü qərarınızdır və üçüncü şəxslər tərəfindən aldatma və ya məcbur etmə halı olmayıb.

---

*5. Qaydaların Dəyişdirilməsi*

5.1. Bu qaydalar dəyişdirilə bilər, lakin yeni qaydalar yalnız Sizin razılığınızla qüvvəyə minəcək.
5.2. Siz yeni qaydaları qəbul edib-etməməkdə sərbəstsiniz. Qəbul edilmədiyi halda yeni ödənişlər və bağışlama xidmətləri təqdim olunmayacaq.
    """
    
    
    await update.message.reply_text(rules_text, parse_mode='Markdown')

#/donate 
async def donate_command_with_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    pool = context.bot_data.get('db_pool')
    if pool:
        async with pool.acquire() as conn:
            locked = await conn.fetchval("SELECT locked FROM users WHERE id=$1", user_id)
            if locked:
                await update.message.reply_text(get_text(user_id, 'active_payment_block'))
                return
    if pool:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT rules_accepted FROM users WHERE id=$1", user_id)
            if not row or not row['rules_accepted']:
                keyboard = [[InlineKeyboardButton(get_text(user_id, 'accept_rules_btn'), callback_data="accept_rules")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(get_text(user_id, 'need_rules'), reply_markup=reply_markup)
                return
   
    await donate_command(update, context)

#Callback buttons
async def rules_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    pool = context.bot_data.get('db_pool')
    if pool:
        async with pool.acquire() as conn:
            await conn.execute("UPDATE users SET rules_accepted=TRUE WHERE id=$1", user_id)
    await query.edit_message_text(get_text(user_id, 'rules_accepted'))

# /crules 
async def crules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Only admin can use this command.")
        return
    pool = context.bot_data.get('db_pool')
    if pool:
        async with pool.acquire() as conn:
            await conn.execute("UPDATE users SET rules_accepted=FALSE;")
    await update.message.reply_text(get_text(user_id, 'rules_reset'))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # detect start payload for referral: expecting payload like 'ref<referrer_id>' or just 'referrer:<id>'
    args = context.args
    referrer_id = None
    if args:
        payload = args[0]
        if payload.startswith('ref'):
            try:
                referrer_id = int(payload[3:])
                if referrer_id == user_id:
                    referrer_id = None
            except Exception:
                referrer_id = None

    # store language default and ensure DB user
    if user_id not in user_languages:
        user_languages[user_id] = 'en'

    if context.bot_data.get('db_pool'):
        await ensure_user(context.bot_data['db_pool'], user_id, user_languages[user_id], referrer_id)
        if referrer_id:
            await set_referrer_if_missing(context.bot_data['db_pool'], user_id, referrer_id)

    caption_text = (
        f"🎮 Welcome to Azebra Donate Bot! 🎮\n\n"
        f"🔥Use /donate to support our server🔥\n"
        f"🔥Use /lang to change language🔥\n"
        f"🔥Use /profile to check your profile🔥\n\n"
        f"Language: {user_languages[user_id].upper()}"
    )

    await update.message.reply_photo(
        photo="https://raw.githubusercontent.com/azebradonate/FUN1/refs/heads/main/%D0%98%D0%B7%D0%BE%D0%B1%D1%80%D0%B0%D0%B6%D0%B5%D0%BD%D0%B8%D0%B5%20WhatsApp%202025-10-06%20%D0%B2%2001.58.24_79bfaee9.jpg",
        caption=caption_text
    )

async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en")],
        [InlineKeyboardButton("🇦🇿 Azərbaycan", callback_data="set_lang_az")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🌍 Choose your language / Dilinizi seçin / Выберите язык:",
        reply_markup=reply_markup
    )


async def donate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data and user_data[user_id].get('locked'):
        await update.message.reply_text(get_text(user_id, 'active_payment_block'))
        return
    keyboard = [
        [InlineKeyboardButton(get_text(user_id, 'donate_balance'), callback_data='balance_topup')],
        [InlineKeyboardButton(get_text(user_id, 'privileges'), callback_data='privileges')],
        [InlineKeyboardButton(get_text(user_id, 'promotions'), callback_data='promotions')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"{get_text(user_id, 'donate_title')}\n\n"
        f"{get_text(user_id, 'donate_description')}",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    pool = context.bot_data.get('db_pool')
    saved_nick = None
    if pool:
        # ensure user exists in DB
        await ensure_user(pool, user_id, user_languages.get(user_id, 'en'))
        invited = await get_invited_list(pool, user_id)
        invited_count = len(invited)
        bonus = await compute_owner_bonus(pool, user_id)
        invite_link = f"https://t.me/{(await context.bot.get_me()).username}?start=ref{user_id}"
        saved_nick = await get_game_nick(pool, user_id)
        # build message
        lines = [get_text(user_id, 'profile_title'), '', f"ID: {user_id}", get_text(user_id, 'profile_link').format(invite_link), get_text(user_id, 'profile_invited').format(invited_count), get_text(user_id, 'profile_bonus').format(bonus)]
        # show nickname in 3 languages explicitly
        nick_label = get_text(user_id, 'nickname_label')
        lines.append(f"{nick_label}: {saved_nick if saved_nick else '—'}")

        if invited_count:
            lines.append('\n' + get_text(user_id, 'profile_list_header'))
            for uid in invited:
                cum = await get_total_accepted_by_user(pool, uid)
                pct = percent_for_cumulative(cum)
                lines.append(f"- {uid} -> {pct}%")
        else:
            lines.append('\n' + get_text(user_id, 'profile_no_invited'))
        
        lines.append('\n\n' + get_text(user_id, 'profile_hint'))
        # add reset button
        keyboard = [[InlineKeyboardButton(get_text(user_id, 'reset_btn'), callback_data='reset_profile')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('\n'.join(lines), reply_markup=reply_markup)
    else:
        await update.message.reply_text('Profile is unavailable because DATABASE_URL not set on the host.')


async def show_subscription_check(update, user_id):
    keyboard = [[InlineKeyboardButton(get_text(user_id, 'continue_btn'), callback_data='continue_after_subscription')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        get_text(user_id, 'subscribe_required').format(INSTAGRAM_LINK, TIKTOK_LINK, TELEGRAM_BOT_LINK),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
  
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    if data.startswith("set_lang_"):
        new_lang = data.split("_")[-1]  # en / az / ru
        user_languages[user_id] = new_lang
        if context.bot_data.get('db_pool'):
            await ensure_user(context.bot_data['db_pool'], user_id, new_lang)
        await query.edit_message_text(get_text(user_id, 'lang_changed'))
        return

    await query.answer()

    if data == 'balance_topup':
        await show_subscription_check(update, user_id)
    elif data == 'privileges':
        await query.edit_message_text(get_text(user_id, 'coming_soon'))
    elif data == 'promotions':
        await query.edit_message_text(get_text(user_id, 'no_promotions'))
    elif data == 'continue_after_subscription':
        await query.edit_message_text(get_text(user_id, 'subscription_check'))
        await asyncio.sleep(1)
        user_data[user_id] = {'step': 'amount'}
        await query.message.reply_text(get_text(user_id, 'amount_question'))
    elif data == 'send_request':
        if user_id in user_data and 'receipt_photo' in user_data[user_id]:
            await send_to_admin(user_id, context)
            await query.edit_message_text(get_text(user_id, 'request_sent'))
        else:
            await query.edit_message_text(get_text(user_id, 'invalid_photo'))

    elif data == 'cancel':
        if user_id in user_data:
        
            if 'invoice_message_id' in user_data[user_id]:
                try:
                    await context.bot.edit_message_text(
                        chat_id=user_id,
                        message_id=user_data[user_id]['invoice_message_id'],
                        text="❌ Оплата отменена.\n\n⏳ Этот счёт больше недействителен."
                    )
                except Exception:
                    pass

            if 'last_message_id' in user_data[user_id]:
                try:
                    await context.bot.edit_message_text(
                        chat_id=user_id,
                        message_id=user_data[user_id]['last_message_id'],
                        text="❌ Оплата отменена."
                    )
                except Exception:
                    pass

            del user_data[user_id]

        await query.edit_message_text(get_text(user_id, 'request_cancelled'))
        await asyncio.sleep(2)
        await donate_command(update, context)


        
    elif data.startswith('accept_'):
        target_user_id = int(data.split('_')[1])
        pool = context.bot_data.get('db_pool')

    
        user_data_target = user_data.get(target_user_id, {})

        nickname = user_data_target.get('nickname')
        amount = user_data_target.get('amount')

    
        if (not nickname or not amount) and pool:
            async with pool.acquire() as conn:
                row = await conn.fetchrow("SELECT nickname, amount FROM pending_requests WHERE user_id=$1", target_user_id)
                if row:
                    nickname = row["nickname"]
                    amount = row["amount"]

        if not nickname:
            nickname = "Unknown"
        if not amount:
            amount = 0
    
        owner_bonus = 0
        if pool:
    
            await add_donation_record(pool, target_user_id, amount, accepted=True)

  
            cum = await get_total_accepted_by_user(pool, target_user_id)
            owner_bonus = percent_for_cumulative(cum)

        adjusted_amount = int(round(float(amount) * (1 + owner_bonus / 100.0)))

    
        try:
            await context.bot.send_message(
                target_user_id,
                get_text(target_user_id, 'request_accepted_with_info')
            )
        except Exception:
            logger.exception("Failed to notify user about accepted donation")
        
        if pool:
            await remove_pending_request(pool, target_user_id)

    
        try:
            card_counter = await get_next_counter(pool, "card") if pool else 1
        except Exception:
            card_counter = 1

    
        await context.bot.send_message(
            ADMIN_ID,
            f"{card_counter}.🎮 Command for console:\n\n"
            f"`points give {nickname} {adjusted_amount}`\n\n"
            f"Click the message to copy!",
            parse_mode='Markdown'
        )

    
        await query.edit_message_text(
            f"✅ Request accepted for user {target_user_id} — "
            f"points: {adjusted_amount} (bonus {owner_bonus}%)."
        )   

    
    elif data == 'cancel_payment':
        if user_id in user_data:
        
            if 'invoice_message_id' in user_data[user_id]:
                try:
                    await context.bot.delete_message(
                        chat_id=user_id,
                        message_id=user_data[user_id]['invoice_message_id']
                    )
                except Exception:
                    pass

       
            user_data.pop(user_id, None)

    
        try:
            await query.edit_message_text(get_text(user_id, 'request_cancelled'))
        except Exception:
            await context.bot.send_message(user_id, get_text(user_id, 'request_cancelled'))


    # record accepted donation into DB
        pool = context.bot_data.get('db_pool')
        if pool:
            await add_donation_record(pool, target_user_id, amount, accepted=True)

        # notify referrer if exists and compute bonus
            async with pool.acquire() as conn:
                row = await conn.fetchrow('SELECT referrer_id FROM users WHERE id = $1', target_user_id)
                if row and row['referrer_id']:
                    ref_id = row['referrer_id']
                # compute percent for this referred player's cumulative donations
                    cum = await get_total_accepted_by_user(pool, target_user_id)
                    pct = percent_for_cumulative(cum)
                # compute owner's total after this change (БЕЗ лимита)
                    async def compute_owner_bonus_unlimited(pool, owner_id):
                        invited = await get_invited_list(pool, owner_id)
                        total = 0
                        for uid in invited:
                            cum_invited = await get_total_accepted_by_user(pool, uid)
                            total += percent_for_cumulative(cum_invited)
                        return total

                    owner_total = await compute_owner_bonus_unlimited(pool, ref_id)

                # notify owner
                    #try:
                        #await context.bot.send_message(
                            #ref_id,
                            #f"🔔 Your invite {target_user_id} donated total {cum} AZN — their tier adds {pct}% to your bonus. "
                            #f"Your current total bonus is {owner_total}% (no limit)."
                        #)
                    #except Exception:
                        #logger.exception('Failed to notify referrer')

    
        # compute owner bonus for the target_user (their own invited players)
        owner_bonus = 0
        if pool:
    
            await add_donation_record(pool, target_user_id, amount, accepted=True)

    
            used_saved = user_data_target.get('use_saved_nick', True)
            if used_saved:
                cum = await get_total_accepted_by_user(pool, target_user_id)
                owner_bonus = percent_for_cumulative(cum)
        else:
            owner_bonus = 0

        adjusted_amount = int(round(float(amount) * (1 + owner_bonus / 100.0)))

    # Notify the player with detailed info (amount and nickname)
        try:
            await context.bot.send_message(target_user_id, get_text(target_user_id, 'request_accepted_with_info').format(adjusted_amount, nickname))
        except Exception:
            logger.exception('Failed to notify user about accepted donation')

    
            # send command to admin with card counter
        if pool:
            try:
                card_counter = await get_next_counter(pool, "card")
            except Exception:
                card_counter = 1
        else:
            card_counter = context.bot_data.get('card_counter', 0) + 1
            if card_counter > 100:
                card_counter = 1
            context.bot_data['card_counter'] = card_counter

        await context.bot.send_message(
            ADMIN_ID,
            f"{card_counter}.🎮 Command for console:\n\n`points give {nickname} {adjusted_amount}`\n\nClick the message to copy!",
            parse_mode='Markdown'
        )

    
        await query.edit_message_text(
            f"✅ Request accepted for user {target_user_id} — points: {adjusted_amount} (bonus {owner_bonus}%)."
        )


    elif data.startswith('reject_'):
        target_user_id = int(data.split('_')[1])
        await context.bot.send_message(target_user_id, get_text(target_user_id, 'request_rejected'))
        await query.edit_message_text(f"❌ Request rejected for user {target_user_id}")
        if pool:
            await remove_pending_request(pool, target_user_id)
    elif data.startswith('reject_reason_'):
        target_user_id = int(data.split('_')[2])
        admin_rejection_data[ADMIN_ID] = {
            'target_user_id': target_user_id,
            'step': 'waiting_reason'
        }
        if pool:
            await remove_pending_request(pool, target_user_id)

    
        await query.message.reply_text("send the reason")
        await query.edit_message_text(
            f"📝 Waiting for reason for user {target_user_id}..."
        )

    #Callback handlers for nickname choices & reset 
    elif data == 'use_saved_nick':
        pool = context.bot_data.get('db_pool')
        saved = None
        if pool:
            saved = await get_game_nick(pool, user_id)
        else:
            saved = user_data.get(user_id, {}).get('saved_nick')
        if not saved:
            await query.edit_message_text(get_text(user_id, 'invalid_amount'))
            return
        # apply saved nick and proceed to card
        user_data.setdefault(user_id, {})['nickname'] = saved
        user_data[user_id]['use_saved_nick'] = True
        user_data[user_id]['step'] = 'confirm_payment'
        await query.edit_message_text(f"Using saved nickname: {saved}")
        await query.message.reply_text(get_text(user_id, 'payment_confirm'))

    elif data == 'enter_other_nick':
        user_data.setdefault(user_id, {})['use_saved_nick'] = False
        user_data[user_id]['step'] = 'nickname'
        await query.edit_message_text(get_text(user_id, 'enter_other_nick'))
        await query.message.reply_text(get_text(user_id, 'nickname_question'))

    elif data == 'reset_profile':
        # Warn user and require type exact phrase
        user_data.setdefault(user_id, {})['reset_pending'] = True
        await query.edit_message_text(get_text(user_id, 'reset_warning'))
        await query.message.reply_text(get_text(user_id, 'reset_confirm_prompt'))

    elif data == 'pay_with_stars':
        amount = user_data[user_id]['amount']
        stars_amount = calculate_stars(amount)
        user_data[user_id]['step'] = 'stars_payment'
        user_data[user_id]['locked'] = True

        pool = context.bot_data.get('db_pool')
        if pool:
            async with pool.acquire() as conn:
                await conn.execute("UPDATE users SET locked=TRUE WHERE id=$1", user_id)

    
        msg = await query.message.reply_text(
            f"💰 Amount: {amount} token\n"
            f"⭐ Stars to pay: {stars_amount}\n"
            f"Click the invoice button below to pay:",
        )
        user_data[user_id]['last_message_id'] = msg.message_id

        await send_stars_invoice(update, context, user_id, amount)

    elif data == 'pay_with_card':
        user_data[user_id]['step'] = 'payment'
        amount = user_data[user_id]['amount']
        payment_amount = amount * 0.1
        await query.edit_message_text(get_text(user_id, 'payment_info').format(MY_CARD, payment_amount), parse_mode='Markdown')

    
    #elif data == 'pay_with_card':
        #user_data[user_id]['step'] = 'enter_card_for_payment'
        #await query.edit_message_text(get_text(user_id, 'card_question'))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # Admin rejection flow
    if user_id == ADMIN_ID and user_id in admin_rejection_data:
        if admin_rejection_data[user_id]['step'] == 'waiting_reason':
            target_user_id = admin_rejection_data[user_id]['target_user_id']
            reason = text

            
            await context.bot.send_message(
                target_user_id,
                get_text(target_user_id, 'request_rejected_with_reason').format(reason)
            )

            # админу подтверждение
            await update.message.reply_text(
                f"❌ Request rejected for user {target_user_id}.\nReason: {reason}"
            )

            del admin_rejection_data[user_id]
            return

    # Handle reset confirmation (exact phrase)
    if user_id in user_data and user_data[user_id].get('reset_pending'):
        if text.strip() == 'resetallthedata':
            pool = context.bot_data.get('db_pool')
            if pool:
                await reset_user_data(pool, user_id)
            else:
                # clear in-memory data
                if user_id in user_data:
                    user_data[user_id].pop('saved_nick', None)
            # remove from in-memory session too
            if user_id in user_data:
                user_data[user_id].pop('reset_pending', None)
            await update.message.reply_text(get_text(user_id, 'reset_success'))
        else:
            await update.message.reply_text('Cancelled. To reset data type exactly: resetallthedata')
            user_data[user_id].pop('reset_pending', None)
        return

    if user_id not in user_data:
        # allow /profile and /start payload to work without interfering
        return

    step = user_data[user_id].get('step')
    pool = context.bot_data.get('db_pool')
    if step == 'amount':
        try:
            amount = float(text)
            if amount < 0:
                await update.message.reply_text(get_text(user_id, 'invalid_amount'))
                return
                pass
            user_data[user_id]['amount'] = amount
            # Check if user already has saved nickname in DB
            saved = None
            if pool:
                await ensure_user(pool, user_id, user_languages.get(user_id, 'en'))
                saved = await get_game_nick(pool, user_id)
            else:
                saved = user_data.get(user_id, {}).get('saved_nick')
            if saved:
                # Offer two buttons: use saved nick (bonuses apply) or enter other nick (no bonus)
                keyboard = [[InlineKeyboardButton(get_text(user_id, 'use_saved_nick'), callback_data='use_saved_nick')], [InlineKeyboardButton(get_text(user_id, 'enter_other_nick'), callback_data='enter_other_nick')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                user_data[user_id]['step'] = 'choose_nick'
                user_data[user_id]['saved_nick'] = saved
                await update.message.reply_text(get_text(user_id, 'choose_saved_nick').format(saved), reply_markup=reply_markup)
                return
            # otherwise ask for nickname and save on first entry
            user_data[user_id]['step'] = 'nickname'
            await update.message.reply_text(get_text(user_id, 'nickname_question'))
        except ValueError:
            await update.message.reply_text(get_text(user_id, 'invalid_amount'))
    elif step == 'nickname':
        user_data[user_id]['nickname'] = text
        saved_now = False
        if pool:
            current_saved = await get_game_nick(pool, user_id)
            if not current_saved:
                await set_game_nick(pool, user_id, text)
                saved_now = True
        else:
            if not user_data[user_id].get('saved_nick'):
                user_data[user_id]['saved_nick'] = text
                saved_now = True

        if saved_now:
            await update.message.reply_text(get_text(user_id, 'nickname_saved').format(text))

    # теперь показываем шаг подтверждения
        user_data[user_id]['step'] = 'confirm_payment'
        await update.message.reply_text(get_text(user_id, 'payment_confirm'))

    #elif step == 'enter_card_for_payment':
        #if len(text.replace(' ', '').replace('-', '')) != 16 or not text.replace(' ', '').replace('-', '').isdigit():
            #await update.message.reply_text(get_text(user_id, 'invalid_card'))
            #return
    
        #user_data[user_id]['user_card'] = text
        #user_data[user_id]['step'] = 'payment'
        #amount = user_data[user_id]['amount']
        #payment_amount = amount * 0.1  # переводим 10% от суммы в AZN
        #await update.message.reply_text(
            #get_text(user_id, 'payment_info').format(MY_CARD, payment_amount),
            #parse_mode='Markdown'
        #)
    
    elif step == 'confirm_payment':
        if text.strip().lower() == "ihavetopay":
            user_data[user_id]['step'] = 'choose_payment'
            await update.message.reply_text(get_text(user_id, 'payment_confirm_success'))

            amount = user_data[user_id]['amount']
            # Build payment options: stars always available, card only if amount >= 150 tokens
            keyboard = [[InlineKeyboardButton(get_text(user_id, 'stars_payment'), callback_data='pay_with_stars')]]
            try:
                # ensure numeric comparison
                amt_val = float(amount)
            except Exception:
                amt_val = 0.0
            if amt_val >= 150:
                keyboard.append([InlineKeyboardButton(get_text(user_id, 'card12'), callback_data='pay_with_card')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Choose payment method:", reply_markup=reply_markup)
        else:
            await update.message.reply_text(get_text(user_id, 'payment_confirm_fail'))



async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data or user_data[user_id].get('step') != 'payment':
        return
    user_data[user_id]['receipt_photo'] = update.message.photo[-1].file_id
    keyboard = [[InlineKeyboardButton(get_text(user_id, 'send_request'), callback_data='send_request')], [InlineKeyboardButton(get_text(user_id, 'cancel'), callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(get_text(user_id, 'confirm_buttons'), reply_markup=reply_markup)

async def send_to_admin(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    data = user_data[user_id]
    pool = context.bot_data.get('db_pool')
    if pool:
        await add_pending_request(pool, user_id, data['nickname'], data['amount'], 'card', data['receipt_photo'])

    
    bonus_percent = 0
    final_amount = int(round(float(data['amount'])))
    if pool:
        invited = await get_invited_list(pool, user_id)
        for uid in invited:
            cum = await get_total_accepted_by_user(pool, uid)
            bonus_percent += percent_for_cumulative(cum)
        final_amount = int(round(float(data['amount']) * (1 + bonus_percent / 100.0)))

    
    keyboard = [
        [InlineKeyboardButton(get_text(ADMIN_ID, 'accept'), callback_data=f'accept_{user_id}')],
        [InlineKeyboardButton(get_text(ADMIN_ID, 'reject'), callback_data=f'reject_{user_id}')],
        [InlineKeyboardButton(get_text(ADMIN_ID, 'reject_with_reason'), callback_data=f'reject_reason_{user_id}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    
    msg = (
        f"🔔 New donation request\n\n"
        f"👤 Nickname: {data['nickname']}\n"
        f"🆔 User ID: {user_id}\n"
        f"💰 Amount: {data['amount']} tokens\n"
        f"🏷 Bonus: {bonus_percent}%\n"
        f"📊 Final credited: {final_amount}\n"
        #f"💳 User card: {data['user_card']}\n\n"
        f"📸 Receipt:"
    )

    await context.bot.send_message(ADMIN_ID, msg, reply_markup=reply_markup)
    await context.bot.send_photo(ADMIN_ID, photo=data['receipt_photo'], caption=f"Receipt from user {user_id}")

def calculate_stars(azn_amount):
    """Конвертирует AZN в звезды (10 AZN = 60 звезд, то есть 1 AZN = 6 звезд)"""
    return int(azn_amount * 3)

async def send_stars_invoice(update, context, user_id, amount):
    """Отправляет инвойс для оплаты звездами"""
    pool = context.bot_data.get('db_pool')
    if pool:
        await add_pending_request(pool, user_id, user_data[user_id].get('nickname', 'Unknown'), amount, 'stars')

    stars_amount = calculate_stars(amount)
    
    
    payload = f"donation_{user_id}_{int(time.time())}"
    user_data[user_id]['payment_payload'] = payload
    
    
    prices = [LabeledPrice("Donation", stars_amount)]
    
    await context.bot.send_invoice(
        chat_id=user_id,
        title=get_text(user_id, 'stars_invoice_title'),
        description=get_text(user_id, 'stars_invoice_description').format(amount),
        payload=payload,
        currency='XTR',  # Telegram Stars currency
        prices=prices,
        provider_token=""  
    )
    user_data[user_id]['invoice_message_id'] = msg.message_id

from aiohttp import web
async def health_check(request):
    return web.Response(text="OK")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logger.info(f"Web server started on port {PORT}")

async def keep_alive():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                url = os.getenv('RENDER_URL')
                async with session.get(f"{url}/health") as response:
                    logger.info(f"Keep alive ping: {response.status}")
        except Exception as e:
            logger.error(f"Keep alive error: {e}")
        await asyncio.sleep(5 * 60)


async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждает предварительную проверку платежа"""
    query = update.pre_checkout_query
    payload = query.invoice_payload
    
    
    user_id = None
    for uid, data in user_data.items():
        if data.get('payment_payload') == payload:
            user_id = uid
            break
    
    if user_id and user_id in user_data:
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Payment expired or invalid")

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает успешный платеж"""
    user_id = update.effective_user.id
    payment = update.message.successful_payment
    
    if user_id not in user_data:
        return
    
    
    await update.message.reply_text(get_text(user_id, 'payment_success'))
    user_data[user_id]['locked'] = False
    pool = context.bot_data.get('db_pool')
    if pool:
        async with pool.acquire() as conn:
            await conn.execute("UPDATE users SET locked=FALSE WHERE id=$1", user_id)
    
    await send_stars_donation_to_admin(user_id, context, payment)
    if pool:
        await remove_pending_request(pool, user_id)

async def send_stars_donation_to_admin(user_id: int, context: ContextTypes.DEFAULT_TYPE, payment):
    pool = context.bot_data.get('db_pool')

   
    data = user_data.get(user_id, {})

    nickname = data.get('nickname')
    amount = data.get('amount')

    
    if (not nickname or not amount) and pool:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT nickname, amount FROM pending_requests WHERE user_id=$1", user_id)
            if row:
                nickname = row["nickname"]
                amount = row["amount"]

    if not nickname:
        nickname = "Unknown"
    if not amount:
        amount = 0

   
    bonus_percent = 0
    final_amount = int(round(float(amount)))
    if pool:
        invited = await get_invited_list(pool, user_id)
        for uid in invited:
            cum = await get_total_accepted_by_user(pool, uid)
            bonus_percent += percent_for_cumulative(cum)
        final_amount = int(round(float(amount) * (1 + bonus_percent / 100.0)))

    
    if pool:
        try:
            stars_counter = await get_next_counter(pool, "stars")
        except Exception:
            stars_counter = 1
    else:
        stars_counter = context.bot_data.get('stars_counter', 0) + 1
        if stars_counter > 100:
            stars_counter = 1
        context.bot_data['stars_counter'] = stars_counter

    
    if pool:
        await add_donation_record(pool, user_id, amount, accepted=True)
        await remove_pending_request(pool, user_id)

   
    command = f"points give {nickname} {final_amount}"
    msg = (
        f"{stars_counter}.⭐ STARS DONATION RECEIVED\n\n"
        f"👤 Nickname: {nickname}\n"
        f"💰 Amount: {amount} tokens\n"
        f"🎁 Bonus: {bonus_percent}%\n"
        f"📊 Final credited: {final_amount}\n"
        f"⭐ Stars paid: {payment.total_amount}\n"
        f"🎮 Command for console:\n"
        f"`{command}`\n\n"
        f"Click the message to copy!"
    )

    await context.bot.send_message(ADMIN_ID, msg, parse_mode='Markdown')

    del user_data[user_id]


if __name__ == "__main__":
    import asyncio
    import logging
    from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, PreCheckoutQueryHandler
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        application = Application.builder().token(BOT_TOKEN).build()

        
        db_pool = await init_db_pool_with_rules()
        application.bot_data['db_pool'] = db_pool

        
        await start_web_server()  
        asyncio.create_task(keep_alive())

       
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("lang", change_language))
        application.add_handler(CommandHandler("donate", donate_command_with_rules))
        application.add_handler(CommandHandler("profile", profile_command))
        application.add_handler(CommandHandler("rules", rules_command))
        application.add_handler(CommandHandler("crules", crules_command))
        application.add_handler(CommandHandler("unlock", unlock_command))
        application.add_handler(CallbackQueryHandler(rules_callback, pattern="^accept_rules$"))
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
        application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

        # Polling 
        logging.info("🚀 Bot started with polling.")
        await application.initialize()
        await application.bot.delete_webhook(drop_pending_updates=True) 
        await application.start()
        await application.updater.start_polling()
        await asyncio.Event().wait()          

    asyncio.run(main())
