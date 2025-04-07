from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from datetime import datetime, timedelta

from residents.models import Resident
from carehomes.models import CareHome
from feedbacks.models import Feedback
from .models import TherapySession
from .serializers import SessionSerializer, SessionCreateUpdateSerializer

class SessionModelTest(TestCase):
    def setUp(self):
        # Create care home for the resident
        self.care_home = CareHome.objects.create(
            name="Test Care Home",
            address="123 Test Street",
            phone_number="1234567890"
        )
        
        # Create a resident
        self.resident = Resident.objects.create(
            name="Test Resident",
            age=75,
            care_home=self.care_home
        )
        
        # Create a session
        self.session = TherapySession.objects.create(
            resident=self.resident,
            scheduled_date=timezone.now() + timedelta(days=1),
            status='scheduled',
            notes="Test session notes"
        )

    def test_session_creation(self):
        """Test the session model creation"""
        self.assertTrue(isinstance(self.session, TherapySession))
        self.assertEqual(self.session.__str__(), f"Session for {self.resident} on {self.session.scheduled_date}")

    def test_session_default_status(self):
        """Test the default status for a session"""
        self.assertEqual(self.session.status, 'scheduled')

    def test_session_mark_completed(self):
        """Test marking a session as completed"""
        self.session.status = 'completed'
        self.session.end_time = timezone.now()
        self.session.save()
        
        # Refresh from db
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, 'completed')
        self.assertIsNotNone(self.session.end_time)

class SessionSerializerTest(TestCase):
    def setUp(self):
        # Create care home for the resident
        self.care_home = CareHome.objects.create(
            name="Test Care Home",
            address="123 Test Street",
            phone_number="1234567890"
        )
        
        # Create a resident
        self.resident = Resident.objects.create(
            name="Test Resident",
            age=75,
            care_home=self.care_home
        )
        
        # Create a session
        self.session = TherapySession.objects.create(
            resident=self.resident,
            scheduled_date=timezone.now() + timedelta(days=1),
            status='scheduled',
            notes="Test session notes"
        )
        
        # Create a completed session without feedback
        self.completed_session = TherapySession.objects.create(
            resident=self.resident,
            scheduled_date=timezone.now() - timedelta(days=1),
            end_time=timezone.now() - timedelta(hours=1),
            status='completed',
            notes="Completed session"
        )
        
        # Create a feedback for another session
        self.feedback = Feedback.objects.create(
            rating=5,
            comments="Great session"
        )
        
        # Create a completed session with feedback
        self.session_with_feedback = TherapySession.objects.create(
            resident=self.resident,
            scheduled_date=timezone.now() - timedelta(days=2),
            end_time=timezone.now() - timedelta(days=2, hours=1),
            status='completed',
            notes="Session with feedback",
            feedback=self.feedback
        )

    def test_session_serializer(self):
        """Test the session serializer"""
        serializer = SessionSerializer(self.session)
        data = serializer.data
        
        self.assertEqual(data['status'], 'scheduled')
        self.assertEqual(data['notes'], 'Test session notes')
        self.assertEqual(data['feedback_status'], 'Not Applicable')
        self.assertIn('resident_details', data)

    def test_feedback_status_method(self):
        """Test the get_feedback_status method in serializer"""
        # Session with feedback
        serializer1 = SessionSerializer(self.session_with_feedback)
        self.assertEqual(serializer1.data['feedback_status'], 'Completed')
        
        # Completed session without feedback
        serializer2 = SessionSerializer(self.completed_session)
        self.assertEqual(serializer2.data['feedback_status'], 'Pending')
        
        # Scheduled session
        serializer3 = SessionSerializer(self.session)
        self.assertEqual(serializer3.data['feedback_status'], 'Not Applicable')

class SessionAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create care home for the resident
        self.care_home = CareHome.objects.create(
            name="Test Care Home",
            address="123 Test Street",
            phone_number="1234567890"
        )
        
        # Create residents
        self.resident1 = Resident.objects.create(
            name="Resident One",
            age=75,
            care_home=self.care_home
        )
        
        self.resident2 = Resident.objects.create(
            name="Resident Two",
            age=80,
            care_home=self.care_home
        )
        
        # Create sessions
        now = timezone.now()
        
        # Scheduled session for today
        self.today_session = TherapySession.objects.create(
            resident=self.resident1,
            scheduled_date=now.replace(hour=14, minute=0),  # Today at 2 PM
            status='scheduled',
            notes="Today's session"
        )
        
        # Scheduled session for future
        self.future_session = TherapySession.objects.create(
            resident=self.resident2,
            scheduled_date=now + timedelta(days=2),
            status='scheduled',
            notes="Future session"
        )
        
        # Completed session
        self.completed_session = TherapySession.objects.create(
            resident=self.resident1,
            scheduled_date=now - timedelta(days=2),
            end_time=now - timedelta(days=2, hours=1),
            status='completed',
            notes="Completed session"
        )
        
        # In progress session
        self.in_progress_session = TherapySession.objects.create(
            resident=self.resident2,
            scheduled_date=now - timedelta(hours=1),
            status='in_progress',
            notes="In progress session"
        )
        
        # Create a feedback
        self.feedback = Feedback.objects.create(
            rating=5,
            comments="Great session"
        )
        
        # Session with feedback
        self.session_with_feedback = TherapySession.objects.create(
            resident=self.resident1,
            scheduled_date=now - timedelta(days=4),
            end_time=now - timedelta(days=4, hours=1),
            status='completed',
            notes="Session with feedback",
            feedback=self.feedback
        )
        
        # Set up URLs
        self.list_url = reverse('session-list')

    def test_list_sessions(self):
        """Test listing all sessions"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)

    def test_create_session(self):
        """Test creating a new session"""
        data = {
            'resident': self.resident1.id,
            'scheduled_date': (timezone.now() + timedelta(days=3)).isoformat(),
            'status': 'scheduled',
            'notes': 'New test session'
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TherapySession.objects.count(), 6)
        self.assertEqual(TherapySession.objects.latest('id').notes, 'New test session')

    def test_retrieve_session(self):
        """Test retrieving a single session"""
        url = reverse('session-detail', args=[self.today_session.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.today_session.id)

    def test_update_session(self):
        """Test updating a session"""
        url = reverse('session-detail', args=[self.future_session.id])
        data = {
            'resident': self.resident2.id,
            'scheduled_date': self.future_session.scheduled_date.isoformat(),
            'status': 'scheduled',
            'notes': 'Updated notes'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.future_session.refresh_from_db()
        self.assertEqual(self.future_session.notes, 'Updated notes')

    def test_delete_session(self):
        """Test deleting a session"""
        initial_count = TherapySession.objects.count()
        url = reverse('session-detail', args=[self.future_session.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TherapySession.objects.count(), initial_count - 1)

    def test_mark_completed_action(self):
        """Test the mark_completed custom action"""
        url = reverse('session-mark-completed', args=[self.today_session.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.today_session.refresh_from_db()
        self.assertEqual(self.today_session.status, 'completed')
        self.assertIsNotNone(self.today_session.end_time)

    def test_mark_in_progress_action(self):
        """Test the mark_in_progress custom action"""
        url = reverse('session-mark-in-progress', args=[self.today_session.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.today_session.refresh_from_db()
        self.assertEqual(self.today_session.status, 'in_progress')

    def test_cancel_session_action(self):
        """Test the cancel_session custom action"""
        url = reverse('session-cancel-session', args=[self.future_session.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.future_session.refresh_from_db()
        self.assertEqual(self.future_session.status, 'cancelled')

    def test_filter_by_status(self):
        """Test filtering sessions by status"""
        url = f"{self.list_url}?status=completed"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # completed_session and session_with_feedback

    def test_filter_by_resident(self):
        """Test filtering sessions by resident"""
        url = f"{self.list_url}?resident={self.resident1.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)  # today_session, completed_session, and session_with_feedback

    def test_filter_by_status_category(self):
        """Test filtering sessions by status category"""
        # Test upcoming sessions
        url = f"{self.list_url}?status_category=upcoming"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['results']) >= 1)  # At least future_session
        
        # Test completed sessions
        url = f"{self.list_url}?status_category=completed"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # completed_session and session_with_feedback
        
        # Test in progress sessions
        url = f"{self.list_url}?status_category=in_progress"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # in_progress_session

    def test_filter_by_feedback_status(self):
        """Test filtering sessions by feedback status"""
        # Sessions with feedback
        url = f"{self.list_url}?feedback_status=completed"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # session_with_feedback
        
        # Sessions pending feedback
        url = f"{self.list_url}?feedback_status=pending"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # completed_session

    def test_search_by_notes(self):
        """Test searching sessions by notes"""
        url = f"{self.list_url}?search=progress"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # in_progress_session
