from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count
from .models import Catalog, Reviews, Category, Clients
from .serializers import (
    CatalogSerializer, ReviewSerializer, 
    CategorySerializer, ClientSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ✅ API для категорий
    GET /api/categories/ - список категорий
    GET /api/categories/1/ - конкретная категория
    POST /api/categories/ - создать категорию
    PUT /api/categories/1/ - обновить категорию
    DELETE /api/categories/1/ - удалить категорию
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class CatalogViewSet(viewsets.ModelViewSet):
    """
    ✅ API для каталога товаров с фильтрацией и поиском
    GET /api/products/ - список товаров
    GET /api/products/1/ - конкретный товар
    POST /api/products/ - создать товар
    PUT /api/products/1/ - обновить товар
    DELETE /api/products/1/ - удалить товар
    """
    queryset = Catalog.objects.filter(is_active=True).select_related('product_card')
    serializer_class = CatalogSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    # ✅ ФИЛЬТРАЦИЯ И ПОИСК
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['brand', 'is_active']
    search_fields = ['brand', 'product_card__name', 'product_card__color']
    ordering_fields = ['price', 'created_at', 'brand']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Кастомная фильтрация"""
        queryset = super().get_queryset()
        
        # Фильтр по цене
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """
        ✅ КАСТОМНЫЙ ЭНДПОИНТ: /api/products/popular/
        Популярные товары с высоким рейтингом
        """
        popular_products = self.get_queryset().annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        ).filter(
            review_count__gte=1
        ).order_by('-avg_rating', '-review_count')[:10]
        
        serializer = self.get_serializer(popular_products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expensive(self, request):
        """
        ✅ КАСТОМНЫЙ ЭНДПОИНТ: /api/products/expensive/
        Дорогие товары (цена > 50000)
        """
        expensive_products = self.get_queryset().filter(price__gte=50000).order_by('-price')
        serializer = self.get_serializer(expensive_products, many=True)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ✅ API для отзывов
    GET /api/reviews/ - список отзывов
    GET /api/reviews/1/ - конкретный отзыв
    POST /api/reviews/ - создать отзыв
    PUT /api/reviews/1/ - обновить отзыв
    DELETE /api/reviews/1/ - удалить отзыв
    """
    queryset = Reviews.objects.filter(is_approved=True).select_related('client', 'sneakers')
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    # ✅ ФИЛЬТРАЦИЯ И ПОИСК
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['rating', 'sneakers__brand', 'is_approved']
    search_fields = ['comment', 'sneakers__brand', 'client__first_name']
    ordering_fields = ['rating', 'created_date']
    ordering = ['-created_date']
    
    def perform_create(self, serializer):
        """Автоматически привязываем текущего пользователя"""
        # Находим клиента по email пользователя
        try:
            client = Clients.objects.get(email=self.request.user.email)
            serializer.save(client=client)
        except Clients.DoesNotExist:
            # Если клиента нет, создаем его
            client = Clients.objects.create(
                email=self.request.user.email,
                first_name=self.request.user.first_name or 'Пользователь',
                last_name=self.request.user.last_name or 'API'
            )
            serializer.save(client=client)
    
    @action(detail=False, methods=['get'])
    def top_rated(self, request):
        """
        ✅ КАСТОМНЫЙ ЭНДПОИНТ: /api/reviews/top_rated/
        Отзывы с высоким рейтингом (4-5 звезд)
        """
        top_reviews = self.get_queryset().filter(rating__gte=4).order_by('-rating', '-created_date')
        serializer = self.get_serializer(top_reviews, many=True)
        return Response(serializer.data)


class ClientViewSet(viewsets.ModelViewSet):
    """
    ✅ API для клиентов
    GET /api/clients/ - список клиентов
    GET /api/clients/1/ - конкретный клиент
    POST /api/clients/ - создать клиента
    PUT /api/clients/1/ - обновить клиента
    DELETE /api/clients/1/ - удалить клиента
    """
    queryset = Clients.objects.filter(is_active=True)
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]  # Только для авторизованных
    
    # ✅ ФИЛЬТРАЦИЯ И ПОИСК
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['first_name', 'last_name', 'email']
    ordering_fields = ['date_joined', 'last_name']
    ordering = ['-date_joined']
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """
        ✅ КАСТОМНЫЙ ЭНДПОИНТ: /api/clients/1/reviews/
        Все отзывы конкретного клиента
        """
        client = self.get_object()
        reviews = Reviews.objects.filter(client=client, is_approved=True)
        serializer = ReviewSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def orders(self, request, pk=None):
        """
        ✅ КАСТОМНЫЙ ЭНДПОИНТ: /api/clients/1/orders/
        Все заказы конкретного клиента
        """
        client = self.get_object()
        orders_count = client.client_orders.count()
        purchases_count = client.client_purchases.count()
        
        return Response({
            'client_id': client.client_id,
            'orders_count': orders_count,
            'purchases_count': purchases_count,
            'total_activity': orders_count + purchases_count
        })

