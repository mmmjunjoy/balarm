"""
URL configuration for balarm project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path , include
from alarm.views import UserbungryListAPI , AlarmAPI , DateAlarmAPI ,DateAlarmDetailAPI, CustomLoginView, UserbungrySignUpView, SaveFCMTokenView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView




router = DefaultRouter()
router.register(r'alarms', AlarmAPI , basename='alarm')

urlpatterns = [
    path('api/signup/', UserbungrySignUpView.as_view()),
    path('api/fcm/', SaveFCMTokenView.as_view()),
    path('api/token/', CustomLoginView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/' , TokenRefreshView.as_view(), name="token_refresh"),
    path('admin/', admin.site.urls),
    path('api/buser/',UserbungryListAPI.as_view()),
    path('api/', include(router.urls)),
    path('api/date/',DateAlarmAPI.as_view() , name='date-alarm-list'),
    path('api/date/<int:pk>/', DateAlarmDetailAPI.as_view() , name='date-alarm-detail')
]
