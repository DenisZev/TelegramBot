"""
Файл для обработки уведомлений о новых заказах.
Запускает поток для регулярной проверки новых заказов на Wildberries.
"""

import time
import threading
from wildberries_api import get_orders
from bot import send_update_to_user  # Предполагаем, что эта функция реализована в bot.py
from config import CHECK_INTERVAL
import logger

def check_new_orders():
    """
    Запускает бесконечный цикл, который регулярно проверяет наличие новых заказов.
    Если новые заказы обнаружены, они отправляются пользователю.
    """
    while True:
        try:
            orders = get_orders()
            if orders:  # Если есть новые заказы
                send_update_to_user(orders)
            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            logger.log_error(f"Error checking new orders: {e}")
            time.sleep(CHECK_INTERVAL)  # Пауза перед следующей попыткой

def start_order_checking():
    """
    Запускает поток для проверки новых заказов.
    """
    thread = threading.Thread(target=check_new_orders)
    thread.start()