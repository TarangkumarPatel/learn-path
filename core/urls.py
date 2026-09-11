from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('courses/<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('assessments/<int:assessment_id>/', views.assessment_detail, name='assessment_detail'),
    path('goals/<int:goal_id>/update/', views.update_learning_goal, name='update_learning_goal'),
    path('curricula/', views.curriculum_browser, name='curriculum_browser'),
]
