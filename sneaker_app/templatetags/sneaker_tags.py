from django import template
from django.db.models import Avg, Count
from ..models import Catalog, Reviews, Category
from django.core.cache import cache  # ✅ Добавляем кеш
from sneaker_app.models import Catalog, Reviews
from django.contrib.auth.models import User
from django.db.models import Count, Avg
register = template.Library()

@register.simple_tag
def total_products():
    """Простой тег - возвращает общее количество товаров"""
    # ✅ Проверяем кеш
    cache_key = 'total_products_count'
    count = cache.get(cache_key)
    
    if count is None:
        count = Catalog.objects.filter(is_active=True).count()
        # Кешируем на 10 минут
        cache.set(cache_key, count, 60 * 10)
    
    return count

@register.simple_tag
def price_range(min_price, max_price):
    """Тег с параметрами - возвращает количество товаров в ценовом диапазоне"""
    # ✅ Создаем уникальный ключ кеша
    cache_key = f'price_range_{min_price}_{max_price}'
    count = cache.get(cache_key)
    
    if count is None:
        count = Catalog.objects.filter(
            price__gte=min_price,
            price__lte=max_price,
            is_active=True
        ).count()
        # Кешируем на 15 минут
        cache.set(cache_key, count, 60 * 15)
    
    return count

@register.inclusion_tag('sneaker_app/top_brands.html')
def show_top_brands(limit=5):
    """Inclusion тег - показывает топ брендов"""
    # ✅ Проверяем кеш
    cache_key = f'top_brands_{limit}'
    brands = cache.get(cache_key)
    
    if brands is None:
        brands = Catalog.objects.values('brand').annotate(
            count=Count('sneakers_id')
        ).filter(is_active=True).order_by('-count')[:limit]
        # Кешируем на 30 минут
        cache.set(cache_key, list(brands), 60 * 30)
    
    return {'top_brands': brands}

@register.simple_tag(takes_context=True)
def user_greeting(context):
    """Тег с контекстом - приветствие пользователя"""
    request = context['request']
    if request.user.is_authenticated:
        return f"Привет, {request.user.username}! 👋"
    return "Добро пожаловать в наш магазин! 🛍️"

@register.filter
def multiply(value, arg):
    """Фильтр - умножение"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def currency(value):
    """Фильтр - форматирование валюты"""
    try:
        return f"{float(value):,.0f} ₽".replace(',', ' ')
    except (ValueError, TypeError):
        return "0 ₽"

# ✅ Новые теги с кешированием
@register.simple_tag
def avg_product_rating():
    """Средний рейтинг всех товаров"""
    cache_key = 'avg_product_rating'
    rating = cache.get(cache_key)
    
    if rating is None:
        rating = Reviews.objects.filter(is_approved=True).aggregate(
            avg_rating=Avg('rating')
        )['avg_rating'] or 0
        # Кешируем на 20 минут
        cache.set(cache_key, round(rating, 1), 60 * 20)
    
    return rating

@register.simple_tag
def cache_status(cache_key):
    """Проверяет статус кеша по ключу"""
    return "✅ Cached" if cache.get(cache_key) is not None else "❌ Not cached"