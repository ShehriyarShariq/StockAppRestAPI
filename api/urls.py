from os import name
from django.urls import path

from . import views

urlpatterns = [
    ################## AUTH ####################
    path('register_user/', views.register_user, name='register_user'),
    path('check_user/', views.check_user, name='check_user'),
    path('register_admin/', views.register_admin, name='register_admin'),

    ################ CUSTOMER ##################
    path('get_recommended_stocks/', views.get_recommended_stocks, name='get_recommended_stocks'),
    path('place_order/', views.place_order, name='place_order'),
    path('get_customer_orders/', views.get_customer_orders, name='get_customer_orders'),
    path('get_portfolio/', views.get_portfolio, name='get_portfolio'),
    path('add_to_portfolio/', views.add_to_portfolio, name='add_to_portfolio'),

    ################## ADMIN ###################
    path('get_admin_recommendations/', views.get_admin_recommendations, name='get_admin_recommendations'),
    path('make_recommendation/', views.make_recommendation, name='make_recommendation'),
    path('get_admin_orders/', views.get_admin_orders, name='get_admin_orders'),
    path('get_executed_orders/', views.get_executed_orders, name='get_executed_orders'),
    path('update_orders_status/', views.update_orders_status, name='update_orders_status'),

    ################# SESSION ##################
    path('get_events/', views.get_events, name='get_events'),
    path('register_for_event/', views.register_for_event, name='register_for_event'),
    path('create_event/', views.create_event, name='create_event'),

    path('get_videos/', views.get_videos, name='get_videos'),
    path('add_video/', views.add_video, name='add_video'),

    path('get_blogs/', views.get_blogs, name='get_blogs'),
    path('create_blog/', views.create_blog, name='create_blog'),

    ################## MISC ####################
    path('get_contacts/', views.get_contacts, name='get_contacts'),
    path('sync_contacts/', views.sync_contacts, name='sync_contacts'),
    path('search/', views.search, name='search'),
    path('get_notifications/', views.get_notifications, name='get_notifications'),
    path('save_token/', views.save_token, name='save_token'),
    path('try_notif_sender/', views.try_notif_sender, name='try_notif_sender')
]