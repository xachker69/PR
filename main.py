import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, ConversationHandler, filters
from components_db import COMPONENTS

# Налаштування логування для зручного відстеження подій у боті
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Стани для ConversationHandler: очікування бюджету та задачі
ASK_BUDGET, ASK_TASK = range(2)

# Стартова команда: пропонує розпочати підбір і виводить кнопку
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🚀 Розпочати новий підбір"], ["⛔ Зупинити бота"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        '👋 Вітаю! Я допоможу підібрати компʼютерні комплектуючі під ваш бюджет.\n\n💸 Вкажіть, будь ласка, ваш бюджет у гривнях:',
        reply_markup=reply_markup
    )
    return ASK_BUDGET

# Обробка введення бюджету: перевіряє число, пропонує вибір задачі
async def ask_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⛔ Зупинити бота":
        await cancel(update, context)
        return ConversationHandler.END
    try:
        budget = int(update.message.text)
        context.user_data['budget'] = budget
        keyboard = [["🎮 Для геймінгу"], ["💼 Для роботи з важкими програмами"], ["🖥️ Для офісних задач"], ["⛔ Зупинити бота"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            '📝 Які основні задачі для компʼютера?\n\nОберіть одну з кнопок нижче:',
            reply_markup=reply_markup
        )
        return ASK_TASK
    except ValueError:
        await update.message.reply_text('❗ Будь ласка, введіть число (бюджет у гривнях):')
        return ASK_BUDGET

# Обробка вибору задачі: підбирає конфігурацію, виводить деталі
async def ask_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⛔ Зупинити бота":
        await cancel(update, context)
        return ConversationHandler.END
    # Видаляємо емодзі для пошуку ключа у базі
    task = update.message.text.replace('🎮 ', '').replace('💼 ', '').replace('🖥️ ', '')
    budget = context.user_data.get('budget', 0)
    options = COMPONENTS.get(task, [])
    if not options:
        await update.message.reply_text('❗ Не розпізнано задачу. Спробуйте ще раз, оберіть одну з кнопок.')
        return ASK_TASK
    # Пошук конфігурації під бюджет
    suitable = [c for c in options if c['price'] <= budget]
    if suitable:
        best = suitable[-1]  # Найдорожча з тих, що підходять
        keyboard = [["🚀 Розпочати новий підбір"], ["⛔ Зупинити бота"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        details = (
            f'✅ <b>{best["name"]} варіант</b> (≈<b>{best["price"]} грн</b>)\n'
            f'🧠 <b>CPU:</b> {best["cpu"]}\n'
            f'🎮 <b>GPU:</b> {best["gpu"]}\n'
            f'💾 <b>RAM:</b> {best["ram"]}\n'
            f'💽 <b>SSD/HDD:</b> {best["storage"]}\n'
            f'🔌 <b>Блок живлення:</b> {best["psu"]}\n'
            f'🖧 <b>Материнська плата:</b> {best["motherboard"]}\n'
            f'🖥️ <b>Корпус:</b> {best["case"]}\n'
            f'🔗 <a href="{best["link"]}">Детальніше/Купити</a>'
        )
        await update.message.reply_text(details, reply_markup=reply_markup, parse_mode='HTML', disable_web_page_preview=True)
        return ASK_BUDGET
    else:
        keyboard = [["🚀 Розпочати новий підбір"], ["⛔ Зупинити бота"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text('😔 На жаль, не знайдено конфігурацій у вашому бюджеті.', reply_markup=reply_markup)
        return ASK_BUDGET

# Обробка скасування підбору
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('⛔ Бот зупинено. Щоб почати знову — натисніть /start.')
    return ConversationHandler.END

# Основна точка входу: створення застосунку та запуск бота
if __name__ == '__main__':
    application = ApplicationBuilder().token("7472880038:AAGumTtc-CXPkZVSLXqfPBaGBjPcM83gt8k").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_budget)],
            ASK_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_task)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(conv_handler)
    application.run_polling()
