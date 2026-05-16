from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core import api_views

router = DefaultRouter()
router.register(r'projects', api_views.ProjectViewSet, basename='api-project')
router.register(r'tasks', api_views.TaskViewSet, basename='api-task')
router.register(r'users', api_views.UserListViewSet, basename='api-user')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('', include('core.urls')),
]
