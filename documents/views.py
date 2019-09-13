from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.decorators.cache import never_cache
from django.urls import reverse_lazy
from .models import *
from .forms import *

@never_cache
def show_category(request, parent_id=None):
    try:
        parent = Category.objects.get(pk=parent_id)
    except:
        parent = None
    categories = Category.objects.filter(parent=parent)

    items = Item.objects.filter(category=parent)
    if parent and parent.order:
        items = items.order_by(parent.order)

    context = {
        'parent': parent,
        'categories': categories,
        'items': items,
    }
    return render(request, 'show_category.html', context)

@never_cache
def show_document(request, document_id):
    document = get_object_or_404(Document, pk=document_id)
    context = {
        'document': document,
    }
    return render(request, 'show_document.html', context)

@never_cache
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

@login_required
def edit_file(request, file_id):
    _file = get_object_or_404(File, pk=file_id)
    if _file.author != request.user:
        return HttpResponseForbidden()
    form = FileForm(instance=_file)
    if request.POST:
        form = FileForm(request.POST, request.FILES, instance=_file)
        if form.is_valid():
            form.save()
            return redirect('my_documents')

    context = {'object': _file, 'form': form}

    return render(request, 'edit_file.html', context)

@login_required
def edit_document(request, document_id):
    document = get_object_or_404(Document, pk=document_id)
    if document.author != request.user:
        return HttpResponseForbidden()
    form = DocumentForm(instance=document)
    if request.POST:
        form = DocumentForm(request.POST, instance=document)
        if form.is_valid():
            form.save()
            return redirect('my_documents')

    context = {'object': document, 'form': form}

    return render(request, 'edit_document.html', context)

class DeleteItem(LoginRequiredMixin, DeleteView):
    model = Item
    success_url = reverse_lazy('my_documents')
    template_name = 'delete_item.html'

    def get_queryset(self):
        return self.model.objects.filter(author=self.request.user)
