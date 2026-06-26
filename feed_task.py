import xml.etree.ElementTree as ET
from datetime import datetime

import unittest


# Исходные данные
CATEGORIES = [
    {"id": 1, "name": "Чай", "is_active": True},
    {"id": 2, "name": "Посуда", "is_active": True},
    {"id": 3, "name": "Подарочные наборы", "is_active": False},
]

PRODUCTS = [
    {
        "id": 101,
        "name": 'Чай "Лес & травы" <сбор №1>',
        "slug": "les-i-travy",
        "category_id": 1,
        "price": "490.00",
        "old_price": "590.00",
        "stock": 12,
        "description": "Вкус: мята & чабрец > классический чай",
        "image_url": "https://example.test/media/tea-101.jpg",
        "is_active": True,
    },
    {
        "id": 102,
        "name": "Чайник стеклянный",
        "slug": "glass-teapot",
        "category_id": 2,
        "price": "1500.00",
        "old_price": "1400.00",
        "stock": 0,
        "description": "Стеклянный чайник объёмом 800 мл",
        "image_url": "https://example.test/media/teapot-102.jpg",
        "is_active": True,
    },
    {
        "id": 103,
        "name": "Скрытый товар",
        "slug": "hidden-product",
        "category_id": 1,
        "price": "350.00",
        "old_price": None,
        "stock": 5,
        "description": "Товар отключён администратором",
        "image_url": "https://example.test/media/product-103.jpg",
        "is_active": False,
    },
    {
        "id": 104,
        "name": "Пробник чая",
        "slug": "tea-sample",
        "category_id": 1,
        "price": "0.00",
        "old_price": None,
        "stock": 30,
        "description": "Бесплатный пробник",
        "image_url": "https://example.test/media/product-104.jpg",
        "is_active": True,
    },
    {
        "id": 105,
        "name": "Чашка фарфоровая",
        "slug": "porcelain-cup",
        "category_id": 2,
        "price": "700.00",
        "old_price": "900.00",
        "stock": 4,
        "description": "Фарфоровая чашка",
        "image_url": None,
        "is_active": True,
    },
    {
        "id": 106,
        "name": "Подарочный набор",
        "slug": "gift-set",
        "category_id": 3,
        "price": "2500.00",
        "old_price": "3000.00",
        "stock": 2,
        "description": "Товар находится в неактивной категории",
        "image_url": "https://example.test/media/product-106.jpg",
        "is_active": True,
    },
    {
        "id": 107,
        "name": "Чай улун молочный",
        "slug": "milk-oolong",
        "category_id": 1,
        "price": "700.50",
        "old_price": None,
        "stock": 3,
        "description": "",
        "image_url": "https://example.test/media/product-107.jpg",
        "is_active": True,
    },
]


def build_yml(products, categories, generated_at):
    if isinstance(generated_at, datetime):
        date_str = generated_at.strftime('%Y-%m-%d %H:%M')
    else:
        date_str = str(generated_at)

    categories_activity = {cat['id']: cat.get('is_active', True) for cat in categories}
    
    categories_names = {cat['id']: cat['name'] for cat in categories}

    valid_offers = []
    used_category_ids = set()

    for prod in products:
        # Товар активен
        if not prod.get('is_active', True):
            continue
            
        # Категория товара активна
        cat_id = prod.get('category_id')
        if not categories_activity.get(cat_id, False):
            continue

        # Название товара присутствует и не пустое
        name = prod.get('name')
        if not name or not str(name).strip():
            continue

        # Цена товара больше нуля
        try:
            price_val = float(prod.get('price'))
        except (ValueError, TypeError):
            continue
        if price_val <= 0:
            continue

        # Ссылка на изображение указана и валидна
        image_url = prod.get('image_url')
        if not image_url or not (image_url.startswith('http://') or image_url.startswith('https://')):
            continue

        # Товар полностью валиден — сохраняем данные для фида
        valid_offers.append((prod, price_val, image_url, name, cat_id))
        
        used_category_ids.add(cat_id)

    # Строим XML структуру
    yml_catalog = ET.Element('yml_catalog', date=date_str)
    shop = ET.SubElement(yml_catalog, 'shop')

    ET.SubElement(shop, 'name').text = "Test Shop"
    ET.SubElement(shop, 'company').text = "Test Company"
    ET.SubElement(shop, 'url').text = "https://example.test"

    currencies = ET.SubElement(shop, 'currencies')
    ET.SubElement(currencies, 'currency', id='RUB', rate='1')

    # Выводим только категории, содержащие хотя бы один товар в фиде (без дублей)
    categories_elem = ET.SubElement(shop, 'categories')
    for cat_id in sorted(used_category_ids):
        cat_node = ET.SubElement(categories_elem, 'category', id=str(cat_id))
        cat_node.text = str(categories_names.get(cat_id))

    # Предложения
    offers_elem = ET.SubElement(shop, 'offers')

    # Сортируем предложения в блоке offers по id товара (prod['id'])
    valid_offers_sorted = sorted(valid_offers, key=lambda x: x[0]['id'])

    for prod, price_val, image_url, name, cat_id in valid_offers_sorted:
        available_str = 'true' if prod.get('stock', 0) > 0 else 'false'
        offer = ET.SubElement(offers_elem, 'offer', id=str(prod['id']), available=available_str)

        ET.SubElement(offer, 'url').text = f"https://example.test/products/{prod['slug']}/"
        ET.SubElement(offer, 'price').text = f"{price_val:.2f}"

        old_price_val = None
        try:
            if prod.get('old_price') is not None:
                old_price_val = float(prod.get('old_price'))
        except (ValueError, TypeError):
            old_price_val = None

        if old_price_val and old_price_val > 0 and old_price_val > price_val:
                ET.SubElement(offer, 'oldprice').text = f"{old_price_val:.2f}"

        ET.SubElement(offer, 'currencyId').text = 'RUB'
        ET.SubElement(offer, 'categoryId').text = str(cat_id)
        ET.SubElement(offer, 'picture').text = str(image_url)
        ET.SubElement(offer, 'name').text = str(name)
        
        if prod.get('description'):
            ET.SubElement(offer, 'description').text = str(prod['description'])

    xml_bytes = ET.tostring(yml_catalog, encoding='utf-8')
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_bytes.decode('utf-8')


if __name__ == "__main__":
    # 1. Запуск основной функции
    print("Запуск генерации YML фида...")
    result = build_yml(PRODUCTS, CATEGORIES, datetime.now())
    print("result =", result)
    print("Функция build_yml успешно завершила работу.\n")
    
    # 2. Автоматический программный запуск тестов
    print("=" * 60)
    print("АВТОМАТИЧЕСКИЙ ЗАПУСК ТЕСТОВ ИЗ ФАЙЛА tests.py")
    print("=" * 60)

    from tests import TestYmlFeed
    
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestYmlFeed)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
