import datetime
import random
from database import init_db, add_attendee, save_attendance_batch, get_attendees, get_db

SAMPLE_ATTENDEES = [
    # Mon, Wed batch
    ("REG-101", "Aarav Sharma", "Batch Mon-Wed", "aarav@example.com", "Monday, Wednesday", "10:00 AM - 11:00 AM", 8),
    ("REG-102", "Priya Patel", "Batch Mon-Wed", "priya@example.com", "Monday, Wednesday", "10:00 AM - 11:00 AM", 8),
    ("REG-103", "Rohan Mehta", "Batch Mon-Wed", "rohan@example.com", "Monday, Wednesday", "11:30 AM - 12:30 PM", 8),
    ("REG-104", "Ananya Verma", "Batch Mon-Wed", "ananya@example.com", "Monday, Wednesday", "04:00 PM - 05:00 PM", 8),
    ("REG-105", "Vikram Singh", "Batch Mon-Wed", "vikram@example.com", "Monday, Wednesday", "05:30 PM - 06:30 PM", 8),

    # Tue, Thu batch
    ("REG-201", "Neha Gupta", "Batch Tue-Thu", "neha@example.com", "Tuesday, Thursday", "10:00 AM - 11:00 AM", 8),
    ("REG-202", "Kabir Nair", "Batch Tue-Thu", "kabir@example.com", "Tuesday, Thursday", "10:00 AM - 11:00 AM", 8),
    ("REG-203", "Sanya Kapoor", "Batch Tue-Thu", "sanya@example.com", "Tuesday, Thursday", "04:00 PM - 05:00 PM", 8),
    ("REG-204", "Rahul Joshi", "Batch Tue-Thu", "rahul@example.com", "Tuesday, Thursday", "05:30 PM - 06:30 PM", 8),
    ("REG-205", "Ishita Roy", "Batch Tue-Thu", "ishita@example.com", "Tuesday, Thursday", "05:30 PM - 06:30 PM", 8),

    # Fri, Sat batch
    ("REG-301", "Aditya Iyer", "Batch Fri-Sat", "aditya@example.com", "Friday, Saturday", "11:00 AM - 12:00 PM", 8),
    ("REG-302", "Diya Mukherjee", "Batch Fri-Sat", "diya@example.com", "Friday, Saturday", "11:00 AM - 12:00 PM", 8),
    ("REG-303", "Arjun Reddy", "Batch Fri-Sat", "arjun@example.com", "Friday, Saturday", "03:00 PM - 04:00 PM", 8),
    ("REG-304", "Tanvi Deshmukh", "Batch Fri-Sat", "tanvi@example.com", "Friday, Saturday", "04:30 PM - 05:30 PM", 8),
    ("REG-305", "Manish Choudhary", "Batch Fri-Sat", "manish@example.com", "Friday, Saturday", "06:00 PM - 07:00 PM", 8),
]

def reseed():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS attendance")
    cursor.execute("DROP TABLE IF EXISTS attendees")
    conn.commit()
    conn.close()

    init_db()

    print("Populating student roster with allocated days and times...")
    for reg, name, dept, email, days, times, target in SAMPLE_ATTENDEES:
        add_attendee(reg, name, dept, email, days, times, target)

    attendees = get_attendees(active_only=True)
    today = datetime.date.today()
    random.seed(42)

    print("Generating monthly attendance history with missed and compensation classes...")
    for offset in [14, 12, 9, 7, 5, 2, 0]:
        rec_date = (today - datetime.timedelta(days=offset)).strftime('%Y-%m-%d')
        records = []
        for att in attendees:
            rand = random.random()
            if rand < 0.72:
                status = "Present"
                remark = ""
                is_comp = 0
            elif rand < 0.86:
                status = "Absent"
                remark = "Missed regular class"
                is_comp = 0
            elif rand < 0.93:
                status = "Late"
                remark = "Late by 10 mins"
                is_comp = 0
            else:
                status = "Compensation"
                remark = "Compensation class attended"
                is_comp = 1

            records.append({
                'attendee_id': att['id'],
                'status': status,
                'remark': remark,
                'is_compensation': is_comp
            })
        save_attendance_batch(rec_date, records)

    print("Reseed complete! Sample attendees and monthly history successfully created.")

if __name__ == '__main__':
    reseed()
