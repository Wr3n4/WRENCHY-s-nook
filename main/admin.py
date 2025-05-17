from django.contrib import admin
from django import forms
from .models import ProductType, Genre, Product, ProductVariant, Order, OrderItem, Cart, CartItem

# Форма для ProductType
class ProductTypeForm(forms.ModelForm):
    class Meta:
        model = ProductType
        fields = ['name', 'slug']

# Форма для Genre
class GenreForm(forms.ModelForm):
    class Meta:
        model = Genre
        fields = ['name', 'slug']

# Inline для вариантов товара
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1  # Одна автоматическая строка
    fields = ['product_type', 'price', 'stock']

# Inline для элементов заказа
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1  # Одна автоматическая строка
    readonly_fields = ['price']
    fields = ['product_variant', 'quantity', 'price']

# Inline для элементов корзины
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1  # Одна автоматическая строка
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
    filter_horizontal = ['genre']
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

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'status', 'total_price']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'id']
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at', 'total_price']
    list_display_links = ['id', 'user']

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