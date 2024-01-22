from django.shortcuts import render 
from rest_framework.response import Response 
from django.shortcuts import get_object_or_404 
from rest_framework import status 
from .serializers import * 
from .models import * 
from rest_framework.decorators import api_view 
from minio import Minio
from django.http import HttpResponseBadRequest
from django.http import HttpResponseServerError
from rest_framework.parsers import FileUploadParser
from rest_framework.decorators import parser_classes
from django.http import HttpResponse
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from rest_framework.parsers import FileUploadParser
from rest_framework.decorators import parser_classes
from rest_framework import status
from rest_framework.test import APITestCase

user= Users.objects.get(id=1)


#GET - получить список всех опций 
@api_view(['Get']) 
def get_teachers(request, format=None): 
    search_query = request.GET.get('search', '')
    faculty = request.GET.get('faculty', '')
    
    teachers = Teachers.objects.filter(available=True).filter(title__icontains=search_query)

    if faculty and faculty != 'Любой факультет':
        teachers = teachers.filter(faculty=faculty)
    
    serializer = TeacherSerializer(teachers, many=True)
    
    #Retrieve the application with customer user and status equal to 1
    application = Applications.objects.filter(customer=user, status=1).first()
    if application:
        application_serializer = ApplicationSerializer(application)
        apps_data = [application_serializer.data]
    else:
        apps_data = []
    
    response_data = {
        'apps': apps_data,
        'teachers': serializer.data,
    }
    
    return Response(response_data)

#POST - добавить новую опцию 
@api_view(['Post']) 
def post_teacher(request):     
    serializer = TeacherSerializer(data=request.data) 
    if serializer.is_valid(): 
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED) 
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 

@api_view(['POST'])
@parser_classes([MultiPartParser])
def postImageToSubscription(request, pk):
    if 'file' in request.FILES:
        file = request.FILES['file']
        teacher = Teachers.objects.get(pk=pk, available=True)
        
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
            
            serializer = TeacherSerializer(instance=teacher, data={'image': file_path}, partial=True)
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
def get_teacher(request, pk, format=None): 
    teacher = get_object_or_404(Teachers, pk=pk) 
    if request.method == 'GET': 
        serializer = TeacherSerializer(teacher) 
        return Response(serializer.data) 
 
#PUT - обновить одну опцию 
@api_view(['Put']) 
def put_teacher(request, pk, format=None): 
    teacher = get_object_or_404(Teachers, pk=pk) 
    serializer = TeacherSerializer(teacher, data=request.data) 
    if serializer.is_valid(): 
        serializer.save() 
        return Response(serializer.data) 
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 
 
#PUT - удалить одну опцию 
@api_view(['Put']) 
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
def add_to_application(request, pk):
    if not Teachers.objects.filter(id=pk).exists():
        return Response(f"Услуги с таким id не существует!")

    teacher = Teachers.objects.get(id=pk)

    application = Applications.objects.filter(status=1).last()

   

    day_lesson = request.data.get("day_lesson")
    time_lesson = request.data.get("time_lesson")
    audit_lesson = request.data.get("audit_lesson")


    
    existing_lessons = Applications.objects.filter(day_lesson=day_lesson, time_lesson=time_lesson)
    
    existing_teachers = Applicationsteachers.objects.filter(application__in=existing_lessons, teacher=teacher) 
    if existing_teachers.exists():
        error_message = 'Опция уже добавлена в одну из существующих заявок' 
        return render(request, 'add_lesson.html', {'error_message': error_message})

    if application is None:
        application = Applications.objects.create(customer_id=user.id, day_lesson=day_lesson, time_lesson = time_lesson, audit_lesson = audit_lesson)

    # if existing_lessons :
        
    #     # Заявка уже существует, выводим сообщение об ошибке
    #     error_message = 'Преподаватель уже занят в выбранное время'
    #     return render(request, 'add_lesson.html', {'error_message': error_message})

    application_teacher = Applicationsteachers.objects.create(
        teacher=teacher
    )

    application_teacher.application = application  # Устанавливаем связь с объектом Applications
    application_teacher.save()  # Сохраняем объект Applicationsteachers

    serializer = TeacherSerializer(application_teacher)
    return Response(serializer.data, status=status.HTTP_201_CREATED)





 
