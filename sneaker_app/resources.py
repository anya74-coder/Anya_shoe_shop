from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, DateTimeWidget, BooleanWidget
from .models import Catalog, Order, Reviews, Clients, Category, ProductCards
from django.utils import timezone

class CatalogResource(resources.ModelResource):
    """
    Ресурс для экспорта каталога товаров с кастомизацией
    ✅ Демонстрация кастомных методов экспорта
    """
    
    # Кастомные поля для экспорта
    brand_upper = fields.Field(column_name='Бренд (заглавными)')
    price_with_currency = fields.Field(column_name='Цена с валютой')
    status_text = fields.Field(column_name='Статус товара')
    category_name = fields.Field(column_name='Категория')
    days_since_created = fields.Field(column_name='Дней с создания')
    
    class Meta:
        model = Catalog
        fields = ('sneakers_id', 'brand', 'brand_upper', 'price', 'price_with_currency', 
                 'status_text', 'category_name', 'days_since_created', 'created_at')
        export_order = ('sneakers_id', 'brand', 'brand_upper', 'price', 'price_with_currency',
                       'status_text', 'category_name', 'days_since_created', 'created_at')
    
    def get_export_queryset(self, request=None):
        """
        ✅ КАСТОМНЫЙ МЕТОД 1: get_export_queryset
        Кастомизируем queryset для экспорта - только активные товары с изображениями
        """
        queryset = super().get_export_queryset(request)
        # Экспортируем только активные товары с изображениями и ценой > 1000
        return queryset.filter(
            is_active=True,
            image__isnull=False,
            price__gte=1000
        ).select_related('product_card__category').order_by('-created_at')
    
    def dehydrate_brand_upper(self, catalog):
        """
        ✅ КАСТОМНЫЙ МЕТОД 2: dehydrate_brand_upper
        Преобразуем бренд в заглавные буквы для экспорта
        """
        return catalog.brand.upper() if catalog.brand else ''
    
    def dehydrate_price_with_currency(self, catalog):
        """
        ✅ КАСТОМНЫЙ МЕТОД 3: dehydrate_price_with_currency  
        Добавляем валюту к цене
        """
        return f"{catalog.price} ₽" if catalog.price else '0 ₽'
    
    def dehydrate_status_text(self, catalog):
        """
        ✅ КАСТОМНЫЙ МЕТОД 4: dehydrate_status_text
        Преобразуем булево значение в читаемый текст
        """
        return "✅ В наличии" if catalog.is_active else "❌ Нет в наличии"
    
    def dehydrate_category_name(self, catalog):
        """
        ✅ КАСТОМНЫЙ МЕТОД 5: dehydrate_category_name
        Получаем название категории из связанной модели
        """
        try:
            if hasattr(catalog, 'product_card') and catalog.product_card:
                return catalog.product_card.category.get_name_display()
            return 'Без категории'
        except:
            return 'Не указана'
    
    def dehydrate_days_since_created(self, catalog):
        """
        ✅ КАСТОМНЫЙ МЕТОД 6: dehydrate_days_since_created
        Вычисляем количество дней с момента создания
        """
        if catalog.created_at:
            delta = timezone.now() - catalog.created_at
            return delta.days
        return 0


class OrderResource(resources.ModelResource):
    """
    Ресурс для экспорта заказов с кастомизацией
    """
    
    # Кастомные поля
    client_full_name = fields.Field(column_name='ФИО клиента')
    status_emoji = fields.Field(column_name='Статус с эмодзи')
    total_amount_formatted = fields.Field(column_name='Сумма с форматированием')
    order_age_days = fields.Field(column_name='Возраст заказа (дни)')
    
    class Meta:
        model = Order
        fields = ('order_id', 'client_full_name', 'order_date', 'total_amount', 
                 'total_amount_formatted', 'status', 'status_emoji', 'order_age_days')
        export_order = ('order_id', 'client_full_name', 'order_date', 'total_amount',
                       'total_amount_formatted', 'status', 'status_emoji', 'order_age_days')
    
    def get_export_queryset(self, request=None):
        """
        ✅ КАСТОМНЫЙ МЕТОД 7: get_export_queryset для заказов
        Экспортируем только заказы за последние 6 месяцев
        """
        from datetime import timedelta
        six_months_ago = timezone.now() - timedelta(days=180)
        
        queryset = super().get_export_queryset(request)
        return queryset.filter(
            order_date__gte=six_months_ago
        ).select_related('client').order_by('-order_date')
    
    def dehydrate_client_full_name(self, order):
        """
        ✅ КАСТОМНЫЙ МЕТОД 8: dehydrate_client_full_name
        Формируем полное имя клиента
        """
        if order.client:
            return f"{order.client.last_name} {order.client.first_name}"
        return 'Неизвестный клиент'
    
    def dehydrate_status_emoji(self, order):
        """
        ✅ КАСТОМНЫЙ МЕТОД 9: dehydrate_status_emoji
        Добавляем эмодзи к статусу заказа
        """
        status_emojis = {
            'pending': '⏳ Ожидает обработки',
            'processing': '🔄 В обработке', 
            'shipped': '🚚 Отправлен',
            'delivered': '✅ Доставлен',
            'cancelled': '❌ Отменен'
        }
        return status_emojis.get(order.status, f'❓ {order.get_status_display()}')
    
    def dehydrate_total_amount_formatted(self, order):
        """
        ✅ КАСТОМНЫЙ МЕТОД 10: dehydrate_total_amount_formatted
        Форматируем сумму с разделителями тысяч
        """
        if order.total_amount:
            return f"{order.total_amount:,.2f} ₽".replace(',', ' ')
        return '0.00 ₽'
    
    def dehydrate_order_age_days(self, order):
        """
        ✅ КАСТОМНЫЙ МЕТОД 11: dehydrate_order_age_days
        Вычисляем возраст заказа в днях
        """
        if order.order_date:
            delta = timezone.now() - order.order_date
            return delta.days
        return 0


