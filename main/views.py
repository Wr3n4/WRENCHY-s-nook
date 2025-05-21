from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db import models
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from .models import Product, Genre, ProductType, Cart, CartItem, Order, OrderItem, ProductVariant
from .forms import ProductForm  # Будет создан ниже

# Вспомогательная функция для вычисления cart_items_count
def get_cart_items_count(request):
    cart_items_count = 0
    user = request.user
    if user.is_authenticated:
        cart = Cart.objects.filter(user=user).first()
        if cart:
            result = CartItem.objects.filter(cart=cart).aggregate(total_quantity=models.Sum('quantity'))
            cart_items_count = result['total_quantity'] or 0
    return cart_items_count

def home(request):
    genres = Genre.objects.all()
    product_types = ProductType.objects.all()

    products = Product.objects.all()
    selected_genre = request.GET.get('genre')
    selected_type = request.GET.get('type')
    selected_artist = request.GET.get('artist')

    if selected_genre:
        products = products.filter(genre__id=selected_genre)
    if selected_type:
        products = products.filter(productvariant__product_type__id=selected_type).distinct()
    if selected_artist:
        products = products.filter(artist__iexact=selected_artist)

    products_count = products.count()
    if products_count == 0:
        messages.warning(request, "Товаров по выбранным фильтрам не найдено.")
    else:
        messages.success(request, f"Найдено товаров: {products_count}")

    artists = Product.objects.values_list('artist', flat=True).distinct().order_by('artist')

    return render(request, 'index.html', {
        'products': products,
        'genres': genres,
        'product_types': product_types,
        'selected_genre': selected_genre,
        'selected_type': selected_type,
        'selected_artist': selected_artist,
        'cart_items_count': get_cart_items_count(request),
        'artists': artists,
    })

def faqs(request):
    return render(request, 'main/faqs.html', {
        'cart_items_count': get_cart_items_count(request),
    })

def about(request):
    return render(request, 'main/about.html', {
        'cart_items_count': get_cart_items_count(request),
    })

def playlists_view(request):
    rock_products = Product.objects.filter(genre__name="Рок").order_by('-created_at')[:5]
    jazz_products = Product.objects.filter(genre__name="Джаз").order_by('-created_at')[:5]
    classical_products = Product.objects.filter(genre__name="Классика").prefetch_related('productvariant_set').order_by('-productvariant__price')[:5]

    context = {
        'rock_products': rock_products,
        'jazz_products': jazz_products,
        'classical_products': classical_products,
        'cart_items_count': get_cart_items_count(request),
    }
    return render(request, 'playlists.html', context)

