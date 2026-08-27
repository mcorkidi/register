from django.shortcuts import get_object_or_404, render, redirect
from .models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.utils.translation import gettext as _
from django.contrib import messages
from django.views import View
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from .serializers import ItemSerializer, LoginSerializer, LogoutSerializer
import pycountry
import json
from django.views.decorators.cache import cache_page
from django.http import HttpResponseForbidden
from django.conf import settings
from django.db.models import Count
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import reverse
from django.contrib.auth.views import redirect_to_login
from ftplib import FTP, error_perm
from urllib.parse import quote, urljoin
from uuid import uuid4
from user.models import Profile

def ipInfo(addr=''):
    from urllib.request import urlopen
    from json import load
    if addr == '':
        url = 'https://ipinfo.io/json'
    else:
        url = 'https://ipinfo.io/' + addr + '/json'
    res = urlopen(url)
    #response from url(if res==None then check connection)
    data = load(res)
    #will load the json response into data
    # for attr in data.keys():
        #will print the data line by line
        # print(attr,' '*13+'\t->\t',data[attr])
    return data


def index(request):
    return render(request, 'index.html')

def register(request, sku):
    #register with sku in url

    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    ip = get_client_ip(request)
    # print(ip)
    try: 
        ipCall = ipInfo(ip)
   
        items = Item.objects.all()
        try: 
            if ipCall['bogon'] ==True:
                # print("Invalid IP")
                city = 'City'
                where = 'NotDetected'   
                country = 'NotDetected'
            else:
                city = ipCall['city']
                where = ipCall['region']    
                country = ipCall['country']
        except:
            city = ipCall['city']
            where = ipCall['region']   
            country = ipCall['country']
    except:
        # print('error getting ip')
        pass
    when = datetime.now()

    if request.method == 'POST':
        if "newUser" in request.POST:
            # print(request.POST)
            # print(ipCall)
            registeredSku = request.POST.get('inputSku',"")
            email = request.POST.get('email',"")
            username = email 
            password = request.POST.get('inputPassword',"")
            first_name = request.POST.get('first_name',"")
            last_name = request.POST.get('last_name',"")
            city = request.POST.get('city', "city")
            getInfo = request.POST.get('getInfo', 'Off')
            
            
            if getInfo == 'on':
                getInfo = True
            else:
                getInfo = False
            #item must exist in db
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Error: Correo ya registrado, ingresa a la pagina con tu correo.')
                return redirect('register', sku=sku)
            user = User.objects.create_user(username,email,password)
            user.first_name = first_name
            user.last_name = last_name
            user.email_address = email
            user.save()
            newProfile = Profile.objects.create(user=user)
            newProfile.save()
            auth = authenticate(request, username=username, password=password)
            if auth:
                login(request, auth)
            messages.success(request, "Te registraste exitosamente, bienvenido.")
            try:
                item=items.get(sku=registeredSku)
            except:
                messages.error(request, "Referencia ingresada no se encontro en el systema. Revisa y trata nuevamente.")
                return redirect('register', sku=sku)
            newConsumer = Consumer(user_id=user,sku=item, where=where,when=when,country=country,city=city,getInfo=getInfo )
            newConsumer.save()
            messages.success(request, f"Producto {item.sku} {item.name} registrado exitosamente a tu perfil. ")
            return redirect('sku_feed', sku=item.sku)
            

        if "loginReg" in request.POST:
            registeredSku = request.POST.get('inputSku',"")
            username = request.POST['email']
            password = request.POST['password']
            auth = authenticate(request, username=username, password=password)
            if auth:
                login(request, auth)
                try:
                    item=items.get(sku=registeredSku)
                except:
                    messages.error(request, "Referencia ingresada no se encontro en el systema. Revisa y trata nuevamente.")
                    return redirect('register', sku=sku)
                newConsumer = Consumer(user_id=request.user,sku=item, where=where,when=when,country=country,city=city )
                newConsumer.save()
                messages.success(request, f'Bienvenido {auth.first_name}. Gracias por registrar un producto.')
                return redirect('sku_feed', sku=item.sku)
            else:
                messages.error(request, "Credenciales incorrectos.")
                return redirect('register', sku=sku)
            
        if "regProd" in request.POST:
            # print("sku is,",sku)
            registeredSku = request.POST.get('inputSku',"")
            try:
                item=items.get(sku=registeredSku)
            except:
                messages.error(request, "Referencia ingresada no se encontro en el systema. Revisa y trata nuevamente.")
                return redirect('register', sku=sku)
            newConsumer = Consumer(user_id=request.user,sku=item, where=where,when=when,country=country,city=city)
            newConsumer.save()
            messages.success(request, f"Producto {item.sku} {item.name} registrado exitosamente a tu perfil. ")
            return redirect('sku_feed', sku=item.sku)

      
        

    if sku == '_':
        pass
    else:
        try: 
            item=items.get(sku=sku)
            if country=='HK' or country=='CN':
                pass
            else:
                newScan = Scan(sku=item,where=where,when=when,country=country,city=city)
                newScan.save()
                # Redirect to Instagram profile
                # return redirect("https://www.instagram.com/britishdenimlatam/")

        except:
            pass
    try: 
        city = city.replace(" ", "_")    
    except:
        city = "_"
    context = {'sku': sku, 'city': city}  

    return render(request, 'britishdenim/registration.html', context)

