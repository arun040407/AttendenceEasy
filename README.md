# AttendEasy - Attendance & Compensation Tracking System

A specialized attendance tracking application designed for batch and schedule-based courses, featuring **allocated schedules**, **monthly 8-class quotas**, and **1-compensation-class-per-month** rules.

---

## 🌟 Key Features

### 1. Student Profile & Schedule Allocation
- **Reg No / ID**: Unique student registration identifier.
- **Student Name**: Full name.
- **Days Allocated**: Scheduled days of the week (e.g. `Monday, Wednesday`, `Tuesday, Thursday`).
- **Time Allocated**: Scheduled time slot (e.g. `10:00 AM - 11:00 AM`, `04:00 PM - 05:00 PM`).
- **Monthly Quota**: Set to **8 classes per month** per student.

### 2. Monthly Quota & Compensation Class Rule
- **Standard Quota**: 8 classes per month.
- **Missed Session Trigger**: Whenever a student misses a regular class (`Absent`), the system automatically flags them as **Eligible for 1 Compensation Make-up Class** for that calendar month.
- **1-Per-Month Limit**: Maximum 1 compensation class can be claimed per month per student.
- **Total Progress**: $\text{Total Attended} = \text{Regular Attended} + \text{Compensation Class}$ (out of 8).
- **Dedicated Tracker (`/monthly`)**:
  - Displays monthly quota progress bar ($X / 8$) for every student.
  - Shows missed classes count.
  - Displays compensation status: `Eligible (1 Available)`, `Used (1/1 Claimed)`, or `0 Missed`.
  - One-click **"Log Make-up Class"** button to directly record a compensation session.

### 3. Daily Attendance Marking (`/attendance`)
- Status pills: **Present**, **Absent**, **Late**, **Compensation**, and **Excused**.
- One-click bulk operations: **Mark All Present**, **Mark All Absent**, or **Clear**.
- Real-time counters showing live counts of marked and unmarked students.
- Schedule badges displaying each student's scheduled days and time.
- Optional remarks for every session.

### 4. Roster Management (`/attendees`)
- Add/edit students with Reg No, Name, Days Allocated, Time Allocated, Batch, and Monthly Target.
- Deactivate or delete students with cascading record cleanup.

### 5. Reports & CSV Export (`/reports`)
- Date range, batch/department, and status filters.
- Overall performance breakdown with attendance rate %.
- One-click **Export to CSV** containing full schedule details (`Days Allocated`, `Time Allocated`, and `Is Compensation Class` flag).

---

## 🚀 How to Run

### Method 1: Double-click Launcher (Windows)
Double-click **`run.bat`** in this folder. It will start the server and automatically open your default browser.

### Method 2: Command Line
```powershell
python app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your web browser.

---

## 📁 Project Structure

```text
├── app.py              # Main Flask server and routes (dashboard, monthly, attendance, roster, reports)
├── database.py         # SQLite database schema, schedule columns & compensation queries
├── seed_data.py        # Demo sample batches & attendance history
├── run.bat             # One-click Windows launch script
├── requirements.txt    # Python dependencies (flask)
├── test_app.py         # Automated test suite
├── static/
│   ├── style.css       # Clean, modern custom stylesheet
│   └── app.js          # Client-side logic (compensation buttons, live counters, search, modals)
├── templates/
│   ├── base.html       # Top navigation & shared layout
│   ├── dashboard.html  # Analytics dashboard & monthly highlights
│   ├── monthly.html    # Monthly 8-class quota & compensation tracker
│   ├── attendance.html # Daily attendance entry matrix with schedule badges
│   ├── attendees.html  # Student roster management with schedule fields
│   └── reports.html    # Filterable logs, statistics, and CSV export
└── attendance.db       # SQLite local database
```
