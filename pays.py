import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- НАСТРОЙКИ ---
# Вставь сюда токен от @BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN")

# В aiogram 3.7+ parse_mode задается через DefaultBotProperties
bot = Bot(token=BOT_TOKEN, default_bot_properties=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
router = Router()

# --- FSM (Состояния) ---
class BotStates(StatesGroup):
    waiting_for_calc = State()

# --- КЛАВИАТУРЫ ---
# 1. Главное меню (Reply)
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💸 PayscrowP2P"), KeyboardButton(text="🏦 PayscrowHUB")]
    ],
    resize_keyboard=True
)

# 2. Меню HUB (Reply)
hub_reply_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Запустить"), KeyboardButton(text="Остановить")],
        [KeyboardButton(text="Общий баланс"), KeyboardButton(text="SwapGo")],
        [KeyboardButton(text="Калькулятор"), KeyboardButton(text="В главное меню")]
    ],
    resize_keyboard=True
)

# 3. Инлайн кнопки для баланса
balance_inline_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Пополнить баланс", callback_data="add_balance"), 
         InlineKeyboardButton(text="Вывести баланс", callback_data="withdraw_balance")],
        [InlineKeyboardButton(text="CompLiance", callback_data="compliance")]
    ]
)

# 4. Инлайн кнопка для SwapGo
swapgo_inline_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Открыть SwapGo", url="https://t.me/swapgo")]
    ]
)


# --- ОБРАБОТЧИКИ ---

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear() # Очищаем состояния (например, если юзер был в калькуляторе)
    text = (
        "👋 Добро пожаловать в экосистему проекта <b>Payscrow!</b> 🦅\n\n"
        "Используйте раздел <b>PayscrowP2P</b> для продажи крипты и раздел <b>PayscrowHUB</b> для всех остальных наших услуг ⤵️"
    )
    await message.answer(text, reply_markup=main_kb)

@router.message(F.text == "💸 PayscrowP2P")
async def process_p2p(message: Message):
    await message.answer("⚠️ Доступ к PayscrowP2P откроется чуть позже!")

@router.message(F.text == "🏦 PayscrowHUB")
async def process_hub(message: Message):
    await message.answer("Пополните общий баланс и переходите к нужному Вам разделу ⤵️", reply_markup=hub_reply_kb)
    await show_balance(message)

# Вспомогательная функция для показа баланса
async def show_balance(message: Message):
    text = (
        "Ваш общий баланс: <b>0.00 USDT</b>\n\n"
        "Payscrow - сервис по обработке платежей, который дает возможность заработать каждому 💳"
    )
    await message.answer(text, reply_markup=balance_inline_kb)

@router.message(F.text.in_({"Запустить", "Остановить"}))
async def process_start_stop(message: Message):
    text = (
        "⚠️ <b>Доступ к разделу ограничен!</b>\n\n"
        "Для подключения обратитесь в комплаенс-отдел, после чего перезапустите бот командой /start\n\n"
        "Адрес для внесения страхового депозита:\n"
        "<code>TTC1****DmPm2Gt</code>"
    )
    await message.answer(text)

@router.message(F.text == "Общий баланс")
async def process_general_balance(message: Message, state: FSMContext):
    await state.clear()
    await show_balance(message)

@router.message(F.text == "SwapGo")
async def process_swapgo(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "💱 <b>SwapGO</b> — ваш анонимный криптообменник в Telegram.\n\n"
        "🤝 <b>Обмен крипта-крипта:</b> Широкий выбор поддерживаемых токенов и сетей.\n"
        "👤 <b>Без KYC:</b> Полная анонимность, никаких проверок личности и предоставления документов.\n"
        "💸 <b>Без ограничений:</b> Никаких лимитов на сумму обмена.\n\n"
        "👇 Начать обмен:"
    )
    await message.answer(text, reply_markup=swapgo_inline_kb)

@router.message(F.text == "В главное меню")
async def process_main_menu(message: Message, state: FSMContext):
    await cmd_start(message, state)

# --- КАЛЬКУЛЯТОР ---

@router.message(F.text == "Калькулятор")
async def process_calculator_start(message: Message, state: FSMContext):
    text = (
        "<b>Примеры выражений:</b>\n\n"
        "2 + 2\n"
        "1000 + 8%\n"
        "8 + (9 * 4.83)\n\n"
        "Введите ваш запрос ⤵️"
    )
    await state.set_state(BotStates.waiting_for_calc)
    await message.answer(text)

# Хендлер перехватит клик по любой системной кнопке, если пользователь находился в режиме калькулятора, и сбросит состояние
@router.message(StateFilter(BotStates.waiting_for_calc), F.text.in_({
    "💸 PayscrowP2P", "🏦 PayscrowHUB", "Запустить", "Остановить", "Общий баланс", "SwapGo", "В главное меню"
}))
async def process_calculator_exit(message: Message, state: FSMContext):
    await state.clear()
    # Просто перенаправляем на нужные функции в зависимости от текста кнопки
    if message.text == "💸 PayscrowP2P":
        await process_p2p(message)
    elif message.text == "🏦 PayscrowHUB":
        await process_hub(message)
    elif message.text in ["Запустить", "Остановить"]:
        await process_start_stop(message)
    elif message.text == "Общий баланс":
        await process_general_balance(message, state)
    elif message.text == "SwapGo":
        await process_swapgo(message, state)
    elif message.text == "В главное меню":
        await cmd_start(message, state)

@router.message(StateFilter(BotStates.waiting_for_calc))
async def process_calculator_input(message: Message, state: FSMContext):
    query = message.text.replace(" ", "").replace(",", ".")
    
    # Обработка процентов (1000+8%)
    if "%" in query:
        query = re.sub(r'(\d+(?:\.\d+)?)\+(\d+(?:\.\d+)?)%', r'\1*1.\2', query)
        query = re.sub(r'(\d+(?:\.\d+)?)\-(\d+(?:\.\d+)?)%', r'\1*(1-0.\2)', query)
        query = query.replace("%", "/100")

    # Разрешаем только цифры и мат. знаки
    if not re.match(r'^[\d\+\-\*\/\(\)\.]+$', query):
        await message.answer("❌ Ошибка: Введены недопустимые символы. Попробуйте еще раз ⤵️")
        return

    try:
        # Вычисляем безопасно (без прямого eval глобальных функций)
        result = eval(compile(query, "<string>", "eval", flags=0, dont_inherit=True), {"__builtins__": None}, {})
        result = round(result, 4) # Округляем
        await message.answer(f"🧮 Результат: <b>{result}</b>\n\nВведите следующий запрос или воспользуйтесь меню ⤵️")
    except Exception:
        await message.answer("❌ Ошибка в выражении. Проверьте правильность ввода ⤵️")

# Запуск бота
async def main():
    dp.include_router(router)
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
