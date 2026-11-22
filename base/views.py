import os
import json
import telebot
import logging

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.contrib.auth import logout, login, authenticate

from .decorators import *
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .forms import PostForm, CustomUserCreationForm, ProfileForm, UserForm
from .filters import PostFilter

from .models import *

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Create your views here.


def home(request):
    posts = Post.objects.filter(active=True, featured=True)[0:3]

    context = {'posts': posts}
    return render(request, 'base/index.html', context)


def posts(request):
    posts = Post.objects.filter(active=True)
    myFilter = PostFilter(request.GET, queryset=posts)
    posts = myFilter.qs

    page = request.GET.get('page')

    paginator = Paginator(posts, 5)

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    context = {'posts': posts, 'myFilter': myFilter}
    return render(request, 'base/posts.html', context)


def post(request, slug):
    post = Post.objects.get(slug=slug)

    if request.method == 'POST':
        PostComment.objects.create(
            author=request.user.profile,
            post=post,
            body=request.POST['comment']
        )
        messages.success(request, "You're comment was successfuly posted!")

        return redirect('post', slug=post.slug)

    context = {'post': post}
    return render(request, 'base/post.html', context)


def profile(request):
    return render(request, 'base/profile.html')


# CRUD VIEWS
@admin_only
@login_required(login_url="home")
def createPost(request):
    form = PostForm()

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
        return redirect('posts')

    context = {'form': form}
    return render(request, 'base/post_form.html', context)


@admin_only
@login_required(login_url="home")
def updatePost(request, slug):
    post = Post.objects.get(slug=slug)
    form = PostForm(instance=post)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
        return redirect('posts')

    context = {'form': form}
    return render(request, 'base/post_form.html', context)


@admin_only
@login_required(login_url="home")
def deletePost(request, slug):
    post = Post.objects.get(slug=slug)

    if request.method == 'POST':
        post.delete()
        return redirect('posts')
    context = {'item': post}
    return render(request, 'base/delete.html', context)


def sendEmail(request):
    # if request.method == 'POST':
    #     template = render_to_string('base/email_template.html', {
    #         'name': request.POST['name'],
    #         'email': request.POST['email'],
    #         'message': request.POST['message'],
    #     })
    #
    #     email = EmailMessage(
    #         request.POST['subject'],
    #         template,
    #         settings.EMAIL_HOST_USER,
    #         ['tony@intellizen.io']
    #     )
    #
    #     email.fail_silently = False
    #     email.send()

    return render(request, 'base/email_sent.html')


def loginPage(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Little Hack to work around re-building the usermodel
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
        except:
            messages.error(request, 'User with this email does not exists')
            return redirect('login')

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Email OR password is incorrect')

    context = {}
    return render(request, 'base/login.html', context)


def registerPage(request):
    form = CustomUserCreationForm()
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            messages.success(request, 'Account successfuly created!')

            user = authenticate(request, username=user.username, password=request.POST['password1'])

            if user is not None:
                login(request, user)

            next_url = request.GET.get('next')
            if next_url == '' or next_url == None:
                next_url = 'home'
            return redirect(next_url)
        else:
            messages.error(request, 'An error has occured with registration')
    context = {'form': form}
    return render(request, 'base/register.html', context)


def logoutUser(request):
    logout(request)
    return redirect('home')


@login_required(login_url="home")
def userAccount(request):
    profile = request.user.profile

    context = {'profile': profile}
    return render(request, 'base/account.html', context)


@login_required(login_url="home")
def updateProfile(request):
    user = request.user
    profile = user.profile
    form = ProfileForm(instance=profile)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        if user_form.is_valid():
            user_form.save()

        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('account')

    context = {'form': form}
    return render(request, 'base/profile_form.html', context)


# # Retrieve environment variables
# TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
# CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
#
# bot = telebot.TeleBot(TOKEN, parse_mode=None)
#
#
# @csrf_exempt  # Disable CSRF protection for this view if it's an external API
# @require_http_methods(["POST"])  # Only allow POST requests
# def trading_view_alert(request):
#     try:
#         # Attempt to decode and load the JSON data from the request
#         data = json.loads(request.body.decode('utf-8'))
#         message_text = json.dumps(data, indent=2)
#         logging.info("Received alert data: %s", message_text)
#
#         # Use the chat ID from environment variables
#         bot.send_message(CHAT_ID, message_text)
#         logging.info("Message sent to Telegram successfully")
#
#         return JsonResponse({"status": "success", "message": "Alert received and sent to Telegram"}, status=200)
#
#     except json.JSONDecodeError as e:
#         logging.error("Failed to decode JSON data: %s", e)
#         return JsonResponse({"status": "error", "message": "Invalid JSON data"}, status=400)
#
#     except Exception as e:
#         logging.error("An error occurred: %s", e)
#         return JsonResponse({"status": "error", "message": "An error occurred while processing the request"}, status=500)
#
#
