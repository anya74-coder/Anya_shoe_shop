from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Avg, Count, Max, Min, Sum
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.cache import cache_page  # ✅ Добавляем для кеширования
from django.core.cache import cache  # ✅ Добавляем для работы с кешем
from django.views.decorators.vary import vary_on_headers  # ✅ Для варьирования кеша
from .forms import ProductForm, SearchForm
from django.contrib.admin.views.decorators import staff_member_required
from datetime import timedelta
from django.utils import timezone
from .models import (
    Category, Catalog, Clients, ProductCards, Address, Order,
    Purchase, Wishlist, Reviews, Positions, Support, Tag, ProductTag
)
from .forms import SearchForm

def redirect_to_home(request):
    """Демонстрация использования reverse"""
    home_url = reverse('home')
    return HttpResponseRedirect(home_url)

#@cache_page(60 * 15)  # ✅ Кешируем главную страницу на 15 минут
#@vary_on_headers('Accept-Language')  # ✅ Варьируем кеш по языку

def home(request):
    """
    Главная страница с 3 виджетами:
    1. Популярные кроссовки (по рейтингу и отзывам)
    2. Новые поступления (последние 30 дней)
    3. Статистика и топ-бренды
    
    ✅ ДОБАВЛЕНО: Демонстрация values_list(), exists(), update()
    """
    
# ✅ ВИДЖЕТ 1: Популярные кроссовки с комбинированным Q-запросом
    cache_key_popular = 'popular_products_widget'
    popular_products = cache.get(cache_key_popular)
    
    if popular_products is None:
        # ✅ Комбинированный Q-запрос для популярных товаров
        # Товары которые: (есть отзывы И рейтинг >= 4) И активны И НЕ дешевые И НЕ без изображения
        popular_products = Catalog.objects.filter(
            (
                Q(reviews__isnull=False) &  # есть отзывы
                Q(reviews__rating__gte=4)  # хороший рейтинг
            ) &
            Q(is_active=True) &  # AND активны
            ~Q(price__lt=5000) &  # NOT дешевые
            ~Q(image__isnull=True)  # NOT без изображения
        ).annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews', distinct=True)
        ).filter(
            review_count__gte=1
        ).order_by('-avg_rating', '-review_count')[:5]
        
        cache.set(cache_key_popular, popular_products, 60 * 15)  # 15 минут
    
    # ✅ ВИДЖЕТ 2: Новые поступления (последние 30 дней)
    cache_key_new = 'new_products_widget'
    new_products = cache.get(cache_key_new)
    
    if new_products is None:
        thirty_days_ago = timezone.now() - timedelta(days=30)
        new_products = Catalog.objects.filter(
            is_active=True,
            created_at__gte=thirty_days_ago
        ).order_by('-created_at')[:6]  # Последние 6
        
        cache.set(cache_key_new, new_products, 60 * 10)  # 10 минут
    
    # ✅ ВИДЖЕТ 3: Статистика с агрегацией и топ-бренды
    cache_key_stats = 'home_stats_widget'
    stats_data = cache.get(cache_key_stats)
    
    if stats_data is None:
        # Общая статистика с агрегацией
        stats = {
            'total_products': Catalog.objects.filter(is_active=True).count(),
            'total_brands': Catalog.objects.filter(is_active=True).values('brand').distinct().count(),
            'total_reviews': Reviews.objects.filter(is_approved=True).count(),
            'avg_rating': Reviews.objects.filter(is_approved=True).aggregate(
                avg=Avg('rating')
            )['avg'] or 0,
            'avg_price': Catalog.objects.filter(is_active=True).aggregate(
                avg=Avg('price')
            )['avg'] or 0,
            'max_price': Catalog.objects.filter(is_active=True).aggregate(
                max=Max('price')
            )['max'] or 0,
        }
        
        # Топ-3 бренда по количеству товаров
        top_brands = Catalog.objects.filter(is_active=True).values('brand').annotate(
            product_count=Count('sneakers_id'),
            avg_price=Avg('price'),
            avg_rating=Avg('reviews__rating')
        ).order_by('-product_count')[:3]
        
        stats_data = {
            'stats': stats,
            'top_brands': top_brands
        }
        
        cache.set(cache_key_stats, stats_data, 60 * 20)  # 20 минут
    
    # ✅ НОВОЕ: Демонстрация values_list()
    demo_values_list_data = {
        'brand_names_flat': list(Catalog.objects.values_list('brand', flat=True).distinct()[:8]),
        'brand_price_tuples': list(Catalog.objects.values_list('brand', 'price')[:5]),
        'price_list': list(Catalog.objects.values_list('price', flat=True)[:10]),
        'comparison': {
            'values_dict': list(Catalog.objects.values('brand', 'price')[:3]),
            'values_list_tuple': list(Catalog.objects.values_list('brand', 'price')[:3]),
        }
    }
    
    # ✅ НОВОЕ: Демонстрация exists()
    demo_exists_data = {
        'nike_exists': Catalog.objects.filter(brand__icontains='Nike').exists(),
        'expensive_exists': Catalog.objects.filter(price__gte=50000).exists(),
        'recent_exists': Catalog.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).exists(),
        'reviews_exist': Reviews.objects.filter(is_approved=True).exists(),
        'wishlist_exists': Wishlist.objects.exists(),
        'categories_exist': Category.objects.exists(),
    }
    
    # ✅ НОВОЕ: Статистика для демонстрации update()
    demo_update_stats = {
        'cheap_inactive': Catalog.objects.filter(price__lt=5000, is_active=False).count(),
        'expensive_active': Catalog.objects.filter(price__gt=100000, is_active=True).count(),
        'unapproved_reviews': Reviews.objects.filter(is_approved=False).count(),
        'old_products': Catalog.objects.filter(
            created_at__lt=timezone.now() - timedelta(days=365)
        ).count(),
    }
    
    # Форма поиска
    search_form = SearchForm()
    
    context = {
        'popular_products': popular_products,
        'new_products': new_products,
        'stats': stats_data['stats'],
        'top_brands': stats_data['top_brands'],
        'search_form': search_form,
        'user': request.user,
        
        # ✅ НОВЫЕ ДАННЫЕ для демонстрации ORM методов
        'demo_values_list': demo_values_list_data,
        'demo_exists': demo_exists_data,
        'demo_update_stats': demo_update_stats,
    }
    
    return render(request, 'home.html', context)


