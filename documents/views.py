from django.shortcuts import render, get_object_or_404
from .models import *

def show_categories(request, parent_id = None):
    try:
        parent = Category.objects.get(pk=parent_id)
    except:
        parent = None
    categories = Category.objects.filter(parent=parent)

    context = {
        'parent': parent,
        'categories': categories,
        'items': Item.objects.filter(category=parent)
    }
    return render(request, 'category_list.html', context)
