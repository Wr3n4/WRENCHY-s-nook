from django.contrib import admin
from django import forms
from .models import ProductType, Genre, Product, Order, OrderItem, Cart, CartItem

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

# Inline для элементов заказа
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    readonly_fields = ['price']
    raw_id_fields = ['product']

# Inline для элементов корзины
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    raw_id_fields = ['product']

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
        return obj.product_set.count()
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
    list_display = ['title', 'artist', 'product_type', 'price', 'stock', 'get_genres']
    list_filter = ['product_type', 'genre']
    search_fields = ['title', 'artist']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['genre']
    list_display_links = ['title', 'artist']
    raw_id_fields = ['product_type']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'

    @admin.display(description="Жанры")
    def get_genres(self, obj):
        return ", ".join([genre.name for genre in obj.genre.all()])
    get_genres.short_description = "Жанры"

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
    list_display = ['order', 'product', 'quantity', 'price']
    list_filter = ['order__status']
    search_fields = ['product__title']
    raw_id_fields = ['order', 'product']
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
    list_display = ['cart', 'product', 'quantity']
    list_filter = ['cart__created_at']
    search_fields = ['product__title']
    raw_id_fields = ['cart', 'product']