# функция для массовых операций update()
@staff_member_required
@require_POST
def demo_mass_update(request):
    """
    Демонстрация массовых операций update() - вызывается с главной страницы
    """
    action = request.POST.get('action')
    
    if action == 'activate_cheap':
        updated_count = Catalog.objects.filter(
            price__lt=5000, 
            is_active=False
        ).update(is_active=True)
        messages.success(request, f'✅ Активировано {updated_count} дешевых товаров (update())')
        
    elif action == 'approve_reviews':
        updated_count = Reviews.objects.filter(
            is_approved=False
        ).update(is_approved=True)
        messages.success(request, f'👍 Одобрено {updated_count} отзывов (update())')
        
    elif action == 'price_increase':
        from django.db.models import F
        updated_count = Catalog.objects.filter(
            price__lt=1000,
            is_active=True
        ).update(price=F('price') * 1.1)
        messages.success(request, f'💰 Поднята цена у {updated_count} товаров на 10% (update() + F())')
    
    return HttpResponseRedirect(reverse('home'))

@cache_page(60 * 10)
def product_list(request):
    """
    Список товаров с фильтрацией и пагинацией
    ✅ СЛОЖНЫЙ Q-ЗАПРОС 2: OR + AND + NOT
    """
    # Базовый queryset активных товаров
    queryset = Catalog.objects.filter(is_active=True)
    
    # Получаем все категории для фильтра
    categories = Category.objects.all().order_by('name')
    
    # Фильтрация по категории
    category_filter = request.GET.get('category')
    brand_filter = request.GET.get('brand')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    
    # ✅ Комбинированный Q-запрос для сложной фильтрации
    if any([category_filter, brand_filter, price_min, price_max]):
        # Строим сложный Q-запрос
        q_filter = Q()
        
        # Фильтр по категории (если указан)
        if category_filter:
            try:
                category_id = int(category_filter)
                q_filter &= Q(product_card__category_id=category_id)
            except (ValueError, TypeError):
                pass
        
        # Фильтр по бренду (если указан)
        if brand_filter:
            q_filter &= Q(brand__icontains=brand_filter)
        
        # Фильтр по цене
        if price_min:
            try:
                q_filter &= Q(price__gte=float(price_min))
            except (ValueError, TypeError):
                pass
        
        if price_max:
            try:
                q_filter &= Q(price__lte=float(price_max))
            except (ValueError, TypeError):
                pass
        
        # ✅ Применяем комбинированный фильтр с OR, AND и NOT
        # Показываем товары которые:
        # Соответствуют фильтрам И активны И НЕ без изображения И НЕ слишком дешевые
        queryset = Catalog.objects.filter(
            q_filter &  # Пользовательские фильтры
            Q(is_active=True) &  # AND активные
            ~Q(image__isnull=True) &  # NOT без изображения
            ~Q(price__lt=500)  # NOT слишком дешевые
        )
    
    # Сортировка
    sort_by = request.GET.get('sort', '-created_at')
    valid_sorts = ['-created_at', 'created_at', 'price', '-price', 'brand', '-brand']
    if sort_by in valid_sorts:
        queryset = queryset.order_by(sort_by)
    else:
        queryset = queryset.order_by('-created_at')
    
    # Статистика для отфильтрованных товаров
    stats = queryset.aggregate(
        total_products=Count('sneakers_id'),
        avg_price=Avg('price'),
        max_price=Max('price'),
        min_price=Min('price')
    )
    
    # Пагинация
    paginator = Paginator(queryset, 12)
    page = request.GET.get('page')
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    context = {
        'products': products,
        'categories': categories,
        'stats': stats,
        'current_filters': {
            'category': category_filter,
            'brand': brand_filter,
            'price_min': price_min,
            'price_max': price_max,
            'sort': sort_by,
        }
    }
    
    return render(request, 'products/product_list.html', context)


@cache_page(60 * 10)  # ✅ Кешируем каталог на 10 минут  
def catalog_list(request):
    """
    Демонстрация методов filter(), exclude(), order_by() и использования __
    """
    # ✅ Метод filter() с различными вариантами
    active_products = Catalog.objects.filter(is_active=True)
    
    # ✅ Использование __ для обращения к связанной таблице
    nike_products = Catalog.objects.filter(brand__icontains='Nike')
    
    # ✅ Использование __ для методов поля
    recent_products = Catalog.objects.filter(created_at__gte='2024-01-01')
    expensive_products = Catalog.objects.filter(price__gte=10000)
    
    # ✅ Метод exclude()
    not_nike_products = Catalog.objects.exclude(brand__icontains='Nike')
    cheap_products = Catalog.objects.exclude(price__gte=10000)
    
    # ✅ Метод order_by()
    products_by_price = Catalog.objects.order_by('price')
    products_by_price_desc = Catalog.objects.order_by('-price')
    products_by_brand_and_price = Catalog.objects.order_by('brand', 'price')
    
    # ✅ Использование собственного модельного менеджера
    active_catalog = Catalog.objects.active()
    expensive_catalog = Catalog.objects.expensive()
    
    # ✅ Функция агрегирования
    stats = Catalog.objects.aggregate(
        avg_price=Avg('price'),
        max_price=Max('price'),
        min_price=Min('price'),
        total_products=Count('sneakers_id')
    )
    
    # Фильтрация по GET параметрам
    queryset = Catalog.objects.active()
    
    brand_filter = request.GET.get('brand')
    if brand_filter:
        queryset = queryset.filter(brand__icontains=brand_filter)
    
    price_min = request.GET.get('price_min')
    if price_min:
        queryset = queryset.filter(price__gte=price_min)
    
    price_max = request.GET.get('price_max')
    if price_max:
        queryset = queryset.filter(price__lte=price_max)
    
    # ✅ Пагинация с try/except
    paginator = Paginator(queryset, 6)  # 6 товаров на страницу
    page = request.GET.get('page')
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    context = {
        'products': products,
        'stats': stats,
        'active_products_count': active_products.count(),
        'nike_products_count': nike_products.count(),
        'expensive_products_count': expensive_products.count(),
    }
    
    return render(request, 'shop/catalog_list.html', context)

