import django_filters
from .models import Catalog, Reviews
from django.db.models import Q

class CatalogFilter(django_filters.FilterSet):
    # ✅ ДИАПАЗОН ЦЕН
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    price_range = django_filters.RangeFilter(field_name='price')
    
    # ✅ ФИЛЬТР ПО ДАТЕ
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    created_range = django_filters.DateRangeFilter(field_name='created_at')
    
    # ✅ ПОИСК ПО БРЕНДУ (нечувствительный к регистру)
    brand = django_filters.CharFilter(field_name='brand', lookup_expr='icontains')
    
    class Meta:
        model = Catalog
        fields = ['is_active', 'brand', 'min_price', 'max_price']

class ReviewFilter(django_filters.FilterSet):
    # ✅ ФИЛЬТР ПО РЕЙТИНГУ
    rating = django_filters.NumberFilter(field_name='rating', lookup_expr='exact')
    min_rating = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
    
    # ✅ ФИЛЬТР ПО БРЕНДУ ТОВАРА
    brand = django_filters.CharFilter(field_name='sneakers__brand', lookup_expr='icontains')
    
    # ✅ ФИЛЬТР ПО ДАТЕ
    created_after = django_filters.DateFilter(field_name='created_date', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_date', lookup_expr='lte')
    
    # ✅ КАСТОМНЫЙ ФИЛЬТР ПО ИМЕНИ КЛИЕНТА
    client_name = django_filters.CharFilter(method='filter_client_name')
    
    def filter_client_name(self, queryset, name, value):
        return queryset.filter(
            Q(client__first_name__icontains=value) |
            Q(client__last_name__icontains=value)
        )
    
    class Meta:
        model = Reviews
        fields = ['rating', 'is_approved', 'brand']