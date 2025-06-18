from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, DateTimeWidget, BooleanWidget
from django.db.models import Avg, Count
from .models import Catalog, Order, Reviews, Clients, ProductCards

class CatalogResource(resources.ModelResource):
    """
    ✅ РЕСУРС ДЛЯ ЭКСПОРТА КАТАЛОГА ТОВАРОВ
    """
    # ✅ КАСТОМНЫЕ ПОЛЯ
    average_rating = fields.Field(attribute='average_rating', readonly=True)
    reviews_count = fields.Field(attribute='reviews_count', readonly=True)
    status_display = fields.Field(attribute='status_display', readonly=True)
    formatted_price = fields.Field(attribute='formatted_price', readonly=True)
    
    class Meta:
        model = Catalog
        fields = (
            'sneakers_id', 'brand', 'price', 'formatted_price', 
            'is_active', 'status_display', 'created_at', 
            'average_rating', 'reviews_count'
        )
        export_order = (
            'sneakers_id', 'brand', 'formatted_price', 'status_display', 
            'created_at', 'average_rating', 'reviews_count'
        )

    def get_export_queryset(self, request):
        """
        ✅ КАСТОМИЗАЦИЯ 1: get_export_queryset
        Фильтруем только активные товары и добавляем аннотации
        """
        queryset = super().get_export_queryset(request)
        return queryset.filter(is_active=True).annotate(
            average_rating=Avg('reviews__rating'),
            reviews_count=Count('reviews')
        ).order_by('-created_at')

    def dehydrate_formatted_price(self, obj):
        """
        ✅ КАСТОМИЗАЦИЯ 2: dehydrate_{field_name}
        Форматируем цену с валютой
        """
        return f"{obj.price:,.0f} ₽".replace(',', ' ')

    def dehydrate_status_display(self, obj):
        """
        ✅ КАСТОМИЗАЦИЯ 3: dehydrate_{field_name}
        Человекочитаемый статус
        """
        return "✅ Активен" if obj.is_active else "❌ Неактивен"

    def dehydrate_average_rating(self, obj):
        """
        ✅ КАСТОМИЗАЦИЯ 4: dehydrate_{field_name}
        Форматируем рейтинг
        """
        if hasattr(obj, 'average_rating') and obj.average_rating:
            return f"{obj.average_rating:.1f} ⭐"
        return "Нет оценок"

    def dehydrate_reviews_count(self, obj):
        """
        ✅ КАСТОМИЗАЦИЯ 5: dehydrate_{field_name}
        Форматируем количество отзывов
        """
        if hasattr(obj, 'reviews_count'):
            return f"{obj.reviews_count} отзывов"
        return "0 отзывов"


class OrderResource(resources.ModelResource):
    """
    ✅ РЕСУРС ДЛЯ ЭКСПОРТА ЗАКАЗОВ
    """
    client_name = fields.Field(attribute='client_name', readonly=True)
    status_display = fields.Field(attribute='status_display', readonly=True)
    formatted_amount = fields.Field(attribute='formatted_amount', readonly=True)
    order_age_days = fields.Field(attribute='order_age_days', readonly=True)
    
    class Meta:
        model = Order
        fields = (
            'order_id', 'client_name', 'order_date', 'order_age_days',
            'total_amount', 'formatted_amount', 'status', 'status_display',
            'tracking_number'
        )
        export_order = (
            'order_id', 'client_name', 'order_date', 'formatted_amount', 
            'status_display', 'tracking_number'
        )

    def get_export_queryset(self, request):
        """
        ✅ КАСТОМИЗАЦИЯ 1: get_export_queryset
        Сортируем заказы по дате (новые первыми)
        """
        queryset = super().get_export_queryset(request)
        return queryset.select_related('client').order_by('-order_date')

    def dehydrate_client_name(self, obj):
        """
        ✅ КАСТОМИЗАЦИЯ 2: dehydrate_{field_name}
        Полное имя клиента
        """
        return f"{obj.client.last_name} {obj.client.first_name}"

    def dehydrate_status_display(self, obj):
        """
        ✅ КАСТОМИЗАЦИЯ 3: dehydrate_{field_name}
        Человекочитаемый статус заказа
        """
        status_map = {
            'pending': '⏳ Ожидает',
            'processing': '🔄 Обрабатывается',
            'shipped': '🚚 Отправлен',
            'delivered': '✅ Доставлен',
            'cancelled': '❌ Отменен'
        }
        return status_map.get(obj.status, obj.status)

    def dehydrate_formatted_amount(self, obj):
        """
        ✅ КАСТОМИЗАЦИЯ 4: dehydrate_{field_name}
        Форматированная сумма
        """
        return f"{obj.total_amount:,.0f} ₽".replace(',', ' ')

    def dehydrate_order_age_days(self, obj):
        """
        ✅ КАСТОМИЗАЦИЯ 5: dehydrate_{field_name}
        Возраст заказа в днях
        """
        from django.utils import timezone
        age = (timezone.now().date() - obj.order_date.date()).days
        return f"{age} дней назад"


