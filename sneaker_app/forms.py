from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import (
    Catalog, ProductCards, Category, Reviews, Clients, 
    Order, Address, Tag, ProductTag
)

class SearchForm(forms.Form):
    """Форма поиска товаров - обязательное требование"""
    query = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Поиск кроссовок по бренду, названию, цвету...',
            'id': 'search-input'
        }),
        label='',
        help_text='Введите название бренда, модели или характеристики'
    )
    
    def clean_query(self):
        query = self.cleaned_data['query']
        if len(query) < 2:
            raise ValidationError('Поисковый запрос должен содержать минимум 2 символа')
        return query

class ProductFilterForm(forms.Form):
    """Форма фильтрации товаров"""
    brand = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Бренд'
        })
    )
    
    price_min = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Цена от'
        })
    )
    
    price_max = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Цена до'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="Все категории",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

class ReviewForm(forms.ModelForm):
    """Форма для отзывов"""
    class Meta:
        model = Reviews
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={
                'class': 'form-select'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Поделитесь своим мнением о товаре...'
            })
        }
        labels = {
            'rating': 'Оценка',
            'comment': 'Комментарий'
        }

# Остальные формы остаются без изменений...
class ProductForm(forms.ModelForm):
    """Форма создания/редактирования товара"""
    
    class Meta:
        model = Catalog
        fields = ['brand', 'price', 'image', 'is_active']
        
        widgets = {
            'brand': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Введите название бренда'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'step': '0.01',
                'min': '0'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
        labels = {
            'brand': 'Бренд кроссовок',
            'price': 'Цена (в рублях)',
            'image': 'Изображение товара',
            'is_active': 'Товар активен'
        }
        
        help_texts = {
            'brand': 'Укажите официальное название бренда',
            'price': 'Цена должна быть больше 0',
            'image': 'Загрузите качественное изображение товара',
            'is_active': 'Неактивные товары не отображаются в каталоге'
        }
        
        error_messages = {
            'brand': {
                'required': 'Название бренда обязательно для заполнения',
                'max_length': 'Название бренда не может превышать 100 символов'
            },
            'price': {
                'required': 'Цена товара обязательна для заполнения',
                'invalid': 'Введите корректную цену'
            }
        }
    
    class Media:
        css = {
            'all': ('css/forms.css',)
        }
        js = ('js/forms.js',)
    
    def clean_price(self):
        price = self.cleaned_data['price']
        if price <= 0:
            raise ValidationError('Цена должна быть больше нуля')
        if price > 1000000:
            raise ValidationError('Цена не может превышать 1,000,000 рублей')
        return price
    
    def clean_brand(self):
        brand = self.cleaned_data['brand']
        if len(brand) < 2:
            raise ValidationError('Название бренда должно содержать минимум 2 символа')
        return brand.title()
    
    def clean(self):
        cleaned_data = super().clean()
        brand = cleaned_data.get('brand')
        price = cleaned_data.get('price')
        
        # Проверка премиум брендов
        premium_brands = ['Nike', 'Adidas', 'Jordan']
        if brand and price:
            if brand in premium_brands and price < 5000:
                raise ValidationError(
                    f"Для премиум бренда {brand} минимальная цена должна быть 5000 рублей"
                )
        
        return cleaned_data


class ProductCardForm(forms.ModelForm):
    """
    Форма для карточки товара с кастомными виджетами
    """
    
    class Meta:
        model = ProductCards
        fields = ['name', 'size', 'category', 'color', 'material', 'description']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Полное название модели'
            }),
            'size': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: 36, 37, 38, 39, 40'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Основной цвет'
            }),
            'material': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Материал верха'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Подробное описание товара...'
            })
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 5:
            raise ValidationError("Название должно содержать минимум 5 символов")
        return name


class ReviewForm(forms.ModelForm):
    """
    Форма для отзывов с кастомным виджетом для рейтинга
    """
    
    class Meta:
        model = Reviews
        fields = ['rating', 'comment']
        
        widgets = {
            'rating': forms.RadioSelect(
                choices=Reviews.RATING_CHOICES,
                attrs={'class': 'rating-radio'}
            ),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Поделитесь своим мнением о товаре...',
                'maxlength': '1000'
            })
        }
        
        labels = {
            'rating': 'Ваша оценка',
            'comment': 'Ваш отзыв'
        }
    
    def clean_comment(self):
        comment = self.cleaned_data.get('comment')
        
        if len(comment) < 10:
            raise ValidationError("Отзыв должен содержать минимум 10 символов")
        
        # Проверяем на спам-слова
        spam_words = ['спам', 'реклама', 'купить дешево']
        if any(word.lower() in comment.lower() for word in spam_words):
            raise ValidationError("Отзыв содержит недопустимый контент")
        
        return comment


class ClientForm(forms.ModelForm):
    """
    Форма для регистрации клиентов
    """
    
    class Meta:
        model = Clients
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваше имя'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваша фамилия'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'example@email.com'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (999) 123-45-67'
            })
        }
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        
        # Убираем все символы кроме цифр и +
        import re
        cleaned_phone = re.sub(r'[^\d+]', '', phone)
        
        # Проверяем формат российского номера
        if not re.match(r'^\+7\d{10}$', cleaned_phone):
            raise ValidationError("Введите корректный российский номер телефона")
        
        return cleaned_phone


