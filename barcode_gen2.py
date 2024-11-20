import io
import os
import barcode
from barcode.writer import ImageWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import asyncio

# Регистрация шрифта Arial
pdfmetrics.registerFont(TTFont('Arial', 'arialmt.ttf'))

async def generate_barcode(sku, product_name, article, brand):
    # Увеличенные размеры этикетки в дюймах
    width_inch = 2.40  # 58 мм
    height_inch = 1.57  # 40 мм  # Увеличиваем высоту для текста

    # Генерация баркода в формате PNG (векторное изображение)
    code128 = barcode.get('code128', str(sku), writer=ImageWriter())

    # Сохранение баркода в временный файл
    temp_barcode_path = "temp_barcode"
    code128.save(temp_barcode_path)

    # Проверка, был ли создан файл
    full_temp_barcode_path = f"{temp_barcode_path}.png"
    if not os.path.exists(full_temp_barcode_path):
        print(f"Не удалось создать файл: {full_temp_barcode_path}")
        return None

    # Создаем PDF с размерами этикетки
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=(width_inch *inch, height_inch* inch))

    # Устанавливаем шрифт Arial
    c.setFont("Arial", 10)  # Уменьшаем размер шрифта

    # Функция для переноса текста
    def draw_multiline_text(c, text, x, y, max_width, line_height):
        words = text.split(' ')
        current_line = ''
        current_y = y

        for word in words:
            # Проверяем ширину текущей строки
            if c.stringWidth(current_line + word, "Arial", 10) < max_width:
                current_line += word + ' '
            else:
                c.drawString(x, current_y, current_line)
                current_line = word + ' '
                current_y -= line_height

        # Рисуем последнюю строку
        if current_line:
            c.drawString(x, current_y, current_line)

    # Добавляем текст на PDF
    texts = [
        "ИП Зеваев Д.В.",
        f"Наименование: {product_name}",
        f"Артикул: {article}",
        f"Бренд: {brand}",
    ]

    current_height = height_inch - 0.2  # Начинаем от верхней части с отступом
    for text in texts:
        text_width = c.stringWidth(text, "Arial", 10)
        c.drawString((width_inch

*inch - text_width) / 2, current_height*

 inch, text)
        current_height -= 0.1  # Уменьшаем высоту для следующей строки

    # Вставляем PNG с баркодом в основной PDF
    barcode_height = 1  # Высота для баркода в дюймах (примерно)
    c.drawImage(full_temp_barcode_path, (width_inch *inch - 100) / 2, current_height* inch - barcode_height * inch, width=100, height=65)

    c.save()  # Сохраняем PDF

    # Удаляем временный файл
    os.remove(full_temp_barcode_path)

    pdf_buffer.seek(0)  # Сбрасываем указатель буфера на начало

    return pdf_buffer

async def main():
    # Примерные данные для теста
    sku = "123456789012"
    product_name = "Примерный продукт"
    article = "ART-001"
    brand = "Бренд XYZ"

    # Генерация PDF с этикеткой
    pdf_buffer = await generate_barcode(sku, product_name, article, brand)

    # Если PDF не был сгенерирован, выходим
    if pdf_buffer is None:
        return

    # Сохранение PDF в файл
    with open("test_label.pdf", "wb") as f:
        f.write(pdf_buffer.getvalue())

    print("Этикетка успешно сгенерирована и сохранена как test_label.pdf")

if __name__ == '__main__':
    asyncio.run(main())