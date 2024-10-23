from django.shortcuts import render
from rest_framework.response import Response
from .models import Userbungry , Alarm , Group
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
import random
import string




# 회원탈퇴 api

class WithdrawView(APIView):
    permission_classes = [IsAuthenticated]  # 인증된 유저만 접근 가능
    authentication_classes = [JWTAuthentication]  # JWT 토큰으로 인증
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
            refresh_token = request.data.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()

            print("블랙리스트에 등록되었습니다 -> 로그아웃")

            return Response(status=status.HTTP_205_RESET_CONTENT)
        
        except Exception as e:
            print(f"로그아웃 오류 발생: {str(e)}")
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

        user = self.request.user

        # 그룹 계정일때, 
        if user.group:
            return Alarm.objects.filter(group=user.group)
        
        # 개인 계정일떄, 
        else:
            return Alarm.objects.filter(id_user=user)
   
    
    def perform_create(self, serializer):
        user = self.request.user
        # user = Userbungry.objects.get(id=1)
        serializer.save(id_user = user , group = user.group)


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




# group 관련 api


# 랜덤으로 그룹 코드 생성해주는 api

class GenerateGroupCodeView(APIView):
    permission_classes = [IsAuthenticated]  # 인증된 유저만 접근 가능
    authentication_classes = [JWTAuthentication]  # JWT 토큰으로 인증
    def generate_group_code(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    def post(self,request):
        while True:
            group_code = self.generate_group_code()
            if not Group.objects.filter(group_code=group_code).exists():
                break
        print("group code 가 정상적으로 생성되었습니다 -> ", group_code)
        return Response({"group_code":group_code}, status=status.HTTP_200_OK)



# group 생성 api - 초기 생성자 해당

class CreateGroupView(APIView):
    permission_classes = [IsAuthenticated]  # 인증된 유저만 접근 가능
    authentication_classes = [JWTAuthentication]  # JWT 토큰으로 인증
    def post(self, request):
        group_code = request.data.get('group_code')
        group_name = request.data.get('group_name')
        user_id = request.data.get('user_id')

        if not group_code or not group_name or not user_id:
            print("error : 모든 필드를 입력해주세요.-> Group 생성 오류")
            return Response({"error :모든 필드를 다 입력해주세요"}, status=status.HTTP_400_BAD_REQUEST)
        
        
        group , created = Group.objects.get_or_create(group_code=group_code, defaults={'group_name':group_name})

        if not created:
            print("error : 이미 존재하는 그룹입니다.")
            return Response({"error :이미 존재하는 그룹입니다"} , status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user= Userbungry.objects.get(id=user_id)
            user.group = group
            user.save()
            print("good : 그룹이 성공적으로 생성되고, 유저에게 원활하게 활당되었습니다")
            return Response({"good : 그룹이 성공적으로 생성되고, 유저에게 할당되었습니다"},status=status.HTTP_200_OK)
        
        except Userbungry.DoesNotExist:
            print("error : 해당 유저를 찾을 수 없습니다")
            return Response ({"error : 해당 유저를 찾을 수 없습니다"})
        



# group 확인 api


class JoinGroupView(APIView):
    permission_classes = [IsAuthenticated]  # 인증된 유저만 접근 가능
    authentication_classes = [JWTAuthentication]  # JWT 토큰으로 인증

    def post(self, request):
        group_code = request.data.get('group_code')
        user_id = request.data.get('user_id')

        try:
            group = Group.objects.get(group_code=group_code)
            user = Userbungry.objects.get(id=user_id)
            user.group = group
            user.save()
            print(f"그룹{group.group_name}에 성공적으로 가입 했습니다.")
            return Response({"message" : f"그룹 {group.group_name}에 성공적으로 가입했습니다"},status=status.HTTP_200_OK)
        
        except Group.DoesNotExist:
            print("유효하지 않은 그룹 코드 입니다 !!!")
            return Response({"error : 유효하지 않은 그룹 코드 입니다."}, status=status.HTTP_400_BAD_REQUEST)
    
        except Userbungry.DoesNotExist:
            return Response({"error : 사용자를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)


class LeaveGroupView(APIView):
    permission_classes = [IsAuthenticated]  # 인증된 유저만 접근 가능
    authentication_classes = [JWTAuthentication]  # JWT 토큰으로 인증

    def post(self,request):
        user = request.user
        group = user.group
        if group:
            user.group = None
            user.save()
            print("그룹에서 탈퇴했습니다")

            # 그룹 인원 수 체킹
            group_member = Userbungry.objects.filter(group=group).count()

            if group_member == 0:
                Alarm.objects.filter(group = group).delete()
                group.delete()
                print("마지막 인원 탈퇴로 인해, 모든 그룹 정보가 삭제되었습니다")
                return Response({"message: 마지막 인원이 탈퇴하여, 그룹관련 정보가 모두 삭제되었습니다."}, status=status.HTTP_200_OK)
            else:
                print("원활하게 그룹에서 탈퇴되엇으며, 아직 인원이 남아있습니다.")
                return Response({"message : group에서 탈퇴했습니다."}, status=status.HTTP_200_OK)
        
        else:
            print("그룹에 속해있지 않습니다")
            return Response({"error : group에 속해있지 않은 사용자입니다."}, status=status.HTTP_400_BAD_REQUEST)