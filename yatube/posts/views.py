from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page

from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm

from django.conf import settings


@require_http_methods(['GET'])
@cache_page(20)
def index(request):
    posts = Post.objects.all()
    comments = Comment.objects.all()
    paginator = Paginator(posts, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'posts/index.html',
        {
            'page': page,
            'comments': comments,
            'posts': posts,
        },
    )


@require_http_methods(['GET'])
def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()[:10]
    paginator = Paginator(posts, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'posts/group.html',
        {
            'group': group,
            'posts': posts,
            'page': page,
        },
    )


@require_http_methods(['GET'])
def profile(request, username):
    following = False
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user,
                                          author=author).exists()
    signatories = author.following.all()
    followers = author.follower.all()
    paginator = Paginator(posts, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(
        request,
        'posts/profile.html',
        {
            'author': author,
            'page': page,
            'signatories': signatories,
            'followers': followers,
            'following': following,
            'posts': posts,
        },
    )


@require_http_methods(['GET'])
def post_view(request, username, post_id):
    user = get_object_or_404(User, username=username)
    message = get_object_or_404(Post, id=post_id, author=user)
    posts = user.posts.all()
    comments = message.comments.all()
    form = CommentForm()
    return render(
        request,
        'posts/post.html',
        {
            'user': user,
            'message': message,
            'add_comment': True,
            'comments': comments,
            'posts': posts,
            'form': form,
            'post_id': post_id,
        },
    )


@require_http_methods(["GET", "POST"])
@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        new = form.save(commit=False)
        new.author = request.user
        new.save()
        return redirect('index')
    return render(request, 'posts/new_post.html', {'form': form})


@require_http_methods(["GET", "POST"])
@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)

    if request.user.username != username:
        return redirect("post", username=post.author, post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        post = form.save()
        return redirect("post", username=post.author, post_id=post_id)
    return render(
        request,
        'posts/new_post.html',
        {
            'form': form,
            'post_id': post_id,
            'edit': True,
            'post': post,
        },
    )


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        form.save()
        return redirect('post', post.author, post_id)
    return render(request, 'posts/comments.html', {'form': form,
                                                   'post_id': post_id})


@login_required
def follow_index(request):
    post = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'posts/follow.html', {'page': page})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(author_id=author.id,
                                     user_id=request.user.id)
    return redirect('profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = get_object_or_404(User, username=request.user)
    Follow.objects.filter(user=user, author=author).delete()
    return redirect('profile', username)
