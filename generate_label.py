import aiohttp
import httpx
import logging
import certifi
ETIKETKA_API_URL = "https://etiketka.wbcon.su/put"


async def generate_label(barcode, product_name, article, brand, color):
    """Генерирует этикетку с баркодом товара и возвращает ссылку на файл."""
    url = "https://etiketka.wbcon.su/put"  # Эндпоинт для генерации этикетки

    # Данные для запроса
    data = {
        "viewBarcode": True,  # Если нужно отображать штрихкод
        "barcode": barcode,
        "name": product_name,
        "article": article,
        "manuf_name": "ИП Зеваев Д.В.",
        "brand": brand,
        "color": color,
        "font_size": 11,
        "width": 58,
        "height": 40
    }

    # Заголовки запроса
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(verify=certifi.where()) as client:
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()  # Проверка на успешный статус ответа

            # Обработка ответа
            result = response.json()
            return result.get('link')  # Возвращаем ссылку на файл с этикеткой

    except httpx.HTTPStatusError as e:
        logging.error(f"Ошибка при генерации этикетки: {e.response.text}")
        return None
    except Exception as e:
        logging.error(f"Неизвестная ошибка при генерации этикетки: {e}")
        return None