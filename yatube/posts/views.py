from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Follow, Group, Post, User
from yatube.settings import NUMBER_POSTS_PAGE, CACHE_STORAGE_TIME
from .forms import CommentForm, PostForm


def _paginator(request, obj):
    """Возвращает page_obj"""
    paginator = Paginator(obj, NUMBER_POSTS_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


@login_required
def add_comment(request, post_id):
    """Добавление комментария к посту."""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    user = User.objects.get(username=request.user.username)
    posts = Post.objects.filter(
        author__following__user=user
    )
    page_obj = _paginator(request, posts)
    context = {
        'page_obj': page_obj,
    }
    template = 'posts/follow.html'

    return render(request, template, context)


def group_posts(request, slug):
    """Настройка отображения страницы группы."""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related(
        'author',
        'group',
    ).all()
    page_obj = _paginator(request, posts)
    context = {
        'page_obj': page_obj,
        'group': group,
    }
    template = 'posts/group_list.html'

    return render(request, template, context)


@cache_page(CACHE_STORAGE_TIME)
def index(request):
    """Настройка отображения главной страницы."""
    posts = Post.objects.select_related(
        'author',
        'group',
    ).all()
    page_obj = _paginator(request, posts)
    context = {
        'page_obj': page_obj,
    }
    template = 'posts/index.html'

    return render(request, template, context)


@login_required
def post_create(request):
    """Создание нового поста."""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)
    context = {
        'form': form,
    }
    template = 'posts/create_post.html'

    return render(request, template, context)


def post_detail(request, post_id):
    """Отображение подробной информации о посте."""
    post = get_object_or_404(Post, pk=post_id)
    post_comments = post.comments.select_related(
        'author',
    ).all()
    posts_count = post.author.posts.count()
    form = CommentForm()
    context = {
        'author_post': post.author,
        'form': form,
        'post': post,
        'post_comments': post_comments,
        'posts_count': posts_count,
    }
    template = 'posts/post_detail.html'

    return render(request, template, context,)


@login_required
def post_edit(request, post_id):
    """Изменение поста."""
    post = get_object_or_404(Post, id=post_id)

    if request.user != post.author:
        return redirect('posts:post_detail', post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    is_edit = True
    context = {
        'form': form,
        'is_edit': is_edit,
        'post_id': post_id,
    }
    template = 'posts/create_post.html'

    return render(request, template, context)


def profile(request, username):
    """Отображение личной страницы пользователя."""
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(
        author=user
    ).select_related(
        'author',
        'group',
    ).all()
    page_obj = _paginator(request, posts)
    posts_count = user.posts.count()
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user,
        author=user
    ).exists()
    context = {
        'page_obj': page_obj,
        'author': user,
        'posts_count': posts_count,
        'following': following,
    }
    template = 'posts/profile.html'

    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    following = Follow.objects.filter(
        user=request.user,
        author=author
    ).exists()
    if not following and author != request.user:
        Follow.objects.create(
            user=request.user,
            author=author
        )

    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    control = Follow.objects.filter(
        user=request.user,
        author=author
    ).exists()
    if control:
        Follow.objects.filter(
            user=request.user,
            author=author
        ).delete()

    return redirect('posts:profile', username)
