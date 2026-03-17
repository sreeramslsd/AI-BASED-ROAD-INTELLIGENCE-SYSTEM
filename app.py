import subprocess
import os
import sys
from flask import Flask, Response, render_template, request, redirect, url_for, session
import datetime
import os
from flask import Flask, render_template, request, redirect, url_for, session, Response
import os
import cv2
from ultralytics import YOLO

from flask import Flask, request
import threading
import cv2
from ultralytics import YOLO
import yt_dlp



app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

def login_required():
    return "officer_id" in session

# DEMO OFFICERS DATA - ONLY 5 DISTRICTS
DEMO_OFFICERS = [
    ("OFF-AP-123", "Andhra Pradesh", "Vijayawada", "12345"),
    ("OFF-TS-123", "Telangana", "Hyderabad", "12345"),
    ("OFF-TN-123", "Tamil Nadu", "Chennai", "12345"),
    ("OFF-KA-123", "Karnataka", "Bengaluru Urban", "12345"),
    ("OFF-MH-123", "Maharashtra", "Mumbai", "12345"),
]

# COMPLETE DYNAMIC DATA FOR 5 DISTRICTS ONLY
AREAS_DATA = {
    'vijayawada': {
        'state': 'Andhra Pradesh',
        'location': 'Vijayawada',
        'location_type': 'Road Infrastructure',
        'background_image': 'images/default-highway.jpg',
        'welcome_color': 'rgb(77, 190, 190)',
        'officer_name': 'S. Rama Krishna',
        'officer_title': 'District Roads Engineer (NRIP)',
        'employee_id': 'OFF-AP-123',
        'organization': 'Vijayawada Municipal Corporation',
        'jurisdiction': 'Vijayawada Urban Division',
        'programs': 'PMGSY, CRF, NRIDP',
        'critical_roads': '42',
        'current_date': 'Feb 01, 2026',
        'total_length': '1,264',
        'highways': 'NH-16, SH-41',
        'pmgsy_count': '2,847',
        'total_km': '1,264',
        'critical_count': '42',
        'under_repair': '187',
        'orders_count': '156',
        'complaints_total': '89',
        'active_contractors': '12',
        'budget_cr': '4.2',
        'inspections_live': 'LIVE',
        'alert_title': 'CRF URGENT ACTION REQUIRED',
        'alert_location': 'Benz Circle - MG Road (NH-16)',
        'alert_details': 'Priority CRF funding | Severe pothole damage | 24hr repair deadline',
        'alert_deadline': '24 HRS',
        'system_status': 'NRIP System Active',
        'last_login': 'Today 15:28',
        'budget_info': 'CRF Budget: ₹4.2 Cr',
        'repairs_km': '187 km',
        'inspections_due': '67'
    },
    
    'hyderabad': {
        'state': 'Telangana',
        'location': 'Hyderabad',
        'location_type': 'Metro Highways',
        'background_image': 'images/default-highway.jpg',
        'welcome_color': 'rgb(255, 193, 7)',
        'officer_name': 'A. Rahman',
        'officer_title': 'Hyderabad R&B Chief Engineer',
        'employee_id': 'OFF-TS-123',
        'organization': 'Hyderabad Metropolitan Development',
        'jurisdiction': 'ORR & Greater Hyderabad',
        'programs': 'NHDP, ORR, State Roads',
        'critical_roads': '67',
        'current_date': 'Feb 01, 2026',
        'total_length': '3,456',
        'highways': 'NH-44, NH-65, ORR',
        'pmgsy_count': '5,678',
        'total_km': '3,456',
        'critical_count': '67',
        'under_repair': '456',
        'orders_count': '678',
        'complaints_total': '289',
        'active_contractors': '34',
        'budget_cr': '12.4',
        'inspections_live': '24x7',
        'alert_title': 'ORR TRAFFIC JAM',
        'alert_location': 'ORR Exit 12 - Gachibowli',
        'alert_details': 'Construction blockade | IT traffic affected | Immediate clearance',
        'alert_deadline': '6 HRS',
        'system_status': 'ORR System Active',
        'last_login': 'Today 15:28',
        'budget_info': 'NHDP Budget: ₹12.4 Cr',
        'repairs_km': '456 km',
        'inspections_due': '234'
    },
    
    'chennai': {
        'state': 'Tamil Nadu',
        'location': 'Chennai',
        'location_type': 'Metro Expressways',
        'background_image': 'images/default-highway.jpg',
        'welcome_color': 'rgb(76, 175, 80)',
        'officer_name': 'R. Srinivasan',
        'officer_title': 'Chennai Highways Director',
        'employee_id': 'OFF-TN-123',
        'organization': 'Chennai City Traffic Police',
        'jurisdiction': 'Chennai Metro Area',
        'programs': 'CMRL, NHDP, State Expressways',
        'critical_roads': '89',
        'current_date': 'Feb 01, 2026',
        'total_length': '4,567',
        'highways': 'NH-48, NH-32',
        'pmgsy_count': '7,234',
        'total_km': '4,567',
        'critical_count': '89',
        'under_repair': '678',
        'orders_count': '1,234',
        'complaints_total': '567',
        'active_contractors': '56',
        'budget_cr': '18.9',
        'inspections_live': 'EMERGENCY',
        'alert_title': 'MONSOON FLOODING',
        'alert_location': 'Anna Salai - Mount Road',
        'alert_details': 'Waterlogging critical | CBD traffic paralyzed | Pump deployment',
        'alert_deadline': '8 HRS',
        'system_status': 'CMRL System Active',
        'last_login': 'Today 15:28',
        'budget_info': 'CMRL Budget: ₹18.9 Cr',
        'repairs_km': '678 km',
        'inspections_due': '345'
    },
    
    'bengaluru-urban': {
        'state': 'Karnataka',
        'location': 'Bengaluru Urban',
        'location_type': 'Silicon Valley Roads',
        'background_image': 'images/default-highway.jpg',
        'welcome_color': 'rgb(33, 150, 243)',
        'officer_name': 'N. Ravi Kumar',
        'officer_title': 'Bengaluru BBMP Engineer',
        'employee_id': 'OFF-KA-123',
        'organization': 'Bruhat Bengaluru Mahanagara Palike',
        'jurisdiction': 'BBMP 8 Zones',
        'programs': 'NMT, BSRP, Tech Corridor',
        'critical_roads': '156',
        'current_date': 'Feb 01, 2026',
        'total_length': '8,765',
        'highways': 'NH-48, NH-44, NICE Road',
        'pmgsy_count': '12,456',
        'total_km': '8,765',
        'critical_count': '156',
        'under_repair': '1,234',
        'orders_count': '2,345',
        'complaints_total': '1,789',
        'active_contractors': '89',
        'budget_cr': '45.2',
        'inspections_live': 'CRITICAL',
        'alert_title': 'TECH CORRIDOR CRISIS',
        'alert_location': 'Outer Ring Road - Marathahalli',
        'alert_details': 'IT traffic collapse | Tech company access blocked | Emergency widening',
        'alert_deadline': '4 HRS',
        'system_status': 'BBMP System Active',
        'last_login': 'Today 15:28',
        'budget_info': 'BSRP Budget: ₹45.2 Cr',
        'repairs_km': '1,234 km',
        'inspections_due': '789'
    },
    
    'mumbai': {
        'state': 'Maharashtra',
        'location': 'Mumbai',
        'location_type': 'Financial Capital Roads',
        'background_image': 'images/default-highway.jpg',
        'welcome_color': 'rgb(244, 67, 54)',
        'officer_name': 'V. Patil',
        'officer_title': 'Mumbai BMC Road Engineer',
        'employee_id': 'OFF-MH-123',
        'organization': 'Brihanmumbai Municipal Corporation',
        'jurisdiction': 'Mumbai Island & Suburban',
        'programs': 'MMRDA, Coastal Road, Eastern Freeway',
        'critical_roads': '234',
        'current_date': 'Feb 01, 2026',
        'total_length': '5,678',
        'highways': 'Western Expressway, Eastern Freeway',
        'pmgsy_count': '9,876',
        'total_km': '5,678',
        'critical_count': '234',
        'under_repair': '2,345',
        'orders_count': '5,678',
        'complaints_total': '3,456',
        'active_contractors': '123',
        'budget_cr': '89.5',
        'inspections_live': '24x7',
        'alert_title': 'MONSOON COLLAPSE',
        'alert_location': 'Bandra-Worli Sea Link Approach',
        'alert_details': 'Monsoon damage critical | Sea link access blocked | Emergency repair',
        'alert_deadline': '12 HRS',
        'system_status': 'BMC System Active',
        'last_login': 'Today 15:28',
        'budget_info': 'MMRDA Budget: ₹89.5 Cr',
        'repairs_km': '2,345 km',
        'inspections_due': '1,234'
    }
}






BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "runs", "pothole_model", "weights", "best.pt")

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("❌ best.pt not found! Train your model first.")

# Load YOLO model once
model = YOLO(MODEL_PATH)

# Default video source (can be changed dynamically per node)
VIDEO_SOURCES = {
    "vijayawada": "https://www.youtube.com/watch?v=Uuaemo4RwFU",
    "hyderabad": "https://www.youtube.com/watch?v=8JCk5M_xrBs",
    "chennai": "https://www.youtube.com/watch?v=Lxqcg1qt0XU",
    "bengaluru-urban": "https://www.youtube.com/watch?v=WKGK_hYnlGE",
    "mumbai": "https://www.youtube.com/watch?v=OkQ0utdxwBY"
}






@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        officer_id = request.form.get("officer_id")
        password = request.form.get("password")

        for demo_id, _, city, demo_pass in DEMO_OFFICERS:
            if officer_id == demo_id and password == demo_pass:
                session["officer_id"] = officer_id
                area = city.lower().replace(" ", "-")
                return redirect(url_for("dashboard", area=area))

        return render_template("index.html", error="Invalid credentials")

    return render_template("index.html")


# -------------------------------------------------
# DASHBOARD
# -------------------------------------------------

@app.route("/dashboard/<area>")
def dashboard(area):
    if not login_required():
        return redirect(url_for("index"))

    area_key = area.lower().replace(" ", "-")
    data = AREAS_DATA.get(area_key)

    if not data:
        return redirect(url_for("dashboard", area="vijayawada"))

    return render_template(
        "dashboard.html",
        dynamic_data=data,
        current_area=area_key,
        officer_id=session["officer_id"],
    )

