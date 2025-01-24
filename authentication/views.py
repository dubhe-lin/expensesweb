from django.shortcuts import render, redirect
from django.views import View
import json
from django.http import JsonResponse
from django.contrib.auth.models import User
from email_validator import validate_email, EmailNotValidError
from django.contrib import messages
from django.urls import reverse 
from django.utils.encoding import force_bytes, smart_str, DjangoUnicodeDecodeError
from django.core.mail import EmailMessage, send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from .utils import token_generator
from django.contrib import auth


# Create your views here.
class EmailValidationView(View):
    def post(self, request):
        data = json.loads(request.body)
        email = data['email']
        try: 
            validate_email(email) 
        except EmailNotValidError as e: 
            return JsonResponse({'email_error': str(e)}, status=400)

        # if not validate_email(email):
        #     return JsonResponse({'email_error': 'Email is invalid.'}, status=400)
        if User.objects.filter(email=email).exists():
            return JsonResponse({'email_error': 'Sorry, this email is already taken. Please try another one'}, status=409)
        return JsonResponse({'email_valid': True})


class UsernameValidationView(View):
    def post(self, request):
        data = json.loads(request.body)
        username = data['username']

        if not str(username).isalnum():
            return JsonResponse({'username_error': 'Username should only contain alphanumeric characters'}, status=400)
        if User.objects.filter(username=username).exists():
            return JsonResponse({'username_error': 'Sorry, this username is already taken. Please try another one'}, status=409)
        return JsonResponse({'username_valid': True})
        
class RegistrationView(View):
    def get(self, request):
        return render(request, 'authentication/register.html')
    def post(self,request):
        # Get user data
        # Validate user data
        # Create a user account

        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        context = {
            'fieldValues' : request.POST
        }

        if not User.objects.filter(username=username).exists():
            if not User.objects.filter(email=email).exists():
                if len(password) < 8:
                    messages.error(request, 'Password cannot be less than 8 characters')
                    return render(request, 'authentication/register.html', context)
                
                user = User.objects.create_user(username=username, email=email)
                user.set_password(password)
                user.is_active = False
                user.save()

                token = token_generator.make_token(user) 
                #activation_link = f"{request.scheme}://{get_current_site(request).domain}/activate/{uid}/{token}/"

                #path_to_view:
                    #+getting domain we are on
                    #+relative url to verification
                    #+encode uid
                    #+token
                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                domain = get_current_site(request).domain
                link =  reverse('activate', kwargs={'uidb64':uidb64, 'token':token})
                activation_link = 'http://' + domain + link

                email_subject = 'Activate your account'
                email_body = f'Dear + {user.username},\
                    \nPlease use this link below to activate your account: \n{activation_link}'
                email = EmailMessage(
                    email_subject,
                    email_body,
                    "noreply@semicolon.com",
                    [email],
                    headers={"Message-ID": "foo"},
                )

                email.send(fail_silently=False)
                
                messages.success(request, 'Account created successfully')
                return render(request, 'authentication/register.html')
        return render(request, 'authentication/register.html', context)
    
class VerificationView(View):
    def get(self,request, uidb64, token):
        try:
            id=smart_str(urlsafe_base64_decode(uidb64))
            user=User.objects.get(pk=id)

            if user is None: 
                messages.error(request, 'User not found.') 
                return redirect('login') 
            
            if user.is_active: 
                messages.info(request, 'User already activated. Please log in.') 
                return redirect('login')

            if not token_generator.check_token(user, token):
                messages.error(request, 'Token is invalid or has expired.')
                return redirect ('login'+'?message='+'User already activated')

            user.is_active=True
            user.save()

            messages.success(request, 'Account activated successfully')
            return redirect('login')
        except Exception as ex:
            return redirect('login')

class LoginView(View):
    def get(self, request):
        return render(request, 'authentication/login.html')
    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']

        if username and password:
            user = auth.authenticate(request, username=username, password=password)
            if user:
                if user.is_active:
                    auth.login(request, user)
                    messages.success(request, 'Welcome, ' + user.username + '. You are now logged in.')
                    return redirect('expenses')
                messages.error(request, 'Account is not active, please check your email.')
                return render(request, 'authentication/login.html')            
            messages.error(request, 'Invalid credentials, try again.')
            return render(request, 'authentication/login.html')
        messages.error(request, 'Please fill in all fields.')
        return render(request, 'authentication/login.html')
    
class LogoutView(View):
    def post(self, request):
        auth.logout(request)
        messages.success(request, 'You have been logged out.')
        return redirect('login')