#GET - получить список всех заявок 
@api_view(['Get']) 
def get_applications(request, format=None): 
    print('get') 
    applications = Applications.objects.all() 
    serializer = ApplicationSerializer(applications, many=True) 
    return Response(serializer.data) 
 
#GET - получить одну заявку 
@api_view(['GET'])
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
            # teacher_data['day_less'] = app_teacher.day_less
            # teacher_data['time_less'] = app_teacher.time_less
            # teacher_data['audit_less'] = app_teacher.audit_less
            teachers_data.append(teacher_data)
        
        # Добавить данные об опциях в данные о заявке
        application_data['teachers'] = teachers_data
        
        return Response(application_data)


@api_view(["PUT"]) 
def update_by_user(request, pk): 
    if not Applications.objects.filter(pk=pk).exists(): 
        return Response(f"Заявки с таким id не существует!") 
 
    request_status = request.data["status"] 
 
    if int(request.data["status"]) not in [2, 3]: 
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED) 
 
    application = Applications.objects.get(pk=pk) 
    app_status = application.status 
 
    if int(request.data["status"]) in [3]: 
        application.formed_at=timezone.now() 
     
 
    application.status = request_status 
    application.save() 
 
    serializer = ApplicationSerializer(application, many=False) 
    return Response(serializer.data)

@api_view(["PUT"]) 
def update_by_admin(request, pk): 
    if not Applications.objects.filter(pk=pk).exists(): 
        return Response(f"Заявки с таким id не существует!") 
 
    request_status = request.data["status"] 
 
    if int(request.data["status"]) not in [4, 5]: 
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED) 
 
    application = Applications.objects.get(pk=pk) 
    if int(request.data["status"]) in [4]: 
        application.formed_at=timezone.now() 
    # app_status = application.status 
 
    # if app_status == 5: 
    #     return Response("Статус изменить нельзя") 
 
    application.status = request_status 
    application.save() 
 
    serializer = ApplicationSerializer(application, many=False) 
    return Response(serializer.data)


#DELETE - удалить одну заявку
@api_view(['Delete']) 
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
def delete_teacher_from_application(request, application_id, teacher_id):
    if not Applications.objects.filter(pk=application_id).exists():
        return Response("Заявки с таким id не существует", status=status.HTTP_404_NOT_FOUND)

    if not Teachers.objects.filter(pk=teacher_id).exists():
        return Response("Опции с таким id не существует", status=status.HTTP_404_NOT_FOUND)

    application = Applications.objects.get(pk=application_id)
    teacher = Teachers.objects.get(pk=teacher_id)

    application.applicationsteachers_set.filter(teacher=teacher).delete()
    application.save()

    return Response("Опция успешно удалена из заявки", status=status.HTTP_204_NO_CONTENT)


# #PUT - изменить кол-во конкретной опции в заявке
# @api_view(["PUT"])
# def update_teacher_amount(request, application_id, teacher_id):
#     if not Applications.objects.filter(pk=application_id).exists() or not Teachers.objects.filter(pk=teacher_id).exists():
#         return Response("Заявки или опции с такими id не существует", status=status.HTTP_404_NOT_FOUND)

#     application_teacher = Applicationsteachers.objects.filter(application_id=application_id, teacher_id=teacher_id).first()

#     if not application_teacher:
#         return Response("В этой заявке нет такой опции", status=status.HTTP_404_NOT_FOUND)

#     new_amount = request.data.get("amount",1)
#     application_teacher.amount = new_amount
#     application_teacher.save()
#     return Response("Amount успешно обновлен", status=status.HTTP_200_OK)
