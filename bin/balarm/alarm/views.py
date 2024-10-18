from django.shortcuts import render
from rest_framework.response import Response
from .models import Userbungry , Alarm
from rest_framework.views import APIView
from .serializers import UserbungrySerializer,AlarmSerializer
from rest_framework import status
from rest_framework import generics
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.views import TokenViewBase
from rest_framework.permissions import IsAuthenticated , AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils import timezone



# 회원탈퇴 api

class WithdrawView(APIView):
    permission_classes =[AllowAny]
    def post(self,request):
        user_id = request.data.get('user_id')
        try:
            user = Userbungry.objects.get(id=user_id)
            user.delete()
            print("회원탈퇴 완료되었습니다")
            return Response({'detail':'회원 탈퇴가 완료되었습니다'}, status=status.HTTP_204_NO_CONTENT)
        except:
            print("유저를 찾을 수 없습니다")
            return Response({'detail' : '유저를 찾을 수 없습니다'}, status=status.HTTP_404_NOT_FOUND)
    


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]  # 인증된 유저만 접근 가능
    authentication_classes = [JWTAuthentication]  

    def post(self,request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            print("블랙리스트에 등록되었습니다 -> 로그아웃")

            return Response(status=status.HTTP_205_RESET_CONTENT)
        
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
    
    

class UserbungrySignUpView(APIView):
    permission_classes =[AllowAny]

    def post(self,request):
        serializer = UserbungrySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            print("회원가입이 완료되었습니다.")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomLoginView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'detail' : 'Please use POST method to log in'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


    def post(self, request):
        b_id = request.data.get('b_id')
        password = request.data.get('password')
        device_type = request.data.get('device_type')

        try: 
            user = Userbungry.objects.get(b_id=b_id)
            user_id = user.id
        except Userbungry.DoesNotExist:
            return Response({'detail':'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if user.password != password:
            return Response({'detail':'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        user.device_type = device_type
        user.save()

        try:
            refresh = RefreshToken.for_user(user)
            print("good")

        except Exception as e:
            print("not good")
            # 정확한 오류 메시지 반환
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        print(refresh.access_token)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user_id':user_id
        })


# fcm 토큰을 받을 부분
class SaveFCMTokenView(APIView):
    permission_classes = [IsAuthenticated]  # 인증된 유저만 접근 가능
    authentication_classes = [JWTAuthentication]  # JWT 토큰으로 인증

    def post(self, request):
        user = request.user  # JWT 토큰을 통해 인증된 유저 정보
        token = request.data.get('fcm_token')

        if user and token:
            # Serializer를 사용하여 FCM 토큰 업데이트
            serializer = UserbungrySerializer(user, data={'fcm_token': token}, partial=True)
            if serializer.is_valid():
                serializer.save()  # 이 부분에서 serializer의 update 메서드 호출
                print("fcm 토큰 저장 완료")
                return Response({"message": "FCM 토큰이 저장되었습니다."}, status=status.HTTP_200_OK)
            return Response({"error": "유저 정보를 업데이트할 수 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": "유저 또는 FCM 토큰이 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)



# 가입한 사람들의 목록을 조회하는 api - user 확인용 test
class UserbungryListAPI(APIView):
    permission_classes =[AllowAny]
    def get(self,request):
        queryset = Userbungry.objects.all()
        print(queryset)
        serializer = UserbungrySerializer(queryset,many = True)
        return Response(serializer.data)


# 알림 관련 api - 생성,수정,삭제,조회(4가지)

# viewset으로 사용하였더니, 알아서 crud 기능 구현 : 개인에 대하여로 변경
class AlarmAPI(viewsets.ModelViewSet):
    serializer_class = AlarmSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]


    def get_queryset(self):


        # user = Userbungry.objects.get(id=1)
        user = self.request.user
        return Alarm.objects.filter(id_user = user)
    
    def perform_create(self, serializer):
        user = self.request.user
        # user = Userbungry.objects.get(id=1)
        serializer.save(id_user = user)


#parameter 가 url에 붙어서 오지 않게 할것 - 보안 문제 !, 나의생각

# 날짜별 알림 정보 api - today 에 대한 알림 api로 사용
class DateAlarmAPI(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    def get(self,request): 

        # date = requeset.query_params.get("date") -> 이부분을, 프론트한테 받아야겠다.
        # date = timezone.now().date()
        date = request.data['date']
        print("오늘날짜", date)

        queryset = Alarm.objects.filter(date__date = date)

        serializer = AlarmSerializer(queryset, many = True)

        print("이 날짜에는 : ",serializer.data)

        return Response(serializer.data , status=status.HTTP_200_OK)

class DateAlarmDetailAPI(APIView):
    # 나의 것만, 수정하고 삭제할 수 있도록
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    def get(self, request, pk = None):
        date = request.data['date']
        alarm = get_object_or_404(Alarm, pk=pk, date__date= date)
        serializer = AlarmSerializer(alarm)
        return Response(serializer.data, status=status.HTTP_200_OK)


    def patch(self,request, pk=None):

        date = request.data['dates']
        id = request.data['user_id']
        try:
            user = Userbungry.objects.get(id=id)
        
        except:
            return Response("수정할 수 없습니다.")

        alarm = get_object_or_404(Alarm, pk=pk, date__date = date)
        if alarm.id_user != user:
            raise PermissionDenied("해당알림을 수정할 권한이 없습니다")
        serializer = AlarmSerializer(alarm, data=request.data, partial = True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request, pk=None):

        date = request.data['dates']
        id = request.data['user_id']
        try:
            user = Userbungry.objects.get(id=id)
        
        except:
            return Response("삭제할 수 없습니다.")
        
        alarm = get_object_or_404(Alarm, pk=pk , date__date =date)
        if alarm.id_user != user:
            raise PermissionDenied("해당 알람을 삭제할 권한이 없습니다")
        alarm.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)





  # Alarm API 초기 버전

   
    #  ------여기까지하면, 수정과 삭제측면에서 다른 사용자것을 건드릴수 있게 된다.----------
    #  수정, 삭제시 내것만 가능하도록
    # 어차피, 나의 것만 보이기 때문에, 남의 것을 볼일이 없기때문에 아래 perform_update와
    # perform_destroy는 존재할 필요가 없다고 생각되어 주석처리

    # def perform_update(self, serializer):
    #     # 업데이트 시 현재 사용자가 알람의 등록자인지 확인
    #     # user = self.request.user
    #     user = Userbungry.objects.get(id=1)
    #     if serializer.instance.id_user != user:
    #         raise PermissionDenied("해당 알람을 수정할 권한이 없습니다.")
    #     serializer.save()  # id_user는 읽기 전용 필드로 설정되어 수정되지 않음

    # def perform_destroy(self, instance):
    #     # 삭제 시 현재 사용자가 알람의 등록자인지 확인
    #     # user = self.request.user
    #     user = Userbungry.objects.get(id=1)
    #     if instance.id_user != user:
    #         raise PermissionDenied("해당 알람을 삭제할 권한이 없습니다.")
    #     instance.delete()
    
  # 아래 코드는, 접근 자체가 안되도록 되어버린다. -> 이건 기획의도가 x
    # def get_object(self):
    #     obj = super().get_object()
    #     user = get_object_or_404(Userbungry , id = 1)

    #     if obj.id_user != user:
    #         raise PermissionError("해당 알림에 접근할 수 없습니다")
    #     return obj


    # generics.CreateAPIView 를 사용했을때의 방식 - create
    # queryset = Alarm.objects.all()
    # serializer_class= AlarmSerializer

    # APIView 를 사용했을때의 방식 - create
    # def post(self,request):
    #     serializer = AlarmSerializer(data = request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data , status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors , status=status.HTTP_400_BAD_REQUEST)