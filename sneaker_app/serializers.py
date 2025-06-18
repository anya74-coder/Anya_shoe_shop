from rest_framework import serializers
from .models import Catalog, Reviews, Category, Clients, ProductCards
from django.core.exceptions import ValidationError


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий"""
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'product_count']
    
    def get_product_count(self, obj):
        """Подсчет количества товаров в категории"""
        return obj.product_cards.filter(sneakers__is_active=True).count()


class ProductCardSerializer(serializers.ModelSerializer):
    """Сериализатор для карточек товаров"""
    category_name = serializers.CharField(source='category.get_name_display', read_only=True)
    
    class Meta:
        model = ProductCards
        fields = [
            'id', 'name', 'size', 'category', 'category_name', 
            'color', 'material', 'description', 'official_store_url'
        ]


class CatalogSerializer(serializers.ModelSerializer):
    """Сериализатор для каталога товаров"""
    product_card = ProductCardSerializer(read_only=True)
    avg_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Catalog
        fields = [
            'sneakers_id', 'brand', 'price', 'image', 'image_url',
            'created_at', 'is_active', 'product_card', 
            'avg_rating', 'review_count'
        ]
        read_only_fields = ['sneakers_id', 'created_at']
    
    def get_avg_rating(self, obj):
        """Средний рейтинг товара"""
        reviews = obj.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / len(reviews), 1)
        return 0
    
    def get_review_count(self, obj):
        """Количество отзывов"""
        return obj.reviews.filter(is_approved=True).count()
    
    def get_image_url(self, obj):
        """Полный URL изображения"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None
    
    def validate_price(self, value):
        """✅ ВАЛИДАЦИЯ ЦЕНЫ - бизнес-логика"""
        if value <= 0:
            raise serializers.ValidationError("Цена должна быть больше нуля")
        if value > 1000000:
            raise serializers.ValidationError("Цена не может превышать 1,000,000 рублей")
        return value
    
    def validate_brand(self, value):
        """✅ ВАЛИДАЦИЯ БРЕНДА - бизнес-логика"""
        if len(value) < 2:
            raise serializers.ValidationError("Название бренда должно содержать минимум 2 символа")
        
        # Проверка на запрещенные бренды
        forbidden_brands = ['test', 'fake', 'spam']
        if value.lower() in forbidden_brands:
            raise serializers.ValidationError("Данный бренд запрещен")
        
        return value.title()
    
    def validate(self, data):
        """✅ КОМПЛЕКСНАЯ ВАЛИДАЦИЯ - бизнес-логика"""
        brand = data.get('brand')
        price = data.get('price')
        
        # Премиум бренды должны иметь высокую цену
        premium_brands = ['Nike', 'Adidas', 'Jordan', 'Balenciaga']
        if brand and price:
            if brand in premium_brands and price < 5000:
                raise serializers.ValidationError({
                    'price': f"Для премиум бренда {brand} минимальная цена должна быть 5000 рублей"
                })
        
        return data


class ClientSerializer(serializers.ModelSerializer):
    """Сериализатор для клиентов"""
    full_name = serializers.SerializerMethodField()
    orders_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Clients
        fields = [
            'client_id', 'first_name', 'last_name', 'full_name',
            'email', 'phone_number', 'date_joined', 'is_active',
            'orders_count'
        ]
        read_only_fields = ['client_id', 'date_joined']
    
    def get_full_name(self, obj):
        return f"{obj.last_name} {obj.first_name}"
    
    def get_orders_count(self, obj):
        return obj.client_orders.count()
    
    def validate_phone_number(self, value):
        """✅ ВАЛИДАЦИЯ ТЕЛЕФОНА - бизнес-логика"""
        import re
        # Убираем все символы кроме цифр и +
        cleaned_phone = re.sub(r'[^\d+]', '', value)
        
        # Проверяем формат российского номера
        if not re.match(r'^\+7\d{10}$', cleaned_phone):
            raise serializers.ValidationError("Введите корректный российский номер телефона (+7XXXXXXXXXX)")
        
        return cleaned_phone


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор для отзывов"""
    client_name = serializers.CharField(source='client.full_name', read_only=True)
    product_brand = serializers.CharField(source='sneakers.brand', read_only=True)
    rating_stars = serializers.SerializerMethodField()
    
    class Meta:
        model = Reviews
        fields = [
            'review_id', 'client', 'client_name', 'sneakers', 'product_brand',
            'rating', 'rating_stars', 'comment', 'created_date', 'is_approved'
        ]
        read_only_fields = ['review_id', 'created_date']
    
    def get_rating_stars(self, obj):
        """Звездный рейтинг"""
        if obj.rating:
            return "★" * obj.rating + "☆" * (5 - obj.rating)
        return "Нет оценки"
    
    def validate_comment(self, value):
        """✅ ВАЛИДАЦИЯ КОММЕНТАРИЯ - бизнес-логика"""
        if len(value) < 10:
            raise serializers.ValidationError("Отзыв должен содержать минимум 10 символов")
        
        # Проверяем на спам-слова
        spam_words = ['спам', 'реклама', 'купить дешево', 'скидка 90%']
        if any(word.lower() in value.lower() for word in spam_words):
            raise serializers.ValidationError("Отзыв содержит недопустимый контент")
        
        return value
    
    def validate(self, data):
        """✅ КОМПЛЕКСНАЯ ВАЛИДАЦИЯ отзывов"""
        client = data.get('client')
        sneakers = data.get('sneakers')
        
        # Проверяем, что клиент не оставлял отзыв на этот товар
        if client and sneakers:
            existing_review = Reviews.objects.filter(
                client=client, 
                sneakers=sneakers
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing_review.exists():
                raise serializers.ValidationError(
                    "Вы уже оставили отзыв на этот товар"
                )
        
        return data