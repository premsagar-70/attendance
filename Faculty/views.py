from django.shortcuts import render
from django.contrib import messages
from Students.models import Attendance
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def facultyLoginCheck(request):
    if request.method == 'POST':
        loginid = request.POST.get('loginid', '')
        password = request.POST.get('password', '')

        if loginid == "admin" and password == 'admin':
            request.session['admin'] = True
            return JsonResponse({'status': 'success', 'message': 'Logged in successfully'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid details, please try again later'}, status=401)
    else:
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    


from django.shortcuts import render

@csrf_exempt
def facultyHome(request):
    if not request.session.get('admin'):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)
    return JsonResponse({'status': 'success', 'data': 'Welcome to Faculty Home'})

@csrf_exempt
def log(request):
    request.session.flush()
    return JsonResponse({'status': 'success', 'message': 'Logged out'})




# import os
# import cv2
# import numpy as np
# from mtcnn import MTCNN
# import face_recognition
# from sklearn.preprocessing import LabelEncoder
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import confusion_matrix
# from tensorflow.keras.models import Sequential
# from tensorflow.keras.layers import Dense
# import pickle
# from django.shortcuts import render
# from django.contrib.auth.decorators import login_required
# from django.conf import settings

# # Initialize MTCNN detector
# detector = MTCNN()

# # Path to dataset (update in settings.py or hardcode for testing)
# DATASET_PATH = "media"

# # Load and preprocess dataset
# import os
# import cv2
# import numpy as np
# import face_recognition
# from pathlib import Path

# def load_dataset(dataset_path):
   
#     embeddings = []
#     labels = []
    
#     # Convert dataset_path to Path object for robust handling
#     dataset_path = Path(dataset_path)
    
#     # Iterate through person directories
#     for person_name in dataset_path.iterdir():
#         if not person_name.is_dir():
#             continue
        
#         # Iterate through images in person directory
#         for image_path in person_name.glob("*.jpg"):  # Adjust for other formats if needed
#             try:
#                 # Load image using OpenCV
#                 image = cv2.imread(str(image_path))
#                 if image is None:
#                     print(f"Failed to load image: {image_path}")
#                     continue
                
#                 # Convert BGR to RGB
#                 image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
#                 # Detect face locations using face_recognition
#                 face_locations = face_recognition.face_locations(image_rgb, model="hog")  # Use 'cnn' for GPU
#                 if not face_locations:
#                     print(f"No faces detected in: {image_path}")
#                     continue
                
#                 # Compute face embeddings for all detected faces
#                 face_embeddings = face_recognition.face_encodings(image_rgb, face_locations)
#                 if not face_embeddings:
#                     print(f"No embeddings computed for: {image_path}")
#                     continue
                
#                 # Append the first embedding (modify for multiple faces if needed)
#                 embeddings.append(face_embeddings[0])
#                 labels.append(person_name.name)
                
#             except Exception as e:
#                 print(f"Error processing {image_path}: {e}")
#                 continue
    
#     # Convert to NumPy arrays
#     embeddings = np.array(embeddings)
#     labels = np.array(labels)
    
#     # Validate output
#     if embeddings.size == 0:
#         print("Warning: No valid embeddings were computed.")
    
#     return embeddings, labels

# # Build SoftMax classifier
# def build_classifier(input_dim, num_classes):
#     model = Sequential([
#         Dense(64, activation='relu', input_dim=input_dim),
#         Dense(num_classes, activation='softmax')
#     ])
#     model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
#     return model

# # Calculate performance metrics
# def calculate_metrics(y_true, y_pred):
#     cm = confusion_matrix(y_true, y_pred)
#     if cm.shape == (2, 2):
#         tn, fp, fn, tp = cm.ravel()
#     else:
#         tn = cm.sum() - (cm.sum(axis=0) + cm.sum(axis=1) - np.diag(cm)).sum()
#         fp = cm.sum(axis=0) - np.diag(cm)
#         fn = cm.sum(axis=1) - np.diag(cm)
#         tp = np.diag(cm)
#         tn, fp, fn, tp = np.sum(tn), np.sum(fp), np.sum(fn), np.sum(tp)
    
#     accuracy = (tp + tn) / (tp + tn + fp + fn)
#     sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
#     specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
#     precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    
#     return {
#         'accuracy': round(accuracy * 100, 2),
#         'sensitivity': round(sensitivity * 100, 2),
#         'specificity': round(specificity * 100, 2),
#         'precision': round(precision * 100, 2)
#     }


# def training(request):
#     if not request.session.get('admin'):
#         return render(request, 'facultyLogin.html')

#     # Load dataset
#     embeddings, labels = load_dataset(DATASET_PATH)
#     print("Dataset loading successful")

#     if len(embeddings) == 0:
#         return render(request, 'faculty/training.html', {
#             'error': 'No valid data loaded. Check dataset path and images.'
#         })

#     # Encode labels
#     encoder = LabelEncoder()
#     encoded_labels = encoder.fit_transform(labels)

#     # Train-test split
#     X_train, X_test, y_train, y_test = train_test_split(
#         embeddings, encoded_labels, test_size=0.3, random_state=42
#     )

#     # Build and train the model
#     num_classes = len(np.unique(encoded_labels))
#     model = build_classifier(input_dim=128, num_classes=num_classes)
#     model.fit(X_train, y_train, epochs=10, batch_size=32, verbose=1)

#     # Evaluate model
#     y_pred = model.predict(X_test).argmax(axis=1)
#     metrics = calculate_metrics(y_test, y_pred)

#     # Save model and label encoder
#     model_path = os.path.join(settings.BASE_DIR, 'models', 'softmax_model.h5')
#     encoder_path = os.path.join(settings.BASE_DIR, 'models', 'label_encoder.pkl')
#     os.makedirs(os.path.dirname(model_path), exist_ok=True)
#     model.save(model_path)
#     with open(encoder_path, 'wb') as f:
#         pickle.dump(encoder, f)

#     # Render training result
#     return render(request, 'faculty/training.html', {
#         'metrics': metrics,
#         'success': 'Model trained successfully.'    
#     })

from collections import defaultdict
from django.shortcuts import render
from django.utils.timezone import localtime
from Students.models import Attendance, UserProfile
import json
from collections import defaultdict

from collections import defaultdict
from django.shortcuts import render
from django.utils.timezone import localtime

@csrf_exempt
def studentAttendance(request):
    if not request.session.get('admin'):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)

    records = Attendance.objects.order_by('date', 'period', 'student_id')
    
    data = []
    for rec in records:
        rec.local_time = localtime(rec.timestamp)
        data.append({
            'date': str(rec.date),
            'period': rec.period,
            'student_id': rec.student_id,
            'department': rec.department,
            'year': rec.year,
            'semester': rec.semester,
            'section': rec.section,
            'classification': rec.classification,
            'local_time': rec.local_time.strftime("%I:%M %p"),
            'is_lab': rec.is_lab
        })

    return JsonResponse({'status': 'success', 'data': data})


