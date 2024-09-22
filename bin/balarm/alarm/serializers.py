from rest_framework import serializers
from .models import Userbungry , Alarm


class UserbungrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Userbungry
        fields = '__all__'



class AlarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alarm
        fields = '__all__'
        #
        read_only_fields = ['id_user']

        