from django import template
from .models import Product

register = template.Library()

@register.simple_tag
def get_playlists():
    """
    Возвращает словарь с тремя QuerySet'ами для подборок товаров.
    """
    playlists = {
        'new_releases': Product.objects.order_by('-created_at')[:6],           # Новинки
        'popular': Product.objects.order_by('-created_at')[:6],                # Популярное (пока по дате)
        'premium': Product.objects.prefetch_related('productvariant_set')
                   .order_by('-productvariant__price')[:6],                    # Премиум (самые дорогие)
    }
    return playlists
