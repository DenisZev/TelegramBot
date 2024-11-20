from apscheduler.schedulers.asyncio import AsyncIOScheduler  # Импортируем асинхронный планировщик
from wildberries_api import get_orders  # Импортируем функцию для получения заказов
from notifications import send_notification  # Импортируем функцию для отправки уведомлений
import logging
import asyncio

# Инициализируем планировщик
scheduler = AsyncIOScheduler()

# Множество для хранения ID уже отправленных заказов
sent_orders = set()

async def process_order(order_id, task):
    """Обработчик для отправки уведомлений о новом заказе."""
    try:
        await send_notification(order_id, task)  # Ждем завершения отправки уведомления
        logging.info(f"Notification sent for new order ID: {order_id}")
    except Exception as e:
        logging.error(f"Error sending notification for order ID {order_id}: {e}")


async def check_for_new_orders():
    """Проверяет наличие новых заказов и отправляет уведомления, если они есть."""
    try:
        orders = await get_orders()  # Используем await для вызова асинхронной функции get_orders

        for task in orders:  # Итерируемся по списку заказов
            order_id = task.get('id')
            if order_id not in sent_orders:  # Проверяем, был ли уже отправлен этот заказ
                await process_order(order_id, task)  # Отправляем уведомление
                sent_orders.add(order_id)  # Добавляем ID заказа в множество отправленных
            else:
                logging.info(f"Order ID {order_id} already processed, skipping.")

    except Exception as e:
        logging.error(f"Error while checking for new orders: {e}")


# Добавляем задачу в планировщик
scheduler.add_job(check_for_new_orders, 'interval', seconds=60)

# Основная асинхронная функция для запуска планировщика
async def main():
    logging.info("Starting order processing scheduler...")
    scheduler.start()  # Запуск планировщика
    while True:
        await asyncio.sleep(3600)  # Держим цикл событий активным

if __name__ == "__main__":
    asyncio.run(main())  # Запуск основного асинхронного цикла событий