@cache_page(60 * 30)  # ✅ Кешируем детали товара на 30 минут
def product_detail(request, pk):
    """
    ✅ Демонстрация get_object_or_404()
    """
    product = get_object_or_404(Catalog, pk=pk, is_active=True)
    
    # Получаем связанные данные через related_name
    product_card = getattr(product, 'product_card', None)
    reviews = product.reviews.filter(is_approved=True).select_related('client')
    
    # Агрегация для отзывов
    review_stats = product.reviews.aggregate(
        avg_rating=Avg('rating'),
        total_reviews=Count('review_id')
    )
    
    context = {
        'product': product,
        'product_card': product_card,
        'reviews': reviews,
        'review_stats': review_stats,
    }
    
    return render(request, 'product_detail.html', context)




@login_required
@require_POST
def create_order(request, product_pk):
    """
    Создание заказа для товара
    """
    product = get_object_or_404(Catalog, pk=product_pk, is_active=True)
    
    try:
        client = Clients.objects.get(email=request.user.email)
    except Clients.DoesNotExist:
        # Создаем клиента если его нет
        client = Clients.objects.create(
            email=request.user.email,
            first_name=request.user.first_name or 'Пользователь',
            last_name=request.user.last_name or 'Системы',
            phone_number='Не указан'
        )
    
    quantity = int(request.POST.get('quantity', 1))
    total_cost = product.price * quantity
    
    # Создаем адрес по умолчанию если его нет
    address, created = Address.objects.get_or_create(
        city='Москва',
        street='Не указана',
        house_number='0',
        postal_code='000000'
    )
    
    # Создаем заказ
    order = Order.objects.create(
        client=client,
        total_amount=total_cost,
        shipping_address=address,
        status='pending'
    )
    
    # Создаем покупку
    Purchase.objects.create(
        client=client,
        sneakers=product,
        total_cost=total_cost,
        quantity=quantity
    )
    
    messages.success(request, f'Заказ №{order.order_id} успешно создан! Общая сумма: {total_cost} ₽')
    return HttpResponseRedirect(reverse('product_detail', args=[product_pk]))


def category_detail(request, pk):
    """
    Детальная страница категории с товарами
    """
    category = get_object_or_404(Category, pk=pk)
    
    # Используем related_name для получения товаров категории
    products = category.product_cards.filter(sneakers__is_active=True)
    
    # Пагинация
    paginator = Paginator(products, 8)
    page = request.GET.get('page')
    
    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)
    
    context = {
        'category': category,
        'products': products_page,
        'total_products': products.count(),
    }
    
    return render(request, 'shop/category_detail.html', context)


def client_detail(request, pk):
    """
    Детальная страница клиента
    """
    client = get_object_or_404(Clients, pk=pk)
    
    # Используем related_name для получения связанных данных
    orders = client.client_orders.all()
    purchases = client.client_purchases.all()
    reviews = client.client_reviews.filter(is_approved=True)
    wishlist = client.client_wishlist.all()
    
    # Статистика клиента
    client_stats = {
        'total_orders': orders.count(),
        'total_purchases': purchases.count(),
        'total_spent': purchases.aggregate(total=Sum('total_cost'))['total'] or 0,
        'avg_rating_given': reviews.aggregate(avg=Avg('rating'))['avg'] or 0,
    }
    
    context = {
        'client': client,
        'orders': orders[:5],  # Последние 5 заказов
        'purchases': purchases[:5],  # Последние 5 покупок
        'reviews': reviews[:5],  # Последние 5 отзывов
        'wishlist': wishlist[:5],  # Последние 5 в wishlist
        'client_stats': client_stats,
    }
    
    return render(request, 'shop/client_detail.html', context)


def search_products(request):
    """
    Поиск товаров с демонстрацией сложных Q-запросов
    ✅ СЛОЖНЫЙ Q-ЗАПРОС 1: OR + AND + NOT
    """
    query = request.GET.get('q')
    results = []
    
    if query:
        # ✅ Комбинированный Q-запрос с OR, AND и NOT
        # Ищем товары где:
        # (бренд содержит запрос ИЛИ название содержит запрос ИЛИ описание содержит запрос)
        # И товар активен
        # И НЕ товары без изображения
        # И НЕ товары дешевле 1000 рублей (исключаем возможный мусор)
        results = Catalog.objects.filter(
            (
                Q(brand__icontains=query) |
                Q(product_card__name__icontains=query) |
                Q(product_card__description__icontains=query) |
                Q(product_card__color__icontains=query)
            ) &
            Q(is_active=True) &
            ~Q(image__isnull=True) &  # NOT (НЕ без изображения)
            ~Q(price__lt=1000)  # NOT (НЕ дешевле 1000)
        ).distinct()
        
        # Сортировка результатов
        results = results.order_by('-created_at', 'price')
    
    # Пагинация результатов поиска
    paginator = Paginator(results, 10)
    page = request.GET.get('page')
    
    try:
        search_results = paginator.page(page)
    except PageNotAnInteger:
        search_results = paginator.page(1)
    except EmptyPage:
        search_results = paginator.page(paginator.num_pages)
    
    context = {
        'query': query,
        'results': search_results,
        'total_found': results.count() if query else 0,
    }
    
    return render(request, 'search/search_results.html', context)


