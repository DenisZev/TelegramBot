import logging
from typing import Dict, Any
from telegram import Bot
from config import BOT_KEY, CHAT_ID
from wildberries_api import fetch_product_info
from barcode_gen import generate_barcode

logging.basicConfig(level=logging.INFO)

async def send_notification(order_id: str, task: Dict[str, Any]) -> None:
    """
    Отправляет уведомление о новом заказе пользователю.

    :param order_id: ID заказа.
    :param task: Словарь с данными о заказе.
    """
    bot = Bot(token=BOT_KEY)
    chat_id = CHAT_ID

    # Инициализация параметров по умолчанию
    product_info = await fetch_product_info(task.get('article'))
    product_name, vendor_code, brand = "Не указано", "Не указано", "Не указано"
    selected_sku, selected_size, photo_link = "Не указано", "Не указано", "Фото отсутствует."

    # Обработка информации о продукте
    try:
        if product_info and product_info.get('cards'):
            product = product_info['cards'][0]
            product_name = product.get('title', product_name)
            vendor_code = product.get('vendorCode', vendor_code)
            brand = product.get('brand', brand)

            sizes = product.get('sizes', [])
            chrt_id = task.get('chrtId')

            # Определяем SKU и размер
            for size in sizes:
                if size.get('chrtID') == chrt_id:
                    selected_sku = size.get('skus', [''])[0]
                    selected_size = size.get('wbSize', selected_size)
                    break

            # Фото товара
            photos = product.get('photos', [])
            photo_link = photos[0]['big'] if photos else photo_link
    except Exception as e:
        logging.error(f"Ошибка при обработке информации о продукте: {e}")

    # Форматируем цену
    price = task.get('price', 0)
    converted_price = task.get('convertedPrice', price)
    sale_price = converted_price if isinstance(converted_price, (int, float)) else price
    formatted_price = f"{sale_price // 100},{sale_price % 100:02d}"

    try:
        # Генерация PDF с баркодом
        pdf_data = await generate_barcode(selected_sku, product_name, vendor_code, brand, selected_size)
    except Exception as e:
        logging.error(f"Ошибка при генерации баркода: {e}")
        pdf_data = None

    # Формирование сообщения
    message = (
        f"Новый заказ!\n"
        f"ID: {order_id}\n"
        f"Артикул: {vendor_code}\n"
        f"Название: {product_name}\n"
        f"{f'Размер: {selected_size}' if selected_size else ''}\n"
        f"Баркод: {selected_sku}\n"
        f"Цена: {formatted_price} руб.\n"
        f"Фото: {photo_link}\n"
    )

    try:
        # Отправка сообщения в Telegram
        await bot.send_message(chat_id=chat_id, text=message)

        # Отправка PDF с баркодом
        if pdf_data:
            pdf_data.seek(0)
            await bot.send_document(
                chat_id=chat_id,
                document=pdf_data,
                filename='barcode.pdf',
                caption="Этикетка с баркодом",
            )
        else:
            await bot.send_message(chat_id=chat_id, text="Не удалось сгенерировать этикетку.")
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления в Telegram: {e}")
        await bot.send_message(chat_id=chat_id, text="Произошла ошибка при обработке заказа.")