class ReviewResource(resources.ModelResource):
    """
    ✅ РЕСУРС ДЛЯ ЭКСПОРТА ОТЗЫВОВ
    """
    client_name = fields.Field(attribute='client_name', readonly=True)
    product_brand = fields.Field(attribute='product_brand', readonly=True)
    rating_stars = fields.Field(attribute='rating_stars', readonly=True)
    comment_preview = fields.Field(attribute='comment_preview', readonly=True)
    approval_status = fields.Field(attribute='approval_status', readonly=True)
    
    class Meta:
        model = Reviews
        fields = (
            'review_id', 'client_name', 'product_brand', 'rating', 
            'rating_stars', 'comment_preview', 'is_approved', 
            'approval_status', 'created_date'
        )
        export_order = (
            'review_id', 'client_name', 'product_brand', 'rating_stars', 
            'comment_preview', 'approval_status', 'created_date'
        )

    def get_export_queryset(self, request):
        """
        ✅ КАСТОМИЗАЦИЯ 1: get_export_queryset
        Только одобренные отзывы, отсортированные по дате
        """
        queryset = super().get_export_queryset(request)
        return queryset.filter(is_approved=True).select_related(
            'client', 'sneakers'
        ).order_by('-created_date')

    def dehydrate_client_name(self, obj):
        """
        ✅ КАСТОМИЗАЦИЯ 2: dehydrate_{field_name}
        Полное имя клиента
        """
        return f"{obj.client.last_name} {obj.client.first_name}"

    def dehydrate_product_brand(self, obj):
        """
        ✅ КАСТОМИЗАЦИЯ 3: dehydrate_{field_name}
        Бренд товара
        """
        return obj.sneakers.brand

    def dehydrate_rating_stars(self, obj):
        """
        ✅ КАСТОМИЗАЦИЯ 4: dehydrate_{field_name}
        Рейтинг звездочками
        """
        return "⭐" * obj.rating + "☆" * (5 - obj.rating)

    def dehydrate_comment_preview(self, obj):
        """
        ✅ КАСТОМИЗАЦИЯ 5: dehydrate_{field_name}
        Превью комментария (первые 100 символов)
        """
        if len(obj.comment) > 100:
            return obj.comment[:100] + "..."
        return obj.comment

    def dehydrate_approval_status(self, obj):
        """
        ✅ КАСТОМИЗАЦИЯ 6: dehydrate_{field_name}
        Статус одобрения
        """
        return "✅ Одобрен" if obj.is_approved else "⏳ На модерации"


class ClientResource(resources.ModelResource):
    """
    ✅ РЕСУРС ДЛЯ ЭКСПОРТА КЛИЕНТОВ
    """
    full_name = fields.Field(attribute='full_name', readonly=True)
    orders_count = fields.Field(attribute='orders_count', readonly=True)
    total_spent = fields.Field(attribute='total_spent', readonly=True)
    status_display = fields.Field(attribute='status_display', readonly=True)
    
    class Meta:
        model = Clients
        fields = (
            'client_id', 'full_name', 'email', 'phone_number',
            'orders_count', 'total_spent', 'is_active', 'status_display',
            'date_joined'
        )
        export_order = (
            'client_id', 'full_name', 'email', 'phone_number',
            'orders_count', 'total_spent', 'status_display', 'date_joined'
        )

    def get_export_queryset(self, request):
        """
        ✅ КАСТОМИЗАЦИЯ 1: get_export_queryset
        Только активные клиенты с подсчетом заказов
        """
        from django.db.models import Sum
        queryset = super().get_export_queryset(request)
        return queryset.filter(is_active=True).annotate(
            orders_count=Count('client_orders'),
            total_spent=Sum('client_purchases__total_cost')
        ).order_by('-date_joined')

    def dehydrate_full_name(self, obj):
        """
        ✅ КАСТОМИЗАЦИЯ 2: dehydrate_{field_name}
        Полное имя клиента
        """
        return f"{obj.last_name} {obj.first_name}"

    def dehydrate_orders_count(self, obj):
        """
        ✅ КАСТОМИЗАЦИЯ 3: dehydrate_{field_name}
        Количество заказов
        """
        if hasattr(obj, 'orders_count'):
            return f"{obj.orders_count} заказов"
        return "0 заказов"

    def dehydrate_total_spent(self, obj):
        """
        ✅ КАСТОМИЗАЦИЯ 4: dehydrate_{field_name}
        Общая потраченная сумма
        """
        if hasattr(obj, 'total_spent') and obj.total_spent:
            return f"{obj.total_spent:,.0f} ₽".replace(',', ' ')
        return "0 ₽"

    def dehydrate_status_display(self, obj):
        """
        ✅ КАСТОМИЗАЦИЯ 5: dehydrate_{field_name}
        Статус клиента
        """
        return "✅ Активен" if obj.is_active else "❌ Неактивен"