def reviews_list(request):
    """
    Список отзывов с фильтрацией и агрегацией
    ✅ СЛОЖНЫЙ Q-ЗАПРОС 3: OR + AND + NOT
    """
    # Получаем параметры фильтрации
    rating_filter = request.GET.get('rating')
    brand_filter = request.GET.get('brand')
    
    # ✅ Комбинированный Q-запрос для отзывов
    # Показываем отзывы которые:
    # (одобрены И есть комментарий) И (фильтры пользователя) И НЕ от неактивных клиентов И НЕ спам
    base_filter = (
        Q(is_approved=True) &  # одобрены
        Q(comment__isnull=False) &  # есть комментарий
        ~Q(comment__exact='') &  # НЕ пустой комментарий
        ~Q(client__is_active=False) &  # НЕ от неактивных клиентов
        ~Q(comment__icontains='спам') &  # НЕ спам
        ~Q(comment__icontains='реклама')  # НЕ реклама
    )
    
    # Добавляем пользовательские фильтры
    user_filters = Q()
    
    if rating_filter:
        try:
            user_filters &= Q(rating=int(rating_filter))
        except (ValueError, TypeError):
            pass
    
    if brand_filter:
        user_filters &= Q(sneakers__brand__icontains=brand_filter)
    
    # Объединяем все фильтры
    reviews = Reviews.objects.filter(
        base_filter & user_filters
    ).select_related('client', 'sneakers')
    
    # Сортировка
    sort_by = request.GET.get('sort', '-created_date')
    reviews = reviews.order_by(sort_by)
    
    # Агрегация статистики
    review_stats = Reviews.objects.filter(is_approved=True).aggregate(
        avg_rating=Avg('rating'),
        total_reviews=Count('review_id'),
        max_rating=Max('rating'),
        min_rating=Min('rating')
    )
    
    # Пагинация
    paginator = Paginator(reviews, 15)
    page = request.GET.get('page')
    
    try:
        reviews_page = paginator.page(page)
    except PageNotAnInteger:
        reviews_page = paginator.page(1)
    except EmptyPage:
        reviews_page = paginator.page(paginator.num_pages)
    
    context = {
        'reviews': reviews_page,
        'review_stats': review_stats,
        'rating_choices': Reviews.RATING_CHOICES,
    }
    
    return render(request, 'reviews/reviews_list.html', context)


# ==================== CRUD операции ====================

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

@login_required
@require_http_methods(["GET", "POST"])
def product_create(request):
    """
    Создание нового товара (только для персонала)
    """
    if not request.user.is_staff:
        messages.error(request, 'У вас нет прав для создания товаров.')
        return HttpResponseRedirect(reverse('product_list'))
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                product = form.save()
                messages.success(request, f'Товар "{product.brand}" успешно создан!')
                return HttpResponseRedirect(reverse('product_detail', args=[product.sneakers_id]))
            except Exception as e:
                messages.error(request, f'Ошибка при создании товара: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'title': 'Создание нового товара'
    }
    return render(request, 'products/product_create.html', context)

@login_required
@require_http_methods(["POST"])
def product_quick_create(request):
    """
    Быстрое создание товара с минимальными данными
    """
    if not request.user.is_staff:
        messages.error(request, 'У вас нет прав для создания товаров.')
        return HttpResponseRedirect(reverse('product_list'))
    
    brand = request.POST.get('brand', '').strip()
    price = request.POST.get('price', '').strip()
    
    if not brand or not price:
        messages.error(request, 'Заполните все обязательные поля (бренд и цена).')
        return HttpResponseRedirect(reverse('product_list'))
    
    try:
        price_float = float(price)
        if price_float <= 0:
            raise ValueError("Цена должна быть больше нуля")
            
        product = Catalog.objects.create(
            brand=brand,
            price=price_float,
            is_active=True
        )
        
        messages.success(request, f'Товар "{brand}" быстро создан! Вы можете отредактировать его детали.')
        return HttpResponseRedirect(reverse('product_detail', args=[product.sneakers_id]))
        
    except ValueError as e:
        messages.error(request, f'Ошибка в данных: {str(e)}')
    except Exception as e:
        messages.error(request, f'Ошибка при создании товара: {str(e)}')
    
    return HttpResponseRedirect(reverse('product_list'))

