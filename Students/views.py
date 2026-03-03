import pickle
from django.utils import timezone
from django.shortcuts import render
from django.conf import settings
from django.contrib import messages
import os
from .models import Attendance, UserProfile  # Adjust based on your app's models
import os
import shutil
from django.shortcuts import render
from django.contrib import messages
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from .models import UserProfile

try:
    import cv2
    import numpy as np
    from insightface.app import FaceAnalysis

    # ==========================================
    # LOAD ARCFACE MODEL (ONCE)
    # ==========================================
    face_app = FaceAnalysis(name="buffalo_l")
    face_app.prepare(ctx_id=0, det_size=(1024, 1024))
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    face_app = None

from django.views.decorators.csrf import csrf_exempt


from django.views.decorators.csrf import csrf_exempt

# ==========================================
# STUDENT REGISTRATION (SAFE VERSION)
# ==========================================
@csrf_exempt
def student_register(request):
    if not ML_AVAILABLE:
        return JsonResponse({"error": "Registration endpoint requires ML dependencies on local server."}, status=501)
    
    if request.method == "POST":
        # Temporary storage for cleanup
        created_user = None
        image_dir = None

        try:
            name = request.POST.get("name")
            loginid = request.POST.get("loginid")
            mobile = request.POST.get("mobile")
            password = request.POST.get("password")
            
            # New Class Fields
            department = request.POST.get("department")
            year = request.POST.get("year")
            semester = request.POST.get("semester")
            section = request.POST.get("section")
            
            images = request.FILES.getlist("images")

            # -------------------------------
            # BASIC VALIDATION
            # -------------------------------
            print("Received form data:", request.POST)
            print("Received files:", request.FILES)
            if not all([name, loginid, mobile, password, department, year, semester, section]):
                print(f"Missing fields! name={name}, loginid={loginid}, mobile={mobile}, password={password}, dept={department}, year={year}, sem={semester}, sec={section}")
                return JsonResponse({"error": "All fields are required."}, status=400)

            print(f"Number of images received: {len(images)}")
            if len(images) < 10:
                return JsonResponse({"error": "Please upload at least 10 face images."}, status=400)

            # Prepare temporary path for image extraction
            image_dir = os.path.join(settings.MEDIA_ROOT, 'temp', loginid)

            # Check if user already exists
            if UserProfile.objects.filter(loginid=loginid).exists():
                return JsonResponse({"error": "A user with this Login ID already exists."}, status=400)

            embeddings = []

            # -------------------------------
            # PROCESS IMAGES (create folder only now)
            # -------------------------------
            os.makedirs(image_dir, exist_ok=True)

            for idx, image_file in enumerate(images, 1):
                img_path = os.path.join(image_dir, f"img_{idx}.jpg")

                # Save uploaded image
                with open(img_path, "wb") as f:
                    for chunk in image_file.chunks():
                        f.write(chunk)

                # Load and process with OpenCV
                img = cv2.imread(img_path)
                if img is None:
                    continue  # Skip bad image

                faces = face_app.get(img)
                if len(faces) == 0:
                    continue  # No face detected

                # Select largest face
                face = max(
                    faces,
                    key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])
                )
                embeddings.append(face.embedding)

            # -------------------------------
            # FINAL VALIDATION: Face detection
            # -------------------------------
            if len(embeddings) == 0:
                raise Exception("No valid face embeddings detected in any of the uploaded images.")

            mean_embedding = np.mean(embeddings, axis=0)
            # Convert to list for MongoDB JSONField storage
            embedding_list = mean_embedding.tolist()

            # -------------------------------
            # DATABASE TRANSACTION (Atomic)
            # -------------------------------
            with transaction.atomic():
                # Create user inside transaction
                created_user = UserProfile.objects.create(
                    name=name,
                    loginid=loginid,
                    mobile=mobile,
                    password=password, # ⚠️ Remember to hash in production!
                    department=department,
                    year=int(year),
                    semester=int(semester),
                    section=section,
                    face_embedding=embedding_list
                )

            # Reload cached faces globally so the realtime pipeline knows about this new user immediately!
            global KNOWN_FACES
            KNOWN_FACES = load_known_faces()

            # Clean up temp folder immediately after success
            if image_dir and os.path.exists(image_dir):
                shutil.rmtree(image_dir)

            # If we reach here → Everything succeeded
            return JsonResponse({"success": True, "message": "Registration successful! Face data registered (Images deleted)."})

        except Exception as e:
            # -------------------------------
            # CLEANUP ON ANY ERROR
            # -------------------------------
            error_msg = str(e) or "An unexpected error occurred during registration."
            if not error_msg.strip():  # In case e is empty
                error_msg = "Registration failed due to invalid data or processing error."

            # Delete database entry if it was created
            if created_user:
                try:
                    created_user.delete()
                except:
                    pass  # Best effort

            # Delete uploaded images folder
            if image_dir and os.path.exists(image_dir):
                try:
                    shutil.rmtree(image_dir)
                except:
                    pass

            return JsonResponse({"error": f"Registration failed: {error_msg}"}, status=400)

    # GET request
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def student_api_login(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=400)
    try:
        data = json.loads(request.body)
        loginid = data.get('loginid')
        password = data.get('password')
        
        user = UserProfile.objects.filter(loginid=loginid, password=password).first()
        if user:
            return JsonResponse({
                "success": True, 
                "message": "Login successful",
                "data": {
                    "loginid": user.loginid,
                    "name": user.name,
                    "department": user.department,
                    "year": user.year,
                    "semester": user.semester,
                    "section": user.section
                }
            })
        return JsonResponse({"error": "Invalid credentials"}, status=401)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def student_my_attendance(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=400)
    try:
        data = json.loads(request.body)
        loginid = data.get('loginid')
        
        if not loginid:
            return JsonResponse({"error": "Missing loginid"}, status=400)
            
        records = Attendance.objects.filter(student_id=loginid).order_by('-date', '-period')
        
        results = []
        for r in records:
            from django.utils.timezone import localtime
            local_time = localtime(r.timestamp)
            results.append({
                "date": str(r.date),
                "period": r.period,
                "classification": r.classification,
                "is_lab": r.is_lab,
                "time": local_time.strftime("%I:%M %p")
            })
            
        return JsonResponse({"success": True, "data": results})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


