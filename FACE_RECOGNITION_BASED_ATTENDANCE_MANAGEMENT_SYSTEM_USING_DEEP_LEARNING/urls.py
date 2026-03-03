
from django.contrib import admin
from django.urls import path
from FACE_RECOGNITION_BASED_ATTENDANCE_MANAGEMENT_SYSTEM_USING_DEEP_LEARNING import views as mv
from Students import views as sv
from django.conf import settings
from django.conf.urls.static import static
from Faculty import views as fv
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',mv.index,name='index'),
    path('studentRegister',mv.studentRegister,name='studentRegister'),
    path('facultyLogin',mv.facultyLogin,name='facultyLogin'),
    path('studentLogin',mv.studentLogin,name='studentLogin'),




    path('facultyLoginCheck',fv.facultyLoginCheck,name='facultyLoginCheck'),
    path('facultyHome',fv.facultyHome,name='facultyHome'),
    # path('training',fv.training,name='training'),
    path('studentAttendance',fv.studentAttendance,name='studentAttendance'),
    path('dayWiseReports',fv.dayWiseReports,name='dayWiseReports'),
    path('download_daywise_csv/<str:date>/', fv.download_daywise_csv, name='download_daywise_csv'),     
    path('log',fv.log,name='log'),


    # ==========================
    # ADMIN CRUD MODIFICATIONS
    # ==========================
    path('api/admin/students', fv.get_all_students, name='get_all_students'),
    path('api/admin/student/update', fv.update_student, name='update_student'),
    path('api/admin/student/delete', fv.delete_student, name='delete_student'),
    path('api/admin/attendance/update', fv.update_attendance, name='update_attendance'),
    path('api/admin/attendance/mark_absentees', fv.mark_absentees, name='mark_absentees'),
    # ==========================
    # STUDENT DASHBOARD APIS
    # ==========================
    path('api/student/login', sv.student_api_login, name='student_api_login'),
    path('api/student/attendance', sv.student_my_attendance, name='student_my_attendance'),

    path('student_register', sv.student_register, name='student_register'),
    path('live_stream/', sv.realtime, name='live_stream'),

    # Automatic attendance (NO capture button, multi-face, once/day)
    path('auto_attendance/', sv.auto_attendance, name='auto_attendance'),
    path('validate_face/', sv.auto_attendance, name='validate_face')



]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)