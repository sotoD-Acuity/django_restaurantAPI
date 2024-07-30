from django.shortcuts import render, get_object_or_404
from rest_framework import views, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.contrib.auth.models import User, Group
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import *
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from .models import MenuItem, Cart, Order, OrderItem
from .serializers import MenuItemSerializer, CartSerializer, OrderSerializer, OrderItemSerializer, UserSerializer


from decimal import Decimal

# Create your views here.
class menuItemView(viewsets.ModelViewSet):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    pagination_class = PageNumberPagination
    pagination_class.page_size = 10
    ordering_fields = ['price']
    search_fields = ['title', 'category__title']
    
    def list(self, request):
        queryset = MenuItem.objects.all()
        filter_category = request.query_params.get('category', None)
        if filter_category is not None:
            queryset = queryset.filter(category__title=filter_category)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)    
        
        serializer = MenuItemSerializer(queryset, many=True)
        return Response(serializer.data, 200)
        
class managerView(views.APIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    def get(self, request):
        if request.user.groups.filter(name="manager").exists():
            managers = Group.objects.get(name='manager').user_set.all()
            serializer = UserSerializer(managers, many=True)
            return Response(serializer.data, 200)
        return Response(status=403)
    
    def post(self, request):
        if request.user.groups.filter(name="manager").exists():
            try:
                user = User.objects.get(username=request.data['username'])
                user.groups.add(Group.objects.get(name='manager'))
                return Response(user.username + " is now a manager", 201)
            except:
                return Response("User does not exist, specify valid user_id",status=404)
        return Response(status=403)
    
class removeManagerView(views.APIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    def delete(self, request, pk):
        if request.user.groups.filter(name="manager").exists():
            try:
                user = User.objects.get(id=pk)
                user.groups.remove(Group.objects.get(name="manager"))
                return Response(user.username + " is no longer a manager.", 200)
            except:
                return Response("Specify valid user_id", 404)
        return Response(status=403)
    
class dcView(views.APIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    def get(self, request):
        if request.user.groups.filter(name="manager").exists():
            crew = Group.objects.get(name='delivery_crew').user_set.all()
            serializer = UserSerializer(crew, many=True)
            return Response(serializer.data, 200)
        return Response(status=403)
    
    def post(self, request):
        if request.user.groups.filter(name="manager").exists():
            try:
                user = User.objects.get(id=request.data['user_id'])
                user.groups.add(Group.objects.get(name='delivery_crew'))
                return Response(user.username + " is now a delivery crew member", 201)
            except:
                return Response("User does not exist, specify valid user_id",status=404)
        return Response(status=403)
    
class dcRemoveView(views.APIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    def delete(self, request, pk):
        if request.user.groups.filter(name="manager").exists():
            try:
                user = User.objects.get(id=pk)
                user.groups.remove(Group.objects.get(name="delivery_crew"))
                return Response(user.username + " is no longer on the delivery crew.", 200)
            except:
                return Response("Specify valid user_id", 404)
        return Response(status=403)
    
class cartView(viewsets.ModelViewSet):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Cart.objects.all().filter(user=self.request.user)
    
    def perform_create(self, serializer):
        menuitem = serializer.validated_data['menuitem']
        quantity = serializer.validated_data['quantity']
        unit_price = menuitem.price
        price = unit_price * Decimal(quantity)
        serializer.save(
            user = self.request.user,
            unit_price = unit_price,
            price = price
        )
    
    def destroy(self, pk):
        cart = Cart.objects.all().filter(user=self.request.user)
        cart.delete()
        return Response(status=204)
    
class orderView(viewsets.ModelViewSet):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    pagination_class.page_size = 20
    ordering_fields = ['price', 'date', 'total', 'delivery_crew']
    search_fields = ['status', 'date', 'delivery_crew__username']
    filterset_fields = ['status', 'date', 'delivery_crew']
    
    # We want to return each order with the order items when a manager makes a GET request. We can do this by overriding the list method.
    def list(self, request):
        if request.user.groups.filter(name="manager").exists():
            orders = Order.objects.all()
            serializer = OrderSerializer(orders, many=True)
            for order in serializer.data:
                order_items = OrderItem.objects.all().filter(order=order['id'])
                order['order_items'] = OrderItemSerializer(order_items, many=True).data
            return Response(serializer.data, 200)
        elif request.user.groups.filter(name="delivery_crew").exists():
            # If the user is a delivery crew member, return all orders assigned to any delivery crew member
            orders = Order.objects.all().filter(delivery_crew=request.user)
            serializer = OrderSerializer(orders, many=True)
            for order in serializer.data:
                order_items = OrderItem.objects.all().filter(order=order['id'])
                order['order_items'] = OrderItemSerializer(order_items, many=True).data
            return Response(serializer.data, 200)
        elif request.user.is_authenticated:
            orders = Order.objects.all().filter(user=request.user)
            serializer = OrderSerializer(orders, many=True)
            for order in serializer.data:
                order_items = OrderItem.objects.all().filter(order=order['id'])
                order['order_items'] = OrderItemSerializer(order_items, many=True).data
            return Response(serializer.data, 200)
    
    def perform_create(self, serializer):
        cart_items = Cart.objects.all().filter(user=self.request.user)
        total = Decimal(0)
        for item in cart_items:
            total += item.price
        if total == 0:
            raise ValidationError("Cart is empty", 400)
        serializer.save(
            user = self.request.user,
            total = total
        )
        
        for item in cart_items:
            OrderItem.objects.create(
                order = serializer.instance,
                menuitem = item.menuitem,
                quantity = item.quantity,
                unit_price = item.unit_price,
                price = item.price
            )
        cart_items.delete()
        return Response(serializer.data, 201)
        
    def retrieve(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if request.user == order.user or request.user.groups.filter(name="manager").exists():
            order_items = OrderItem.objects.all().filter(order=order)
            serializer = OrderItemSerializer(order_items, many=True)
            return Response(serializer.data, 200)
        return Response(status=403)
    
    def perform_update(self, serializer):
        if self.request.user.groups.filter(name='manager').exists():
            serializer.save()
        elif self.request.user.groups.filter(name='delivery_crew').exists():
            if len(self.request.data) == 1 and 'status' in self.request.data:
                serializer.save()
            else:
                raise ValidationError({"detail": "Delivery crew can only update the status field."}, 400)
            
    def destroy(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if request.user.groups.filter(name="manager").exists():
            order.delete()
            return Response(status=204)
        return Response(status=403)