import sqlite3
import os
import base64
from datetime import datetime
from flask import Flask, request, jsonify, redirect, url_for, flash, render_template, session, send_file
import io
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# --------------------- DATABASE SETUP ---------------------
def create_tables():
    with sqlite3.connect('attendance.db') as conn:
        cursor = conn.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            user_id TEXT NOT NULL UNIQUE,
            email TEXT,
            phone TEXT,
            address TEXT,
            image_path TEXT
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            user_id TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            image_path TEXT,
            late_reason TEXT
        )''')

        conn.commit()

create_tables()

@app.route('/face_capture')
def face_capture():
    return render_template('face_capture.html')


# --------------------- ATTENDANCE LOGIC ---------------------
@app.route('/submit_attendance', methods=['POST'])
def submit_attendance():
    try:
        user_name = request.form.get('user_name')
        user_id = request.form.get('user_id')
        late_reason = request.form.get('late_reason')
        image_data = request.form.get('image_data')
        current_time = datetime.now().time()

        if not user_name or not user_id or not image_data:
            return jsonify({'status': 'error', 'message': 'Required fields are missing.'})

        with sqlite3.connect('attendance.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE LOWER(user_id) = ? AND LOWER(user_name) = ?", (user_id.lower(), user_name.lower()))
            user = cursor.fetchone()

        if not user:
            return jsonify({'status': 'error', 'message': 'User not found or credentials do not match.'})

        try:
            image_filename = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            image_path = os.path.join("static", "attendance_images", image_filename)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            with open(image_path, "wb") as f:
                f.write(base64.b64decode(image_data.split(',')[1]))
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Failed to save image: {str(e)}'})

        allowed_start = datetime.strptime("08:00:00", "%H:%M:%S").time()
        allowed_end = datetime.strptime("08:15:00", "%H:%M:%S").time()

        with sqlite3.connect('attendance.db') as conn:
            cursor = conn.cursor()
            if allowed_start <= current_time <= allowed_end:
                cursor.execute("""
                    INSERT INTO attendance (user_name, user_id, image_path)
                    VALUES (?, ?, ?)
                """, (user[1], user[2], image_path))
                conn.commit()
                return jsonify({'status': 'success', 'message': 'Attendance marked successfully!'}), 200
            else:
                if not late_reason:
                    return jsonify({'status': 'error', 'message': 'Please provide a reason for being late.'}), 400
                cursor.execute("""
                    INSERT INTO attendance (user_name, user_id, image_path, late_reason)
                    VALUES (?, ?, ?, ?)
                """, (user[1], user[2], image_path, late_reason))
                conn.commit()
                return jsonify({'status': 'success', 'message': 'Late attendance marked with reason.'}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Unexpected error occurred: {str(e)}'}), 500


# --------------------- ADD USER ---------------------
@app.route('/add_user', methods=['POST'])
def add_user():
    try:
        if not session.get('admin_logged_in'):
            return redirect(url_for('login'))

        user_name = request.form.get('username')
        user_id = request.form.get('user_id')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        image_file = request.files.get('image')

        if not user_name or not user_id or not email or not phone or not address:
            flash('All fields are required.', 'error')
            return redirect(url_for('admin_page'))

        image_path = ""
        if image_file and image_file.filename != '':
            image_filename = f"{user_id}_{image_file.filename}"
            image_path = os.path.join("static", "user_images", image_filename)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            image_file.save(image_path)

        with sqlite3.connect('attendance.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash('User with this ID already exists.', 'error')
            else:
                cursor.execute("""
                    INSERT INTO users (user_name, user_id, email, phone, address, image_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_name, user_id, email, phone, address, image_path))
                conn.commit()
                flash('User added successfully!', 'success')

    except Exception as e:
        flash(f'Error adding user: {str(e)}', 'error')

    return redirect(url_for('admin_page'))


# --------------------- LOGIN ---------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['admin_logged_in'] = True
        return redirect(url_for('admin_page'))
    return render_template('login.html')


# --------------------- ADMIN PAGE ---------------------
@app.route('/admin')
def admin_page():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    with sqlite3.connect('attendance.db') as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT user_name, user_id, email, phone, address, image_path FROM users")
        users = cursor.fetchall()

        # Include attendance ID here
        cursor.execute("SELECT id, user_id, user_name, timestamp, image_path, late_reason FROM attendance")
        attendance_records = cursor.fetchall()

    return render_template('admin.html', users=users, attendance_records=attendance_records)


# ✅ --------------------- DELETE ATTENDANCE ---------------------
@app.route('/delete_attendance/<int:attendance_id>', methods=['POST'])
def delete_attendance(attendance_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    try:
        with sqlite3.connect('attendance.db') as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM attendance WHERE id = ?", (attendance_id,))
            conn.commit()
            flash("Attendance record deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting record: {str(e)}", "error")

    return redirect(url_for('admin_page'))


# --------------------- DOWNLOAD ---------------------
@app.route('/download_attendance', methods=['GET'])
def download_attendance():
    try:
        with sqlite3.connect('attendance.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, user_name, timestamp, image_path, late_reason FROM attendance")
            attendance_records = cursor.fetchall()

        df = pd.DataFrame(attendance_records, columns=['User ID', 'User Name', 'Timestamp', 'Image Path', 'Late Reason'])

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Attendance Records')
        output.seek(0)

        return send_file(output, as_attachment=True, download_name='attendance_records.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error generating Excel file: {str(e)}'}), 500


# --------------------- Attendance Chart ---------------------
@app.route('/get_attendance_data')
def get_attendance_data():
    with sqlite3.connect('attendance.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_name, COUNT(*) 
            FROM attendance 
            GROUP BY user_id
        """)
        data = cursor.fetchall()

    if not data:
        return jsonify({
            'labels': [],
            'attendance_counts': []
        })

    labels = [row[0] for row in data]
    attendance_counts = [row[1] for row in data]

    return jsonify({
        'labels': labels,
        'attendance_counts': attendance_counts
    })


# --------------------- LOGOUT ---------------------
@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('You have successfully logged out.', 'success')
    return redirect(url_for('login'))

# --------------------- START ---------------------
if __name__ == '__main__':
    app.run(debug=True)
