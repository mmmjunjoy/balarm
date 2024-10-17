from rest_framework import serializers
from .models import Userbungry , Alarm


class UserbungrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Userbungry
        fields = '__all__'
    
    def create(self, validated_data):
        user = Userbungry.objects.create(**validated_data)
        return user

    def update(self, instance, validated_data):
        # fcm_token 업데이트 로직 추가
        fcm_token = validated_data.get('fcm_token', None)
        if fcm_token is not None:
            instance.fcm_token = fcm_token
        instance.save()
        return instance



class AlarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alarm
        fields = '__all__'
        
        read_only_fields = ['id_user']

        