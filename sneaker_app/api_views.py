from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count
from .models import Catalog, Order, Reviews, Category, Clients
from .filters import CatalogFilter, ReviewFilter
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
    queryset = Catalog.objects.select_related('product_card').filter(is_active=True)
    serializer_class = CatalogSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    # ✅ ФИЛЬТРАЦИЯ И ПОИСК
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CatalogFilter  # ✅ ИСПОЛЬЗУЕМ КАСТОМНЫЙ ФИЛЬТР
    search_fields = ['brand', 'product_card__name', 'product_card__color', 'product_card__description']
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

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """
        ✅ НОВЫЙ ЭНДПОИНТ: /api/products/1/history/
        История изменений конкретного товара
        """
        product = self.get_object()
        history = product.history.all()
        
        history_data = []
        for record in history:
            history_data.append({
                'history_id': record.history_id,
                'history_date': record.history_date,
                'history_type': record.get_history_type_display(),
                'brand': record.brand,
                'price': str(record.price),
                'is_active': record.is_active,
                'history_user': record.history_user.username if record.history_user else 'Система'
            })
        
        return Response({
            'product_id': product.sneakers_id,
            'current_brand': product.brand,
            'history_count': len(history_data),
            'history': history_data
        })

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
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """
        ✅ НОВЫЙ ЭНДПОИНТ: /api/reviews/1/history/
        История изменений конкретного отзыва
        """
        review = self.get_object()
        history = review.history.all()
        
        history_data = []
        for record in history:
            history_data.append({
                'history_id': record.history_id,
                'history_date': record.history_date,
                'history_type': record.get_history_type_display(),
                'rating': record.rating,
                'comment': record.comment[:100] + '...' if len(record.comment) > 100 else record.comment,
                'is_approved': record.is_approved,
                'history_user': record.history_user.username if record.history_user else 'Система'
            })
        
        return Response({
            'review_id': review.review_id,
            'current_rating': review.rating,
            'history_count': len(history_data),
            'history': history_data
        })


class ClientViewSet(viewsets.ModelViewSet):
    """
    ✅ API для клиентов
    GET /api/clients/ - список клиентов
    GET /api/clients/1/ - конкретный клиент
    POST /api/clients/ - создать клиента
    PUT /api/clients/1/ - обновить клиента
    DELETE /api/clients/1/ - удалить клиента
    """
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]  # ✅ ТОЛЬКО АВТОРИЗОВАННЫЕ
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email']
    ordering_fields = ['registration_date', 'first_name']
    ordering = ['-registration_date']
    
    def get_queryset(self):
        """
        ✅ ФИЛЬТРАЦИЯ ПО ТЕКУЩЕМУ ПОЛЬЗОВАТЕЛЮ
        Каждый пользователь видит только свои данные
        """
        user = self.request.user
        
        # Если суперпользователь - видит всех
        if user.is_superuser:
            return Clients.objects.all()
        
        # Обычный пользователь видит только себя
        return Clients.objects.filter(email=user.email)

    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """
        ✅ ОТЗЫВЫ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ
        /api/clients/my_reviews/
        """
        user = request.user
        try:
            client = Clients.objects.get(email=user.email)
            reviews = Reviews.objects.filter(client=client)
            serializer = ReviewSerializer(reviews, many=True, context={'request': request})
            
            return Response({
                'client': f"{client.first_name} {client.last_name}",
                'reviews_count': reviews.count(),
                'reviews': serializer.data
            })
        except Clients.DoesNotExist:
            return Response({'error': 'Профиль клиента не найден'}, status=404)

    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        """
        ✅ ЗАКАЗЫ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ
        /api/clients/my_orders/
        """
        user = request.user
        try:
            client = Clients.objects.get(email=user.email)
            orders = Order.objects.filter(client=client).order_by('-order_date')
            
            orders_data = []
            for order in orders:
                orders_data.append({
                    'order_id': order.order_id,
                    'order_date': order.order_date,
                    'status': order.status,
                    'total_amount': str(order.total_amount)
                })
            
            return Response({
                'client': f"{client.first_name} {client.last_name}",
                'orders_count': orders.count(),
                'orders': orders_data
            })
        except Clients.DoesNotExist:
            return Response({'error': 'Профиль клиента не найден'}, status=404)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class ProductsByBrandView(APIView):
    """
    ✅ ФИЛЬТРАЦИЯ ПО БРЕНДУ ЧЕРЕЗ URL
    /api/products/brand/Nike/
    """
    def get(self, request, brand_name):
        products = Catalog.objects.filter(
            brand__icontains=brand_name,
            is_active=True
        ).order_by('-created_at')
        
        serializer = CatalogSerializer(products, many=True, context={'request': request})
        return Response({
            'brand': brand_name,
            'count': products.count(),
            'results': serializer.data
        })

class ProductsByPriceRangeView(APIView):
    """
    ✅ ФИЛЬТРАЦИЯ ПО ДИАПАЗОНУ ЦЕН ЧЕРЕЗ URL
    /api/products/price-range/10000/50000/
    """
    def get(self, request, min_price, max_price):
        products = Catalog.objects.filter(
            price__gte=min_price,
            price__lte=max_price,
            is_active=True
        ).order_by('price')
        
        serializer = CatalogSerializer(products, many=True, context={'request': request})
        return Response({
            'price_range': f'{min_price} - {max_price} руб',
            'count': products.count(),
            'results': serializer.data
        })

class ReviewsByRatingView(APIView):
    """
    ✅ ФИЛЬТРАЦИЯ ПО РЕЙТИНГУ ЧЕРЕЗ URL
    /api/reviews/rating/5/
    """
    def get(self, request, rating):
        if rating < 1 or rating > 5:
            return Response(
                {'error': 'Рейтинг должен быть от 1 до 5'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reviews = Reviews.objects.filter(
            rating=rating,
            is_approved=True
        ).order_by('-created_date')
        
        serializer = ReviewSerializer(reviews, many=True, context={'request': request})
        return Response({
            'rating': rating,
            'count': reviews.count(),
            'results': serializer.data
        })
