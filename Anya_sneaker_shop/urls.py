"""
URL configuration for Anya_sneaker_shop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

"""
URL configuration for Anya_sneaker_shop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns  # ✅ Добавляем для интернационализации
from django.conf.urls.static import static
from sneaker_app.views import *

urlpatterns = [
    path("admin/", admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),  # ✅ Добавляем для переключения языков

    # Главная страница

    path('', home, name='home'),
    path('home/', home, name='home_page'),
    path('redirect-home/', redirect_to_home, name='redirect_home'),
    
    # Аутентификация  
    path('register/', user_register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('profile/', user_profile, name='profile'),

    # Товары
    path('products/', product_list, name='product_list'),
    path('product/<int:pk>/', product_detail, name='product_detail'),
    path('product/create/', product_create, name='product_create'),
    path('product/<int:pk>/edit/', product_edit, name='product_edit'),
    path('product/<int:pk>/delete/', product_delete, name='product_delete'),
    
    # Заказы
    path('product/<int:product_pk>/order/', create_order, name='create_order'),
    
    # Отзывы
    path('product/<int:product_pk>/review/create/', review_create, name='review_create'),
    path('review/<int:pk>/edit/', review_edit, name='review_edit'),
    path('review/<int:pk>/delete/', review_delete, name='review_delete'),
    path('reviews/', reviews_list, name='reviews_list'),
    
    # Избранное
    path('wishlist/', wishlist_view, name='wishlist'),
    path('product/<int:product_pk>/toggle-wishlist/', toggle_wishlist, name='toggle_wishlist'),
    # ✅ Новый URL для удаления из избранного
    path('wishlist/remove/<int:wishlist_id>/', remove_from_wishlist, name='remove_from_wishlist'),
    
    # Категории
    path('categories/', category_list, name='category_list'),
    path('category/<int:pk>/', category_detail, name='category_detail'),
    
    # Клиенты
    path('client/<int:pk>/', client_detail, name='client_detail'),
    
    # Поиск
    path('search/', search_products, name='search_products'),
    
    # Статистика
    path('statistics/', statistics_view, name='statistics'),
    
    # Дополнительные страницы
    path('about/', about_view, name='about'),
    path('contact/', contact_view, name='contact'),
    
    # API endpoints
    path('api/products/', api_products_json, name='api_products'),
    path('api/product/<int:pk>/', api_product_detail_json, name='api_product_detail'),
    
    # Демонстрационные страницы
    path('demo/orm/', demo_orm_queries, name='demo_orm'),
    
    # Товары по бренду и ценовому диапазону
    path('brand/<str:brand_name>/', brand_products, name='brand_products'),
    path('price/<int:min_price>-<int:max_price>/', price_range_products, name='price_range_products'),

 # ✅ Управление кешем (только для админов)
    path('admin-tools/cache-stats/', cache_stats, name='cache_stats'),
    path('admin-tools/clear-cache/', clear_cache, name='clear_cache'),  

    # Джанго-форма создания кроссовок
    path('product/create-django-form/', product_create_django_form, name='product_create_django_form'),

    # Лаба 4
    path('popular/', popular_products, name='popular_products'),
    path('new/', new_products, name='new_products'),

]

# Добавляем обслуживание медиа файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # ✅ Для продакшн режима
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)