def product_create_with_form(request):
    """Создание товара с использованием Django формы"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Товар "{product.brand}" успешно создан!')
            return HttpResponseRedirect(reverse('product_detail', args=[product.sneakers_id]))
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'title': 'Создание нового товара'
    }
    return render(request, 'shop/product_create_form.html', context)


@login_required
def product_edit(request, pk):
    """
    Редактирование товара (только для персонала)
    """
    if not request.user.is_staff:
        messages.error(request, 'У вас нет прав для редактирования товаров.')
        return HttpResponseRedirect(reverse('product_list'))
    
    product = get_object_or_404(Catalog, pk=pk)
    
    if request.method == 'POST':
        brand = request.POST.get('brand')
        price = request.POST.get('price')
        image = request.FILES.get('image')
        is_active = request.POST.get('is_active') == 'on'
        
        if brand and price:
            try:
                product.brand = brand
                product.price = float(price)
                if image:
                    product.image = image
                product.is_active = is_active
                product.save()
                
                messages.success(request, f'Товар "{brand}" успешно обновлен!')
                return HttpResponseRedirect(reverse('product_detail', args=[product.sneakers_id]))
            except ValueError:
                messages.error(request, 'Неверный формат цены.')
        else:
            messages.error(request, 'Заполните все обязательные поля.')
    
    context = {'product': product}
    return render(request, 'products/product_edit.html', context)


@login_required
def product_delete(request, pk):
    """
    Удаление товара - демонстрация DELETE операции
    """
    product = get_object_or_404(Catalog, pk=pk)
    
    if request.method == 'POST':
        brand_name = product.brand
        product.delete()
        messages.success(request, f'Товар "{brand_name}" успешно удален!')
        return redirect('product_list')
    
    context = {
        'product': product,
    }
    
    return render(request, 'products/product_confirm_delete.html', context)


@login_required
@require_POST
def review_create(request, product_pk):
    """
    Создание отзыва для товара
    """
    product = get_object_or_404(Catalog, pk=product_pk)
    
    # Проверяем, есть ли уже отзыв от этого пользователя
    try:
        client = Clients.objects.get(email=request.user.email)
        existing_review = Reviews.objects.filter(client=client, sneakers=product).first()
        if existing_review:
            messages.warning(request, 'Вы уже оставили отзыв для этого товара.')
            return HttpResponseRedirect(reverse('product_detail', args=[product_pk]))
    except Clients.DoesNotExist:
        messages.error(request, 'Профиль клиента не найден.')
        return HttpResponseRedirect(reverse('product_detail', args=[product_pk]))
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if rating and comment:
            try:
                Reviews.objects.create(
                    client=client,
                    sneakers=product,
                    rating=int(rating),
                    comment=comment,
                    is_approved=True  # Автоматически одобряем отзывы
                )
                messages.success(request, 'Ваш отзыв успешно добавлен!')
                return HttpResponseRedirect(reverse('product_detail', args=[product_pk]))
            except ValueError:
                messages.error(request, 'Неверный формат оценки.')
        else:
            messages.error(request, 'Заполните все поля.')
    
    context = {'product': product}
    return render(request, 'reviews/review_create.html', context)


@login_required
def review_edit(request, pk):
    """
    Редактирование отзыва
    """
    review = get_object_or_404(Reviews, pk=pk)
    
    # Проверяем, что пользователь может редактировать этот отзыв
    try:
        client = Clients.objects.get(email=request.user.email)
        if review.client != client:
            messages.error(request, 'Вы можете редактировать только свои отзывы.')
            return HttpResponseRedirect(reverse('product_detail', args=[review.sneakers.sneakers_id]))
    except Clients.DoesNotExist:
        messages.error(request, 'Профиль клиента не найден.')
        return HttpResponseRedirect(reverse('home'))
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if rating and comment:
            try:
                review.rating = int(rating)
                review.comment = comment
                review.save()
                messages.success(request, 'Отзыв успешно обновлен!')
                return HttpResponseRedirect(reverse('product_detail', args=[review.sneakers.sneakers_id]))
            except ValueError:
                messages.error(request, 'Неверный формат оценки.')
        else:
            messages.error(request, 'Заполните все поля.')
    
    context = {'review': review}
    return render(request, 'reviews/review_edit.html', context)


@login_required
def review_delete(request, pk):
    """
    Удаление отзыва
    """
    review = get_object_or_404(Reviews, pk=pk)
    
    # Проверяем, что пользователь может удалить этот отзыв
    try:
        client = Clients.objects.get(email=request.user.email)
        if review.client != client and not request.user.is_staff:
            messages.error(request, 'Вы можете удалять только свои отзывы.')
            return HttpResponseRedirect(reverse('product_detail', args=[review.sneakers.sneakers_id]))
    except Clients.DoesNotExist:
        messages.error(request, 'Профиль клиента не найден.')
        return HttpResponseRedirect(reverse('home'))
    
    product_id = review.sneakers.sneakers_id
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Отзыв успешно удален!')
        return HttpResponseRedirect(reverse('product_detail', args=[product_id]))
    
    context = {'review': review}
    return render(request, 'reviews/review_delete.html', context)


@login_required
def toggle_wishlist(request, product_pk):
    """
    Добавление/удаление товара из избранного
    """
    try:
        product = get_object_or_404(Catalog, pk=product_pk, is_active=True)
        
        # Пытаемся найти клиента по email пользователя
        try:
            client = Clients.objects.get(email=request.user.email)
        except Clients.DoesNotExist:
            # Если клиента нет, создаем его
            client = Clients.objects.create(
                email=request.user.email,
                first_name=request.user.first_name or request.user.username,
                last_name=request.user.last_name or '',
                phone_number='',  # Можно будет заполнить позже
            )
        
        # Получаем размер и количество (для GET-запросов используем значения по умолчанию)
        if request.method == 'POST':
            size = request.POST.get('size', 'Универсальный')
            quantity = int(request.POST.get('quantity', 1))
        else:
            size = 'Универсальный'
            quantity = 1
        
        # Проверяем, есть ли товар в избранном
        wishlist_item, created = Wishlist.objects.get_or_create(
            client=client,
            sneakers=product,
            size=size,
            defaults={'quantity': quantity}
        )
        
        if created:
            messages.success(request, f'Товар "{product.brand}" добавлен в избранное!')
        else:
            wishlist_item.delete()
            messages.success(request, f'Товар "{product.brand}" удален из избранного!')
            
    except Exception as e:
        messages.error(request, f'Произошла ошибка: {str(e)}')
    
    # Возвращаемся на предыдущую страницу
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('product_list')))

# ✅ Добавляем альтернативную функцию для GET-запросов
@login_required
def remove_from_wishlist(request, wishlist_id):
    """
    Удаление конкретного товара из избранного по ID записи
    """
    try:
        # Получаем клиента
        client = Clients.objects.get(email=request.user.email)
        
        # Находим и удаляем запись из избранного
        wishlist_item = get_object_or_404(Wishlist, pk=wishlist_id, client=client)
        product_name = wishlist_item.sneakers.brand
        wishlist_item.delete()
        
        messages.success(request, f'Товар "{product_name}" удален из избранного!')
        
    except Clients.DoesNotExist:
        messages.error(request, 'Клиент не найден!')
    except Exception as e:
        messages.error(request, f'Произошла ошибка: {str(e)}')
    
    return HttpResponseRedirect(reverse('wishlist'))



@login_required
def wishlist(request):
    """
    Список избранного пользователя
    """
    try:
        client = Clients.objects.get(email=request.user.email)
        wishlist_items = Wishlist.objects.filter(client=client).order_by('-added_date')
    except Clients.DoesNotExist:
        wishlist_items = []
        messages.info(request, 'Профиль клиента не найден.')
    
    context = {'wishlist_items': wishlist_items}
    return render(request, 'wishlist/wishlist.html', context)


# ✅ Аутентификация и регистрация пользователя
def user_register(request):
    """
    Регистрация нового пользователя
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Аккаунт создан для {username}!')
            return HttpResponseRedirect(reverse('login'))
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})


