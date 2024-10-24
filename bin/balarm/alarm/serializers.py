from rest_framework import serializers
from .models import Userbungry , Alarm
import re

class UserbungrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Userbungry
        fields = '__all__'

    # 로그인 - 한국어 들어가 있지 x
    def validate_b_id(self, value):
        if re.search(r'[ㄱ-ㅎㅏ-ㅣ가-힣]', value):
            print("아이디에, 한국어 들어가면 안돼요")
            raise serializers.ValidationError(1)
        return value

    
    # 비밀번호, 필드 검증 - 8글자 이상이여야,가능 / 한국어 들어가 있지 x
    def validate_password(self, value):
        if len(value) < 8:
            print("비밀번호 8글자 이상이여됩니다.")
            raise serializers.ValidationError(3)
        if re.search(r'[ㄱ-ㅎㅏ-ㅣ가-힣]', value):
            print("비밀번호에, 한국어 들어가면 안돼요")
            raise serializers.ValidationError(2)
        return value
    
    
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

        