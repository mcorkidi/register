from django.shortcuts import render, redirect
from .models import Item, Consumer, Scan, Coupon
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
    for attr in data.keys():
        #will print the data line by line
        print(attr,' '*13+'\t->\t',data[attr])
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
    print(ip)
    
    ipCall = ipInfo(ip)
    items = Item.objects.all()
    try: 
        if ipCall['bogon'] ==True:
            print("Invalid IP")
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
    when = datetime.now()

    if request.method == 'POST':
        if "newUser" in request.POST:
            print(request.POST)
            print(ipCall)
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
            return redirect('profile')
            

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
                return redirect('profile')
            else:
                messages.error(request, "Credenciales incorrectos.")
                return redirect('register', sku=sku)
            
        if "regProd" in request.POST:
            print("sku is,",sku)
            registeredSku = request.POST.get('inputSku',"")
            try:
                item=items.get(sku=registeredSku)
            except:
                messages.error(request, "Referencia ingresada no se encontro en el systema. Revisa y trata nuevamente.")
                return redirect('register', sku=sku)
            newConsumer = Consumer(user_id=request.user,sku=item, where=where,when=when,country=country,city=city)
            newConsumer.save()
            messages.success(request, f"Producto {item.sku} {item.name} registrado exitosamente a tu perfil. ")
            return redirect('profile')

      
        

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
        except:
            pass

    city = city.replace(" ", "_")    
    context = {'sku': sku, 'city': city}  

    return render(request, 'britishdenim/registration.html', context)

def contact(request):

    return render(request, 'britishdenim/contact.html')

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
    scans = Scan.objects.all()
    users = User.objects.all().filter()
    items = Item.objects.all()
    totalItems = items.count()
    totalUsers = users.count()
    totalScans = scans.count()
    scansByCountry = {}
    for scan in scans:
        country = get_country_name(scan.country)
        if country in scansByCountry:
            scansByCountry[country] += 1
        else:
            scansByCountry[country] = 1
    
    scansByCountry = dict(sorted(scansByCountry.items(), key=lambda x: x[1], reverse=True))
    scansByItem = {}
    for item in scans:
        if item.sku.sku in scansByItem:
            scansByItem[item.sku.sku] += 1 
        else:
            scansByItem[item.sku.sku] = 1
    scansByItem = dict(sorted(scansByItem.items(), key=lambda x: x[1], reverse=True)[:20])
    context = {'totalScans': totalScans, 
               'scansByCountry': scansByCountry,
               'totalUsers': totalUsers, 
               'totalItems': totalItems, 
               'scansByItem' : scansByItem}
    
    return render(request, 'britishdenim/stats.html', context)

@cache_page(60 * 1440)
@staff_member_required
def charts(request):
    scans = Scan.objects.all()
    scansLast12Months = {}
    today = datetime.now().date()
    date_format = "%Y-%m-%d %H:%M:%S.%f"
    aYearAgo = today -timedelta(days=30*12)
# Chart for last 12 months of scans
    for scan in scans:
        try: 
            dateScanned = datetime.strptime(scan.when, date_format)
            monthYear = dateScanned.strftime("%m-%Y")
           
            if dateScanned.date() > aYearAgo:
                if monthYear in scansLast12Months:
                    scansLast12Months[monthYear] += 1
                else:
                    scansLast12Months[monthYear] = 1
        except Exception as e:
            pass
    months = json.dumps(list(scansLast12Months.keys()))
    values = json.dumps(list(scansLast12Months.values()))

#Charts for to 12 items scanned last 12 months
    itemsDict = {}
    today = datetime.now()
    last_12_months = []

    for i in range(12):
        month = today.month - i
        year = today.year

        if month <= 0:
            month += 12
            year -= 1
        month = '{:02d}'.format(month)
        last_12_months.append(f'{month}-{year}')
    for scan in scans:
        try: 
            dateScanned = datetime.strptime(scan.when, date_format)
            monthYear = dateScanned.strftime("%m-%Y")
            if dateScanned.date() > aYearAgo:
                if scan.sku.sku in itemsDict:
                    if monthYear in itemsDict[scan.sku.sku]:
                        itemsDict[scan.sku.sku][monthYear] += 1
                    else:
                        itemsDict[scan.sku.sku][monthYear] = 1
                else:
                    itemsDict[scan.sku.sku] = {monthYear: 1}
        except Exception as e:
            print('error', e)
            pass
    top20Scaned = {}
    for item in scans:
        if datetime.strptime(item.when, date_format).date() > aYearAgo:
            if item.sku.sku in top20Scaned:
                top20Scaned[item.sku.sku] += 1 
            else:
                top20Scaned[item.sku.sku] = 1
    top20Scaned = dict(sorted(top20Scaned.items(), key=lambda x: x[1], reverse=True)[:20])

    itemsWithMonthly = {}
    for item in itemsDict:
        if item in top20Scaned:
            for month_year in last_12_months:
                if item in itemsWithMonthly:
                    itemsWithMonthly[item][month_year] = 0 
                else:
                    itemsWithMonthly[item]={month_year: 0}

    for item, value in itemsDict.items():
        if item in top20Scaned:
            for month_year, scan in value.items():
                itemsWithMonthly[item][month_year] = scan
        # else:
        #     del itemsWithMonthly[item]
    itemsWithMonthlyJson = json.dumps(list(itemsWithMonthly.keys()))

#Chart for last 2 weeks of scans
    scansLast15Days = {}
    today = datetime.now().date()
    twoWeeksAgo = today -timedelta(days=15)
    for scan in scans:
        try: 
            dateScanned = datetime.strptime(scan.when, date_format)
            dayScan = dateScanned.strftime("%d-%m-%Y")
           
            if dateScanned.date() > twoWeeksAgo:
                if dayScan in scansLast15Days:
                    scansLast15Days[dayScan] += 1
                else:
                    scansLast15Days[dayScan] = 1
        except Exception as e:
            pass
    days = json.dumps(list(scansLast15Days.keys()))
    day_values = json.dumps(list(scansLast15Days.values()))


    context = {'scansLast12Months' : scansLast12Months, 'months' : months, 
               'values':values, 'items': itemsWithMonthlyJson, 
               'itemList': itemsWithMonthly, 'days':days,
               'day_values':day_values}
    return render(request, 'britishdenim/charts.html', context)

@staff_member_required()
def consumer(request):
    consumer = Consumer.objects.all().order_by('country')
    consumers = {}
   
    for c in consumer:
        
        if c.user_id.username in consumers:
            print("1", c.sku.sku)
            consumers[c.user_id.username].append(c.sku.sku)
        else:
            consumers[c.user_id.username] = [c.sku.sku]
            
    print(consumers.keys())
    count = consumer.count()
    context = {'consumers':consumers, 'count':count}
    return render(request, 'britishdenim/consumer.html', context)

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





