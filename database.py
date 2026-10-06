import sqlite3
import os
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'attendance.db')

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Create attendees table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identifier TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            email TEXT,
            days_allocated TEXT DEFAULT '',
            time_allocated TEXT DEFAULT '',
            monthly_target INTEGER DEFAULT 8,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create attendance table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attendee_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Present', 'Absent', 'Late', 'Excused', 'Compensation')),
            remark TEXT DEFAULT '',
            is_compensation INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (attendee_id) REFERENCES attendees(id) ON DELETE CASCADE,
            UNIQUE(attendee_id, date)
        )
    """)

    # Schema migration checks for existing databases
    cursor.execute("PRAGMA table_info(attendees)")
    columns = [col['name'] for col in cursor.fetchall()]
    if 'days_allocated' not in columns:
        cursor.execute("ALTER TABLE attendees ADD COLUMN days_allocated TEXT DEFAULT ''")
    if 'time_allocated' not in columns:
        cursor.execute("ALTER TABLE attendees ADD COLUMN time_allocated TEXT DEFAULT ''")
    if 'monthly_target' not in columns:
        cursor.execute("ALTER TABLE attendees ADD COLUMN monthly_target INTEGER DEFAULT 8")

    cursor.execute("PRAGMA table_info(attendance)")
    att_columns = [col['name'] for col in cursor.fetchall()]
    if 'is_compensation' not in att_columns:
        cursor.execute("ALTER TABLE attendance ADD COLUMN is_compensation INTEGER DEFAULT 0")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_attendee ON attendance(attendee_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendees_department ON attendees(department)")
    conn.commit()
    conn.close()

def get_attendees(active_only=False, department=None, search=None):
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT * FROM attendees WHERE 1=1"
    params = []

    if active_only:
        query += " AND active = 1"
    if department:
        query += " AND department = ?"
        params.append(department)
    if search:
        query += " AND (name LIKE ? OR identifier LIKE ? OR email LIKE ? OR days_allocated LIKE ? OR time_allocated LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term, term])

    query += " ORDER BY department ASC, name ASC"
    cursor.execute(query, params)
    attendees = cursor.fetchall()
    conn.close()
    return attendees

def get_attendee_by_id(attendee_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attendees WHERE id = ?", (attendee_id,))
    attendee = cursor.fetchone()
    conn.close()
    return attendee

def add_attendee(identifier, name, department, email=None, days_allocated='', time_allocated='', monthly_target=8):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO attendees 
               (identifier, name, department, email, days_allocated, time_allocated, monthly_target) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                identifier.strip(),
                name.strip(),
                department.strip(),
                email.strip() if email else '',
                days_allocated.strip() if days_allocated else '',
                time_allocated.strip() if time_allocated else '',
                int(monthly_target) if monthly_target else 8
            )
        )
        conn.commit()
        attendee_id = cursor.lastrowid
        return attendee_id, None
    except sqlite3.IntegrityError:
        return None, f"An attendee with Reg No / ID '{identifier}' already exists."
    finally:
        conn.close()

def update_attendee(attendee_id, identifier, name, department, email=None, days_allocated='', time_allocated='', monthly_target=8, active=1):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """UPDATE attendees 
               SET identifier = ?, name = ?, department = ?, email = ?, 
                   days_allocated = ?, time_allocated = ?, monthly_target = ?, active = ?
               WHERE id = ?""",
            (
                identifier.strip(),
                name.strip(),
                department.strip(),
                email.strip() if email else '',
                days_allocated.strip() if days_allocated else '',
                time_allocated.strip() if time_allocated else '',
                int(monthly_target) if monthly_target else 8,
                active,
                attendee_id
            )
        )
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, f"Reg No / ID '{identifier}' is already taken by another attendee."
    finally:
        conn.close()

def delete_attendee(attendee_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM attendees WHERE id = ?", (attendee_id,))
    conn.commit()
    conn.close()

def get_departments():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT department FROM attendees WHERE department != '' ORDER BY department ASC")
    rows = cursor.fetchall()
    conn.close()
    return [r['department'] for r in rows]

def get_attendance_sheet(date_str, department=None):
    """
    Returns all active attendees along with their attendance status for date_str.
    """
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT a.id, a.identifier, a.name, a.department, a.email,
               a.days_allocated, a.time_allocated, a.monthly_target,
               att.status, att.remark, att.is_compensation, att.updated_at
        FROM attendees a
        LEFT JOIN attendance att ON a.id = att.attendee_id AND att.date = ?
        WHERE a.active = 1
    """
    params = [date_str]
    if department:
        query += " AND a.department = ?"
        params.append(department)
    query += " ORDER BY a.department ASC, a.name ASC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def save_attendance_batch(date_str, records):
    """
    records is a list of dicts: [{'attendee_id': int, 'status': str, 'remark': str, 'is_compensation': int}]
    """
    conn = get_db()
    cursor = conn.cursor()
    for rec in records:
        attendee_id = rec['attendee_id']
        status = rec['status']
        remark = rec.get('remark', '')
        is_comp = 1 if (rec.get('is_compensation') or status == 'Compensation') else 0

        if not status:
            cursor.execute("DELETE FROM attendance WHERE attendee_id = ? AND date = ?", (attendee_id, date_str))
        else:
            cursor.execute("""
                INSERT INTO attendance (attendee_id, date, status, remark, is_compensation, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(attendee_id, date) DO UPDATE SET
                    status = excluded.status,
                    remark = excluded.remark,
                    is_compensation = excluded.is_compensation,
                    updated_at = CURRENT_TIMESTAMP
            """, (attendee_id, date_str, status, remark, is_comp))
    conn.commit()
    conn.close()