from datetime import time, datetime

# EXACTLY FROM YOUR IMAGE
TIME_SLOTS = [
    ("P1", time(9, 40),  time(10, 40)),
    ("P2", time(10, 40), time(11, 30)),
    ("P3", time(11, 40), time(12, 30)),
    ("P4", time(12, 30), time(13, 20)),
    ("P5", time(14, 0),  time(14, 50)),
    ("P6", time(14, 50), time(15, 40)),
    ("P7", time(15, 40), time(16, 40)),
]

def get_current_period():
    now = datetime.now().time()
    for period, start, end in TIME_SLOTS:
        if start <= now <= end:
            start_dt = datetime.combine(datetime.today(), start)
            now_dt = datetime.combine(datetime.today(), now)
            duration_minutes = (now_dt - start_dt).total_seconds() / 60
            if duration_minutes <= 5:
                return period
            else:
                return f"{period}_CLOSED"
    return None



import os
import json
import base64
import logging
import csv
from datetime import date, datetime, time
from django.http import JsonResponse, StreamingHttpResponse
from django.conf import settings
from .models import Attendance

logger = logging.getLogger(__name__)

if ML_AVAILABLE:
    import numpy as np
    import cv2
    from insightface.app import FaceAnalysis

# =====================================================
# CONFIG
# =====================================================
EMBEDDING_DIR = os.path.join(settings.BASE_DIR, "embeddings")
THRESHOLD = 0.45
live_cap = None

# =====================================================
# TIMETABLE (FROM YOUR IMAGE)
# =====================================================
TIME_SLOTS = [
    ("P1", time(9, 40),  time(10, 40)),
    ("P2", time(10, 40), time(11, 30)),
    ("P3", time(11, 40), time(12, 30)),
    ("P4", time(12, 30), time(13, 20)),
    ("P5", time(14, 0),  time(14, 50)),
    ("P6", time(14, 50), time(15, 40)),
    ("P7", time(15, 40), time(16, 40)),
]

