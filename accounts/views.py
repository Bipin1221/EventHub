from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from .forms import OrganizerRegistrationForm, UserRegistrationForm, LoginForm

def signup_view(request):
    organizer_form = OrganizerRegistrationForm()
    user_form = UserRegistrationForm()

    if request.method == 'POST':
        if 'organizer_signup' in request.POST:  # Organizer signup button clicked
            organizer_form = OrganizerRegistrationForm(request.POST)
            if organizer_form.is_valid():
                organizer = organizer_form.save(commit=False)
                organizer.is_organizer = True
                organizer.is_user = False
                organizer.set_password(organizer_form.cleaned_data['password'])
                organizer.save()
                login(request, organizer)
                return redirect('organizer_dashboard')  # Redirect to organizer dashboard
        elif 'user_signup' in request.POST:  # User signup button clicked
            user_form = UserRegistrationForm(request.POST)
            if user_form.is_valid():
                user = user_form.save(commit=False)
                user.is_user = True
                user.is_organizer = False
                user.set_password(user_form.cleaned_data['password'])
                user.save()
                login(request, user)
                return redirect('user_dashboard')  # Redirect to user dashboard

    return render(request, 'accounts/signup.html', {
        'organizer_form': organizer_form,
        'user_form': user_form,
    })


def login_view(request):
    organizer_form = LoginForm()
    user_form = LoginForm()

    if request.method == 'POST':
        if 'organizer_login' in request.POST:  # Organizer login
            organizer_form = LoginForm(request.POST)
            if organizer_form.is_valid():
                username = organizer_form.cleaned_data['username']
                password = organizer_form.cleaned_data['password']
                user = authenticate(request, username=username, password=password)
                if user and user.is_organizer:
                    login(request, user)
                    return redirect('organizer_dashboard')  # Redirect to organizer dashboard
        elif 'user_login' in request.POST:  # User login
            user_form = LoginForm(request.POST)
            if user_form.is_valid():
                username = user_form.cleaned_data['username']
                password = user_form.cleaned_data['password']
                user = authenticate(request, username=username, password=password)
                if user and user.is_user:
                    login(request, user)
                    return redirect('user_dashboard')  # Redirect to user dashboard

    return render(request, 'accounts/login.html', {
        'organizer_form': organizer_form,
        'user_form': user_form,
    })

def logout_view(request):
    logout(request)
    return redirect('login')


def organizer_dashboard(request):
    return render(request, 'accounts/organizer_dashboard.html')


def user_dashboard(request):
    return render(request, 'accounts/user_dashboard.html')


# Organizer Login View
def organizer_login_view(request):
    form = LoginForm()
    if request.method == 'POST' and 'organizer_login' in request.POST:
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None and user.is_organizer:
                login(request, user)
                return redirect('organizer_dashboard')  # Redirect to Organizer Dashboard
    return render(request, 'accounts/login.html', {'organizer_form': form})

# User Login View
def user_login_view(request):
    form = LoginForm()
    if request.method == 'POST' and 'user_login' in request.POST:
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None and user.is_user:
                login(request, user)
                return redirect('user_dashboard')  # Redirect to User Dashboard
    return render(request, 'accounts/login.html', {'user_form': form})

# Organizer Signup View
def organizer_signup_view(request):
    form = OrganizerRegistrationForm()
    if request.method == 'POST' and 'organizer_signup' in request.POST:
        form = OrganizerRegistrationForm(request.POST)
        if form.is_valid():
            organizer = form.save(commit=False)
            organizer.is_organizer = True
            organizer.is_user = False
            organizer.set_password(form.cleaned_data['password'])
            organizer.save()
            login(request, organizer)
            return redirect('organizer_dashboard')
    return render(request, 'accounts/signup.html', {'organizer_form': form})

# User Signup View
def user_signup_view(request):
    form = UserRegistrationForm()
    if request.method == 'POST' and 'user_signup' in request.POST:
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_user = True
            user.is_organizer = False
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('user_dashboard')
    return render(request, 'accounts/signup.html', {'user_form': form})