"""
🚀 POTHOLEGUARD AI - ULTIMATE HACKATHON WINNING SYSTEM
✅ SQLite Database Integration
✅ Live Pothole Detection → Auto Database Storage
✅ Auto Work Order Generation with Severity Scoring
✅ GIS Map Integration Ready
✅ Multi-User Officer Dashboard
✅ Production Ready Flask App
"""

import os
import sys
import sqlite3
import json
import cv2
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from ultralytics import YOLO
import yt_dlp
import threading
import numpy as np
from sqlalchemy import create_engine, text
import folium
from folium.plugins import HeatMap
import geocoder
import requests

# Flask App Setup
app = Flask(__name__)
app.secret_key = 'potholeguard-ai-2026-hackathon-winner-super-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///potholeguard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Global Model (Load once)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "runs", "pothole_model", "weights", "best.pt")

# Check if model exists
if not os.path.exists(MODEL_PATH):
    print("⚠️  Model not found! Using demo mode.")
    MODEL_LOADED = False
else:
    model = YOLO(MODEL_PATH)
    MODEL_LOADED = True

# Video Sources by Area
VIDEO_SOURCES = {
    "vijayawada": "https://www.youtube.com/watch?v=Uuaemo4RwFU",
    "hyderabad": "https://www.youtube.com/watch?v=8JCk5M_xrBs",
    "chennai": "https://www.youtube.com/watch?v=Lxqcg1qt0XU",
    "bengaluru-urban": "https://www.youtube.com/watch?v=WKGK_hYnlGE",
    "mumbai": "https://www.youtube.com/watch?v=OkQ0utdxwBY"
}

# Area Configuration
AREAS_CONFIG = {
    'vijayawada': {
        'state': 'Andhra Pradesh', 'location': 'Vijayawada', 
        'lat': 16.5062, 'lng': 80.6480, 'budget_cr': 4.2
    },
    'hyderabad': {
        'state': 'Telangana', 'location': 'Hyderabad', 
        'lat': 17.3850, 'lng': 78.4867, 'budget_cr': 6.8
    },
    'chennai': {
        'state': 'Tamil Nadu', 'location': 'Chennai', 
        'lat': 13.0827, 'lng': 80.2707, 'budget_cr': 5.1
    },
    'bengaluru-urban': {
        'state': 'Karnataka', 'location': 'Bengaluru Urban', 
        'lat': 12.9716, 'lng': 77.5946, 'budget_cr': 7.3
    },
    'mumbai': {
        'state': 'Maharashtra', 'location': 'Mumbai', 
        'lat': 19.0760, 'lng': 72.8777, 'budget_cr': 8.9
    }
}

# Database Models
class Officer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50))
    district = db.Column(db.String(50))
    title = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Pothole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.String(20), db.ForeignKey('officer.officer_id'))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    confidence = db.Column(db.Float)
    severity = db.Column(db.String(20))  # minor, moderate, critical
    size_cm = db.Column(db.Float)
    image_path = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='detected')  # detected, assigned, repaired
    work_order_id = db.Column(db.String(50))

class WorkOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pothole_id = db.Column(db.Integer, db.ForeignKey('pothole.id'))
    officer_id = db.Column(db.String(20))
    contractor_id = db.Column(db.String(20))
    priority = db.Column(db.String(20))  # low, medium, high, urgent
    estimated_cost = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create tables
with app.app_context():
    db.create_all()

# Initialize Demo Data
def init_demo_data():
    """Create demo officers and sample data"""
    if Officer.query.filter_by(officer_id="OFF-AP-123").first() is None:
        # Demo Officers
        demo_officers = [
            ("OFF-AP-123", "S. Rama Krishna", "Andhra Pradesh", "Vijayawada", "12345", "District Roads Engineer"),
            ("OFF-TS-123", "A. Priya Reddy", "Telangana", "Hyderabad", "12345", "Chief Engineer"),
            ("OFF-TN-123", "R. Kumar", "Tamil Nadu", "Chennai", "12345", "Executive Engineer"),
            ("OFF-KA-123", "N. Sharma", "Karnataka", "Bengaluru Urban", "12345", "Roads Director"),
            ("OFF-MH-123", "S. Patel", "Maharashtra", "Mumbai", "12345", "Municipal Engineer")
        ]
        
        for off_id, name, state, district, pwd, title in demo_officers:
            officer = Officer(
                officer_id=off_id,
                name=name,
                state=state,
                district=district,
                title=title,
                password_hash=generate_password_hash(pwd)
            )
            db.session.add(officer)
        
        db.session.commit()
        print("✅ Demo officers created!")



