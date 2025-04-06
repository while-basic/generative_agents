from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('simulator_home', views.home, name='simulator_home'),
    path('replay/<str:sim_code>/<int:step>/', views.replay, name='replay'),
    path('replay_persona_state/<str:sim_code>/<int:step>/<str:persona_name>/', views.replay_persona_state, name='replay_persona_state'),
    path('demo/<str:sim_code>/<int:step>/<int:speed>/', views.demo, name='demo'),
    path('path_tester', views.path_tester, name='path_tester'),
    path('process_environment', views.process_environment, name='process_environment'),
    path('update_environment', views.update_environment, name='update_environment'),
    path('path_tester_update', views.path_tester_update, name='path_tester_update'),
]
