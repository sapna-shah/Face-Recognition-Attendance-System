# 🧠 Face Recognition Attendance System

A smart attendance management system powered by face recognition. This project automates attendance marking through facial verification using a webcam, and provides powerful admin tools like reporting, alerts, and visual insights.

---

## 📸 Overview

This Face Recognition Attendance System uses Python, OpenCV, and Flask to:
- Detect and recognize faces using a webcam
- Mark attendance with date and time
- Restrict attendance to specific users and times
- Alert stakeholders for low attendance
- Export data and generate charts

---

## 🚀 Features

✅ **User Authentication via Face Recognition**  
✅ **Time-based Attendance Restriction** (e.g. 8:00–8:15 AM)  
✅ **Late Entry Detection + Reason Collection**  
✅ **Admin Dashboard**  
✅ **Attendance History (User & Admin Views)**  
✅ **Live Image Preview on Attendance Logs**  
✅ **Export to Excel and PDF**  
✅ **Attendance Visualization via Charts**  
✅ **Low Attendance Alert System (below 75%)**  
✅ **Monthly Reports to Parents via Email (Planned)**

---

## 🛠 Tech Stack

| Frontend    | Backend    | Database | Others           |
|-------------|------------|----------|------------------|
| HTML, CSS, JS, Bootstrap | Flask (Python) | SQLite   | OpenCV, Pandas, FPDF, Matplotlib |

---

## 🗂️ Folder Structure
/templates → HTML templates
/static → CSS, JS, and images
/static/images → Stored face images
/app.py → Main Flask app
/attendance.db → SQLite database


---

## 🖥️ How to Run

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/your-repo-name.git
   cd your-repo-name

Install the dependencies
pip install -r requirements.txt

Run the application
python app.py

Visit
http://localhost:5000



