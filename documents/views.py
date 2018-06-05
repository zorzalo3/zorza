from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView, UpdateView
from .models import *
from .forms import *

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

@login_required
def create_file(request):
    form = FileForm()
    if request.POST:
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.author = request.user
            obj.save()
            return redirect('my_documents')

    context = {'form': form}

    return render(request, 'edit_file.html', context)

@login_required
def create_document(request):
    form = DocumentForm()
    if request.POST:
        form = DocumentForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.author = request.user
            obj.save()
            return redirect('my_documents')

    context = {'form': form}

    return render(request, 'edit_document.html', context)
