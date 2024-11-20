import logging
import re
from datetime import datetime

import pytz
from dateutil.relativedelta import relativedelta
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from barcode_gen import generate_barcode
from config import BOT_KEY
from final_report import create_final_report
from messages import start_message, orders_message, assembly_tasks_message
from report_generator import generate_sales_report_excel, generate_stock_report_excel, generate_orders_report_excel
from sales_report import g_sales_report_excel
from scheduler import scheduler  # Importing the scheduler
from wildberries_api import get_orders, get_assembly_tasks, fetch_product_info, get_sales_report, get_sales_data, \
    get_stock_data, get_orders_data

logging.getLogger("httpx").setLevel(logging.WARNING)  # Устанавливаем уровень WARNING, чтобы не выводились INFO логи
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Старт бота и добавление кнопок
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        ['Проверить заказы'],
        ['Отчет по складу','Отчет по заказам', 'Отчет по продажам', 'Еженедельный отчет по реализации'],
        ['Помощь']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(start_message, reply_markup=reply_markup)

# Извлечение артикула из сообщения для дальнейшего поиска
def extract_article(message):
    match = re.search(r'артикул:\s*(\w+)', message, re.IGNORECASE)
    return match.group(1) if match else None

# Работа с сообщениями
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text

    if text == 'Проверить заказы':
        await check_orders(update, context)
    elif text == 'Итог':
        await  get_final_report_command(update, context)
    elif text == 'Получить сборочные задания':
        await get_assembly_tasks_command(update, context)
    elif text == 'Помощь':
        await update.message.reply_text("Чем я могу помочь?")
    elif text == 'Отчет по складу':
        await get_stock_report_command(update, context)
    elif text == 'Отчет по заказам':
        await get_orders_data_command(update, context)
    elif text == 'Отчет по продажам':
        await get_sales_data_command(update, context)
    elif text == 'Еженедельный отчет по реализации':
        await get_sales_report_command(update, context)
    else:
        article = extract_article(text)
        if article:
            product_info = await fetch_product_info(article)
            if product_info and product_info['cards']:
                product = product_info['cards'][0]
                title = product.get('title', 'Не указано')
                vendorCode = product.get('nmID', 'Не указано')
                brand = product.get('brand', 'Не указано')
                sku = product.get('sizes', [])[0].get('skus', [''])[0]
                size = product.get('sizes', [])[0].get('techSize', [])[0]
                pdf_data = await generate_barcode(sku, title, vendorCode, brand, size)
                response_message = f"Товар найден:\nНазвание: {title}\nБренд: {brand}\nАртикул: {vendorCode}\n"
                await update.message.reply_text(response_message)
                await context.bot.send_document(chat_id=update.effective_chat.id, document=pdf_data, filename='barcode.pdf')
            else:
                await update.message.reply_text("Товар не найден.")
        else:
            await update.message.reply_text('Пожалуйста, укажите артикул в формате "артикул: ___".')

# Проверить заказы
async def check_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        orders = await get_orders()
        await update.message.reply_text(orders_message(orders))
    except Exception as e:
        logging.error(f"Error while checking orders: {e}")
        await update.message.reply_text("Ошибка при получении заказов. Попробуйте позже.")

# Получить информацию о сборочных заданиях. (Требуется изменение, так как сборочные берутся все существующие)
async def get_assembly_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        result = await get_assembly_tasks()
        if not result or 'orders' not in result:
            raise ValueError("Не удалось получить данные о сборочных заданиях.")
        tasks = result['orders']
        message = assembly_tasks_message(tasks)
        await update.message.reply_text(message)
    except Exception as e:
        logging.error(f"Error while fetching assembly tasks: {e}")
        await update.message.reply_text("Ошибка при получении сборочных заданий. Попробуйте позже.")

