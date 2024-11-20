import logging
import aiohttp
from aiohttp import ClientTimeout
import asyncio
from config import API_KEY, BASE_URL, API_KEY_CONTENT, CONTENT_URL, API_KEY_STATISTICS

# Обработчик тайм-аутов
DEFAULT_TIMEOUT = 10

async def fetch_data(url, headers, params=None, timeout=DEFAULT_TIMEOUT):
    """Общая асинхронная функция для выполнения GET-запроса к API."""
    logging.info(f"Sending GET request to {url} with params: {params}")
    timeout = ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                logging.info(f"API response data: {data}")
                return data
        except aiohttp.ClientError as e:
            logging.error(f"Request failed: {str(e)} to {url}")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {str(e)}")
            return None

# Функция для получения информации о товаре по артикулу
async def fetch_product_info(article):
    timeout = ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        url = f"{CONTENT_URL}/list"
        headers = {
            "Authorization": f"Bearer {API_KEY_CONTENT}",
            "Content-Type": "application/json",
        }
        body = {
            "settings": {
                "cursor": {"limit": 100},
                "filter": {
                    "textSearch": article,
                    "withPhoto": -1
                }
            }
        }
        logging.info(f"Fetching product info for article: {article}")
        try:
            async with session.post(url, headers=headers, json=body) as response:
                response.raise_for_status()
                data = await response.json()
                logging.info(f"Successfully fetched product info for article: {article}")
                return data
        except aiohttp.ClientError as e:
            logging.error(f"Request failed: {str(e)} for article {article}")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {str(e)}")
            return None

# Получение новых заказов
async def get_orders():
    url = f"{BASE_URL}/orders/new"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    data = await fetch_data(url, headers)
    if not data:
        logging.error("Нет данных от API.")
        return []

    orders = data.get('orders', [])
    if not isinstance(orders, list):
        logging.warning("Полученные данные не являются списком.")
        return []

    logging.info(f"Получено {len(orders)} новых заказов.")
    return orders

# Получение данных по сборочным заданиям
async def get_assembly_tasks(limit=100, next=0, date_from=None, date_to=None):
    url = f"{BASE_URL}/orders"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    params = {"limit": limit, "next": next}

    if date_from:
        params["dateFrom"] = date_from
    if date_to:
        params["dateTo"] = date_to

    data = await fetch_data(url, headers, params)
    if not data or 'orders' not in data:
        raise Exception("Не удалось найти ключ 'orders' в ответе.")
    return data

# Получение данных по складу
async def get_stock_data(date_from):
    url = "https://statistics-api.wildberries.ru/api/v1/supplier/stocks"
    headers = {
        "Authorization": f"Bearer {API_KEY_STATISTICS}",

    }

    params = {"dateFrom": date_from}

    try:
        async with aiohttp.ClientSession() as session:
            # Отправляем асинхронный GET запрос
            async with session.get(url, headers=headers, params=params) as response:
                # Проверка статуса ответа
                if response.status != 200:
                    logging.error(f"API request failed with status code {response.status}: {await response.text()}")
                    return None

                # Обрабатываем полученные данные
                data = await response.json()  # Парсим JSON ответ
                return data

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None

# Получение отчета по продажам
async def get_sales_report(date_from, date_to, rrdid=0):
    url = "https://statistics-api.wildberries.ru/api/v5/supplier/reportDetailByPeriod"
    headers = {"Authorization": f"Bearer {API_KEY_STATISTICS}"}
    params = {"dateFrom": date_from, "dateTo": date_to, "rrdid": rrdid}
    data = []

    while True:
        response = await fetch_data(url, headers, params)
        if response:
            data.extend(response)
            if len(response) < 100000:
                break
            params["rrdid"] = response[-1]["rrd_id"]
        else:
            break
    return data

# Получение данных по заказам
async def get_orders_data(date_from, date_to):
    url = "https://statistics-api.wildberries.ru/api/v1/supplier/orders"
    headers = {"Authorization": f"Bearer {API_KEY_STATISTICS}"}
    params = {"dateFrom": date_from, "dateTo": date_to}
    response = await fetch_data(url, headers, params)
    return response if response else []

# Получение данных по продажам
async def get_sales_data(date_from):
    url = "https://statistics-api.wildberries.ru/api/v1/supplier/sales"
    headers = {"Authorization": f"Bearer {API_KEY_STATISTICS}"}
    params = {"dateFrom": date_from, "flag": 0}
    data = []

    while True:
        response = await fetch_data(url, headers, params)
        if response:
            data.extend(response)
            if len(response) < 100000:
                break
            params["rrdid"] = response[-1]["rrd_id"]
        else:
            break

    return data
