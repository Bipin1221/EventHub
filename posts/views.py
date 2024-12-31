from django.shortcuts import render, get_object_or_404, redirect
from .models import Post
from .forms import PostForm
from django.http import HttpResponse
from .decorators import organizer_required

# Create a Post
@organizer_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.organizer = request.user
            post.save()
            return redirect('post_list')
    else:
        form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})

# List Posts
def post_list(request):
    posts = Post.objects.all()
    return render(request, 'posts/post_list.html', {'posts': posts})

# Detail View
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    is_interested = request.user in post.interested_users.all() if request.user.is_authenticated else False
    return render(request, 'posts/detail.html', {'post': post, 'is_interested': is_interested})

# Update a Post
@organizer_required
def update_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('post_list')
    else:
        form = PostForm(instance=post)
    return render(request, 'posts/update_post.html', {'form': form})

# Delete a Post
@organizer_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.delete()
    return redirect('post_list')

# Show Interest
def show_interest(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')
    post = get_object_or_404(Post, pk=pk)
    if request.user in post.interested_users.all():
        post.interested_users.remove(request.user)
    else:
        post.interested_users.add(request.user)
    return redirect('post_detail', pk=post.pk)