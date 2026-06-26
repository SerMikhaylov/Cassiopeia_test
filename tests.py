import xml.etree.ElementTree as ET
from datetime import datetime
import unittest

# Импортируем тестируемые компоненты
from feed_task import build_yml, PRODUCTS, CATEGORIES


class TestYmlFeed(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.gen_time = datetime(2026, 6, 18, 12, 0)
        cls.xml_str = build_yml(PRODUCTS, CATEGORIES, cls.gen_time)
        cls.root = ET.fromstring(cls.xml_str)

    def test_yml_root_date_format(self):
        """Проверка требования: корневой элемент yml_catalog содержит атрибут date в формате YYYY-MM-DD hh:mm."""
        self.assertEqual(self.root.tag, 'yml_catalog')
        self.assertIn('date', self.root.attrib, "Атрибут 'date' отсутствует в корневом элементе")
        
        expected_date = '2026-06-18 12:00'
        self.assertEqual(self.root.attrib['date'], expected_date)
        self.assertTrue(
            self.xml_str.startswith(f'<?xml version="1.0" encoding="UTF-8"?>\n<yml_catalog date="{expected_date}"')
        )

    def test_yml_metadata(self):
        """Проверка корневого тега и формата даты."""
        self.assertEqual(self.root.tag, 'yml_catalog')
        self.assertEqual(self.root.attrib['date'], '2026-06-18 12:00')

    def test_yml_categories_filtering(self):
        """Проверка, что выводятся ТОЛЬКО те категории, товары из которых попали в фид."""
        categories = self.root.findall('.//category')
        
        self.assertEqual(len(categories), 2)
        
        cat_ids = [c.attrib['id'] for c in categories]
        self.assertIn('1', cat_ids)
        self.assertIn('2', cat_ids)
        self.assertNotIn('3', cat_ids)

    def test_categories_no_duplicates(self):
        """Проверка, что каждая категория присутствует только один раз."""
        categories = self.root.findall('.//category')
        cat_ids = [c.attrib['id'] for c in categories]
        
        self.assertEqual(len(cat_ids), len(set(cat_ids)), "Обнаружены дубликаты категорий в фиде!")

    def test_yml_offers_filtering(self):
        """Проверка фильтрации предложений: должны остаться ровно 3 активных товаров."""
        offers = self.root.findall('.//offer')
        self.assertEqual(len(offers), 3)
    
    def test_yml_offers_sorting_by_id(self):
        """Проверка, что товары в блоке <offers> отсортированы по возрастанию идентификатора."""
        offers = self.root.findall('.//offer')
        
        actual_ids = [int(o.attrib['id']) for o in offers]
        
        expected_sorted_ids = sorted(actual_ids)
        
        self.assertEqual(
            actual_ids, 
            expected_sorted_ids, 
            f"Порядок товаров нарушен! Ожидалось {expected_sorted_ids}, но получено {actual_ids}"
        )

    def test_yml_offer_availability(self):
        """Проверка флага available: true при stock > 0, false при stock == 0."""
        # Товар 101: stock = 12 (> 0) -> должно быть true
        offer_101 = self.root.find(".//offer[@id='101']")
        self.assertEqual(offer_101.attrib['available'], 'true')

        # Товар 102: stock = 0 -> должно быть false
        offer_102 = self.root.find(".//offer[@id='102']")
        self.assertEqual(offer_102.attrib['available'], 'false')
    
    def test_price_constraints(self):
        """Проверка, что цена больше 0, формат с двумя знаками."""
        # Проверяем, что товар с ценой 0.00 (id 104) не попал в фид
        offer_104 = self.root.find(".//offer[@id='104']")
        self.assertIsNone(offer_104, "Товар с нулевой ценой должен быть исключен из фида!")
        
        # Проверяем округление и формат для товара с копейками (id 107)
        offer_107 = self.root.find(".//offer[@id='107']")
        self.assertIsNotNone(offer_107)
        self.assertEqual(offer_107.find('price').text, '700.50')

        # Проверяем округление и формат для товара без копеек (id 101)
        offer_101 = self.root.find(".//offer[@id='101']")
        self.assertEqual(offer_101.find('price').text, '490.00')

    def test_xml_escaping(self):
        """Проверка корректного сохранения спецсимволов (&, <, >)."""
        offer_101 = self.root.find(".//offer[@id='101']")
        self.assertEqual(offer_101.find('name').text, 'Чай "Лес & травы" <сбор №1>')
        
        # Проверяем, что в сыром XML-тексте символы корректно заэкранированы
        self.assertIn('Чай "Лес &amp; травы" &lt;сбор №1&gt;', self.xml_str)

    def test_old_price_conditions(self):
        """Проверка, что старая цена убирается, если она меньше текущей цены."""
        offer_102 = self.root.find(".//offer[@id='102']")
        self.assertIsNone(offer_102.find('oldprice'))

        """Проверка, что старая цена указана и больше текущей цены."""
        offer_101 = self.root.find(".//offer[@id='101']")
        self.assertIsNotNone(offer_101.find('oldprice'))
        self.assertEqual(offer_101.find('oldprice').text, '590.00')

        """Проверка, что старая цена убирается, если она не задана в исходных данных."""
        offer_107 = self.root.find(".//offer[@id='107']")
        self.assertIsNone(offer_107.find('oldprice'))
    
    def test_yml_description_handling(self):
        """Проверка описания"""
        # Товар 101: описание имеется -> элемент <description> должен быть в фиде
        offer_101 = self.root.find(".//offer[@id='101']")
        self.assertIsNotNone(offer_101.find('description'))
        self.assertEqual(offer_101.find('description').text, "Вкус: мята & чабрец > классический чай")

        # Товар 107: описание пустое ("") -> элемента <description> не должно быть в фиде
        offer_107 = self.root.find(".//offer[@id='107']")
        self.assertIsNone(offer_107.find('description'), "Элемент <description> не должен создаваться для пустого описания")

    def test_feed_does_not_crash_on_corrupted_data(self):
        """Проверка, что фид успешно строится, даже если имеются некорректные данные (например, цена с буквами вместо цифр)."""
        bad_products = [
            {
                "id": 999,
                "name": "Сломанный товар",
                "slug": "bad",
                "category_id": 1,
                "price": "цена",  # Вызовет ValueError при float()
                "image_url": "https://example.test/img.jpg",
                "is_active": True,
            }
        ]
        # Функция должна отработать без исключений и вернуть валидный XML
        try:
            xml_result = build_yml(bad_products, CATEGORIES, datetime.now())
            root = ET.fromstring(xml_result)
            offers = root.findall('.//offer')
            self.assertEqual(len(offers), 0, "Товар с буквами вместо цены должен быть исключен")
        except Exception as e:
            self.fail(f"Генератор фида упал с ошибкой {type(e).__name__}: {e}")

if __name__ == "__main__":
    unittest.main()
    