def get_current_period():
    now = datetime.now().time()
    for period, start, end in TIME_SLOTS:
        if start <= now <= end:
            return period
    return None

# =====================================================
# LOAD REGISTERED EMBEDDINGS FROM DB
# =====================================================
def load_known_faces():
    """Returns a dict mapping student_id to (numpy_embedding_array, UserProfile)"""
    known = {}
    if not ML_AVAILABLE:
        return known
        
    users_with_faces = UserProfile.objects.exclude(face_embedding__isnull=True)
    for user in users_with_faces:
        if user.face_embedding:
            # Convert JSON list back to numpy array
            known[user.loginid] = (np.array(user.face_embedding), user)
    return known

KNOWN_FACES = load_known_faces()

# =====================================================
# COSINE DISTANCE
# =====================================================
def cosine_distance(a, b):
    if not ML_AVAILABLE:
        return 1.0
    return 1 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# =====================================================
# CAMERA INIT
# =====================================================
def init_live_capture():
    global live_cap
    if not ML_AVAILABLE:
        return
    if live_cap is None or not live_cap.isOpened():
        live_cap = cv2.VideoCapture(0)
        if not live_cap.isOpened():
            logger.error("❌ Camera not accessible")
            live_cap = None

# =====================================================
# CSV EXPORT (HOURLY)
# =====================================================
def write_attendance_csv(attendance):
    csv_dir = os.path.join(settings.MEDIA_ROOT, "attendance_csv")
    os.makedirs(csv_dir, exist_ok=True)

    date_str = attendance.date.strftime("%Y-%m-%d")
    csv_path = os.path.join(csv_dir, f"attendance_{date_str}.csv")

    file_exists = os.path.exists(csv_path)

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Student ID", "Date", "Period", "Status", "Time"])

        writer.writerow([
            attendance.student_id,
            attendance.date,
            attendance.period,
            attendance.classification,
            attendance.timestamp.strftime("%H:%M:%S")
        ])

# =====================================================
# 🎥 REALTIME STREAM (HOURLY ATTENDANCE)
# =====================================================
@csrf_exempt
def realtime(request):

    def generate_frames():
        init_live_capture()
        today = date.today()

        while True:
            success, frame = live_cap.read()
            if not success:
                break

            period = get_current_period()
            faces = face_app.get(frame)

            for face in faces:
                emb = face.embedding
                bbox = face.bbox.astype(int)

                name = "Unknown"
                min_dist = 1.0
                matched_user = None

                for sid, (ref_emb, user) in KNOWN_FACES.items():
                    dist = cosine_distance(emb, ref_emb)
                    if dist < min_dist:
                        min_dist = dist
                        name = sid
                        matched_user = user

                if min_dist < THRESHOLD and period and matched_user:
                    
                    # -------------------------------
                    # CROSS-SECTION LOGIC
                    # -------------------------------
                    # Default: Assume this camera belongs to the same class as the student for now
                    # (In a real scenario, the camera/client would pass its location context)
                    current_camera_dept = request.GET.get('camera_dept', matched_user.department)
                    current_camera_year = int(request.GET.get('camera_year', matched_user.year))
                    current_camera_sem = int(request.GET.get('camera_sem', matched_user.semester))
                    current_camera_sec = request.GET.get('camera_sec', matched_user.section)
                    is_lab = request.GET.get('is_lab', 'false').lower() == 'true'

                    # Check if student belongs in this class
                    belongs_here = (
                        matched_user.department == current_camera_dept and 
                        matched_user.year == current_camera_year and 
                        matched_user.semester == current_camera_sem and 
                        matched_user.section == current_camera_sec
                    )

                    if belongs_here or is_lab:
                        attendance, created = Attendance.objects.get_or_create(
                            student_id=name,
                            date=today,
                            period=period,
                            defaults={
                                "classification": "Present",
                                "department": matched_user.department,
                                "year": matched_user.year,
                                "semester": matched_user.semester,
                                "section": matched_user.section,
                                "is_lab": is_lab
                            }
                        )
                        if created:
                            write_attendance_csv(attendance)
                    else:
                        # Reject cross section
                        name = f"{name} (Wrong Section)"
                        min_dist = 1.0 # Force red box

                color = (0,255,0) if min_dist < THRESHOLD else (0,0,255)

                cv2.rectangle(frame, bbox[:2], bbox[2:], color, 2)
                cv2.putText(
                    frame,
                    f"{name} | {period}",
                    (bbox[0], bbox[1]-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2
                )

            _, buffer = cv2.imencode(".jpg", frame)
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" +
                buffer.tobytes() +
                b"\r\n"
            )

        if live_cap:
            live_cap.release()

    return StreamingHttpResponse(
        generate_frames(),
        content_type="multipart/x-mixed-replace; boundary=frame"
    )