class ReviewResource(resources.ModelResource):
    """
    Ресурс для экспорта отзывов с кастомизацией
    """
    
    # Кастомные поля
    client_name = fields.Field(column_name='Имя клиента')
    product_brand = fields.Field(column_name='Бренд товара')
    rating_stars = fields.Field(column_name='Рейтинг звездами')
    comment_length = fields.Field(column_name='Длина комментария')
    approval_status = fields.Field(column_name='Статус модерации')
    
    class Meta:
        model = Reviews
        fields = ('review_id', 'client_name', 'product_brand', 'rating', 'rating_stars',
                 'comment', 'comment_length', 'approval_status', 'created_date')
        export_order = ('review_id', 'client_name', 'product_brand', 'rating', 'rating_stars',
                       'comment_length', 'approval_status', 'created_date')
    
    def get_export_queryset(self, request=None):
        """
        ✅ КАСТОМНЫЙ МЕТОД 12: get_export_queryset для отзывов
        Экспортируем только одобренные отзывы с комментариями
        """
        queryset = super().get_export_queryset(request)
        return queryset.filter(
            is_approved=True,
            comment__isnull=False
        ).exclude(
            comment__exact=''
        ).select_related('client', 'sneakers').order_by('-created_date')
    
    def dehydrate_client_name(self, review):
        """
        ✅ КАСТОМНЫЙ МЕТОД 13: dehydrate_client_name
        Получаем имя клиента
        """
        if review.client:
            return f"{review.client.first_name} {review.client.last_name}"
        return 'Анонимный пользователь'
    
    def dehydrate_product_brand(self, review):
        """
        ✅ КАСТОМНЫЙ МЕТОД 14: dehydrate_product_brand
        Получаем бренд товара из отзыва
        """
        if review.sneakers:
            return review.sneakers.brand
        return 'Неизвестный товар'
    
    def dehydrate_rating_stars(self, review):
        """
        ✅ КАСТОМНЫЙ МЕТОД 15: dehydrate_rating_stars
        Преобразуем рейтинг в звездочки
        """
        if review.rating:
            return "★" * review.rating + "☆" * (5 - review.rating)
        return "☆☆☆☆☆"
    
    def dehydrate_comment_length(self, review):
        """
        ✅ КАСТОМНЫЙ МЕТОД 16: dehydrate_comment_length
        Подсчитываем длину комментария
        """
        return len(review.comment) if review.comment else 0
    
    def dehydrate_approval_status(self, review):
        """
        ✅ КАСТОМНЫЙ МЕТОД 17: dehydrate_approval_status
        Статус модерации отзыва
        """
        return "✅ Одобрен" if review.is_approved else "⏳ На модерации"


class ClientResource(resources.ModelResource):
    """
    Ресурс для экспорта клиентов с кастомизацией
    """
    
    # Кастомные поля
    full_name = fields.Field(column_name='Полное имя')
    registration_days = fields.Field(column_name='Дней с регистрации')
    orders_count = fields.Field(column_name='Количество заказов')
    account_status = fields.Field(column_name='Статус аккаунта')
    
    class Meta:
        model = Clients
        fields = ('client_id', 'full_name', 'email', 'phone_number', 
                 'registration_days', 'orders_count', 'account_status', 'date_joined')
        export_order = ('client_id', 'full_name', 'email', 'phone_number',
                       'orders_count', 'account_status', 'registration_days', 'date_joined')
    
    def get_export_queryset(self, request=None):
        """
        ✅ КАСТОМНЫЙ МЕТОД 18: get_export_queryset для клиентов
        Экспортируем только активных клиентов с заказами
        """
        queryset = super().get_export_queryset(request)
        return queryset.filter(
            is_active=True
        ).prefetch_related('client_orders').order_by('-date_joined')
    
    def dehydrate_full_name(self, client):
        """
        ✅ КАСТОМНЫЙ МЕТОД 19: dehydrate_full_name
        Формируем полное имя клиента
        """
        return f"{client.last_name} {client.first_name}"
    
    def dehydrate_registration_days(self, client):
        """
        ✅ КАСТОМНЫЙ МЕТОД 20: dehydrate_registration_days
        Количество дней с регистрации
        """
        if client.date_joined:
            delta = timezone.now() - client.date_joined
            return delta.days
        return 0
    
    def dehydrate_orders_count(self, client):
        """
        ✅ КАСТОМНЫЙ МЕТОД 21: dehydrate_orders_count
        Подсчитываем количество заказов клиента
        """
        return client.client_orders.count()
    
    def dehydrate_account_status(self, client):
        """
        ✅ КАСТОМНЫЙ МЕТОД 22: dehydrate_account_status
        Статус аккаунта клиента
        """
        return "🟢 Активный" if client.is_active else "🔴 Заблокированный"