def user_login(request):
    """
    Вход пользователя
    """
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {username}!')
            return HttpResponseRedirect(reverse('home'))
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    
    return render(request, 'registration/login.html')


def user_logout(request):
    """
    Выход пользователя
    """
    username = request.user.username if request.user.is_authenticated else "Пользователь"
    logout(request)
    messages.success(request, f'До свидания, {username}! Вы успешно вышли из системы.')
    return redirect('home')



@login_required
def user_profile(request):
    """
    Профиль пользователя (требует авторизации)
    """
    # Пример работы с авторизованным пользователем
    user_orders = Order.objects.filter(
        client__email=request.user.email
    ).order_by('-order_date')
    
    # Получаем клиента или создаем если его нет
    try:
        client = Clients.objects.get(email=request.user.email)
        user_wishlist = client.client_wishlist.all()[:5]
        user_reviews = client.client_reviews.filter(is_approved=True)[:5]
    except Clients.DoesNotExist:
        user_wishlist = []
        user_reviews = []
    context = {
        'user_orders': user_orders[:10],  # Последние 10 заказов
        'user_wishlist': user_wishlist,
        'user_reviews': user_reviews,
    }
    
    return render(request, 'registration/profile.html', context)


@login_required
def wishlist_view(request):
    """
    Просмотр списка избранного
    """
    try:
        # Получаем клиента
        client = Clients.objects.get(email=request.user.email)
        
        # Получаем товары из избранного
        wishlist_items = Wishlist.objects.filter(client=client).select_related('sneakers')
        
        # Вычисляем общую стоимость
        total_value = sum(item.sneakers.price * item.quantity for item in wishlist_items)
        
        # Получаем уникальные категории товаров в избранном
        categories = set()
        for item in wishlist_items:
            try:
                # Получаем категорию через product_card
                if hasattr(item.sneakers, 'product_card') and item.sneakers.product_card:
                    categories.add(item.sneakers.product_card.category.get_name_display())
            except:
                pass
        
        context = {
            'wishlist_items': wishlist_items,
            'total_value': total_value,
            'categories': list(categories),
            'categories_count': len(categories),
        }
        
    except Clients.DoesNotExist:
        context = {
            'wishlist_items': [],
            'total_value': 0,
            'categories': [],
            'categories_count': 0,
        }
    
    return render(request, 'wishlist/wishlist.html', context)


@staff_member_required
@cache_page(60 * 60)  # ✅ Кешируем статистику на 1 час
def statistics_view(request):
    """Полная статистика - переход из виджета"""
    # Общая статистика
    catalog_stats = Catalog.objects.aggregate(
        total_products=Count('sneakers_id'),
        active_products=Count('sneakers_id', filter=Q(is_active=True)),
        avg_price=Avg('price'),
        max_price=Max('price'),
        min_price=Min('price'),
        total_value=Sum('price')
    )
    
    # Статистика по брендам
    brand_stats = Catalog.objects.filter(is_active=True).values('brand').annotate(
        count=Count('sneakers_id'),
        avg_price=Avg('price'),
        avg_rating=Avg('reviews__rating')
    ).order_by('-count')[:10]
    
    # Статистика по категориям
    category_stats = Category.objects.annotate(
        product_count=Count('product_cards'),
        avg_price=Avg('product_cards__sneakers__price')
    )
    
    # Статистика отзывов
    review_stats = Reviews.objects.aggregate(
        total_reviews=Count('review_id'),
        approved_reviews=Count('review_id', filter=Q(is_approved=True)),
        avg_rating=Avg('rating'),
        five_star_count=Count('review_id', filter=Q(rating=5)),
        one_star_count=Count('review_id', filter=Q(rating=1))
    )
    
    context = {
        'catalog_stats': catalog_stats,
        'brand_stats': brand_stats,
        'category_stats': category_stats,
        'review_stats': review_stats,
    }
    
    return render(request, 'sneaker_app/statistics.html', context)


def brand_products(request, brand_name):
    """
    Товары определенного бренда (демонстрация регулярных выражений в URL)
    """
    products = Catalog.objects.filter(
        brand__icontains=brand_name,
        is_active=True
    ).annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    ).order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    
    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)
    
    context = {
        'products': products_page,
        'brand_name': brand_name,
        'total_products': products.count(),
    }
    
    return render(request, 'products/brand_products.html', context)


