"""
Файл для тестирования функционала Телеграмм-бота.
Использует библиотеку unittest для написания юнит-тестов.
"""

import unittest
from unittest.mock import patch
from wildberries_api import get_orders
from bot import orders_message


class TestWildberriesAPI(unittest.TestCase):

    @patch('wildberries_api.requests.get')
    def test_get_orders_success(self, mock_get):
        """Тест успешного получения заказов."""
        # Настраиваем мок для успешного ответа
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{"id": 1, "status": "новый"}, {"id": 2, "status": "выполнен"}]

        orders = get_orders()
        self.assertEqual(len(orders), 2)
        self.assertEqual(orders[0]['status'], 'новый')

    @patch('wildberries_api.requests.get')
    def test_get_orders_failure(self, mock_get):
        """Тест на случай ошибки при получении заказов."""
        # Настраиваем мок для ошибки
        mock_get.return_value.status_code = 500

        with self.assertRaises(Exception):
            get_orders()


class TestMessages(unittest.TestCase):

    def test_orders_message_empty(self):
        """Тест сообщения при отсутствии заказов."""
        result = orders_message([])
        self.assertEqual(result, "Нет новых заказов.")

    def test_orders_message_with_orders(self):
        """Тест сообщения с заказами."""
        result = orders_message([{"id": 1, "status": "новый"}])
        self.assertIn("Вот ваши новые заказы:", result)


if __name__ == '__main__':
    unittest.main()