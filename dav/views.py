from django.shortcuts import render 
from rest_framework.response import Response 
from django.shortcuts import get_object_or_404 
from rest_framework import status 
from .serializers import * 
from .models import * 
from rest_framework.decorators import api_view,parser_classes
from minio import Minio
from datetime import datetime
from django.http import HttpResponseBadRequest,HttpResponseServerError
from rest_framework import viewsets
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from django.views.decorators.csrf import csrf_exempt
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from .permissions import *
from django.contrib.auth import get_user_model
import redis
import uuid
import requests
from django.conf import settings
from rest_framework.parsers import MultiPartParser
from django.db.models import Count


session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

#user= Users.objects.get(id=20)

@swagger_auto_schema(method='post', request_body=UserSerializer)
@api_view(['Post'])
@permission_classes([AllowAny])
def create(request):
    if Users.objects.filter(email=request.data['email']).exists():
        return Response({'status': 'Exist'}, status=400)
    serializer = UserSerializer(data=request.data)
    print('sss')
    if serializer.is_valid():
        print(serializer.data)
        Users.objects.create_user(email=serializer.data['email'],
                                    password=serializer.data['password'],
                                    is_moderator=serializer.data['is_moderator'])
        return Response({'status': 'Success'}, status=200)
    return Response({'status': 'Error', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuth])
def user_info(request):
    print(request.headers.get('Authorization'))
    try:
        access_token = request.COOKIES["access_token"]
        print('access_token', access_token)
        if session_storage.exists(access_token):
            email = session_storage.get(access_token).decode('utf-8')
            user = Users.objects.get(email=email)
            application = Applications.objects.filter(customer_id=user.id).filter(status=1).first()
            user_data = {
                "user_id": user.id,
                "email": user.email,
                "is_moderator": user.is_moderator,
                "current_cart": application.id if application else -1,
            }
            print(user_data)
            return Response(user_data, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'Error', 'message': 'Session does not exist'})
    except:
        return Response({'status': 'Error', 'message': 'Cookies are not transmitted'})