def price_range_products(request, min_price, max_price):
    """
    Товары в определенном ценовом диапазоне
    """
    products = Catalog.objects.filter(
        price__gte=min_price,
        price__lte=max_price,
        is_active=True
    ).annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    ).order_by('price')
    
    # Пагинация
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    
    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)
    
    context = {
        'products': products_page,
        'min_price': min_price,
        'max_price': max_price,
        'total_products': products.count(),
    }
    
    return render(request, 'products/price_range_products.html', context)


# ==================== API-подобные представления ====================

def api_products_json(request):
    """
    API endpoint для получения списка товаров в JSON
    """
    from django.http import JsonResponse
    
    products = Catalog.objects.filter(is_active=True).values(
        'sneakers_id', 'brand', 'price', 'created_at'
    )[:20]  # Ограничиваем количество
    
    return JsonResponse(list(products), safe=False)


def api_product_detail_json(request, pk):
    """
    API endpoint для получения детальной информации о товаре в JSON
    """
    from django.http import JsonResponse
    
    try:
        product = Catalog.objects.get(pk=pk, is_active=True)
        data = {
            'id': product.sneakers_id,
            'brand': product.brand,
            'price': float(product.price),
            'created_at': product.created_at.isoformat(),
            'is_active': product.is_active,
        }
        
        # Добавляем информацию о карточке товара, если есть
        if hasattr(product, 'product_card'):
            card = product.product_card
            data.update({
                'name': card.name,
                'size': card.size,
                'color': card.color,
                'material': card.material,
                'description': card.description,
            })
        
        return JsonResponse(data)
    except Catalog.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)


# ==================== Дополнительные представления ====================

def about_view(request):
    """
    Страница "О нас"
    """
    return render(request, 'pages/about.html')


def contact_view(request):
    """
    Страница "Контакты"
    """
    return render(request, 'pages/contact.html')


# ==================== Обработка ошибок ====================

def handler404(request, exception):
    """
    Обработчик ошибки 404
    """
    return render(request, 'errors/404.html', status=404)


def handler500(request):
    """
    Обработчик ошибки 500
    """
    return render(request, 'errors/500.html', status=500)


# ==================== Демонстрационные представления ====================

def demo_orm_queries(request):
    """
    Демонстрационная страница с примерами ORM запросов
    """
    # Примеры различных ORM запросов
    examples = {
        'all_products': Catalog.objects.all().count(),
        'active_products': Catalog.objects.filter(is_active=True).count(),
        'expensive_products': Catalog.objects.filter(price__gte=10000).count(),
        'nike_products': Catalog.objects.filter(brand__icontains='Nike').count(),
        'recent_products': Catalog.objects.filter(created_at__gte='2024-01-01').count(),
        'avg_price': Catalog.objects.aggregate(avg_price=Avg('price'))['avg_price'],
        'max_price': Catalog.objects.aggregate(max_price=Max('price'))['max_price'],
        'min_price': Catalog.objects.aggregate(min_price=Min('price'))['min_price'],
        'brands_count': Catalog.objects.values('brand').distinct().count(),
        'total_reviews': Reviews.objects.count(),
        'approved_reviews': Reviews.objects.filter(is_approved=True).count(),
                'avg_rating': Reviews.objects.filter(is_approved=True).aggregate(avg=Avg('rating'))['avg'],
        'total_clients': Clients.objects.count(),
        'active_clients': Clients.objects.filter(is_active=True).count(),
    }
    
    # Примеры сложных запросов
    complex_queries = {
        'top_rated_products': Catalog.objects.filter(is_active=True).annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        ).filter(review_count__gte=1).order_by('-avg_rating')[:5],
        
        'most_reviewed_products': Catalog.objects.filter(is_active=True).annotate(
            review_count=Count('reviews')
        ).order_by('-review_count')[:5],
        
        'brands_with_stats': Catalog.objects.values('brand').annotate(
            count=Count('sneakers_id'),
            avg_price=Avg('price'),
            min_price=Min('price'),
            max_price=Max('price')
        ).order_by('-count')[:10],
        
        'categories_with_products': Category.objects.annotate(
            product_count=Count('product_cards__sneakers', filter=Q(product_cards__sneakers__is_active=True)),
            avg_price=Avg('product_cards__sneakers__price')
        ).order_by('-product_count'),
    }
    
    context = {
        'examples': examples,
        'complex_queries': complex_queries,
    }
    
    return render(request, 'demo/orm_queries.html', context)

# ✅ Добавляем в конец файла новые функции для управления кешем

@staff_member_required
def cache_stats(request):
    """
    Страница статистики кэша для администраторов
    """
    # Список ключей кэша, которые мы отслеживаем
    cache_keys = [
        'total_products_count',
        'price_range_0_50000',
        'price_range_1000_5000',
        'top_brands_5',
        'top_brands_3',
        'avg_product_rating',
    ]
    
    # Проверяем статус каждого ключа
    cache_info = {}
    for key in cache_keys:
        cache_info[key] = cache.get(key) is not None
    
    # Дополнительная информация
    context = {
        'cache_info': cache_info,
        'was_cleared': request.GET.get('cleared') == 'true',
    }
    
    return render(request, 'admin/cache_stats.html', context)


@staff_member_required
@require_http_methods(["POST", "GET"])
def clear_cache(request):
    """
    Очистка всего кэша
    """
    try:
        cache.clear()
        messages.success(request, '✅ Кэш успешно очищен!')
    except Exception as e:
        messages.error(request, f'❌ Ошибка при очистке кэша: {str(e)}')
    
    return HttpResponseRedirect(reverse('cache_stats') + '?cleared=true')


