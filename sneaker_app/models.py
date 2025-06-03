from django.db import models
from django.contrib import admin
from django.utils.html import format_html
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone  # ✅ Добавляем timezone
from django.urls import reverse
from django.db.models import Avg, Count



class CategoryManager(models.Manager):
    """Собственный менеджер для категорий"""
    def active_categories(self):
        return self.filter(productcards__sneakers__is_active=True).distinct()
    
    def with_product_count(self):
        return self.annotate(product_count=Count('productcards'))


class Category(models.Model):
    """Модель категорий товаров"""
    CATEGORY_CHOICES = [
        ('men', 'Мужская'),
        ('women', 'Женская'),
        ('kids', 'Детская'),
    ]
    
    name = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        unique=True,
        verbose_name="Название категории"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание категории"
    )
    
    objects = CategoryManager()  # ✅ Собственный менеджер
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']
    
    def __str__(self):
        return self.get_name_display()
    
    def get_absolute_url(self):  # ✅ get_absolute_url
        return reverse('category_detail', kwargs={'pk': self.pk})


class Tag(models.Model):
    """
    Модель тегов для товаров
    Демонстрация ManyToMany через through
    """
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Название тега"
    )
    color = models.CharField(
        max_length=7,
        default='#007bff',
        verbose_name="Цвет тега",
        help_text="Цвет в формате HEX (#ffffff)"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата создания"
    )
    
    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('tag_detail', kwargs={'pk': self.pk})


class CatalogManager(models.Manager):
    """Собственный менеджер для каталога"""
    def active(self):
        return self.filter(is_active=True)
    
    def by_brand(self, brand):
        return self.filter(brand__icontains=brand)
    
    def expensive(self):
        return self.filter(price__gte=10000)
    
    def with_avg_rating(self):
        return self.annotate(avg_rating=Avg('reviews__rating'))


class Catalog(models.Model):
    """Модель каталога кроссовок"""
    sneakers_id = models.AutoField(
        primary_key=True,
        verbose_name="ID кроссовок"
    )
    brand = models.CharField(
        max_length=100,
        verbose_name="Бренд"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,

        verbose_name="Цена"
    )
    image = models.ImageField(
        upload_to='sneakers/',
        blank=True,
        null=True,
        verbose_name="Изображение"
    )
    created_at = models.DateTimeField(

        default=timezone.now,  # ✅ Используем timezone
        verbose_name="Дата добавления"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )
    
    # ✅ ManyToMany через through модель
    tags = models.ManyToManyField(
        Tag,
        through='ProductTag',
        related_name='products',
        blank=True,
        verbose_name="Теги"
    )
    
    objects = CatalogManager()  # ✅ Собственный менеджер
    
    class Meta:
        verbose_name = "Товар в каталоге"
        verbose_name_plural = "Каталог товаров"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.brand} - {self.price} руб."
    
    def get_absolute_url(self):  # ✅ get_absolute_url
        return reverse('product_detail', kwargs={'pk': self.pk})
    
    def image_preview(self):
        if self.image:
            return format_html('<img src="{}" width="50" height="50" />', self.image.url)
        return "Нет изображения"
    image_preview.short_description = "Превью"


class ProductTag(models.Model):
    """
    ✅ Промежуточная модель для ManyToMany связи товаров и тегов
    Демонстрация through модели с дополнительными полями
    """
    product = models.ForeignKey(
        Catalog,
        on_delete=models.CASCADE,
        verbose_name="Товар"
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name="Тег"
    )
    priority = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(100)],
        verbose_name="Приоритет",
        help_text="Приоритет отображения тега (0-100)"
    )
    added_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата добавления"
    )
    
    class Meta:
        verbose_name = "Тег товара"
        verbose_name_plural = "Теги товаров"
        unique_together = ['product', 'tag']
        ordering = ['-priority', 'added_at']
    
    def __str__(self):
        return f"{self.product.brand} - {self.tag.name}"


class Clients(models.Model):
    """Модель клиентов"""
    client_id = models.AutoField(
        primary_key=True,
        verbose_name="ID клиента"
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name="Фамилия"
    )
    first_name = models.CharField(
        max_length=100,
        verbose_name="Имя"
    )
    phone_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Номер телефона"
    )
    email = models.EmailField(
        unique=True,
        verbose_name="Email"
    )
    date_joined = models.DateTimeField(

        default=timezone.now,  # ✅ Используем timezone
        verbose_name="Дата регистрации"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )
    
    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.last_name} {self.first_name}"
    

    def get_absolute_url(self):  # ✅ get_absolute_url
        return reverse('client_detail', kwargs={'pk': self.pk})
    
    def full_name(self):
        return f"{self.last_name} {self.first_name}"
    full_name.short_description = "ФИО"
    
    def orders_count(self):
        return self.client_orders.count()  # ✅ Используем related_name
    orders_count.short_description = "Количество заказов"


