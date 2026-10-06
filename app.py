import csv
import datetime
import io
import threading
import webbrowser
from flask import Flask, render_template, request, redirect, url_for, flash, Response
from database import (
    init_db,
    get_attendees,
    get_departments,
    add_attendee,
    update_attendee,
    delete_attendee,
    get_attendance_sheet,
    save_attendance_batch,
    get_dashboard_data,
    get_detailed_report,
    get_attendee_statistics,
    get_monthly_student_summary,
    log_compensation_class
)

app = Flask(__name__)
app.secret_key = 'attendeasy-secret-key-local-app-2026'

@app.route('/')
def dashboard():
    date_str = request.args.get('date')
    if not date_str:
        date_str = datetime.date.today().strftime('%Y-%m-%d')

    stats = get_dashboard_data(date_str)
    
    try:
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
    except Exception:
        formatted_date = date_str

    current_month = datetime.date.today().strftime('%Y-%m')
    monthly_stats = get_monthly_student_summary(current_month)

    return render_template(
        'dashboard.html',
        stats=stats,
        selected_date=date_str,
        selected_date_formatted=formatted_date,
        monthly_stats=monthly_stats,
        current_month=current_month
    )

@app.route('/monthly')
def monthly_tracker():
    month_str = request.args.get('month')
    if not month_str:
        month_str = datetime.date.today().strftime('%Y-%m')
    dept = request.args.get('dept', '')

    summary = get_monthly_student_summary(month_str, department=dept if dept else None)
    departments = get_departments()
    today_date = datetime.date.today().strftime('%Y-%m-%d')

    return render_template(
        'monthly.html',
        summary=summary,
        selected_month=month_str,
        selected_dept=dept,
        departments=departments,
        today_date=today_date
    )

@app.route('/monthly/claim_compensation', methods=['POST'])
def claim_compensation_route():
    try:
        student_id = int(request.form.get('student_id'))
    except (TypeError, ValueError):
        flash('Invalid student selected.', 'error')
        return redirect(url_for('monthly_tracker'))

    date_str = request.form.get('date', '').strip()
    remark = request.form.get('remark', '').strip()
    month = request.form.get('month', datetime.date.today().strftime('%Y-%m'))

    if not date_str:
        date_str = datetime.date.today().strftime('%Y-%m-%d')

    log_compensation_class(student_id, date_str, remark)
    flash(f'Compensation class for student successfully recorded on {date_str}!', 'success')
    return redirect(url_for('monthly_tracker', month=month))

