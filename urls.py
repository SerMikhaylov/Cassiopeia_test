from django.urls import path
from .views import yml_market_feed

urlpatterns = [
    path('sitemaps/market.yml', yml_market_feed, name='market_yml'),
]
