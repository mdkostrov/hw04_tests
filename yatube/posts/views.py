from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models.functions import Length
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm
from .models import Group, Post

User = get_user_model()

POSTS_PER_PAGE = 10


def pagination(request, posts):
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    posts = (
        Post.objects.all().
        select_related('author', 'group').
        annotate(post_length=Length('text'))
    )
    page_obj = pagination(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = (
        group.posts.select_related('author').
        annotate(post_length=Length('text'))
    )
    page_obj = pagination(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author)
    page_obj = pagination(request, posts)
    context = {
        'author': author,
        'page_obj': page_obj,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.
        select_related('author', 'group'),
        id=post_id
    )
    context = {
        'post': post,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    context = {}
    form = PostForm(request.POST or None)
    if request.method == 'POST':
        context['form'] = form
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', username=request.user)
        context['errors'] = form.errors
        return render(request, 'posts/create_post.html', context)
    context['form'] = form
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = Post.objects.get(id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(
        request,
        'posts/create_post.html',
        {'form': form, 'is_edit': True}
    )