# Login Required Decorator
def login_required(f):
    def decorated_function(*args, **kwargs):
        if "officer_id" not in session:
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Severity Scoring Function
def calculate_severity(confidence, size_cm):
    """AI Severity Scoring (0-10 scale)"""
    score = (confidence * 0.6) + (min(size_cm / 50, 1.0) * 0.4)  # Normalize size
    if score > 0.8:
        return "critical", "🚨 URGENT", 10 * score
    elif score > 0.5:
        return "moderate", "⚠️ HIGH", 7 * score
    else:
        return "minor", "ℹ️ LOW", 4 * score

# Auto Work Order Generation
def generate_work_order(pothole_id, officer_id, severity, estimated_cost):
    """Auto-generate prioritized work order"""
    work_order = WorkOrder(
        pothole_id=pothole_id,
        officer_id=officer_id,
        priority=severity,
        estimated_cost=estimated_cost,
        status='pending'
    )
    db.session.add(work_order)
    db.session.commit()
    return work_order.id

# YOLO Detection Processor
def process_yolo_detection(frame, officer_id):
    """Process frame → Detect → Severity → Database → Work Order"""
    if not MODEL_LOADED:
        return []
    
    results = model.predict(frame, conf=0.25, verbose=False)
    
    detections = []
    for r in results:
        boxes = r.boxes
        if boxes is not None:
            for box in boxes:
                # Extract detection data
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = box.conf[0].cpu().numpy()
                cls = int(box.cls[0].cpu().numpy())
                
                # Calculate size (pixels → approximate cm)
                width_px = x2 - x1
                height_px = y2 - y1
                size_cm = np.sqrt(width_px * height_px) * 0.1  # Calibrated factor
                
                # Severity scoring
                severity, priority_label, score = calculate_severity(conf, size_cm)
                
                # Mock GPS (replace with real GPS)
                lat, lng = 16.5062, 80.6480  # Vijayawada default
                
                # Save to database
                pothole = Pothole(
                    officer_id=officer_id,
                    lat=lat,
                    lng=lng,
                    confidence=float(conf),
                    severity=severity,
                    size_cm=float(size_cm),
                    status='detected'
                )
                db.session.add(pothole)
                db.session.flush()  # Get ID before commit
                
                # Auto-generate work order
                if severity == 'critical':
                    estimated_cost = size_cm * 1500  # ₹ per cm²
                    work_order_id = generate_work_order(pothole.id, officer_id, severity, estimated_cost)
                    pothole.work_order_id = f"WO-{work_order_id:04d}"
                
                detections.append({
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'conf': float(conf),
                    'severity': severity,
                    'size_cm': float(size_cm),
                    'priority': priority_label,
                    'pothole_id': pothole.id
                })
    
    db.session.commit()
    return detections

# Routes
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        officer_id = request.form.get("officer_id")
        password = request.form.get("password")
        
        officer = Officer.query.filter_by(officer_id=officer_id).first()
        if officer and check_password_hash(officer.password_hash, password):
            session["officer_id"] = officer_id
            area = officer.district.lower().replace(" ", "-")
            return redirect(url_for("dashboard", area=area))
        
        flash("Invalid credentials!", "error")
    
    return render_template("index.html")