class ProductCards(models.Model):
    """Модель карточек товаров"""
    sneakers = models.OneToOneField(
        Catalog,
        on_delete=models.CASCADE,
        related_name='product_card',  # ✅ related_name
        verbose_name="Кроссовки"
    )
    name = models.CharField(
        max_length=200,
        verbose_name="Название"
    )
    size = models.CharField(
        max_length=100,
        verbose_name="Размеры"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='product_cards',  # ✅ related_name
        verbose_name="Категория"
    )
    color = models.CharField(
        max_length=100,
        verbose_name="Цвет"
    )
    material = models.CharField(
        max_length=100,
        verbose_name="Материал"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание"
    )
    
    # ✅ Добавляем URLField
    official_store_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Ссылка на официальный магазин",
        help_text="Ссылка на товар в официальном интернет-магазине"
    )
    
    manufacturer_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Ссылка на сайт производителя",
        help_text="Ссылка на страницу товара у производителя"
    )
    
    class Meta:
        verbose_name = "Карточка товара"
        verbose_name_plural = "Карточки товаров"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    

    def get_absolute_url(self):  # ✅ get_absolute_url
        return reverse('product_card_detail', kwargs={'pk': self.pk})
    
    def brand_name(self):
        return self.sneakers.brand
    brand_name.short_description = "Бренд"
    
    def price(self):
        return self.sneakers.price
    price.short_description = "Цена"
    
    # ✅ Методы для работы с URL
    def has_store_links(self):
        """Проверяет, есть ли ссылки на магазины"""
        return bool(self.official_store_url or self.manufacturer_url)
    has_store_links.boolean = True
    has_store_links.short_description = "Есть ссылки"
    
    def get_store_links(self):
        """Возвращает список доступных ссылок"""
        links = []
        if self.official_store_url:
            links.append(('Официальный магазин', self.official_store_url))
        if self.manufacturer_url:
            links.append(('Сайт производителя', self.manufacturer_url))
        return links


class Address(models.Model):
    """Модель адресов доставки"""
    city = models.CharField(
        max_length=100,
        verbose_name="Город"
    )
    street = models.CharField(
        max_length=200,
        verbose_name="Улица"
    )
    house_number = models.CharField(
        max_length=20,
        verbose_name="Номер дома"
    )
    apartment = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Квартира"
    )
    postal_code = models.CharField(
        max_length=10,
        verbose_name="Почтовый индекс"
    )
    
    class Meta:
        verbose_name = "Адрес"
        verbose_name_plural = "Адреса"
        ordering = ['city', 'street']
    
    def __str__(self):
        return f"{self.city}, {self.street}, {self.house_number}"
    

    def get_absolute_url(self):  # ✅ get_absolute_url
        return reverse('address_detail', kwargs={'pk': self.pk})


