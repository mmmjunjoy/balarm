from rest_framework import serializers
from .models import Userbungry , Alarm


class UserbungrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Userbungry
        fields = '__all__'
    
    def create(self, validated_data):
        user = Userbungry.objects.create(**validated_data)
        return user



class AlarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alarm
        fields = '__all__'
        
        read_only_fields = ['id_user']

        