import json

@csrf_exempt
def dayWiseReports(request):
    if not request.session.get('admin'):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)

    if request.method == "POST":
        try:
            body = json.loads(request.body)
        except:
            body = request.POST

        selected_date = body.get("date")
        department = body.get("department")
        year = body.get("year")
        semester = body.get("semester")
        section = body.get("section")

        filters = {"date": selected_date}
        if department: filters["department"] = department
        if year: filters["year"] = int(year)
        if semester: filters["semester"] = int(semester)
        if section: filters["section"] = section

        records = Attendance.objects.filter(**filters).order_by('period', 'student_id')

        if records.exists():
            data = []
            for rec in records:
                data.append({
                    'student_id': rec.student_id,
                    'department': rec.department,
                    'year': rec.year,
                    'semester': rec.semester,
                    'section': rec.section,
                    'date': str(rec.date),
                    'period': rec.period,
                    'classification': rec.classification,
                    'local_time': localtime(rec.timestamp).strftime("%I:%M %p"),
                    'is_lab': rec.is_lab
                })
            return JsonResponse({'status': 'success', 'data': data})
        else:
            return JsonResponse({'status': 'error', 'message': 'No attendance found for selected date and filters'}, status=404)

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

import csv
from django.http import Http404, HttpResponse
from django.utils.timezone import localtime
from Students.models import Attendance