def run_yolo_on_youtube(youtube_url):
    # Get playable URL
    ydl_opts = {'format': 'best'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        stream_url = info['url']

    cap = cv2.VideoCapture(stream_url)

    while True:
        ret, frame = cap.read()
        if not ret:
            break  # End of video or stream

        # Keep aspect ratio
        h, w = frame.shape[:2]
        scale = 640 / max(h, w)
        frame_resized = cv2.resize(frame, (int(w*scale), int(h*scale)))

        results = model.predict(frame_resized, conf=0.3, verbose=False)
        annotated = results[0].plot()

        cv2.imshow("Pothole Detection", annotated)

        # Press 'q' or close window
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        if cv2.getWindowProperty("Pothole Detection", cv2.WND_PROP_VISIBLE) < 1:
            break

    cap.release()
    cv2.destroyAllWindows()




@app.route('/profile')
def view_profile():
    # Fetching Chief Engineer Sreeram's specific credentials
    return render_template('profile.html')

import threading

@app.route("/run_yolo", methods=["POST"])
def run_yolo():
    data = request.get_json()
    yt_link = data.get("youtube_link")
    if yt_link:
        thread = threading.Thread(target=run_yolo_on_youtube, args=(yt_link,))
        thread.start()
        return {"status": "started"}
    return {"status": "failed"}



@app.route("/run_yolo", methods=["POST"])
def run_yolo_endpoint():
    data = request.get_json()
    yt_link = data.get("youtube_link")
    if yt_link:
        # Run YOLO in a separate thread so Flask doesn't block
        import threading
        thread = threading.Thread(target=run_yolo_on_youtube, args=(yt_link,))
        thread.start()
        return {"status": "started"}
    return {"status": "failed"}





    
    
    
# -------------------------------------------------
# MODULE ROUTES
# -------------------------------------------------

@app.route("/<area>/road_inspections")
def road_inspections(area):
    if not login_required():
        return redirect(url_for("index"))
    return render_template("road_inspections.html", current_area=area)


@app.route("/<area>/work-orders")
def work_orders(area):
    if not login_required():
        return redirect(url_for("index"))
    return render_template("work_orders.html", current_area=area)


@app.route("/<area>/contractors")
def contractors(area):
    if not login_required():
        return redirect(url_for("index"))
    return render_template("contractors.html", current_area=area)


@app.route("/<area>/budget")
def budget(area):
    if not login_required():
        return redirect(url_for("index"))
    return render_template("budget.html", current_area=area)


@app.route("/<area>/complaints")
def complaints(area):
    if not login_required():
        return redirect(url_for("index"))
    return render_template("complaints.html", current_area=area)


@app.route("/<area>/reports")
def reports(area):
    if not login_required():
        return redirect(url_for("index"))
    return render_template("reports.html", current_area=area)






# -------------------------------------------------
# LOGOUT
# -------------------------------------------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# -------------------------------------------------
# RUN
# -------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)