def log_compensation_class(attendee_id, date_str, remark=''):
    """
    Directly logs a compensation class for an attendee for a given date.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO attendance (attendee_id, date, status, remark, is_compensation, updated_at)
        VALUES (?, ?, 'Compensation', ?, 1, CURRENT_TIMESTAMP)
        ON CONFLICT(attendee_id, date) DO UPDATE SET
            status = 'Compensation',
            remark = excluded.remark,
            is_compensation = 1,
            updated_at = CURRENT_TIMESTAMP
    """, (attendee_id, date_str, remark or 'Compensation Class attended'))
    conn.commit()
    conn.close()

def get_monthly_student_summary(year_month, department=None):
    """
    year_month string in format 'YYYY-MM' (e.g. '2026-10')
    Calculates per student:
      - monthly_target (default 8)
      - regular_attended (Present / Late, is_compensation = 0)
      - missed_classes (Absent, is_compensation = 0)
      - compensation_attended (is_compensation = 1 or status = 'Compensation')
      - total_attended = regular_attended + compensation_attended
      - compensation_eligible: (missed_classes >= 1 and compensation_attended == 0)
      - compensation_status: 'Eligible (1 Available)' | 'Used (1/1 Claimed)' | 'Not Needed'
    """
    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT a.id, a.identifier, a.name, a.department, a.days_allocated, a.time_allocated,
               COALESCE(a.monthly_target, 8) AS monthly_target,
               SUM(CASE WHEN att.status IN ('Present', 'Late') AND att.is_compensation = 0 THEN 1 ELSE 0 END) AS regular_attended,
               SUM(CASE WHEN att.status = 'Absent' AND att.is_compensation = 0 THEN 1 ELSE 0 END) AS missed_classes,
               SUM(CASE WHEN att.is_compensation = 1 OR att.status = 'Compensation' THEN 1 ELSE 0 END) AS compensation_attended
        FROM attendees a
        LEFT JOIN attendance att ON a.id = att.attendee_id AND strftime('%Y-%m', att.date) = ?
        WHERE a.active = 1
    """
    params = [year_month]

    if department:
        query += " AND a.department = ?"
        params.append(department)

    query += " GROUP BY a.id ORDER BY a.department ASC, a.name ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    total_eligible_count = 0
    total_comp_claimed_count = 0
    total_target_met_count = 0

    for r in rows:
        target = r['monthly_target'] or 8
        reg_att = r['regular_attended'] or 0
        missed = r['missed_classes'] or 0
        comp_att = r['compensation_attended'] or 0
        total_att = reg_att + comp_att

        # Max 1 compensation class allowed per month
        if comp_att > 0:
            comp_status = "Used (1/1 Claimed)"
            comp_eligible = False
            total_comp_claimed_count += 1
        elif missed > 0:
            comp_status = "Eligible (1 Available)"
            comp_eligible = True
            total_eligible_count += 1
        else:
            comp_status = "Not Needed (0 Missed)"
            comp_eligible = False

        if total_att >= target:
            total_target_met_count += 1

        pct = min(100, round((total_att / target * 100), 1)) if target > 0 else 0.0

        results.append({
            'id': r['id'],
            'identifier': r['identifier'],
            'name': r['name'],
            'department': r['department'],
            'days_allocated': r['days_allocated'] or 'Flexible',
            'time_allocated': r['time_allocated'] or 'Flexible',
            'monthly_target': target,
            'regular_attended': reg_att,
            'missed_classes': missed,
            'compensation_attended': comp_att,
            'total_attended': total_att,
            'completion_pct': pct,
            'compensation_status': comp_status,
            'can_claim_compensation': comp_eligible
        })

    conn.close()
    return {
        'students': results,
        'year_month': year_month,
        'total_students': len(results),
        'total_target_met': total_target_met_count,
        'total_eligible_for_comp': total_eligible_count,
        'total_comp_claimed': total_comp_claimed_count
    }

def get_dashboard_data(target_date):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS total FROM attendees WHERE active = 1")
    total_active = cursor.fetchone()['total']

    cursor.execute("""
        SELECT 
            SUM(CASE WHEN att.status = 'Present' THEN 1 ELSE 0 END) AS present_count,
            SUM(CASE WHEN att.status = 'Absent' THEN 1 ELSE 0 END) AS absent_count,
            SUM(CASE WHEN att.status = 'Late' THEN 1 ELSE 0 END) AS late_count,
            SUM(CASE WHEN att.status = 'Excused' THEN 1 ELSE 0 END) AS excused_count,
            SUM(CASE WHEN att.status = 'Compensation' OR att.is_compensation = 1 THEN 1 ELSE 0 END) AS comp_count,
            COUNT(att.id) AS marked_count
        FROM attendees a
        JOIN attendance att ON a.id = att.attendee_id
        WHERE a.active = 1 AND att.date = ?
    """, (target_date,))
    row = cursor.fetchone()

    present_count = row['present_count'] or 0
    absent_count = row['absent_count'] or 0
    late_count = row['late_count'] or 0
    excused_count = row['excused_count'] or 0
    comp_count = row['comp_count'] or 0
    marked_count = row['marked_count'] or 0
    unmarked_count = max(0, total_active - marked_count)

    attended_total = present_count + late_count + comp_count
    attendance_rate = round((attended_total / marked_count * 100), 1) if marked_count > 0 else 0.0

    # Trend for last 7 dates
    cursor.execute("""
        SELECT date, 
               SUM(CASE WHEN status IN ('Present', 'Late', 'Compensation') THEN 1 ELSE 0 END) AS present_count,
               SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) AS absent_count,
               COUNT(*) AS total_marked
        FROM attendance
        GROUP BY date
        ORDER BY date DESC
        LIMIT 7
    """)
    trend_rows = cursor.fetchall()
    trend_rows.reverse()

    trend_labels = [r['date'] for r in trend_rows]
    trend_rates = [
        round((r['present_count'] / r['total_marked'] * 100), 1) if r['total_marked'] > 0 else 0
        for r in trend_rows
    ]
    trend_present = [r['present_count'] for r in trend_rows]
    trend_absent = [r['absent_count'] for r in trend_rows]

    conn.close()
    return {
        'total_active': total_active,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'excused_count': excused_count,
        'comp_count': comp_count,
        'unmarked_count': unmarked_count,
        'marked_count': marked_count,
        'attendance_rate': attendance_rate,
        'trend_labels': trend_labels,
        'trend_rates': trend_rates,
        'trend_present': trend_present,
        'trend_absent': trend_absent
    }

def get_detailed_report(start_date=None, end_date=None, department=None, attendee_id=None, status=None):
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT att.id, att.date, att.status, att.remark, att.is_compensation,
               a.identifier, a.name, a.department, a.email, a.days_allocated, a.time_allocated
        FROM attendance att
        JOIN attendees a ON att.attendee_id = a.id
        WHERE 1=1
    """
    params = []
    if start_date:
        query += " AND att.date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND att.date <= ?"
        params.append(end_date)
    if department:
        query += " AND a.department = ?"
        params.append(department)
    if attendee_id:
        query += " AND a.id = ?"
        params.append(attendee_id)
    if status:
        if status == 'Compensation':
            query += " AND (att.status = 'Compensation' OR att.is_compensation = 1)"
        else:
            query += " AND att.status = ?"
            params.append(status)

    query += " ORDER BY att.date DESC, a.department ASC, a.name ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_attendee_statistics(start_date=None, end_date=None, department=None):
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT a.id, a.identifier, a.name, a.department, a.days_allocated, a.time_allocated,
               COUNT(att.id) AS total_records,
               SUM(CASE WHEN att.status = 'Present' THEN 1 ELSE 0 END) AS present_count,
               SUM(CASE WHEN att.status = 'Late' THEN 1 ELSE 0 END) AS late_count,
               SUM(CASE WHEN att.status = 'Absent' THEN 1 ELSE 0 END) AS absent_count,
               SUM(CASE WHEN att.status = 'Excused' THEN 1 ELSE 0 END) AS excused_count,
               SUM(CASE WHEN att.status = 'Compensation' OR att.is_compensation = 1 THEN 1 ELSE 0 END) AS comp_count
        FROM attendees a
        LEFT JOIN attendance att ON a.id = att.attendee_id
    """
    where_clauses = ["a.active = 1"]
    params = []

    if start_date:
        where_clauses.append("(att.date >= ? OR att.date IS NULL)")
        params.append(start_date)
    if end_date:
        where_clauses.append("(att.date <= ? OR att.date IS NULL)")
        params.append(end_date)
    if department:
        where_clauses.append("a.department = ?")
        params.append(department)

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " GROUP BY a.id ORDER BY a.department ASC, a.name ASC"

    cursor.execute(query, params)
    stats = []
    for r in cursor.fetchall():
        total = r['total_records']
        pres = r['present_count'] or 0
        late = r['late_count'] or 0
        absent = r['absent_count'] or 0
        excused = r['excused_count'] or 0
        comp = r['comp_count'] or 0
        attended = pres + late + comp
        rate = round((attended / total * 100), 1) if total > 0 else 0.0
        stats.append({
            'id': r['id'],
            'identifier': r['identifier'],
            'name': r['name'],
            'department': r['department'],
            'days_allocated': r['days_allocated'] or 'Flexible',
            'time_allocated': r['time_allocated'] or 'Flexible',
            'total_records': total,
            'present_count': pres,
            'late_count': late,
            'absent_count': absent,
            'excused_count': excused,
            'comp_count': comp,
            'rate': rate
        })
    conn.close()
    return stats
