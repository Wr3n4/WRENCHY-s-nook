from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('playlists/', views.playlists_view, name='playlists'),
    path('faqs/', views.faqs, name='faqs'),
    path('about/', views.about, name='about'),
    path('search/', views.search, name='search'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('product/<slug:slug>/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('register/', views.register_view, name='register'),
    path('orders/', views.orders, name='orders'),
    path('orders/delete/<int:order_id>/', views.delete_order, name='delete_order'),
    path('logout/', views.custom_logout, name='logout'),
    path('products/', views.product_list, name='product_list'),
    path('product/edit/<slug:slug>/', views.product_edit, name='product_edit'),
    path('product/delete/<slug:slug>/', views.product_delete, name='product_delete'),
    path('product/add/', views.product_add, name='product_add'),
]