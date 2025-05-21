from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from .models import Product, Genre, ProductType, ProductVariant
import re
from django.core.files.uploadedfile import UploadedFile

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'artist', 'description', 'image', 'slug', 'genre']
        widgets = {
            'genre': forms.CheckboxSelectMultiple,
            'description': forms.Textarea(attrs={'rows': 4}),
            'slug': forms.TextInput(attrs={'placeholder': 'например, dark-side-of-the-moon'}),
            'image': forms.FileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['genre'].queryset = Genre.objects.all()

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        print(f"Validating slug: {slug}")  # Отладка
        if not re.match(r'^[a-zA-Z0-9_-]+$', slug):
            raise ValidationError("URL-имя может содержать только буквы, цифры, дефисы и подчеркивания.")
        instance = self.instance
        if Product.objects.filter(slug=slug).exclude(id=instance.id if instance else None).exists():
            raise ValidationError("Это URL-имя уже используется. Выберите другое.")
        return slug

    def clean_image(self):
        image = self.cleaned_data.get('image')
        print(f"Image received: {image}")  # Отладка
        if image:
            max_size = 5 * 1024 * 1024  # 5 МБ
            if isinstance(image, UploadedFile):  # Новый загруженный файл
                print(f"New image: size={image.size}, content_type={image.content_type}")
                if image.size > max_size:
                    raise ValidationError("Изображение слишком большое. Максимальный размер: 5 МБ.")
                valid_mime_types = ['image/jpeg', 'image/png', 'image/gif']
                if image.content_type not in valid_mime_types:
                    raise ValidationError("Недопустимый формат файла. Поддерживаются: JPEG, PNG, GIF.")
            else:  # Существующий файл (ImageFieldFile)
                print(f"Existing image: path={image.path}")
                if image.size > max_size:
                    raise ValidationError("Изображение слишком большое. Максимальный размер: 5 МБ.")
                # Пропускаем проверку content_type, так как файл уже загружен
                # Можно добавить проверку типа файла через mimetypes или Pillow, если требуется
        return image

    def clean(self):
        cleaned_data = super().clean()
        print(f"Form cleaned data: {cleaned_data}")  # Отладка
        return cleaned_data

class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['product_type', 'price', 'stock']
        widgets = {
            'product_type': forms.Select,
            'price': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'min': '0'}),
        }

    def clean_price(self):
        price = self.cleaned_data['price']
        if price < 0:
            raise ValidationError("Цена не может быть отрицательной.")
        return price

    def clean_stock(self):
        stock = self.cleaned_data['stock']
        if stock < 0:
            raise ValidationError("Количество на складе не может быть отрицательным.")
        return stock

ProductVariantFormSet = inlineformset_factory(
    Product,
    ProductVariant,
    form=ProductVariantForm,
    extra=1,
    can_delete=True
)