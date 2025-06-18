from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import CatalogViewSet, ReviewViewSet, CategoryViewSet, ClientViewSet

# ✅ СОЗДАЕМ РОУТЕР ДЛЯ API
router = DefaultRouter()
router.register(r'products', CatalogViewSet, basename='product')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'clients', ClientViewSet, basename='client')

urlpatterns = [
    # ✅ API ЭНДПОИНТЫ
    path('', include(router.urls)),
    
    # ✅ ДОПОЛНИТЕЛЬНЫЕ API ЭНДПОИНТЫ
    path('auth/', include('rest_framework.urls')),  # Авторизация через DRF
]

# ✅ ДОСТУПНЫЕ API ЭНДПОИНТЫ:
"""
GET    /api/products/           - Список товаров
GET    /api/products/1/         - Конкретный товар
POST   /api/products/           - Создать товар
PUT    /api/products/1/         - Обновить товар
DELETE /api/products/1/         - Удалить товар
GET    /api/products/popular/   - Популярные товары
GET    /api/products/expensive/ - Дорогие товары

GET    /api/reviews/            - Список отзывов
GET    /api/reviews/1/          - Конкретный отзыв
POST   /api/reviews/            - Создать отзыв
PUT    /api/reviews/1/          - Обновить отзыв
DELETE /api/reviews/1/          - Удалить отзыв
GET    /api/reviews/top_rated/  - Топ отзывы

GET    /api/categories/         - Список категорий
GET    /api/categories/1/       - Конкретная категория
POST   /api/categories/         - Создать категорию
PUT    /api/categories/1/       - Обновить категорию
DELETE /api/categories/1/       - Удалить категорию

GET    /api/clients/            - Список клиентов
GET    /api/clients/1/          - Конкретный клиент
POST   /api/clients/            - Создать клиента
PUT    /api/clients/1/          - Обновить клиента
DELETE /api/clients/1/          - Удалить клиента
GET    /api/clients/1/reviews/  - Отзывы клиента
GET    /api/clients/1/orders/   - Заказы клиента
"""