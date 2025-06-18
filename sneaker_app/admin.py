from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from django.utils import timezone
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import os
from .models import Tag, ProductTag

from .models import (
    Category, Catalog, Clients, ProductCards, Address, Order,
    Purchase, Wishlist, Reviews, Positions, Support
)

# ✅ Импорт для Excel экспорта
from .resources import CatalogResource, OrderResource, ReviewResource, ClientResource
from tablib import Dataset

# ✅ ФУНКЦИИ ДЛЯ EXCEL ЭКСПОРТА
def export_catalog_to_excel(modeladmin, request, queryset):
    """Экспорт каталога в Excel"""
    resource = CatalogResource()
    dataset = resource.export(queryset)
    
    response = HttpResponse(
        dataset.xlsx, 
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="catalog_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    return response

export_catalog_to_excel.short_description = "📊 Экспорт в Excel"


def export_orders_to_excel(modeladmin, request, queryset):
    """Экспорт заказов в Excel"""
    resource = OrderResource()
    dataset = resource.export(queryset)
    
    response = HttpResponse(
        dataset.xlsx, 
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="orders_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    return response

export_orders_to_excel.short_description = "📊 Экспорт в Excel"


def export_reviews_to_excel(modeladmin, request, queryset):
    """Экспорт отзывов в Excel"""
    resource = ReviewResource()
    dataset = resource.export(queryset)
    
    response = HttpResponse(
        dataset.xlsx, 
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="reviews_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    return response

export_reviews_to_excel.short_description = "📊 Экспорт в Excel"


def export_clients_to_excel(modeladmin, request, queryset):
    """Экспорт клиентов в Excel"""
    resource = ClientResource()
    dataset = resource.export(queryset)
    
    response = HttpResponse(
        dataset.xlsx, 
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="clients_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    return response

export_clients_to_excel.short_description = "📊 Экспорт в Excel"

# ✅ Простая и надежная настройка шрифтов
def get_fonts():
    """Получение доступных шрифтов с поддержкой кириллицы"""
    try:
        # Пытаемся найти системные шрифты
        font_paths = {
            'normal': None,
            'bold': None
        }
        
        # Возможные пути к шрифтам
        possible_fonts = [
            # macOS
            ('/System/Library/Fonts/Arial.ttf', '/System/Library/Fonts/Arial Bold.ttf'),
            ('/System/Library/Fonts/Helvetica.ttc', '/System/Library/Fonts/Helvetica.ttc'),
            # Linux
            ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
            ('/usr/share/fonts/TTF/DejaVuSans.ttf', '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf'),
            # Windows
            ('C:/Windows/Fonts/arial.ttf', 'C:/Windows/Fonts/arialbd.ttf'),
        ]
        
        for normal_path, bold_path in possible_fonts:
            if os.path.exists(normal_path):
                try:
                    pdfmetrics.registerFont(TTFont('CustomFont', normal_path))
                    if os.path.exists(bold_path):
                        pdfmetrics.registerFont(TTFont('CustomFont-Bold', bold_path))
                    else:
                        pdfmetrics.registerFont(TTFont('CustomFont-Bold', normal_path))
                    return 'CustomFont', 'CustomFont-Bold'
                except:
                    continue
        
        # Если ничего не найдено, используем стандартные
        return 'Helvetica', 'Helvetica-Bold'
        
    except Exception as e:
        print(f"Ошибка настройки шрифтов: {e}")
        return 'Helvetica', 'Helvetica-Bold'

def generate_orders_pdf(modeladmin, request, queryset):
    """Генерация PDF отчета по заказам"""
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="orders_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Получаем шрифты
    normal_font, bold_font = get_fonts()
    
    # Заголовок
    p.setFont(bold_font, 16)
    p.drawString(50, height - 50, "Otchet po zakazam - Sneaker Shop")
    
    # Дата генерации
    p.setFont(normal_font, 10)
    p.drawString(50, height - 70, f"Data generacii: {timezone.now().strftime('%d.%m.%Y %H:%M')}")
    
    # Заголовки таблицы
    y_position = height - 120
    p.setFont(bold_font, 12)
    p.drawString(50, y_position, "No. zakaza")
    p.drawString(150, y_position, "Klient")
    p.drawString(300, y_position, "Summa")
    p.drawString(400, y_position, "Status")
    p.drawString(500, y_position, "Data")
    
    # Линия под заголовками
    p.line(50, y_position - 5, 550, y_position - 5)
    
    # Данные заказов
    p.setFont(normal_font, 10)
    y_position -= 25
    
    total_amount = 0
    for order in queryset:
        if y_position < 50:
            p.showPage()
            p.setFont(normal_font, 10)
            y_position = height - 50
        
        # Используем только ASCII символы
        client_name = transliterate_russian(str(order.client)[:20])
        status_text = transliterate_russian(order.get_status_display())
        
        p.drawString(50, y_position, str(order.order_id))
        p.drawString(150, y_position, client_name)
        p.drawString(300, y_position, f"{order.total_amount} RUB")
        p.drawString(400, y_position, status_text)
        p.drawString(500, y_position, order.order_date.strftime('%d.%m.%Y'))
        
        total_amount += order.total_amount
        y_position -= 20
    
    # Итого
    y_position -= 20
    p.line(50, y_position, 550, y_position)
    y_position -= 20
    p.setFont(bold_font, 12)
    p.drawString(50, y_position, f"Vsego zakazov: {queryset.count()}")
    p.drawString(300, y_position, f"Obshaya summa: {total_amount} RUB")
    
    p.showPage()
    p.save()
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response

generate_orders_pdf.short_description = "📄 Сгенерировать PDF отчет по заказам"


def generate_products_pdf(modeladmin, request, queryset):
    """Генерация PDF каталога товаров"""
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="products_catalog_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Получаем шрифты
    normal_font, bold_font = get_fonts()
    
    # Заголовок
    p.setFont(bold_font, 18)
    p.drawString(50, height - 50, "Katalog tovarov - Sneaker Shop")
    
    p.setFont(normal_font, 10)
    p.drawString(50, height - 70, f"Data: {timezone.now().strftime('%d.%m.%Y %H:%M')}")
    
    # Заголовки
    y_position = height - 120
    p.setFont(bold_font, 12)
    p.drawString(50, y_position, "ID")
    p.drawString(100, y_position, "Brand")
    p.drawString(250, y_position, "Cena")
    p.drawString(350, y_position, "Status")
    p.drawString(450, y_position, "Data dobavleniya")
    
    p.line(50, y_position - 5, 550, y_position - 5)
    
    # Товары
    p.setFont(normal_font, 10)
    y_position -= 25
    
    for product in queryset:
        if y_position < 50:
            p.showPage()
            p.setFont(normal_font, 10)
            y_position = height - 50
        
        # Используем только ASCII символы
        brand_name = transliterate_russian(product.brand[:20])
        status_text = "Aktiven" if product.is_active else "Neaktiven"
        
        p.drawString(50, y_position, str(product.sneakers_id))
        p.drawString(100, y_position, brand_name)
        p.drawString(250, y_position, f"{product.price} RUB")
        p.drawString(350, y_position, status_text)
        p.drawString(450, y_position, product.created_at.strftime('%d.%m.%Y'))
        
        y_position -= 20
    
    # Статистика
    y_position -= 20
    p.line(50, y_position, 550, y_position)
    y_position -= 20
    p.setFont(bold_font, 12)
    p.drawString(50, y_position, f"Vsego tovarov: {queryset.count()}")
    
    if queryset.count() > 0:
        avg_price = sum(float(product.price) for product in queryset) / queryset.count()
        p.drawString(300, y_position, f"Srednyaya cena: {avg_price:.2f} RUB")
    
    p.showPage()
    p.save()
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response

generate_products_pdf.short_description = "📄 Сгенерировать PDF каталог"


def transliterate_russian(text):
    """Транслитерация русского текста в латиницу"""
    translit_dict = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'YO',
        'Ж': 'ZH', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'H', 'Ц': 'C', 'Ч': 'CH', 'Ш': 'SH', 'Щ': 'SCH',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'YU', 'Я': 'YA'
    }
    
    result = ''
    for char in text:
        result += translit_dict.get(char, char)
    return result



@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'client_name', 'order_date', 'total_amount', 'status', 'tracking_number']
    list_display_links = ['order_id']
    list_filter = ['status', 'order_date', 'client__last_name']
    search_fields = ['order_id', 'client__last_name', 'client__first_name', 'tracking_number']
    readonly_fields = ['order_date']
    date_hierarchy = 'order_date'
    list_editable = ['status']
    raw_id_fields = ['client', 'shipping_address']
    
    actions = [export_orders_to_excel, generate_orders_pdf]
    
    fieldsets = (
        ('Информация о заказе', {
            'fields': ('client', 'order_date', 'status')
        }),
        ('Финансовая информация', {
            'fields': ('total_amount',)
        }),
        ('Доставка', {
            'fields': ('shipping_address', 'tracking_number')
        }),
        ('Дополнительная информация', {
            'fields': ('contact_info',),
            'classes': ('collapse',)
        }),
    )






@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    list_filter = ['name']
    search_fields = ['name', 'description']
    ordering = ['name']


class ProductCardsInline(admin.StackedInline):
    model = ProductCards
    extra = 0
    fields = ['name', 'size', 'category', 'color', 'material', 'description']


class ReviewsInline(admin.TabularInline):
    model = Reviews
    extra = 0
    readonly_fields = ['created_date', 'rating_stars']
    fields = ['client', 'rating', 'rating_stars', 'comment', 'is_approved', 'created_date']
    raw_id_fields = ['client']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']

@admin.register(ProductTag)
class ProductTagAdmin(admin.ModelAdmin):
    list_display = ['product', 'tag', 'priority', 'added_at']
    list_filter = ['priority', 'added_at', 'tag']
    search_fields = ['product__brand', 'tag__name']
    raw_id_fields = ['product', 'tag']

class ProductTagInline(admin.TabularInline):
    model = ProductTag
    extra = 0
    fields = ['tag', 'priority']

@admin.register(Catalog)
class CatalogAdmin(admin.ModelAdmin):
    list_display = ['sneakers_id', 'brand', 'price', 'image_preview', 'is_active', 'created_at']
    list_display_links = ['sneakers_id', 'brand']
    list_filter = ['brand', 'is_active', 'created_at']
    search_fields = ['brand']
    readonly_fields = ['created_at', 'image_preview']
    date_hierarchy = 'created_at'
    list_editable = ['is_active']
    inlines = [ProductCardsInline, ReviewsInline, ProductTagInline]
    
    actions = [export_catalog_to_excel, generate_orders_pdf]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('brand', 'price', 'is_active')
        }),
        ('Изображение', {
            'fields': ('image', 'image_preview'),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


class OrderInline(admin.TabularInline):
    model = Order
    extra = 0
    readonly_fields = ['order_date', 'total_amount']
    fields = ['order_id', 'order_date', 'total_amount', 'status', 'tracking_number']


class PurchaseInline(admin.TabularInline):
    model = Purchase
    extra = 0
    readonly_fields = ['purchase_date', 'total_cost']
    fields = ['sneakers', 'purchase_date', 'total_cost', 'quantity']
    raw_id_fields = ['sneakers']


class WishlistInline(admin.TabularInline):
    model = Wishlist
    extra = 0
    readonly_fields = ['added_date']
    fields = ['sneakers', 'size', 'quantity', 'added_date']
    raw_id_fields = ['sneakers']


@admin.register(Clients)
class ClientsAdmin(admin.ModelAdmin):
    list_display = ['client_id', 'full_name', 'email', 'phone_number', 'orders_count', 'is_active', 'date_joined']
    list_display_links = ['client_id', 'full_name']
    list_filter = ['is_active', 'date_joined']
    search_fields = ['last_name', 'first_name', 'email', 'phone_number']
    readonly_fields = ['date_joined', 'orders_count']
    date_hierarchy = 'date_joined'
    list_editable = ['is_active']

    actions = [export_clients_to_excel]
    
    fieldsets = (
        ('Личная информация', {
            'fields': ('last_name', 'first_name')
        }),
        ('Контактная информация', {
            'fields': ('email', 'phone_number')
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
        ('Системная информация', {
            'fields': ('date_joined', 'orders_count'),
            'classes': ('collapse',)
        }),
    )
    
    def get_inlines(self, request, obj):
        """Показываем inline-формы только при редактировании существующего клиента"""
        if obj:  # Если клиент уже существует
            return [OrderInline, PurchaseInline, WishlistInline]
        return []  # При создании нового клиента inline-формы не показываем


@admin.register(ProductCards)
class ProductCardsAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand_name', 'price', 'category', 'color', 'material', 'has_store_links']
    list_display_links = ['name']
    list_filter = ['category', 'color', 'material', 'sneakers__brand']
    search_fields = ['name', 'color', 'material', 'sneakers__brand']
    raw_id_fields = ['sneakers']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('sneakers', 'name', 'category')
        }),
        ('Характеристики', {
            'fields': ('size', 'color', 'material')
        }),
        ('Описание', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        # ✅ Новая секция для URL
        ('Ссылки на магазины', {
            'fields': ('official_store_url', 'manufacturer_url'),
            'classes': ('collapse',),
            'description': 'Ссылки на товар в интернет-магазинах'
        }),
    )
    
    # ✅ Добавляем действие для проверки ссылок
    def check_urls_action(self, request, queryset):
        """Проверка доступности URL"""
        import requests
        from django.contrib import messages
        
        checked = 0
        working = 0
        
        for product_card in queryset:
            for name, url in product_card.get_store_links():
                if url:
                    try:
                        response = requests.head(url, timeout=5)
                        if response.status_code == 200:
                            working += 1
                        checked += 1
                    except:
                        checked += 1
        
        messages.success(
            request, 
            f"Проверено {checked} ссылок, работает: {working}"
        )
    
    check_urls_action.short_description = "🔗 Проверить ссылки на магазины"
    actions = [check_urls_action]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['city', 'street', 'house_number', 'apartment', 'postal_code']
    list_display_links = ['city', 'street']
    list_filter = ['city']
    search_fields = ['city', 'street', 'postal_code']
    ordering = ['city', 'street']


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['purchase_id', 'client', 'sneakers', 'purchase_date', 'total_cost', 'quantity']
    list_display_links = ['purchase_id']
    list_filter = ['purchase_date', 'sneakers__brand']
    search_fields = ['client__last_name', 'client__first_name', 'sneakers__brand']
    readonly_fields = ['purchase_date']
    date_hierarchy = 'purchase_date'
    raw_id_fields = ['client', 'sneakers']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('client', 'sneakers', 'quantity')
        }),
        ('Финансовая информация', {
            'fields': ('total_cost',)
        }),
        ('Системная информация', {
            'fields': ('purchase_date', 'contact_info'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['wishlist_id', 'client', 'sneakers', 'size', 'quantity', 'added_date']
    list_display_links = ['wishlist_id']
    list_filter = ['added_date', 'size', 'sneakers__brand']
    search_fields = ['client__last_name', 'client__first_name', 'sneakers__brand']
    readonly_fields = ['added_date']
    date_hierarchy = 'added_date'
    raw_id_fields = ['client', 'sneakers']


@admin.register(Reviews)
class ReviewsAdmin(admin.ModelAdmin):
    list_display = ['review_id', 'client', 'sneakers', 'rating_stars', 'is_approved', 'created_date']
    list_display_links = ['review_id']
    list_filter = ['rating', 'is_approved', 'created_date', 'sneakers__brand']
    search_fields = ['client__last_name', 'client__first_name', 'sneakers__brand', 'comment']
    readonly_fields = ['created_date', 'rating_stars']
    date_hierarchy = 'created_date'
    list_editable = ['is_approved']
    raw_id_fields = ['client', 'sneakers']
    
    actions = [export_reviews_to_excel]

    fieldsets = (
        ('Основная информация', {
            'fields': ('client', 'sneakers', 'rating', 'rating_stars')
        }),
        ('Отзыв', {
            'fields': ('comment', 'is_approved')
        }),
        ('Системная информация', {
            'fields': ('created_date',),
            'classes': ('collapse',)
        }),
    )


class SupportInline(admin.TabularInline):
    model = Support
    extra = 0
    fields = ['last_name', 'first_name', 'patronymic', 'contact_info', 'is_active']


@admin.register(Positions)
class PositionsAdmin(admin.ModelAdmin):
    list_display = ['position_id', 'name', 'salary_min', 'salary_max']
    list_display_links = ['position_id', 'name']
    search_fields = ['name', 'responsibilities']
    inlines = [SupportInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'responsibilities')
        }),
        ('Зарплата', {
            'fields': ('salary_min', 'salary_max'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Support)
class SupportAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'full_name', 'position', 'contact_info', 'is_active', 'hire_date']
    list_display_links = ['employee_id', 'full_name']
    list_filter = ['position', 'is_active', 'hire_date']
    search_fields = ['last_name', 'first_name', 'patronymic', 'contact_info']
    readonly_fields = ['hire_date']
    date_hierarchy = 'hire_date'
    list_editable = ['is_active']
    
    fieldsets = (
        ('Личная информация', {
            'fields': ('last_name', 'first_name', 'patronymic')
        }),
        ('Рабочая информация', {
            'fields': ('position', 'contact_info', 'is_active')
        }),
        ('Системная информация', {
            'fields': ('hire_date',),
            'classes': ('collapse',)
        }),
    )

# Настройка заголовков админки
admin.site.site_header = "Администрирование магазина кроссовок"
admin.site.site_title = "Sneaker Shop Admin"
admin.site.index_title = "Добро пожаловать в панель администрирования"