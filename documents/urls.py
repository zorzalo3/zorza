from django.urls import path

from .views import *

urlpatterns = [
    path('', show_category, name='documents'),
    path('category/<int:parent_id>/', show_category, name='category'),
    path('<int:document_id>/', show_document, name='document'),
    path('mine/', show_mine, name='my_documents'),
    path('create-file/', create_file, name='create_file'),
    path('edit-file/<int:file_id>/', edit_file, name='edit_file'),
    path('create-document/', create_document, name='create_document'),
    path('edit-document/<int:document_id>/', edit_document, name='edit_document'),
]
