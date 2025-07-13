from rest_framework import serializers
from .models import Address

class AddressSerializer(serializers.ModelSerializer):
    """Serializer for the Address model"""
    class Meta:
        model = Address
        fields = [
            'id', 'address_type', 'first_name', 'last_name', 'company',
            'street_address_1', 'street_address_2', 'city', 'state',
            'postal_code', 'country', 'phone', 'is_default', 'created_at',
            'updated_at'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def validate(self, data):
        """
        Validate that only one default address of each type exists per customer.
        """
        if data.get('is_default', False):
            # If this is a new address or an existing one being set as default
            customer = self.context['request'].user.customer_profiles.first()
            
            # Check if there's already a default address of this type
            if hasattr(self, 'instance') and self.instance:
                # For updates, exclude the current instance
                existing_default = Address.objects.filter(
                    customer=customer,
                    address_type=data.get('address_type', self.instance.address_type),
                    is_default=True
                ).exclude(pk=self.instance.pk).exists()
            else:
                # For creates
                existing_default = Address.objects.filter(
                    customer=customer,
                    address_type=data['address_type'],
                    is_default=True
                ).exists()
            
            if existing_default:
                raise serializers.ValidationError({
                    'is_default': f'There is already a default {data["address_type"]} address.'
                })
        
        return data