@app.route('/attendance')
def mark_attendance():
    date_str = request.args.get('date')
    if not date_str:
        date_str = datetime.date.today().strftime('%Y-%m-%d')
    dept = request.args.get('dept', '')

    try:
        curr_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        prev_date = (curr_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        next_date = (curr_date + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    except Exception:
        curr_date = datetime.date.today()
        prev_date = (curr_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        next_date = (curr_date + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        date_str = curr_date.strftime('%Y-%m-%d')

    today_date = datetime.date.today().strftime('%Y-%m-%d')
    sheet = get_attendance_sheet(date_str, department=dept if dept else None)
    departments = get_departments()

    return render_template(
        'attendance.html',
        sheet=sheet,
        selected_date=date_str,
        selected_dept=dept,
        prev_date=prev_date,
        next_date=next_date,
        today_date=today_date,
        departments=departments
    )

@app.route('/attendance/save', methods=['POST'])
def save_attendance():
    date_str = request.form.get('date')
    if not date_str:
        flash('Invalid date provided.', 'error')
        return redirect(url_for('mark_attendance'))

    records = []
    for key, value in request.form.items():
        if key.startswith('status_'):
            try:
                attendee_id = int(key.replace('status_', ''))
                status = value.strip()
                remark = request.form.get(f'remark_{attendee_id}', '').strip()
                is_comp = 1 if status == 'Compensation' else 0
                records.append({
                    'attendee_id': attendee_id,
                    'status': status,
                    'remark': remark,
                    'is_compensation': is_comp
                })
            except ValueError:
                continue

    save_attendance_batch(date_str, records)
    flash(f'Attendance for {date_str} successfully recorded ({len(records)} entries updated)!', 'success')
    return redirect(url_for('mark_attendance', date=date_str))

@app.route('/attendees')
def manage_attendees():
    attendees = get_attendees(active_only=False)
    departments = get_departments()
    return render_template('attendees.html', attendees=attendees, departments=departments)

@app.route('/attendees/add', methods=['POST'])
def add_attendee_route():
    identifier = request.form.get('identifier', '').strip()
    name = request.form.get('name', '').strip()
    department = request.form.get('department', '').strip()
    email = request.form.get('email', '').strip()
    days_allocated = request.form.get('days_allocated', '').strip()
    time_allocated = request.form.get('time_allocated', '').strip()
    monthly_target = request.form.get('monthly_target', 8)

    if not identifier or not name or not department:
        flash('Reg No, Name, and Batch/Department are required fields.', 'error')
        return redirect(url_for('manage_attendees'))

    attendee_id, err = add_attendee(
        identifier, name, department, email,
        days_allocated=days_allocated,
        time_allocated=time_allocated,
        monthly_target=monthly_target
    )
    if err:
        flash(err, 'error')
    else:
        flash(f'Successfully added student "{name}" ({identifier}).', 'success')

    return redirect(url_for('manage_attendees'))

@app.route('/attendees/edit', methods=['POST'])
def edit_attendee_route():
    try:
        attendee_id = int(request.form.get('id'))
    except (ValueError, TypeError):
        flash('Invalid attendee ID.', 'error')
        return redirect(url_for('manage_attendees'))

    identifier = request.form.get('identifier', '').strip()
    name = request.form.get('name', '').strip()
    department = request.form.get('department', '').strip()
    email = request.form.get('email', '').strip()
    days_allocated = request.form.get('days_allocated', '').strip()
    time_allocated = request.form.get('time_allocated', '').strip()
    monthly_target = request.form.get('monthly_target', 8)
    active = int(request.form.get('active', 1))

    if not identifier or not name or not department:
        flash('Reg No, Name, and Batch/Department are required fields.', 'error')
        return redirect(url_for('manage_attendees'))

    ok, err = update_attendee(
        attendee_id, identifier, name, department, email,
        days_allocated=days_allocated,
        time_allocated=time_allocated,
        monthly_target=monthly_target,
        active=active
    )
    if err:
        flash(err, 'error')
    else:
        flash(f'Updated details for "{name}".', 'success')

    return redirect(url_for('manage_attendees'))

@app.route('/attendees/delete/<int:attendee_id>', methods=['POST'])
def delete_attendee_route(attendee_id):
    delete_attendee(attendee_id)
    flash('Student and associated attendance records were deleted.', 'success')
    return redirect(url_for('manage_attendees'))

@app.route('/reports')
def reports():
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    dept = request.args.get('dept', '')
    status = request.args.get('status', '')

    departments = get_departments()
    attendee_stats = get_attendee_statistics(
        start_date=start_date or None,
        end_date=end_date or None,
        department=dept or None
    )
    detailed_records = get_detailed_report(
        start_date=start_date or None,
        end_date=end_date or None,
        department=dept or None,
        status=status or None
    )

    return render_template(
        'reports.html',
        departments=departments,
        attendee_stats=attendee_stats,
        detailed_records=detailed_records,
        start_date=start_date,
        end_date=end_date,
        selected_dept=dept,
        selected_status=status
    )

@app.route('/export/csv')
def export_csv():
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    dept = request.args.get('dept', '')
    status = request.args.get('status', '')

    records = get_detailed_report(
        start_date=start_date or None,
        end_date=end_date or None,
        department=dept or None,
        status=status or None
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Date',
        'Reg No',
        'Student Name',
        'Batch/Department',
        'Days Allocated',
        'Time Allocated',
        'Email',
        'Status',
        'Is Compensation Class',
        'Remarks'
    ])

    for r in records:
        writer.writerow([
            r['date'],
            r['identifier'],
            r['name'],
            r['department'],
            r['days_allocated'] or '',
            r['time_allocated'] or '',
            r['email'] or '',
            r['status'],
            'Yes' if r['is_compensation'] else 'No',
            r['remark'] or ''
        ])

    csv_data = output.getvalue()
    filename = f"attendance_report_{datetime.date.today().strftime('%Y%m%d')}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    init_db()
    threading.Timer(1.2, open_browser).start()
    print("==================================================")
    print(" AttendEasy Server is running!")
    print(" Open in browser: http://127.0.0.1:5000")
    print(" Press Ctrl+C in terminal to stop.")
    print("==================================================")
    app.run(host='127.0.0.1', port=5000, debug=False)