def LogOutView(request):
    logout(request)
    return redirect('index')


MAX_POST_IMAGES = 3
MAX_POST_IMAGE_SIZE = 5 * 1024 * 1024


def image_extension(upload):
    """Return a verified extension for a supported image upload, or None."""
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


def upload_sku_feed_images(item, uploads):
    """Upload post images to the public Ketengo Storage SKU-feed directory."""
    folder_parts = ('sku-feed-images', str(item.pk))
    uploaded_urls = []

    with FTP(settings.FTP_DOMAIN, timeout=30) as ftp:
        ftp.login(settings.FTP_USER, settings.FTP_PASSWORD)
        for folder in folder_parts:
            try:
                ftp.cwd(folder)
            except error_perm:
                ftp.mkd(folder)
                ftp.cwd(folder)

        for upload, extension in uploads:
            filename = f'{uuid4().hex}.{extension}'
            upload.seek(0)
            ftp.storbinary(f'STOR {filename}', upload)
            remote_path = '/'.join((*folder_parts, filename))
            uploaded_urls.append(urljoin(settings.FTP_BASE, quote(remote_path)))

    return uploaded_urls


def skuFeed(request, sku):
    item = get_object_or_404(Item, sku=sku)
    can_post = (
        request.user.is_authenticated
        and Consumer.objects.filter(user_id=request.user, sku=item).exists()
    )

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not can_post:
            return HttpResponseForbidden('Register this item before posting or liking its feed.')

        if request.POST.get('action') == 'like':
            post = get_object_or_404(
                skuPost,
                pk=request.POST.get('post_id'),
                sku=item,
                is_approved=True,
            )
            _, created = likePost.objects.get_or_create(skuPost=post, user_id=request.user)
            if created:
                messages.success(request, 'Te gustó esta publicación.')
            else:
                messages.info(request, 'Ya registramos tu like en esta publicación.')
            return redirect('sku_feed', sku=item.sku)

        text = request.POST.get('text', '').strip()
        try:
            location = request.user.profile.location
        except Profile.DoesNotExist:
            location = ''
        image_files = request.FILES.getlist('images')

        if not text and not image_files:
            messages.error(request, 'Escribe un comentario o selecciona al menos una imagen.')
        elif len(text) > 280:
            messages.error(request, 'El comentario no puede superar los 280 caracteres.')
        elif len(image_files) > MAX_POST_IMAGES:
            messages.error(request, 'Puedes subir un máximo de 3 imágenes por publicación.')
        else:
            images = []
            for image_file in image_files:
                extension = image_extension(image_file)
                if not extension:
                    messages.error(request, 'Solo se permiten imágenes JPG, PNG, GIF o WebP.')
                    break
                if image_file.size > MAX_POST_IMAGE_SIZE:
                    messages.error(request, 'Cada imagen debe tener un tamaño máximo de 5 MB.')
                    break
                images.append((image_file, extension))
            else:
                try:
                    image_urls = upload_sku_feed_images(item, images) if images else []
                except Exception:
                    messages.error(request, 'No fue posible subir las imágenes. Intenta nuevamente.')
                else:
                    skuPost.objects.create(
                        sku=item,
                        user_id=request.user,
                        text=text,
                        location=location,
                        imageList=json.dumps(image_urls),
                    )
                    messages.success(
                        request,
                        'Tu publicación fue enviada y será publicada cuando un administrador la apruebe.',
                    )
        return redirect('sku_feed', sku=item.sku)

    posts = skuPost.objects.filter(sku=item, is_approved=True).select_related(
        'user_id__profile',
    ).prefetch_related('likepost_set')
    for post in posts:
        try:
            post.images = json.loads(post.imageList) if post.imageList else []
        except json.JSONDecodeError:
            post.images = []
        post.likes = list(post.likepost_set.all())
        post.like_count = len(post.likes)
        post.liked_by_current_user = any(like.user_id_id == request.user.id for like in post.likes)
        try:
            post.profile_image_url = post.user_id.profile.image_url
        except Profile.DoesNotExist:
            post.profile_image_url = ''
    context = {'posts': posts, 'sku': item, 'can_post': can_post}
    return render(request, 'britishdenim/sku_feed.html', context)


