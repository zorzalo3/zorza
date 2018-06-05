from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import *

def show_category(request, parent_id=None):
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
    return render(request, 'show_category.html', context)

def show_document(request, document_id):
    document = get_object_or_404(Document, pk=document_id)
    context = {
        'document': document,
    }
    return render(request, 'show_document.html', context)

@login_required
def show_mine(request):
    items = Item.objects.filter(author=request.user).select_related('category')
    context = {
        'items': items,
    }
    return render(request, 'show_mine.html', context)