@staff_member_required
def cache_test(request):
    """
    Тестовая страница для проверки кэша
    """
    import time
    
    # Тестируем скорость загрузки с кэшем и без
    start_time = time.time()
    
    # Данные, которые кэшируются
    total_products = Catalog.objects.filter(is_active=True).count()
    avg_rating = Reviews.objects.filter(is_approved=True).aggregate(
        avg=Avg('rating')
    )['avg'] or 0
    
    end_time = time.time()
    load_time = round((end_time - start_time) * 1000, 2)  # в миллисекундах
    
    # Проверяем статус кэша
    cache_status = {
        'total_products_cached': cache.get('total_products_count') is not None,
        'avg_rating_cached': cache.get('avg_product_rating') is not None,
    }
    
    context = {
        'total_products': total_products,
        'avg_rating': round(avg_rating, 1),
        'load_time': load_time,
        'cache_status': cache_status,
    }
    
    return render(request, 'admin/cache_test.html', context)

# Добавляем эту функцию в views.py

@login_required
@require_http_methods(["GET", "POST"])
def product_create_django_form(request):
    """
    Создание товара с использованием Django формы
    """
    if not request.user.is_staff:
        messages.error(request, 'У вас нет прав для создания товаров.')
        return HttpResponseRedirect(reverse('product_list'))
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                product = form.save()
                messages.success(request, f'Товар "{product.brand}" успешно создан через Django форму!')
                return HttpResponseRedirect(reverse('product_detail', args=[product.sneakers_id]))
            except Exception as e:
                messages.error(request, f'Ошибка при создании товара: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'title': 'Создание товара (Django форма)',
        'form_type': 'django'
    }
    return render(request, 'products/product_create_django_form.html', context)


def popular_products(request):
    """Популярные товары - для навигации из base.html"""
    products = Catalog.objects.filter(is_active=True).annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    ).filter(review_count__gte=1).order_by('-avg_rating', '-review_count')
    
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    
    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)
    
    return render(request, 'products/product_list.html', {
        'products': products_page,
        'page_title': 'Популярные товары'
    })

def new_products(request):
    """Новые товары - для навигации из base.html"""
    products = Catalog.objects.filter(is_active=True).order_by('-created_at')
    
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    
    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)
    
    return render(request, 'products/product_list.html', {
        'products': products_page,
        'page_title': 'Новые поступления'
    })

def category_list(request):
    """Список категорий"""
    categories = Category.objects.annotate(
        product_count=Count('product_cards__sneakers', filter=Q(product_cards__sneakers__is_active=True)),
        avg_price=Avg('product_cards__sneakers__price', filter=Q(product_cards__sneakers__is_active=True))
    ).order_by('name')
    
    return render(request, 'sneaker_app/category_list.html', {
        'categories': categories
    })


@staff_member_required
@require_http_methods(["POST"])
def clear_cache_ajax(request):
    """
    AJAX очистка кеша без редиректа
    """
    try:
        cache.clear()
        return JsonResponse({
            'success': True,
            'message': '✅ Кэш успешно очищен!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'❌ Ошибка при очистке кэша: {str(e)}'
        }, status=500)

# ✅ ДОБАВЛЯЕМ В КОНЕЦ ФАЙЛА - импорт новой формы
from .forms import DemoFieldForm

@login_required
@require_http_methods(["GET", "POST"])
def product_create_django_fields(request):
    """
    Создание товара с демонстрацией Django field методов:
    {{ field.label_tag }}, {{ field }}, {{ field.errors }}
    """
    if not request.user.is_staff:
        messages.error(request, 'У вас нет прав для создания товаров.')
        return HttpResponseRedirect(reverse('product_list'))
    
    if request.method == 'POST':
        form = DemoFieldForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                product = form.save(commit=False)
                special_notes = form.cleaned_data.get('special_notes')
                # Можно сохранить заметки или использовать как-то еще
                product.save()
                messages.success(request, f'✅ Товар "{product.brand}" создан через Django field методы!')
                return HttpResponseRedirect(reverse('product_detail', args=[product.sneakers_id]))
            except Exception as e:
                messages.error(request, f'❌ Ошибка при создании товара: {str(e)}')
        else:
            messages.error(request, '❌ Исправьте ошибки в форме (проверьте {{ field.errors }})')
    else:
        form = DemoFieldForm()
    
    context = {
        'form': form,
        'title': 'Создание товара (Django Field методы)',
        'form_type': 'django_fields',
        'demo_info': {
            'methods': [
                '{{ field.label_tag }} - генерирует HTML тег <label>',
                '{{ field }} - генерирует HTML поле ввода',
                '{{ field.errors }} - показывает ошибки поля',
                '{{ field.help_text }} - текст подсказки',
                '{{ field.id_for_label }} - ID для связи с label'
            ]
        }
    }
    
    return render(request, 'products/product_create.html', context)

@login_required
@require_http_methods(["GET", "POST"])
def product_delete_quick(request, pk):
    """
    Быстрое удаление товара без подтверждения (только для staff)
    """
    if not request.user.is_staff:
        messages.error(request, '❌ У вас нет прав для удаления товаров.')
        return HttpResponseRedirect(reverse('product_list'))
    
    try:
        product = get_object_or_404(Catalog, pk=pk)
        brand_name = product.brand
        product_id = product.sneakers_id
        
        # Удаляем товар
        product.delete()
        
        messages.success(request, f'✅ Товар "{brand_name}" (ID: {product_id}) успешно удален!')
        
    except Exception as e:
        messages.error(request, f'❌ Ошибка при удалении товара: {str(e)}')
    
    # Возвращаемся на страницу каталога
    return HttpResponseRedirect(reverse('product_list'))