class OrderForm(forms.ModelForm):
    """
    Форма для создания заказов с демонстрацией save(commit=False)
    """
    
    # Дополнительные поля, которых нет в модели
    delivery_notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Особые пожелания по доставке...'
        }),
        label='Примечания к доставке'
    )
    
    agree_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Согласен с условиями доставки'
    )
    
    class Meta:
        model = Order
        fields = ['shipping_address', 'contact_info']
        
        widgets = {
            'shipping_address': forms.Select(attrs={
                'class': 'form-control'
            }),
            'contact_info': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Дополнительная контактная информация'
            })
        }
    
    def save(self, commit=True):
        """
        Демонстрация save() с commit=False
        """
        # Получаем объект, но не сохраняем в БД
        order = super().save(commit=False)
        
        # Добавляем кастомную логику
        delivery_notes = self.cleaned_data.get('delivery_notes')
        if delivery_notes:
            # Добавляем примечания к контактной информации
            if order.contact_info:
                order.contact_info += f" | Примечания: {delivery_notes}"
            else:
                order.contact_info = f"Примечания: {delivery_notes}"
        
        # Устанавливаем статус по умолчанию
        if not order.status:
            order.status = 'pending'
        
        # Сохраняем только если commit=True
        if commit:
            order.save()
            # Дополнительная логика после сохранения
            print(f"Создан заказ №{order.order_id} для {order.client}")
        
        return order


class AddressForm(forms.ModelForm):
    """
    Форма для адресов доставки
    """
    
    class Meta:
        model = Address
        fields = ['city', 'street', 'house_number', 'apartment', 'postal_code']
        
        widgets = {
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Город'
            }),
            'street': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Улица'
            }),
            'house_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Дом'
            }),
            'apartment': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Квартира (необязательно)'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '123456'
            })
        }
    
    def clean_postal_code(self):
        postal_code = self.cleaned_data.get('postal_code')
        
        # Проверяем, что почтовый индекс состоит из 6 цифр
        if not postal_code.isdigit() or len(postal_code) != 6:
            raise ValidationError("Почтовый индекс должен состоять из 6 цифр")
        
        return postal_code


class TagForm(forms.ModelForm):
    """
    Форма для тегов товаров
    """
    
    class Meta:
        model = Tag
        fields = ['name', 'color']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название тега'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'style': 'height: 40px;'
            })
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        
        # Проверяем уникальность (с учетом регистра)
        if Tag.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Тег с таким названием уже существует")
        
        return name.lower()  # Сохраняем в нижнем регистре


class ProductTagForm(forms.ModelForm):
    """
    Форма для связи товаров и тегов (ManyToMany через through)
    """
    
    class Meta:
        model = ProductTag
        fields = ['tag', 'priority']
        
        widgets = {
            'tag': forms.Select(attrs={
                'class': 'form-control'
            }),
            'priority': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'placeholder': 'Приоритет (0-100)'
            })
        }
    
    def clean_priority(self):
        priority = self.cleaned_data.get('priority')
        
        if priority < 0 or priority > 100:
            raise ValidationError("Приоритет должен быть от 0 до 100")
        
        return priority


# Дополнительная форма для демонстрации работы с несколькими моделями
class ProductWithCardForm(forms.Form):
    """
    Комбинированная форма для создания товара и его карточки одновременно
    Демонстрация работы с несколькими моделями
    """
    
    # Поля для Catalog
    brand = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Бренд'
        })
    )
    price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Цена'
        })
    )
    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    
    # Поля для ProductCards
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Название модели'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    color = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Цвет'
        })
    )
    material = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Материал'
        })
    )
    size = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Размеры'
        })
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Описание'
        })
    )
    
    def clean_brand(self):
        brand = self.cleaned_data.get('brand')
        if len(brand) < 2:
            raise ValidationError("Название бренда слишком короткое")
        return brand.title()
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise ValidationError("Цена должна быть больше нуля")
        return price
    
    def save(self):
        """
        Кастомный метод save для создания двух связанных объектов
        """
        # Создаем товар
        catalog = Catalog.objects.create(
            brand=self.cleaned_data['brand'],
            price=self.cleaned_data['price'],
            image=self.cleaned_data.get('image')
        )
        
        # Создаем карточку товара
        product_card = ProductCards.objects.create(
            sneakers=catalog,
            name=self.cleaned_data['name'],
            category=self.cleaned_data['category'],
            color=self.cleaned_data['color'],
            material=self.cleaned_data['material'],
            size=self.cleaned_data['size'],
            description=self.cleaned_data.get('description', '')
        )
        
        return catalog, product_card

# ✅ ДОБАВЛЯЕМ В КОНЕЦ ФАЙЛА - форма для демонстрации Django field методов

class DemoFieldForm(forms.ModelForm):
    """
    Форма для демонстрации {{ field.label_tag }}, {{ field }}, {{ field.errors }}
    """
    
    # Дополнительное поле с Textarea
    special_notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Особые заметки о товаре...'
        }),
        label='Специальные заметки',
        help_text='Дополнительная информация о товаре'
    )
    
    class Meta:
        model = Catalog
        fields = ['brand', 'price', 'image', 'is_active']
        exclude = []  # ✅ Добавляем exclude для демонстрации
        
        widgets = {
            'brand': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название бренда'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
        labels = {
            'brand': 'Бренд товара (Django field)',
            'price': 'Цена товара (Django field)',
            'image': 'Изображение (Django field)',
            'is_active': 'Активный товар (Django field)'
        }
        
        help_texts = {
            'brand': 'Используется {{ field.label_tag }}',
            'price': 'Используется {{ field }}',
            'image': 'Используется {{ field.errors }}',
            'is_active': 'Django field методы'
        }
        
        error_messages = {
            'brand': {
                'required': 'Поле обязательно (через Django field)',
                'max_length': 'Слишком длинное название'
            },
            'price': {
                'required': 'Цена обязательна (Django field)',
                'invalid': 'Некорректная цена'
            }
        }
    
    def clean_brand(self):
        brand = self.cleaned_data['brand']
        if len(brand) < 2:
            raise ValidationError('Название бренда слишком короткое (Django validation)')
        return brand.title()
