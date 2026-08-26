from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from britishdenim.models import Item, Consumer
from user.models import Profile
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.views import View
from django.contrib.auth.models import User
from django.conf import settings
from ftplib import FTP, error_perm
from urllib.parse import quote, urljoin
from uuid import uuid4

# Create your views here.

MAX_PROFILE_IMAGE_SIZE = 5 * 1024 * 1024


def profile_image_extension(upload):
    """Return a supported image extension after checking its file signature."""
    header = upload.read(16)
    upload.seek(0)
    if header.startswith(b'\xff\xd8\xff'):
        return 'jpg'
    if header.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    if header.startswith((b'GIF87a', b'GIF89a')):
        return 'gif'
    if header[:4] == b'RIFF' and header[8:12] == b'WEBP':
        return 'webp'
    return None


def upload_profile_image(user, image_file, extension):
    """Store a profile image in the user's dedicated Ketengo Storage folder."""
    folder_parts = ('profile-images', str(user.pk))
    filename = f'{uuid4().hex}.{extension}'

    with FTP(settings.FTP_DOMAIN, timeout=30) as ftp:
        ftp.login(settings.FTP_USER, settings.FTP_PASSWORD)
        for folder in folder_parts:
            try:
                ftp.cwd(folder)
            except error_perm:
                ftp.mkd(folder)
                ftp.cwd(folder)
        image_file.seek(0)
        ftp.storbinary(f'STOR {filename}', image_file)

    remote_path = '/'.join((*folder_parts, filename))
    return urljoin(settings.PROFILE_IMAGE_BASE, quote(remote_path))


def save_profile_image(request, profile, image_file):
    if not image_file:
        return True
    extension = profile_image_extension(image_file)
    if not extension:
        messages.error(request, 'Solo se permiten imágenes JPG, PNG, GIF o WebP.')
        return False
    if image_file.size > MAX_PROFILE_IMAGE_SIZE:
        messages.error(request, 'La foto de perfil debe tener un tamaño máximo de 5 MB.')
        return False
    try:
        profile.image_url = upload_profile_image(profile.user, image_file, extension)
        profile.save(update_fields=['image_url'])
    except Exception:
        messages.error(request, 'No fue posible subir la foto de perfil. Intenta nuevamente.')
        return False
    return True

@login_required
def profile(request):

    items = Item.objects.all()
    consumer = Consumer.objects.filter(user_id=request.user)
    profileModel = Profile.objects.first()
    profile = Profile.objects.filter(user=request.user)[0]
    if request.method == 'POST':
        if 'edit' in request.POST:
            profile_image = request.FILES.get('profile_image')
            username = request.POST.get('username')
            email =request.POST.get('email')
            password = request.POST.get('password')
            password1 = request.POST.get('password1')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            telephone = request.POST.get('telephone')
            movil = request.POST.get('movil')
            direccion = request.POST.get('direccion')
            location = request.POST.get('pais')

            if password == '' and password1 == '':
                editUser = request.user
                editUser.username = username
                editUser.email = email
                editUser.first_name = first_name
                editUser.last_name = last_name
                editUser.save()
                if Profile.objects.filter(user=editUser).exists():
                    editProfile = Profile.objects.get(user=editUser)
                    editProfile.telephone = telephone
                    editProfile.movil = movil
                    if location != 'Selecciona...':
                        editProfile.location = location
                    editProfile.direccion = direccion
                    editProfile.save()
                    profile = editProfile
                    save_profile_image(request, profile, profile_image)
                    messages.success(request, 'Perfil editado exitosamente!')
                else:
                    newProfile = Profile.objects.create(user=editUser,
                                                        telephone = telephone, 
                                                        movil = movil,
                                                        location = location,
                                                        direccion = direccion,
                                                        )
                    newProfile.save()
                    profile = newProfile
                    save_profile_image(request, profile, profile_image)
            else:
                if password != password1:
                    messages.error(request, 'Error, revisa que la contraseña sea igual a la confirmacion.')
                else:
                    editUser = request.user
                    editUser.username = username
                    editUser.email = email
                    editUser.first_name = first_name
                    editUser.last_name = last_name
                    editUser.set_password(password)
                    editUser.save()
                    editProfile = Profile.objects.get(user=editUser)
                    editProfile.telephone = telephone
                    
                    editProfile.save()
                    profile = editProfile
                    save_profile_image(request, profile, profile_image)
                    messages.success(request, 'Perfil editado exitosamente!')
                    profile = editProfile

    context = {'items': items, 'consumer': consumer, 'profile':profile, 'profileModel':profileModel}

    return render(request, 'user/profile.html', context)


def signin(request):
    if request.method == 'POST':
        print(request.POST)
        email =request.POST.get('username')
        username = request.POST.get('username')
        password = request.POST.get('password')
        password1 = request.POST.get('password1')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        if password != password1:
                messages.error(request, 'Error, revisa que la contraseña sea igual a la confirmacion.')
                return render(request,  'user/signin.html')
        try:
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Error: Correo ya registrado, intenta nuevamente con otro correo.')
                return render(request, 'user/signin.html')
            newUser = User.objects.create_user(username, email, password)
            newUser.first_name = first_name
            newUser.last_name = last_name
            newUser.save()
        except Exception as e:
            print(e)
            messages.error(request, 'Error en el registro intenta nuevamente con otro usuario.')
            return render(request, 'user/signin.html')

        newProfile = Profile.objects.create(user=newUser)
        newProfile.save()

        auth = authenticate(request, username=username, password=password)
        if auth:
            login(request, auth)
            messages.success(request, f'Welcome {auth.first_name}, you are logged in.')
            return redirect('profile')

    
    return render(request, 'user/signin.html')


class LoginView(View):
    def get(self, request):

        return render(request, 'user/login.html')

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        auth = authenticate(request, username=username, password=password)
        if auth:
            login(request, auth)
            messages.success(request, f'Welcome {auth.first_name}, you are logged in.')
            return redirect('profile')
        else:
            messages.error(request, "Wrong credentials please try again.")
            return redirect('login')
