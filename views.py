from django.http import HttpResponse
from django.utils import timezone

from .models import Product, Category 
from .feed_task import build_yml 


def yml_market_feed(request):
    """
    Django-view, которая динамически формирует YML-фид на основе данных из БД.
    """
    categories_queryset = Category.objects.values('id', 'name', 'is_active')
    categories_list = list(categories_queryset)

    products_queryset = Product.objects.values(
        'id', 'name', 'slug', 'category_id', 'price', 'old_price', 'stock', 'description', 'image_url', 'is_active'
    )
    products_list = list(products_queryset)

    for prod in products_list:
        if prod['price'] is not None:
            prod['price'] = str(prod['price'])
        if prod['old_price'] is not None:
            prod['old_price'] = str(prod['old_price'])

    current_time = timezone.now()

    yml_xml_string = build_yml(products_list, categories_list, current_time)

    response = HttpResponse(yml_xml_string, content_type='application/xml')
    response['Content-Type'] = 'application/xml; charset=utf-8'
    
    return response