def search(request):
    query = request.GET.get('q', '')
    products = Product.objects.all()

    if query:
        products = products.filter(models.Q(title__icontains=query) | models.Q(artist__icontains=query))

    products_count = products.count()
    if products_count == 0:
        messages.warning(request, "По вашему запросу ничего не найдено.")
    else:
        messages.success(request, f"Найдено товаров: {products_count}")

    return render(request, 'index.html', {
        'products': products,
        'genres': Genre.objects.all(),
        'product_types': ProductType.objects.all(),
        'selected_genre': None,
        'selected_type': None,
        'selected_artist': None,
        'cart_items_count': get_cart_items_count(request),
        'artists': Product.objects.values_list('artist', flat=True).distinct(),
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    variants = product.productvariant_set.all()
    return render(request, 'main/product_detail.html', {
        'product': product,
        'variants': variants,
        'cart_items_count': get_cart_items_count(request),
    })

@login_required
def product_list(request):
    products = Product.objects.all()
    return render(request, 'main/product_list.html', {
        'products': products,
        'cart_items_count': get_cart_items_count(request),
    })

@login_required
def product_edit(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"Продукт '{product.title}' успешно обновлён.")
            return redirect('product_detail', slug=slug)
    else:
        form = ProductForm(instance=product)
    return render(request, 'main/product_edit.html', {
        'form': form,
        'product': product,
        'cart_items_count': get_cart_items_count(request),
    })

@login_required
def product_delete(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if request.method == 'POST':
        product.delete()
        messages.success(request, f"Продукт '{product.title}' успешно удалён.")
        return redirect('product_list')
    return render(request, 'main/product_delete.html', {
        'product': product,
        'cart_items_count': get_cart_items_count(request),
    })

@login_required
def product_add(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Новый продукт '{product.title}' успешно добавлен.")
            return redirect('product_detail', slug=product.slug)
    else:
        form = ProductForm()
    return render(request, 'main/product_add.html', {
        'form': form,
        'cart_items_count': get_cart_items_count(request),
    })

@login_required
def add_to_cart(request, slug):
    if request.method == 'POST':
        product = get_object_or_404(Product, slug=slug)
        variant_id = request.POST.get('variant')
        variant = get_object_or_404(ProductVariant, id=variant_id)
        if variant.stock < 1:
            messages.error(request, f"Товар {product.title} ({variant.product_type.name}) закончился на складе.")
            return redirect('product_detail', slug=slug)
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product_variant=variant)
        if not created:
            if cart_item.quantity + 1 <= variant.stock:
                cart_item.quantity += 1
                cart_item.save()
            else:
                messages.warning(request, f"Нельзя добавить больше {variant.stock} единиц {product.title}.")
                return redirect('product_detail', slug=slug)
        else:
            cart_item.quantity = 1
            cart_item.save()
        variant.stock -= 1
        variant.save()
        messages.success(request, f"Добавлено в корзину: {product.title} ({variant.product_type.name})")
    return redirect('home')

@login_required
def cart(request):
    cart = Cart.objects.filter(user=request.user).first()
    cart_items = CartItem.objects.filter(cart=cart) if cart else []
    cart_items_with_subtotal = [
        {'item': item, 'subtotal': item.product_variant.price * item.quantity}
        for item in cart_items
    ]
    total = sum(item['subtotal'] for item in cart_items_with_subtotal)
    return render(request, 'main/cart.html', {
        'cart_items_with_subtotal': cart_items_with_subtotal,
        'total': total,
        'cart_items_count': get_cart_items_count(request),
    })

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    variant = cart_item.product_variant
    variant.stock += cart_item.quantity
    variant.save()
    messages.success(request, f"Удалено из корзины: {cart_item.product_variant.product.title}")
    cart_item.delete()
    return redirect('cart')

@login_required
def checkout(request):
    cart = Cart.objects.filter(user=request.user).first()
    if cart and CartItem.objects.filter(cart=cart).exists():
        order = Order.objects.create(user=request.user, total_price=0, status='processing')
        total = 0
        for item in CartItem.objects.filter(cart=cart):
            price = item.product_variant.price * item.quantity
            OrderItem.objects.create(order=order, product_variant=item.product_variant, quantity=item.quantity, price=price)
            total += price
        order.total_price = total
        order.save()
        cart.delete()
        messages.success(request, 'Заказ успешно оформлен!')
        return redirect('home')
    else:
        messages.warning(request, 'Корзина пуста. Добавьте товары перед оформлением заказа.')
        return redirect('cart')

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Регистрация прошла успешно! Теперь вы можете войти.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'main/register.html', {
        'form': form,
        'cart_items_count': get_cart_items_count(request),
    })

@login_required
def orders(request):
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'main/orders.html', {
        'orders': user_orders,
        'cart_items_count': get_cart_items_count(request),
    })

@login_required
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if request.method == 'POST':
        for item in order.orderitem_set.all():
            variant = item.product_variant
            variant.stock += item.quantity
            variant.save()
        order.delete()
        messages.success(request, f"Заказ #{order_id} успешно удалён. Товары возвращены на склад.")
        return redirect('orders')
    return render(request, 'main/confirm_delete.html', {
        'order': order,
        'cart_items_count': get_cart_items_count(request),
    })

@login_required
def custom_logout(request):
    logout(request)
    messages.success(request, "Вы успешно вышли из системы.")
    return redirect('home')