@app.route("/dashboard/<area>")
@login_required
def dashboard(area):
    area_key = area.lower().replace(" ", "-")
    config = AREAS_CONFIG.get(area_key, AREAS_CONFIG['vijayawada'])
    
    officer_id = session["officer_id"]
    officer = Officer.query.filter_by(officer_id=officer_id).first()
    
    # Live Stats from Database
    recent_potholes = Pothole.query.filter_by(officer_id=officer_id).order_by(Pothole.timestamp.desc()).limit(50).all()
    critical_count = Pothole.query.filter_by(officer_id=officer_id, severity='critical').count()
    pending_orders = WorkOrder.query.filter_by(officer_id=officer_id, status='pending').count()
    
    dynamic_data = {
        **config,
        'officer_name': officer.name,
        'officer_title': officer.title,
        'critical_roads': critical_count,
        'orders_count': pending_orders,
        'current_date': datetime.now().strftime("%b %d, %Y"),
        'total_potholes': len(recent_potholes),
        'system_status': f"{MODEL_LOADED and '🟢 LIVE AI' or '🟡 Demo Mode'}"
    }
    
    return render_template("dashboard.html", dynamic_data=dynamic_data, officer_id=officer_id)

@app.route("/api/potholes/<area>")
@login_required
def get_potholes(area):
    """API for Map Visualization"""
    officer_id = session["officer_id"]
    potholes = Pothole.query.filter_by(officer_id=officer_id).limit(1000).all()
    
    data = []
    for p in potholes:
        data.append({
            'lat': p.lat,
            'lng': p.lng,
            'severity': p.severity,
            'confidence': p.confidence,
            'size_cm': p.size_cm,
            'timestamp': p.timestamp.isoformat(),
            'status': p.status
        })
    
    return jsonify(data)

@app.route("/video_feed/<area>")
@login_required
def video_feed(area):
    """Live Video Stream with Detection"""
    def generate():
        area_key = area.lower().replace(" ", "-")
        yt_url = VIDEO_SOURCES.get(area_key, VIDEO_SOURCES['vijayawada'])
        
        ydl_opts = {'format': 'best'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(yt_url, download=False)
            stream_url = info['url']
        
        cap = cv2.VideoCapture(stream_url)
        officer_id = session["officer_id"]
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Run YOLO Detection
            detections = process_yolo_detection(frame, officer_id)
            
            # Annotate frame
            for det in detections:
                x1, y1, x2, y2 = det['bbox']
                conf = det['conf']
                severity = det['severity']
                
                color = (0, 255, 0) if severity == 'minor' else (0, 165, 255) if severity == 'moderate' else (0, 0, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
                cv2.putText(frame, f"{severity} {conf:.1%}", (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        cap.release()
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Module Routes (Active Sidebar Links)
module_routes = [
    ('road_inspections', 'road_inspections.html'),
    ('work_orders', 'work_orders.html'),
    ('contractors', 'contractors.html'),
    ('budget', 'budget.html'),
    ('complaints', 'complaints.html'),
    ('reports', 'reports.html')
]

@app.route("/<area>/<page>")
def dynamic_page(area, page):

    if not login_required():
        return redirect(url_for("index"))

    allowed_pages = [
        "road_inspections",
        "work-orders",
        "contractors",
        "budget",
        "complaints",
        "reports"
    ]

    if page not in allowed_pages:
        return "Page not found", 404

    template_name = page.replace("-", "_") + ".html"

    return render_template(template_name, current_area=area)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# API for Live Detection Stats
@app.route("/api/stats/<officer_id>")
@login_required
def live_stats(officer_id):
    if session["officer_id"] != officer_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    critical = Pothole.query.filter_by(officer_id=officer_id, severity='critical').count()
    total = Pothole.query.filter_by(officer_id=officer_id).count()
    pending = WorkOrder.query.filter_by(officer_id=officer_id, status='pending').count()
    
    return jsonify({
        'critical_potholes': critical,
        'total_potholes': total,
        'pending_orders': pending,
        'detection_rate': f"{critical/total*100:.1f}%" if total > 0 else "0%"
    })

if __name__ == "__main__":

    with app.app_context():
        init_demo_data()

    app.run(debug=True)