# @authentication_classes([])
# @csrf_exempt
@swagger_auto_schema(method='post', request_body=UserSerializer)
@api_view(['Post'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('email')
    password = request.data.get('password')
    user = authenticate(request, email=username, password=password)
    
    if user is not None:
        random_key = str(uuid.uuid4())
        application = Applications.objects.filter(customer_id=user.id).filter(status=1).first()
        user_data = {
            "user_id": user.id,
            "email": user.email,
            "is_moderator": user.is_moderator,
            "access_token": random_key,
            "current_cart": application.id if application else -1,
        }
        session_storage.set(random_key, username)
        response = Response(user_data, status=status.HTTP_201_CREATED)
        response.set_cookie("access_token", random_key)

        return response
    else:
        return Response({'status': 'Error'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['Post'])
@permission_classes([AllowAny])
def logout_view(request):
    access_token = request.COOKIES["access_token"]
    if access_token is None:
        message = {"message": "Token is not found in cookie"}
        return Response(message, status=status.HTTP_401_UNAUTHORIZED)
    session_storage.delete(access_token)
    response = Response({'message': 'Logged out successfully'})
    response.delete_cookie('access_token')

    return response





@api_view(['Get']) 
@permission_classes([AllowAny])
def get_current_cart(request, format=None):

    authorization_header = request.headers.get('Authorization')
    access_token = authorization_header.split(' ')[1] if authorization_header else None

    username = session_storage.get(access_token).decode('utf-8')

    user_id = Users.objects.filter(email=username).values_list('id', flat=True).first()

    application = get_object_or_404(Applications, customer = user_id)
    if request.method == 'GET':
        serializer = ApplicationSerializer(application)
        application_data = serializer.data

        # Получить связанные опции для заявки с полными данными из таблицы Teachers
        application_teachers = Applicationsteachers.objects.filter(application=application)
        teachers_data = []
        for app_teacher in application_teachers:
            teacher_serializer = TeacherSerializer(app_teacher.teacher)
            teacher_data = teacher_serializer.data
            teachers_data.append(teacher_data)
        
        # Добавить данные об опциях в данные о заявке
        application_data['teachers'] = teachers_data
        
        return Response(application_data)



#GET - получить список всех опций 
@api_view(['Get']) 
@permission_classes([AllowAny])
def get_teachers(request, format=None): 
    search_query = request.GET.get('search', '')
    faculty = request.GET.get('faculty', '')
    status = request.GET.get('status', '')
    if status in ['3']:
       teachers  = Teachers.objects.all()
    else:
        teachers = Teachers.objects.filter(available=True).filter(title__icontains=search_query)

    if faculty and faculty != 'Любой факультет':
        teachers = teachers.filter(faculty=faculty)
    
    try:
        access_token = request.COOKIES["access_token"]
        username = session_storage.get(access_token).decode('utf-8')
        print(username)
        user_ind = Users.objects.filter(email=username).first()
        application = Applications.objects.filter(customer_id=user_ind.id, status=1).values_list('id', flat=True).first()
        serializer = TeacherSerializer(teachers, many=True)
        response_data = {
            'app_id': application,
            'teachers': serializer.data,
        }
        return Response(response_data)
    except:
        serializer = TeacherSerializer(teachers, many=True)
        result = {
            'teachers': serializer.data,
        }
        return Response(result)

#POST - добавить новую опцию  
@api_view(['Post']) 
@permission_classes([AllowAny])
def post_teacher(request, format=None):
    serializer = TeacherSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@parser_classes([MultiPartParser])
@permission_classes([AllowAny])
def postImageToTeacher(request, pk):
    if 'file' in request.FILES:
        file = request.FILES['file']
        subscription = Teachers.objects.get(pk=pk, available=True)
        
        client = Minio(endpoint="localhost:9000",
                       access_key='minioadmin',
                       secret_key='minioadmin',
                       secure=False)

        bucket_name = 'images'
        file_name = file.name
        file_path = "http://localhost:9000/images/" + file_name
        
        try:
            client.put_object(bucket_name, file_name, file, length=file.size, content_type=file.content_type)
            print("Файл успешно загружен в Minio.")
            
            serializer = TeacherSerializer(instance=subscription, data={'image': file_path}, partial=True)
            if serializer.is_valid():
                serializer.save()
                return HttpResponse('Image uploaded successfully.')
            else:
                return HttpResponseBadRequest('Invalid data.')
        except Exception as e:
            print("Ошибка при загрузке файла в Minio:", str(e))
            return HttpResponseServerError('An error occurred during file upload.')

    return HttpResponseBadRequest('Invalid request.')


#GET - получить одну опцию 
@api_view(['Get'])
@permission_classes([AllowAny]) 
def get_teacher(request, pk, format=None): 
    teacher = get_object_or_404(Teachers, pk=pk) 
    if request.method == 'GET': 
        serializer = TeacherSerializer(teacher) 
        return Response(serializer.data) 
 
#PUT - обновить одну опцию 
@api_view(['Put']) 
@permission_classes([AllowAny])
def put_teacher(request, pk, format=None): 
    teacher = get_object_or_404(Teachers, pk=pk) 
    serializer = TeacherSerializer(teacher, data=request.data) 
    if serializer.is_valid(): 
        serializer.save() 
        return Response(serializer.data) 
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 
 
#PUT - удалить одну опцию 
@api_view(['Put']) 
@permission_classes([AllowAny])
def delete_teacher(request, pk, format=None):     
    if not Teachers.objects.filter(pk=pk).exists():
        return Response(f"Опции с таким id не существует!") 
    teacher = Teachers.objects.get(pk=pk)
    teacher.available = False
    teacher.save()

    teachers = Teachers.objects.filter(available=True)
    serializer = TeacherSerializer(teachers, many=True)
    return Response(serializer.data)
 
#POST - добавить услугу в заявку(если нет открытых заявок, то создать)
@api_view(['POST'])
@permission_classes([AllowAny])
def add_to_application(request, pk):
    access_token = request.COOKIES["access_token"]
    username = session_storage.get(access_token).decode('utf-8')
    user = Users.objects.filter(email=username).first()
    if user is None:
        print('Не зарегестрирован')

    if not Teachers.objects.filter(id=pk).exists():
        return Response(f"Услуги с таким id не существует!")

    teacher = Teachers.objects.get(id=pk)

    
    application = Applications.objects.filter(status=1,customer_id=user.id).last()
       
    
    if application is None:
        application = Applications.objects.create(customer_id=user.id)

    
    try:
        application_teacher = Applicationsteachers.objects.get(application=application, teacher=teacher)
        application_teacher.save()
    except Applicationsteachers.DoesNotExist:
        application_teacher = Applicationsteachers(application=application, teacher=teacher)
        application_teacher.save()

    serializer = ApplicationSerializer(application)
    application_data = serializer.data

    # Получить связанные опции для заявки с полными данными из таблицы Teachers
    application_teachers = Applicationsteachers.objects.filter(application=application)
    teachers_data = []
    for app_teacher in application_teachers:
        teacher_serializer = TeacherSerializer(app_teacher.teacher)
        teacher_data = teacher_serializer.data
        teachers_data.append(teacher_data)
    
    # Добавить данные об опциях в данные о заявке
    application_data['teachers'] = teachers_data
    
    return Response(application_data)




 
#GET - получить список всех заявок 
@api_view(['Get']) 
@permission_classes([AllowAny])
def get_applications(request, format=None): 

    access_token = request.COOKIES["access_token"]
    username = session_storage.get(access_token).decode('utf-8')
    user_id = Users.objects.filter(email=username).values_list('id', flat=True).first()

    if username is not None and user_id is not None:
        user = Users.objects.get(email=username)
        if user.is_moderator:
            faculty = request.GET.get('status', '')
            start_day = request.GET.get('start_day','-1')
            end_day = request.GET.get('end_day','-1')
            print(start_day, end_day)
            if not start_day:
                start_day="1900-01-01"
            if not end_day:
                end_day="2200-01-01"
            applications = Applications.objects.exclude(status=2)
            if faculty and faculty != '0':
                applications = applications.filter(status=faculty).exclude(status=2)
            if start_day and end_day:
                applications = applications.filter(created_at__range=(start_day, end_day))
        else:
            applications = Applications.objects.filter(customer_id=user_id).exclude(status=2)
        serializer = ApplicationSerializer(applications, many=True)
        return Response(serializer.data)
    else:
        return Response("Invalid user", status=status.HTTP_400_BAD_REQUEST)

#GET - получить одну заявку 
@api_view(['GET'])
@permission_classes([AllowAny])
def get_application(request, pk, format=None):
    application = get_object_or_404(Applications, pk=pk)
    if request.method == 'GET':
        serializer = ApplicationSerializer(application)
        application_data = serializer.data

        # Получить связанные опции для заявки с полными данными из таблицы Teachers
        application_teachers = Applicationsteachers.objects.filter(application=application)
        teachers_data = []
        for app_teacher in application_teachers:
            teacher_serializer = TeacherSerializer(app_teacher.teacher)
            teacher_data = teacher_serializer.data
            teachers_data.append(teacher_data)
        
        # Добавить данные об опциях в данные о заявке
        application_data['teachers'] = teachers_data
        
        return Response(application_data)


def calc_audience(order_id): 
    data = { 
        "lesson_id": order_id, 
        # "access_token": settings.REMOTE_WEB_SERVICE_AUTH_TOKEN, 
    } 
 
    requests.post("http://127.0.0.1:8080/calc_audience/", json=data, timeout=3)

@api_view(["PUT"]) 
@permission_classes([AllowAny])
def update_by_user(request, pk):
  if not Applications.objects.filter(pk=pk).exists():
      return Response(f"Заявки с таким id не существует!")

  request_status = request.data["status"]
  if int(request_status) not in [2, 3]:
      return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
  # Получить текущую заявку
  current_application = Applications.objects.get(pk=pk)
  
  if int(request_status) in [2]:
    print('AAAAAAAAAAAAAAAA')
    current_application.status = request_status 
    current_application.save() 
    serializer = ApplicationSerializer(current_application, many=False)
    response = Response(serializer.data)
    return response

  # Получить опции текущей заявки
  current_teachers = Applicationsteachers.objects.filter(application=current_application).values_list('teacher', flat=True)
  print(request.data["date"])
  print(request.data["time"])
  # Проверка наличия заявки с таким же статусом, временем и датой и с общими опциями
  existing_applications = Applications.objects.filter(
      status=request_status,
      day_lesson=request.data["date"],
      time_lesson=request.data["time"],
  ).exclude(pk=pk)
  print(existing_applications)
  for application in existing_applications:
    application_teachers = Applicationsteachers.objects.filter(application=application).values_list('teacher', flat=True)
    common_teachers = list(set(current_teachers).intersection(application_teachers))
    if common_teachers:
        return Response("Заявка с таким статусом, временем и датой уже существует!", status=status.HTTP_400_BAD_REQUEST)

 
  current_application.status = request_status 
  current_application.day_lesson = request.data["date"] 
  current_application.time_lesson = request.data["time"] 
  current_application.formed_at = timezone.now()
  calc_audience(current_application.pk)
  current_application.save() 
 
  serializer = ApplicationSerializer(current_application, many=False)
  response = Response(serializer.data)

  return response


@swagger_auto_schema(method='put',request_body=ApplicationSerializer)
@api_view(["PUT"]) 
@permission_classes([IsModerator])
def update_by_admin(request, pk): 

    access_token = request.COOKIES["access_token"]
    modername = session_storage.get(access_token).decode('utf-8')
    user = Users.objects.filter(email=modername).first()

    if not Applications.objects.filter(pk=pk).exists(): 
        return Response(f"Заявки с таким id не существует!") 
 
    request_status = request.data["status"] 
 
    if int(request.data["status"]) not in [4, 5]: 
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED) 
 
    application = Applications.objects.get(pk=pk) 
    if int(request.data["status"]) in [4]: 
        application.completed_at=timezone.now() 
    # app_status = application.status 
 
    # if app_status == 5: 
    #     return Response("Статус изменить нельзя") 
 
    application.moderator_id=user.id
    application.status = request_status
    application.save()

    serializer = ApplicationSerializer(application, many=False)
    response = Response(serializer.data)
    # response.setHeader("Access-Control-Allow-Methods", "PUT")
    return response


#DELETE - удалить одну заявку
@api_view(['Delete']) 
@permission_classes([AllowAny])
def delete_application(request, pk, format=None):     
    application = get_object_or_404(Applications, pk=pk) 
    print(application.status)
    if application.status == '1':
        application.delete() 
        return Response("Заявка успешно удалена.")
    else:
        return Response("Невозможно изменить статус заявки. Текущий статус не равен 1.", status=status.HTTP_400_BAD_REQUEST)



#DELETE - удалить конкретную услугу из конкретной заявки
@api_view(["DELETE"])
@permission_classes([AllowAny])
def delete_teacher_from_application(request, application_id, teacher_id):
    if not Applications.objects.filter(pk=application_id).exists():
        return Response("Заявки с таким id не существует", status=status.HTTP_404_NOT_FOUND)

    if not Teachers.objects.filter(pk=teacher_id).exists():
        return Response("Опции с таким id не существует", status=status.HTTP_404_NOT_FOUND)

    application = Applications.objects.get(pk=application_id)
    teacher = Teachers.objects.get(pk=teacher_id)

    application_subscription = get_object_or_404(Applicationsteachers, application=application, teacher=teacher)
    if application_subscription is None:
        print('yeeeeee')
        return Response("Заявка не найдена", status=404)
    application.applicationsteachers_set.filter(teacher=teacher).delete()
    application.save()

    return Response("Опция успешно удалена из заявки", status=200)


@api_view(["PUT"])
@permission_classes([IsRemoteWebService])
def update_audience(request, application_id):
    print("update_audience")
    if not Applications.objects.filter(pk=application_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    application = Applications.objects.get(pk=application_id)
    serializer = ApplicationSerializer(application, data=request.data, many=False, partial=True)

    if serializer.is_valid():
        serializer.save()

    return Response(status=status.HTTP_200_OK)