def contact(request):

    return render(request, 'britishdenim/contact.html')


def privacy_policy(request):
    return render(request, 'britishdenim/privacy_policy.html')


def terms_and_conditions(request):
    return render(request, 'britishdenim/terms_and_conditions.html')

@login_required
def rewards(request):

    coupons = Coupon.objects.all()

    return render(request, 'britishdenim/rewards.html', {'coupons': coupons})

def get_country_name(country_code):
    try:
        country = pycountry.countries.get(alpha_2=country_code)
        if country:
            return country.name
    except LookupError:
        pass
    return None

@cache_page(60 * 1440)
@staff_member_required
def stats(request):
    totalItems = Item.objects.count()
    totalUsers = User.objects.count()
    totalScans = Scan.objects.count()

    scansByCountry = {}
    country_counts = Scan.objects.values('country').annotate(
        scan_count=Count('id'),
    ).order_by('-scan_count', 'country')
    for scan in country_counts:
        country = get_country_name(scan['country']) or scan['country'] or 'Unknown'
        if country in scansByCountry:
            scansByCountry[country] += scan['scan_count']
        else:
            scansByCountry[country] = scan['scan_count']
    scansByCountry = dict(sorted(scansByCountry.items(), key=lambda x: x[1], reverse=True))

    scansByItem = {
        row['sku__sku']: row['scan_count']
        for row in Scan.objects.values('sku__sku').annotate(
            scan_count=Count('id'),
        ).order_by('-scan_count', 'sku__sku')[:20]
    }
    context = {'totalScans': totalScans, 
               'scansByCountry': scansByCountry,
               'totalUsers': totalUsers, 
               'totalItems': totalItems, 
               'scansByItem' : scansByItem}
    
    return render(request, 'britishdenim/stats.html', context)

@cache_page(60 * 1440)
@staff_member_required
def charts(request):
    today = datetime.now().date()
    twelve_months_ago = today - timedelta(days=30 * 12)
    fifteen_days_ago = today - timedelta(days=15)

    # Use fixed, chronological labels so charts include periods with no scans.
    last_12_months = []
    for offset in range(11, -1, -1):
        month_index = today.year * 12 + today.month - 1 - offset
        year, month_index = divmod(month_index, 12)
        last_12_months.append(f'{month_index + 1:02d}-{year}')
    scansLast12Months = dict.fromkeys(last_12_months, 0)

    last_15_days = [today - timedelta(days=offset) for offset in range(14, -1, -1)]
    scansLast15Days = {
        day.strftime('%d-%m-%Y'): 0
        for day in last_15_days
    }
    item_monthly_counts = {}
    item_scan_counts = {}

    # Stream only the fields needed by the charts and parse each timestamp once.
    for scanned_when, sku in Scan.objects.values_list('when', 'sku__sku').iterator(chunk_size=2000):
        try:
            scanned_date = datetime.fromisoformat(scanned_when).date()
        except (TypeError, ValueError):
            continue

        if scanned_date > twelve_months_ago:
            item_scan_counts[sku] = item_scan_counts.get(sku, 0) + 1
            month_year = scanned_date.strftime('%m-%Y')
            if month_year in scansLast12Months:
                scansLast12Months[month_year] += 1
                monthly_counts = item_monthly_counts.setdefault(
                    sku,
                    dict.fromkeys(last_12_months, 0),
                )
                monthly_counts[month_year] += 1

        if scanned_date > fifteen_days_ago:
            day_scan = scanned_date.strftime('%d-%m-%Y')
            if day_scan in scansLast15Days:
                scansLast15Days[day_scan] += 1

    top_skus = sorted(item_scan_counts.items(), key=lambda row: (-row[1], row[0]))[:20]
    itemsWithMonthly = {
        sku: item_monthly_counts.get(sku, dict.fromkeys(last_12_months, 0))
        for sku, _ in top_skus
    }
    months = json.dumps(last_12_months)
    values = json.dumps(list(scansLast12Months.values()))
    itemsWithMonthlyJson = json.dumps(list(itemsWithMonthly.keys()))
    days = json.dumps(list(scansLast15Days.keys()))
    day_values = json.dumps(list(scansLast15Days.values()))


    context = {'scansLast12Months' : scansLast12Months, 'months' : months, 
               'values':values, 'items': itemsWithMonthlyJson, 
               'itemList': itemsWithMonthly, 'days':days,
               'day_values':day_values}
    return render(request, 'britishdenim/charts.html', context)