class Order(models.Model):
    """Модель заказов"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает обработки'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]
    
    order_id = models.AutoField(
        primary_key=True,
        verbose_name="ID заказа"
    )
    client = models.ForeignKey(
        Clients,
        on_delete=models.CASCADE,
        related_name='client_orders',  # ✅ related_name
        verbose_name="Клиент"
    )
    order_date = models.DateTimeField(

        default=timezone.now,  # ✅ Используем timezone
        verbose_name="Дата заказа"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Общая сумма"
    )
    shipping_address = models.ForeignKey(
        Address,
        on_delete=models.CASCADE,
        related_name='orders',  # ✅ related_name
        verbose_name="Адрес доставки"
    )
    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Номер отслеживания"
    )
    contact_info = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Контактная информация"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Статус"
    )
    
    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-order_date']
    
    def __str__(self):
        return f"Заказ №{self.order_id} от {self.order_date.strftime('%d.%m.%Y')}"
    

    def get_absolute_url(self):  # ✅ get_absolute_url
        return reverse('order_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        """
        Переопределенный save() для автоматической генерации трек-номера
        """
        # Генерируем трек-номер только для новых заказов
        if not self.tracking_number and self.status in ['processing', 'shipped']:
            import random
            import string
            self.tracking_number = 'TRK' + ''.join(random.choices(string.digits, k=10))
        
        super().save(*args, **kwargs)
    
    def client_name(self):
        return str(self.client)
    client_name.short_description = "Клиент"


class Purchase(models.Model):
    """Модель покупок"""
    purchase_id = models.AutoField(
        primary_key=True,
        verbose_name="ID покупки"
    )
    client = models.ForeignKey(
        Clients,
        on_delete=models.CASCADE,
        related_name='client_purchases',  # ✅ related_name
        verbose_name="Клиент"
    )
    sneakers = models.ForeignKey(
        Catalog,
        on_delete=models.CASCADE,
        related_name='purchases',  # ✅ related_name
        verbose_name="Кроссовки"
    )
    contact_info = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Контактная информация"
    )
    purchase_date = models.DateTimeField(

        default=timezone.now,  # ✅ Используем timezone
        verbose_name="Дата покупки"
    )
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Общая стоимость"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Количество"
    )
    
    class Meta:
        verbose_name = "Покупка"
        verbose_name_plural = "Покупки"
        ordering = ['-purchase_date']
    
    def __str__(self):
        return f"Покупка №{self.purchase_id} - {self.client}"
    

    def get_absolute_url(self):  # ✅ get_absolute_url
        return reverse('purchase_detail', kwargs={'pk': self.pk})


class Wishlist(models.Model):
    """Модель списка желаний"""
    wishlist_id = models.AutoField(
        primary_key=True,
        verbose_name="ID записи"
    )
    client = models.ForeignKey(
        Clients,
        on_delete=models.CASCADE,
        related_name='client_wishlist',  # ✅ related_name
        verbose_name="Клиент"
    )
    sneakers = models.ForeignKey(
        Catalog,
        on_delete=models.CASCADE,
        related_name='in_wishlist',  # ✅ related_name
        verbose_name="Кроссовки"
    )
    size = models.CharField(
        max_length=100,
        verbose_name="Размер"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Количество"
    )
    added_date = models.DateTimeField(

        default=timezone.now,  # ✅ Используем timezone
        verbose_name="Дата добавления"
    )
    
    class Meta:
        verbose_name = "Список желаний"
        verbose_name_plural = "Списки желаний"
        ordering = ['-added_date']
        unique_together = ['client', 'sneakers', 'size']
    
    def __str__(self):
        return f"{self.client} - {self.sneakers.brand}"
    

    def get_absolute_url(self):  # ✅ get_absolute_url
        return reverse('wishlist_detail', kwargs={'pk': self.pk})


class Reviews(models.Model):
    """Модель отзывов"""
    RATING_CHOICES = [
        (1, '1 звезда'),
        (2, '2 звезды'),
        (3, '3 звезды'),
        (4, '4 звезды'),
        (5, '5 звезд'),
    ]
    
    review_id = models.AutoField(
        primary_key=True,
        verbose_name="ID отзыва"
    )
    client = models.ForeignKey(
        Clients,
        on_delete=models.CASCADE,
        related_name='client_reviews',  # ✅ related_name
        verbose_name="Клиент"
    )
    sneakers = models.ForeignKey(
        Catalog,
        on_delete=models.CASCADE,
        related_name='reviews',  # ✅ related_name
        verbose_name="Кроссовки"
    )
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        verbose_name="Оценка"
    )
    comment = models.TextField(
        verbose_name="Комментарий"
    )
    created_date = models.DateTimeField(
        default=timezone.now,  # ✅ Используем timezone
        verbose_name="Дата создания"
    )
    is_approved = models.BooleanField(
        default=False,
        verbose_name="Одобрен"
    )
    
    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ['-created_date']
        unique_together = ['client', 'sneakers']
    
    def __str__(self):
        return f"Отзыв от {self.client} - {self.rating} звезд"
    
    def get_absolute_url(self):  # ✅ get_absolute_url
        return reverse('review_detail', kwargs={'pk': self.pk})
    
    def rating_stars(self):
        # Исправляем проблему с NoneType
        if self.rating is None:
            return "Нет оценки"
        return "★" * self.rating + "☆" * (5 - self.rating)
    rating_stars.short_description = "Рейтинг"


class Positions(models.Model):
    """Модель должностей"""
    position_id = models.AutoField(
        primary_key=True,
        verbose_name="ID должности"
    )
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Название должности"
    )
    responsibilities = models.TextField(
        verbose_name="Обязанности"
    )
    salary_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Минимальная зарплата"
    )
    salary_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Максимальная зарплата"
    )
    
    class Meta:
        verbose_name = "Должность"
        verbose_name_plural = "Должности"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):  # ✅ get_absolute_url
        return reverse('position_detail', kwargs={'pk': self.pk})


class Support(models.Model):
    """Модель сотрудников поддержки"""
    employee_id = models.AutoField(
        primary_key=True,
        verbose_name="ID сотрудника"
    )
    position = models.ForeignKey(
        Positions,
        on_delete=models.CASCADE,
        related_name='employees',  # ✅ related_name
        verbose_name="Должность"
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name="Фамилия"
    )
    first_name = models.CharField(
        max_length=100,
        verbose_name="Имя"
    )
    patronymic = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Отчество"
    )
    contact_info = models.CharField(
        max_length=255,
        verbose_name="Контактная информация"
    )
    hire_date = models.DateField(
        default=timezone.now,  # ✅ Используем timezone
        verbose_name="Дата найма"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )
    
    class Meta:
        verbose_name = "Сотрудник поддержки"
        verbose_name_plural = "Сотрудники поддержки"
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        if self.patronymic:
            return f"{self.last_name} {self.first_name} {self.patronymic}"
        return f"{self.last_name} {self.first_name}"
    
    def get_absolute_url(self):  # ✅ get_absolute_url
        return reverse('support_detail', kwargs={'pk': self.pk})
    
    def full_name(self):
        return str(self)
    full_name.short_description = "ФИО"
