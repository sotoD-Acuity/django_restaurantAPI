from django.urls import path, include
from .views import menuItemView, managerView, removeManagerView, dcView, dcRemoveView, cartView, orderView

urlpatterns = [
    path('menu-items', menuItemView.as_view({'get': 'list', 'post': 'create'})),
    path('menu-items/<int:pk>',menuItemView.as_view({'get':'retrieve', 'put':'update', 'patch':'partial_update', 'delete':'destroy'})),
    path('groups/manager/users', managerView.as_view()),
    path('groups/manager/users/<int:pk>', removeManagerView.as_view()),
    path('groups/delivery-crew/users', dcView.as_view()),
    path('groups/delivery-crew/users/<int:pk>', dcRemoveView.as_view()),
    path('cart/menu-items', cartView.as_view({'get':'list','post':'create', 'delete':'destroy'})),
    path('orders', orderView.as_view({'get':'list','post':'create'})),
    path('orders/<int:pk>', orderView.as_view({'get':'retrieve','put':'update','patch':'partial_update','delete':'destroy'})),
]