@staff_member_required()
def consumer(request):
    consumer_rows = Consumer.objects.order_by(
        'country', 'user_id__username', 'sku__sku',
    ).values_list(
        'id',
        'user_id__username',
        'user_id__first_name',
        'user_id__last_name',
        'user_id__email',
        'country',
        'sku__sku',
    )
    consumers_by_username = {}
    for consumer_id, username, first_name, last_name, email, country, sku in consumer_rows.iterator(chunk_size=2000):
        consumer = consumers_by_username.setdefault(
            username,
            {
                'username': username,
                'full_name': f'{first_name} {last_name}'.strip(),
                'email': email,
                'countries': set(),
                'skus': set(),
                'registrations': [],
            },
        )
        if country:
            consumer['countries'].add(country)
        consumer['skus'].add(sku)
        consumer['registrations'].append({'id': consumer_id, 'sku': sku})

    consumers = []
    for consumer in consumers_by_username.values():
        consumer['country'] = ', '.join(sorted(consumer.pop('countries'))) or 'Unknown'
        consumer['skus'] = sorted(consumer['skus'])
        consumers.append(consumer)

    context = {'consumers': consumers, 'count': len(consumers)}
    return render(request, 'britishdenim/consumer.html', context)


@staff_member_required
def invite_consumer_to_post(request, consumer_id):
    if request.method != 'POST':
        return redirect('consumer')

    registration = get_object_or_404(
        Consumer.objects.select_related('user_id', 'sku'),
        pk=consumer_id,
    )
    recipient = registration.user_id.email
    if not recipient:
        messages.error(request, 'Este consumidor no tiene un correo electrónico registrado.')
        return redirect('consumer')

    feed_url = request.build_absolute_uri(
        reverse('sku_feed', kwargs={'sku': registration.sku.sku}),
    )
    first_name = registration.user_id.first_name or registration.user_id.username
    subject = f'Cuéntanos tu experiencia con {registration.sku.name or registration.sku.sku}'
    message = (
        f'Hola {first_name},\n\n'
        f'Gracias por registrar tu producto British Denim ({registration.sku.sku}). '
        'Nos encantaría conocer tu experiencia y ver cómo lo usas.\n\n'
        f'Comparte tu reseña aquí: {feed_url}\n\n'
        'Tu publicación será revisada por nuestro equipo antes de aparecer en la comunidad.\n\n'
        'British Denim'
    )
    html_message = render_to_string(
        'britishdenim/emails/invite_to_post.html',
        {
            'first_name': first_name,
            'sku': registration.sku.sku,
            'product_name': registration.sku.name,
            'feed_url': feed_url,
            'logo_url': request.build_absolute_uri(static('britishdenim/images/logo.png')),
        },
    )
    try:
        email = EmailMultiAlternatives(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient])
        email.attach_alternative(html_message, 'text/html')
        email.send()
    except Exception as e:
        print(f'Error sending email to {recipient}: {e}')
        messages.error(request, 'No fue posible enviar la invitación. Intenta nuevamente.')
    else:
        messages.success(request, f'Invitación enviada a {recipient} para el SKU {registration.sku.sku}.')
    return redirect('consumer')

# API VIEWS

class ProductViewSet(viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

    def create(self,request):
    # Override create method to prevent duplicate object creation
        serializer = self.serializer_class(data=self.request.data)

        serializer.is_valid(raise_exception=True)
        sku = serializer.validated_data['sku']
        name = serializer.validated_data['name']
        obj, created = Item.objects.get_or_create(sku=sku, name=name)
        if created:
            obj.save()
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_409_CONFLICT)


class LoginAPIView(viewsets.GenericViewSet,
                   mixins.CreateModelMixin):
    queryset = User.objects.all()
    serializer_class = LoginSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        auth = authenticate(request, username=serializer.data['username'], password=request.data['password'])
        if auth:
            login(request, auth)
            
        else:
            return Response({'error': 'Username or password is error'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.serializer_class(self.request.user).data)




class LogOutAPIView(viewsets.GenericViewSet,
                    mixins.CreateModelMixin):
    queryset = User.objects.all()
    serializer_class = LogoutSerializer

    def create(self, request, *args, **kwargs):
        logout(self.request)
        return Response({'status': 'Log out success'})


class LoggedInUser(viewsets.GenericViewSet,
                   mixins.ListModelMixin):
    queryset = User.objects.all()
    serializer_class = LoginSerializer

    def list(self, request, *args, **kwargs):
        """
        Here you will get the logged in user
        """
        
        return Response(self.serializer_class(self.request.user, many=False).data)
