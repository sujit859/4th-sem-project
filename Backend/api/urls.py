from django.urls import path
from api import views

urlpatterns = [
    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('profile/', views.profile_view, name='profile'),
    
    # Books
    path('books/', views.books_list_create_view, name='books_list_create'),
    path('books/<int:book_id>/', views.book_detail_view, name='book_detail'),
    
    # Reviews
    path('books/<int:book_id>/reviews/', views.book_reviews_view, name='book_reviews'),
    path('reviews/<int:review_id>/', views.review_detail_view, name='review_detail'),
    path('reviews/', views.all_reviews_list_view, name='all_reviews_list'),
    
    # Admin Specific
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin/reviews/', views.admin_reviews_list_view, name='admin_reviews_list'),
    path('admin/reviews/<int:review_id>/', views.admin_review_detail_view, name='admin_review_detail'),
    path('admin/users/', views.admin_users_list_view, name='admin_users_list'),
    path('admin/users/<int:user_id>/toggle-status/', views.admin_user_toggle_status_view, name='admin_user_toggle_status'),
    path('admin/users/<int:user_id>/make-admin/', views.admin_make_user_admin_view, name='admin_make_user_admin'),
    path('admin/users/<int:user_id>/demote-to-user/', views.admin_demote_user_view, name='admin_demote_user'),
    path('admin/users/<int:user_id>/', views.admin_user_delete_view, name='admin_user_delete'),
]
