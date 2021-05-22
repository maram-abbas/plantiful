from django.contrib import admin
from django.urls import path
from plantifultest import views
from django.contrib.auth import views as auth_views
from django.conf.urls import url
from plantifultest.views import update_settings_dropdown

# These are URL patterns for all the pages in our app
urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('app/share/', views.share, name='share'),
    path('app/',views.dashboard,name='dashboard'),
    path('app/newproject/',views.newproject,name='newproject'),
    
    path('change_password/', views.change_password, name='change_password'),
    path('app/newgroup/<str:project_id>/<str:groups_num>/',views.newgroup,name='newgroup'),
    path('app/project_settings/',views.project_settings,name='project_settings'),
    path('app/group_settings/',views.group_settings,name='group_settings'),
  
    path('reset_password/',auth_views.PasswordResetView.as_view(template_name="passwordr.html"), name="reset_password"),
    path('reset_password_sent/',auth_views.PasswordResetDoneView.as_view(template_name="passwordr_done.html"), name="password_reset_done"),
    path('reset/<uidb64>/<token>',auth_views.PasswordResetConfirmView.as_view(template_name="passwordr_confirm.html"), name="password_reset_confirm"),
    path('reset_password_complete/',auth_views.PasswordResetCompleteView.as_view(template_name="passwordr_complete.html"), name="password_reset_complete"),
    
    path('app/newgroup/<str:project_id>/<str:groups_num>/ajax_settings_dropdown', views.update_settings_dropdown)
]