# =====================================================
# 📸 AUTO ATTENDANCE (BASE64 | HOURLY)
# =====================================================
@csrf_exempt
def auto_attendance(request):
    if not ML_AVAILABLE:
        return JsonResponse({"error": "Auto Attendance endpoint requires ML dependencies on local server."}, status=501)

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)
        image_data = data.get("image")

        if not image_data:
            return JsonResponse({"error": "No image"}, status=400)

        _, encoded = image_data.split(",", 1)
        frame = cv2.imdecode(
            np.frombuffer(base64.b64decode(encoded), np.uint8),
            cv2.IMREAD_COLOR
        )

        raw_period = get_current_period() or "After Hours"
        is_closed = raw_period.endswith("_CLOSED")
        period = raw_period.replace("_CLOSED", "")
        today = date.today()

        faces = face_app.get(frame)
        results = []

        for face in faces:
            emb = face.embedding
            min_dist = 1.0
            student_id = None
            matched_user = None

            for sid, (ref_emb, user) in KNOWN_FACES.items():
                dist = cosine_distance(emb, ref_emb)
                if dist < min_dist:
                    min_dist = dist
                    student_id = sid
                    matched_user = user

            # Notice we removed "and period" constraint since it defaults to "After Hours"
            if student_id and min_dist < THRESHOLD and matched_user:
                
                # Context from client
                current_camera_dept = data.get('camera_dept', matched_user.department)
                current_camera_year = int(data.get('camera_year', matched_user.year))
                current_camera_sem = int(data.get('camera_sem', matched_user.semester))
                current_camera_sec = data.get('camera_sec', matched_user.section)
                is_lab = data.get('is_lab', False)

                belongs_here = (
                    matched_user.department == current_camera_dept and 
                    matched_user.year == current_camera_year and 
                    matched_user.semester == current_camera_sem and 
                    matched_user.section == current_camera_sec
                )

                if is_closed:
                    results.append({
                        "id": str(student_id),
                        "student_id": str(student_id),
                        "name": matched_user.name,
                        "period": str(period),
                        "confidence": float(round(1 - float(min_dist), 2)),
                        "status": "Rejected: 5-Minute Window Missed"
                    })
                elif belongs_here or is_lab:
                    attendance, created = Attendance.objects.get_or_create(
                        student_id=student_id,
                        date=today,
                        period=period,
                        defaults={
                            "classification": "Present",
                            "department": matched_user.department,
                            "year": matched_user.year,
                            "semester": matched_user.semester,
                            "section": matched_user.section,
                            "is_lab": is_lab
                        }
                    )
                    if created:
                        write_attendance_csv(attendance)

                    results.append({
                        "id": str(student_id),
                        "student_id": str(student_id),
                        "name": matched_user.name,
                        "period": str(period),
                        "confidence": float(round(1 - float(min_dist), 2)),
                        "status": "Marked" if created else "Already Marked"
                    })
                else:
                    results.append({
                        "id": str(student_id),
                        "student_id": str(student_id),
                        "name": matched_user.name,
                        "period": str(period),
                        "confidence": float(round(1 - float(min_dist), 2)),
                        "status": "Rejected: Wrong Context block"
                    })

        return JsonResponse({
            "period": str(period),
            "faces_detected": len(results),
            "results": results
        })

    except Exception:
        logger.exception("❌ Auto attendance failed")
        return JsonResponse({"error": "Processing error"}, status=500)
