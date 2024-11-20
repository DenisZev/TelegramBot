"""
Файл для настройки логирования событий в боте.
"""

import logging

# Настройка логирования
logging.basicConfig(filename='bot.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

def log_info(message):
    """
    Записывает информационное сообщение в лог.

    Args:
        message (str): Сообщение для записи.
    """
    logging.info(message)

def log_error(message):
    """
    Записывает сообщение об ошибке в лог.

    Args:
        message (str): Сообщение для записи.
    """
    logging.error(message)