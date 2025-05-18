from django.shortcuts import render, redirect
from django.contrib.auth import logout
from .models import Product, Genre, ProductType, Cart, CartItem, Order, OrderItem, ProductVariant
from django.contrib.auth.decorators import login_required
from django.db import models
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm

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
        # Используем iexact для фильтрации, чтобы игнорировать регистр и корректно работать с кириллицей
        products = products.filter(artist__iexact=selected_artist)

    products_count = products.count()
    if products_count == 0:
        messages.warning(request, "Товаров по выбранным фильтрам не найдено.")
    else:
        messages.success(request, f"Найдено товаров: {products_count}")

    cart_items_count = 0
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart_items_count = CartItem.objects.filter(cart=cart).aggregate(total=models.Sum('quantity'))['total'] or 0

    # Получаем список уникальных исполнителей и сортируем
    # Используем values_list с distinct для корректной работы с кириллицей
    artists = Product.objects.values_list('artist', flat=True).distinct().order_by('artist')

    return render(request, 'index.html', {
        'products': products,
        'genres': genres,
        'product_types': product_types,
        'selected_genre': selected_genre,
        'selected_type': selected_type,
        'selected_artist': selected_artist,
        'cart_items_count': cart_items_count,
        'artists': artists,
    })

def faqs(request):
    return render(request, 'main/faqs.html')

def about(request):
    return render(request, 'main/about.html')

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

    cart_items_count = 0
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart_items_count = CartItem.objects.filter(cart=cart).aggregate(total=models.Sum('quantity'))['total'] or 0

    return render(request, 'index.html', {
        'products': products,
        'genres': Genre.objects.all(),
        'product_types': ProductType.objects.all(),
        'selected_genre': None,
        'selected_type': None,
        'selected_artist': None,
        'cart_items_count': cart_items_count,
        'artists': Product.objects.values_list('artist', flat=True).distinct(),
    })

def product_detail(request, slug):
    product = Product.objects.get(slug=slug)
    return render(request, 'main/product_detail.html', {'product': product})

@login_required
def add_to_cart(request, slug):
    if request.method == 'POST':
        product = Product.objects.get(slug=slug)
        variant_id = request.POST.get('variant')
        variant = ProductVariant.objects.get(id=variant_id)
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
    return render(request, 'main/cart.html', {'cart_items_with_subtotal': cart_items_with_subtotal, 'total': total})

@login_required
def remove_from_cart(request, item_id):
    cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
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
    return render(request, 'main/register.html', {'form': form})

@login_required
def orders(request):
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'main/orders.html', {'orders': user_orders})

@login_required
def delete_order(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    if request.method == 'POST':
        for item in order.orderitem_set.all():
            variant = item.product_variant
            variant.stock += item.quantity
            variant.save()
        order.delete()
        messages.success(request, f"Заказ #{order_id} успешно удалён. Товары возвращены на склад.")
        return redirect('orders')
    return render(request, 'main/confirm_delete.html', {'order': order})

@login_required
def custom_logout(request):
    logout(request)
    messages.success(request, "Вы успешно вышли из системы.")
    return redirect('home')