import unittest
from app import app
from database import (
    init_db,
    get_attendees,
    get_monthly_student_summary,
    log_compensation_class,
    get_db
)

class TestAttendanceApp(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        init_db()

    def test_01_dashboard(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Attendance Dashboard', response.data)
        self.assertIn(b'MONTHLY RULE: 8 CLASSES', response.data)

    def test_02_mark_attendance_page(self):
        response = self.client.get('/attendance')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Attendance Entry', response.data)
        self.assertIn(b'Compensation', response.data)

    def test_03_manage_attendees_page(self):
        response = self.client.get('/attendees')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Student &amp; Attendee Roster', response.data)
        self.assertIn(b'Allocated Days', response.data)

    def test_04_monthly_tracker_page(self):
        response = self.client.get('/monthly')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Monthly Quota &amp; Compensation Tracker', response.data)
        self.assertIn(b'8 Classes', response.data)

    def test_05_reports_and_export(self):
        response = self.client.get('/reports')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Attendance Reports', response.data)

        csv_res = self.client.get('/export/csv')
        self.assertEqual(csv_res.status_code, 200)
        self.assertEqual(csv_res.mimetype, 'text/csv')
        self.assertIn(b'Days Allocated', csv_res.data)
        self.assertIn(b'Time Allocated', csv_res.data)
        self.assertIn(b'Is Compensation Class', csv_res.data)

    def test_06_add_student_with_schedule(self):
        post_data = {
            'identifier': 'SCHED-777',
            'name': 'Schedule Test Student',
            'department': 'Batch Alpha',
            'email': 'sched@example.com',
            'days_allocated': 'Monday, Wednesday',
            'time_allocated': '10:00 AM - 11:00 AM',
            'monthly_target': '8'
        }
        res = self.client.post('/attendees/add', data=post_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'SCHED-777', res.data)
        self.assertIn(b'Monday, Wednesday', res.data)
        self.assertIn(b'10:00 AM - 11:00 AM', res.data)

        # Retrieve student
        students = get_attendees(search='SCHED-777')
        self.assertTrue(len(students) > 0)
        s_id = students[0]['id']

        # 1. Mark absent on a date to trigger compensation eligibility
        res_absent = self.client.post('/attendance/save', data={
            'date': '2026-10-01',
            f'status_{s_id}': 'Absent',
            f'remark_{s_id}': 'Missed regular session'
        }, follow_redirects=True)
        self.assertEqual(res_absent.status_code, 200)

        # 2. Check monthly summary: student should now be eligible for 1 compensation class
        summary = get_monthly_student_summary('2026-10')
        student_summary = next((s for s in summary['students'] if s['id'] == s_id), None)
        self.assertIsNotNone(student_summary)
        self.assertEqual(student_summary['missed_classes'], 1)
        self.assertTrue(student_summary['can_claim_compensation'])
        self.assertEqual(student_summary['compensation_status'], 'Eligible (1 Available)')

        # 3. Claim the 1 compensation class
        comp_post = {
            'student_id': s_id,
            'date': '2026-10-04',
            'remark': 'Make-up for Oct 1st missed class',
            'month': '2026-10'
        }
        res_comp = self.client.post('/monthly/claim_compensation', data=comp_post, follow_redirects=True)
        self.assertEqual(res_comp.status_code, 200)

        # 4. Check monthly summary again: compensation should now be claimed/used (1/1)
        summary_after = get_monthly_student_summary('2026-10')
        student_summary_after = next((s for s in summary_after['students'] if s['id'] == s_id), None)
        self.assertEqual(student_summary_after['compensation_attended'], 1)
        self.assertFalse(student_summary_after['can_claim_compensation'])
        self.assertEqual(student_summary_after['compensation_status'], 'Used (1/1 Claimed)')
        self.assertEqual(student_summary_after['total_attended'], 1)

        # Clean up
        self.client.post(f'/attendees/delete/{s_id}', follow_redirects=True)

if __name__ == '__main__':
    unittest.main()