@csrf_exempt
def download_daywise_csv(request, date):
    if not request.session.get('admin'):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)

    # Get filters from query params
    department = request.GET.get("dept")
    year = request.GET.get("yr")
    semester = request.GET.get("sem")
    section = request.GET.get("sec")

    filters = {"date": date}
    if department: filters["department"] = department
    if year: filters["year"] = int(year)
    if semester: filters["semester"] = int(semester)
    if section: filters["section"] = section

    records = Attendance.objects.filter(**filters).order_by(
        'student_id', 'period'
    )

    if not records.exists():
        raise Http404("No attendance found for selected filters")

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="attendance_{date}.csv"'
    )

    writer = csv.writer(response)
    writer.writerow(["Student ID", "Department", "Year", "Semester", "Section", "Date", "Period", "Status", "Time (IST)", "Is Lab"])

    for rec in records:
        local_ts = localtime(rec.timestamp)
        writer.writerow([
            rec.student_id,
            rec.department or "-",
            rec.year or "-",
            rec.semester or "-",
            rec.section or "-",
            rec.date,
            rec.period,
            rec.classification,
            local_ts.strftime("%I:%M %p"),
            "Yes" if rec.is_lab else "No"
        ])

    return response

# =========================================================
# NEW ADMIN DATA MODIFICATION APIS (CRUD)
# =========================================================

@csrf_exempt
def get_all_students(request):
    if not request.session.get('admin'):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)
    
    users = UserProfile.objects.all().order_by('loginid')
    data = []
    for u in users:
        data.append({
            'loginid': u.loginid,
            'name': u.name,
            'department': u.department,
            'year': u.year,
            'semester': u.semester,
            'section': u.section
        })
    return JsonResponse({'status': 'success', 'data': data})

@csrf_exempt
def update_student(request):
    if not request.session.get('admin'):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Invalid Method'}, status=400)
    
    try:
        data = json.loads(request.body)
        loginid = data.get('loginid')
        user = UserProfile.objects.get(loginid=loginid)

        user.department = data.get('department', user.department)
        user.year = int(data.get('year', user.year))
        user.semester = int(data.get('semester', user.semester))
        user.section = data.get('section', user.section)
        user.save()
        
        return JsonResponse({'status': 'success', 'message': f'Student {loginid} updated.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
def delete_student(request):
    if not request.session.get('admin'):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Invalid Method'}, status=400)
    
    try:
        data = json.loads(request.body)
        loginid = data.get('loginid')
        UserProfile.objects.filter(loginid=loginid).delete()
        
        # Also delete all attendance corresponding records so DB is clean
        Attendance.objects.filter(student_id=loginid).delete()
        
        # Refresh Global Dict cache by tricking the system (handled by Student/views in a larger scope)
        # Note: True global sync would require Redis, but for demonstration we delete from DB
        return JsonResponse({'status': 'success', 'message': f'Student {loginid} and all related data purged.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
def update_attendance(request):
    if not request.session.get('admin'):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Invalid Method'}, status=400)
    
    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        date = data.get('date')
        period = data.get('period')
        new_status = data.get('classification')

        att = Attendance.objects.get(student_id=student_id, date=date, period=period)
        att.classification = new_status
        att.save()

        return JsonResponse({'status': 'success', 'message': f'Attendance changed to {new_status}'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
def mark_absentees(request):
    if not request.session.get('admin'):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)
    
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Invalid Method'}, status=400)

    try:
        data = json.loads(request.body)
        target_date = data.get('date')
        target_period = data.get('period')
        dept = data.get('department')
        year = data.get('year')
        sem = data.get('semester')
        sec = data.get('section')

        if not target_date or not target_period:
            return JsonResponse({"status": "error", "message": "Date and Period are strongly required."}, status=400)

        # Build dynamic query filter for UserProfile table
        student_filter = {}
        if dept and dept != '': student_filter['department'] = dept
        if year and year != '': student_filter['year'] = year
        if sem and sem != '': student_filter['semester'] = sem
        if sec and sec != '': student_filter['section'] = sec

        students = UserProfile.objects.filter(**student_filter)
        absent_count = 0

        for student in students:
            # Check if an attendance record ALREADY exists for this student on this date+period
            record_exists = Attendance.objects.filter(
                student_id=student.loginid,
                date=target_date,
                period=target_period
            ).exists()

            if not record_exists:
                # Target absent row detected - Inject synthetic record
                Attendance.objects.create(
                    student_id=student.loginid,
                    date=target_date,
                    period=target_period,
                    department=student.department,
                    year=student.year,
                    semester=student.semester,
                    section=student.section,
                    classification="Absent", # Crucial Marker
                    is_lab=False
                )
                absent_count += 1

        return JsonResponse({'status': 'success', 'message': f'Generated {absent_count} absolute absent records.', 'generated': absent_count})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
