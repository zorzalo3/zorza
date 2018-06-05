from django.urls import path

from . import views

urlpatterns = [
    path('', views.show_category, name='documents'),
    path('category/<int:parent_id>/', views.show_category, name='category'),
    path('<int:document_id>/', views.show_document, name='document'),
    path('mine/', views.show_mine, name='my_documents'),
]
