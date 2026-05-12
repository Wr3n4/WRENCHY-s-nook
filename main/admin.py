from django.contrib import admin
from django import forms
from .models import ProductType, Genre, Product, ProductVariant, Order, OrderItem, Cart, CartItem, Srexam
from django.http import HttpResponse
from django.template.loader import render_to_string
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

class ProductTypeForm(forms.ModelForm):
    class Meta:
        model = ProductType
        fields = ['name', 'slug']

class GenreForm(forms.ModelForm):
    class Meta:
        model = Genre
        fields = ['name', 'slug']

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ['product_type', 'price', 'stock']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    readonly_fields = ['price']
    fields = ['product_variant', 'quantity', 'price']

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    fields = ['product_variant', 'quantity']

@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    form = ProductTypeForm
    list_display = ['name', 'slug', 'product_count']
    list_filter = ['name']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    fields = ['name', 'slug']

    @admin.display(description="Количество товаров")
    def product_count(self, obj):
        return obj.productvariant_set.count()
    product_count.short_description = "Количество товаров"

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    form = GenreForm
    list_display = ['name', 'slug', 'product_count']
    list_filter = ['name']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    fields = ['name', 'slug']

    @admin.display(description="Количество товаров")
    def product_count(self, obj):
        return obj.product_set.count()
    product_count.short_description = "Количество товаров"

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'artist', 'get_product_types', 'get_genres']
    list_filter = ['genre']
    search_fields = ['title', 'artist']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['genre',]
    list_display_links = ['title', 'artist']
    inlines = [ProductVariantInline]
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'

    @admin.display(description="Типы товара")
    def get_product_types(self, obj):
        return ", ".join([pt.name for pt in obj.product_type.all()])
    get_product_types.short_description = "Типы товара"

    @admin.display(description="Жанры")
    def get_genres(self, obj):
        return ", ".join([genre.name for genre in obj.genre.all()])
    get_genres.short_description = "Жанры"

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'product_type', 'price', 'stock']
    list_filter = ['product_type']
    search_fields = ['product__title', 'product_type__name']
    raw_id_fields = ['product', 'product_type']


def register_fonts():
    font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'DejaVuSans.ttf')

    # Если шрифт DejaVuSans не найден, используем встроенный (менее надёжно)
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
        pdfmetrics.registerFontFamily('DejaVuSans', normal='DejaVuSans')
    else:
        # Fallback — используем стандартный шрифт с кириллицей
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))  # будет искать в системе


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_price', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'user__email']
    ordering = ['-created_at']

    actions = ['generate_pdf']

    def generate_pdf(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Выберите только ОДИН заказ для генерации PDF", level='warning')
            return

        # Регистрируем шрифт перед генерацией
        register_fonts()

        order = queryset.first()
        items = order.orderitem_set.all()

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Заказ_{order.id}.pdf"'

        doc = SimpleDocTemplate(response, pagesize=A4, leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=50)
        styles = getSampleStyleSheet()

        # Создаём стиль с поддержкой русского языка
        title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], fontName='DejaVuSans', fontSize=18)
        normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontName='DejaVuSans', fontSize=11)
        heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading2'], fontName='DejaVuSans', fontSize=14)

        elements = []

        elements.append(Paragraph("WЯENCHY's nook", title_style))
        elements.append(Paragraph(f"Товарный чек № {order.id}", heading_style))
        elements.append(Spacer(1, 20))

        elements.append(Paragraph(f"<b>Дата:</b> {order.created_at.strftime('%d.%m.%Y %H:%M')}", normal_style))
        elements.append(
            Paragraph(f"<b>Покупатель:</b> {order.user.get_full_name or order.user.username}", normal_style))
        elements.append(Paragraph(f"<b>Email:</b> {order.user.email}", normal_style))
        elements.append(Spacer(1, 20))

        # Таблица
        data = [['Товар', 'Формат', 'Кол-во', 'Цена', 'Сумма']]
        for item in items:
            data.append([
                item.product_variant.product.title,
                item.product_variant.product_type.name,
                str(item.quantity),
                f"{item.price} ₽",
                f"{item.price * item.quantity} ₽"
            ])

        table = Table(data, colWidths=[200, 80, 50, 70, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans'),
            ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSans'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(f"<b>Итого к оплате: {order.total_price} ₽</b>", heading_style))

        doc.build(elements)
        return response

    generate_pdf.short_description = "📄 Сгенерировать PDF чек"
    generate_pdf.allowed_permissions = ['change']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_variant', 'quantity', 'price']
    list_filter = ['order__status']
    search_fields = ['product_variant__product__title']
    fields = ['order', 'product_variant', 'quantity', 'price']
    readonly_fields = ['price']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'item_count']
    list_filter = ['created_at']
    search_fields = ['user__username']
    inlines = [CartItemInline]
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']

    @admin.display(description="Количество товаров")
    def item_count(self, obj):
        return obj.cartitem_set.count()
    item_count.short_description = "Количество товаров"

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product_variant', 'quantity']
    list_filter = ['cart__created_at']
    search_fields = ['product_variant__product__title']
    fields = ['cart', 'product_variant', 'quantity']

@admin.register(Srexam)
class SrexamAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'exam_date', 'is_public')
    list_filter = ('is_public', 'created_at')
    search_fields = ('title', 'users__email')
    filter_horizontal = ('users',)
    date_hierarchy = 'exam_date'
    fieldsets = (
        (None, {
            'fields': ('title', 'image', 'is_public')
        }),
        ('Даты', {
            'fields': ('created_at', 'exam_date'),
        }),
        ('Пользователи', {
            'fields': ('users',),
        }),
    )
    readonly_fields = ('created_at',)