#Остатки на складах и вещи которые в пути
async def get_stock_report_command(update, context):
    # Устанавливаем часовой пояс Москвы
    moscow_tz = pytz.timezone('Europe/Moscow')
    current_time = datetime.now(moscow_tz)

    # Получаем дату два месяца назад
    date_from = (current_time - relativedelta(months=1)).strftime('%Y-%m-%dT%H:%M:%S')

    try:
        data = await get_stock_data(date_from)

        if data:
            excel_file = generate_stock_report_excel(data)

            with open(excel_file, "rb") as file:
                await context.bot.send_document(chat_id=update.effective_chat.id, document=file)
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Данных по складу нет.")
    except Exception as e:
        logging.error(f"Ошибка при получении данных по складу: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Ошибка при получении данных по складу.")


# Команда для получения данных по заказам и генерации отчета в Excel
async def get_orders_data_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Устанавливаем временную зону Московское время
    moscow_tz = pytz.timezone('Europe/Moscow')
    current_time = datetime.now(moscow_tz)

    # Дата начала (например, с 1 сентября) и текущая дата как date_to
    date_from = '2024-09-01T00:00:00'
    date_to = current_time.strftime('%Y-%m-%dT%H:%M:%S')

    try:
        # Получаем данные о заказах
        orders_data = await get_orders_data(date_from, date_to)

        # Если данные получены, генерируем отчет и отправляем
        if orders_data:
            excel_file = generate_orders_report_excel(orders_data)
            with open(excel_file, "rb") as file:
                await context.bot.send_document(chat_id=update.effective_chat.id, document=file)
        else:
            await update.message.reply_text("Нет заказов за указанный период.")

    except Exception as e:
        logging.error(f"Ошибка при получении заказов: {e}")
        await update.message.reply_text("Произошла ошибка при получении данных о заказах.")


#Итоговый еженедельный отчет
async def get_sales_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date_from, date_to = "2024-09-01", "2024-09-30"
    report_data = await get_sales_report(date_from, date_to)
    if report_data:
        excel_file = generate_sales_report_excel(report_data)
        with open(excel_file, "rb") as file:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=file)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Отчет за выбранный период не найден.")


#Продажи начиная с даты
async def get_sales_data_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    date_from = "2024-09-01"
    try:
        sales_data = await get_sales_data(date_from)
        if sales_data:
            excel_file = g_sales_report_excel(sales_data)
            with open(excel_file, "rb") as file:
                await context.bot.send_document(chat_id=update.effective_chat.id, document=file)
            await update.message.reply_text("Отчет по продажам успешно сформирован.")
        else:
            await update.message.reply_text("Нет данных по продажам за выбранный период.")
    except Exception as e:
        logging.error(f"Error in get_sales_data_command: {e}")
        await update.message.reply_text("Произошла ошибка при получении данных о продажах. Попробуйте позже.")


# Команда для генерации и отправки итогового отчета
async def get_final_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Установка временной зоны Московского времени
    moscow_tz = pytz.timezone('Europe/Moscow')
    current_time = datetime.now(moscow_tz)

    # Указание временных диапазонов
    date_from = '2024-09-01'
    date_to = '2024-10-31'

    try:
        # Генерация итогового отчета
        excel_file, logistics_total = await create_final_report(date_from, date_to)

        # Проверка, если файл не был создан
        if excel_file is None:
            raise ValueError("Не удалось создать итоговый отчет. Проверьте логи для получения подробной информации.")

        # Отправка отчета пользователю
        with open(excel_file, "rb") as file:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=file)

        # Отправка суммы логистики
        await update.message.reply_text(f"Логистические расходы: {logistics_total:.2f} руб.")

    except Exception as e:
        logging.error(f"Ошибка при генерации итогового отчета: {e}")
        await update.message.reply_text("Произошла ошибка при создании итогового отчета.")


def main():
    application = ApplicationBuilder().token(f"{BOT_KEY}").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CommandHandler("get_orders_data", get_orders_data_command))

    scheduler.start()
    application.run_polling()

if __name__ == '__main__':
    main()
