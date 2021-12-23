from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.forms.utils import to_current_timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Comment, Follow


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, settings.NUM_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'paginator': paginator,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.group_with_posts.all()
    title = group.title
    description = group.description
    paginator = Paginator(posts, settings.NUM_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'title': title,
        'description': description,
        'page_obj': page_obj,
        'paginator': paginator,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user,
        author=author
    ).exists()
    paginator = Paginator(posts, settings.NUM_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'author': author,
        'posts': posts,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = post.author
    pub_date = post.pub_date
    form = CommentForm(instance=None)
    comments = post.comments.all()
    context = {
        'post': post,
        'author': author,
        'pub_date': pub_date,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
@csrf_exempt
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None,)
    all_groups = Group.objects.all()
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.pub_date = to_current_timezone
        post.save()
        return redirect('posts:profile', username=post.author)
    context = {
        'form': form,
        'all_groups': all_groups,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
@csrf_exempt
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    is_edit = True
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.id)
    else:
        context = {
            'post': post,
            'form': form,
            'is_edit': is_edit,
        }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, settings.NUM_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'paginator': paginator}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    follower = get_object_or_404(User, username=request.user.username)
    author = get_object_or_404(User, username=username)
    if author == follower:
        return redirect('posts:profile', username=author.username)
    if follower.follower.filter(author=author).exists():
        return redirect('posts:profile', username=author.username)
    follow = Follow.objects.create(user=follower, author=author)
    follow.save()
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follower = get_object_or_404(User, username=request.user.username)
    Follow.objects.filter(user=follower, author=author).delete()
    return redirect('posts:profile', username=username)
