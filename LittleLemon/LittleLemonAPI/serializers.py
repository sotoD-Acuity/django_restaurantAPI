from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from django.contrib.auth.models import User, Group

from .models import Category, MenuItem, Cart, Order, OrderItem

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields =['id','title']
        
class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), source='category', write_only=True)
    price = serializers.DecimalField(max_digits=6, decimal_places=2)
    
    class Meta:
        model = MenuItem
        fields = ['id','title','featured','price','category', 'category_id']
        extra_kwargs = {
            'price': {'max_digits':6, 'decimal_places':2}
        }
        
class CartSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=serializers.CurrentUserDefault())
    menuitem = MenuItemSerializer(read_only=True)
    menuitem_id = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all(), source='menuitem', write_only=True)
    unit_price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    
    class Meta:
        model = Cart
        fields = ['id','user','menuitem','menuitem_id','quantity','unit_price','price']
        extra_kwargs = {
            'price': {'decimal_places':2, 'max_digits':6},
            'unit_price': {'decimal_places':2, 'max_digits':6},
            'quantity': {'min_value':0, 'max_value':9}
        }
        validators = [
            UniqueTogetherValidator(
                queryset=Cart.objects.all(),
                fields=['user','menuitem_id']
            )
        ]
    
        
class OrderItemSerializer(serializers.ModelSerializer):
    menuitem = MenuItemSerializer()
    
    class Meta:
        model = OrderItem
        fields = ['id','order','menuitem','quantity','unit_price','price']
        validators = [
            UniqueTogetherValidator(
                queryset=OrderItem.objects.all(),
                fields=['order','menuitem']
            )
        ]
        
    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username']
        
class OrderSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=serializers.CurrentUserDefault())
    delivery_crew = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(groups__name='delivery_crew'), default=None, allow_null=True)
    total = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    date = serializers.DateField()
    order_items = OrderItemSerializer(read_only=True)
        
    class Meta:
        model = Order
        fields = ['id','user','delivery_crew','status','total','date','order_items']
        extra_kwargs = {
            'total': {'decimal_places':2, 'max_digits':6}
        }