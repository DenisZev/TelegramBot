import io
import os
import barcode
from barcode.writer import ImageWriter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# Регистрация шрифта Arial
pdfmetrics.registerFont(TTFont('Arial', 'arialmt.ttf'))

async def generate_barcode(sku, product_name, article, brand, size):
    width_inch = 2.40  # 58 мм
    height_inch = 1.57  # 40 мм

    code128 = barcode.get('code128', str(sku), writer=ImageWriter())
    temp_barcode_path = "temp_barcode"
    code128.save(temp_barcode_path)

    full_temp_barcode_path = f"{temp_barcode_path}.png"
    if not os.path.exists(full_temp_barcode_path):
        print(f"Не удалось создать файл: {full_temp_barcode_path}")
        return None

    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=(width_inch *inch, height_inch* inch))
    c.setFont("Arial", 10)

    # Функция для переноса текста
    def draw_multiline_text(c, text, x, y, max_width, line_height):
        words = text.split(' ')
        current_line = ''
        current_y = y
        lines_drawn = 0  # Счетчик линий

        for word in words:
            # Проверяем ширину текущей строки
            if c.stringWidth(current_line + word, "Arial", 10) < max_width:
                current_line += word + ' '
            else:
                c.drawString(x, current_y, current_line.strip())
                current_line = word + ' '
                current_y -= line_height
                lines_drawn += 1
                if current_y < 0:  # Проверка выхода за пределы
                    break

        # Рисуем последнюю строку
        if current_line and current_y >= 0:
            c.drawString(x, current_y, current_line.strip())
            lines_drawn += 1

        return lines_drawn  # Возвращаем количество нарисованных линий

    texts = [
        "ИП Зеваев Д.В.",
        f"{product_name}",
        f"{article}",
    ]
    if brand:
        texts.append(f"Бренд: {brand}")
    # Добавляем размер только если он задан
    if size:
        texts.append(f"Размер: {size}")

    current_height = height_inch - 0.1
    max_width = width_inch * inch - 20  # Отступы по 10 пикселей с каждой стороны
    for text in texts:
        lines_drawn = draw_multiline_text(c, text, 10, current_height *inch, max_width, 0.1* inch)
        current_height -= lines_drawn * 0.1  # Уменьшаем высоту на количество нарисованных линий

    # Вставляем PNG с баркодом в основной PDF
    barcode_height = 1
    c.drawImage(full_temp_barcode_path, (width_inch

*inch - 100) / 2, (current_height - barcode_height)*

 inch, width=90, height=65)

    c.save()
    os.remove(full_temp_barcode_path)

    pdf_buffer.seek(0)
    return pdf_buffer

