from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from datetime import timedelta

from residents.models import Resident
from carehomes.models import CareHomes
from carehome_managers.models import CarehomeManagers
from feedbacks.models import Feedback
from feedbacks.serializers import FeedbackSerializer
from authentication.test_utils import VirtuAidTestCase
from authentication.models import InterfaceUser

class FeedbackModelTest(TestCase):
    def setUp(self):
        # Create care home
        self.care_home = CareHomes.objects.create(
            name="Test Care Home",
            address="123 Test Street"
        )
        
        # Create a resident
        self.resident = Resident.objects.create(
            name="Test Resident",
            age=75,
            care_home=self.care_home
        )
        
        # Create a feedback
        self.feedback = Feedback.objects.create(
            resident=self.resident,
            session_date=timezone.now().date(),
            session_duration=60,
            vr_experience="Test VR experience",
            engagement_level=4,
            satisfaction=5,
            physical_impact=3,
            cognitive_impact=4,
            emotional_response="Test emotional response",
            feedback_notes="Test feedback notes"
        )

    def test_feedback_creation(self):
        """Test the feedback model creation"""
        self.assertTrue(isinstance(self.feedback, Feedback))
        self.assertEqual(self.feedback.resident, self.resident)
        self.assertEqual(self.feedback.vr_experience, "Test VR experience")
        self.assertEqual(self.feedback.engagement_level, 4)
        self.assertEqual(self.feedback.satisfaction, 5)
        self.assertEqual(self.feedback.physical_impact, 3)
        self.assertEqual(self.feedback.cognitive_impact, 4)
        self.assertEqual(self.feedback.emotional_response, "Test emotional response")
        self.assertEqual(self.feedback.feedback_notes, "Test feedback notes")
        self.assertEqual(self.feedback.session_duration, 60)

    def test_feedback_validators(self):
        """Test the validators for rating fields"""
        # Test with invalid values
        with self.assertRaises(Exception):
            Feedback.objects.create(
                resident=self.resident,
                session_date=timezone.now().date(),
                session_duration=60,
                vr_experience="Test VR experience",
                engagement_level=6,  # Invalid (>5)
                satisfaction=5,
                physical_impact=3,
                cognitive_impact=4,
                emotional_response="Test emotional response"
            )
        
        with self.assertRaises(Exception):
            Feedback.objects.create(
                resident=self.resident,
                session_date=timezone.now().date(),
                session_duration=60,
                vr_experience="Test VR experience",
                engagement_level=4,
                satisfaction=0,  # Invalid (<1)
                physical_impact=3,
                cognitive_impact=4,
                emotional_response="Test emotional response"
            )


class FeedbackSerializerTest(TestCase):
    def setUp(self):
        # Create care home
        self.care_home = CareHomes.objects.create(
            name="Test Care Home",
            address="123 Test Street"
        )
        
        # Create a resident
        self.resident = Resident.objects.create(
            name="Test Resident",
            age=75,
            care_home=self.care_home
        )
        
        # Create a feedback
        self.feedback = Feedback.objects.create(
            resident=self.resident,
            session_date=timezone.now().date(),
            session_duration=60,
            vr_experience="Test VR experience",
            engagement_level=4,
            satisfaction=5,
            physical_impact=3,
            cognitive_impact=4,
            emotional_response="Test emotional response",
            feedback_notes="Test feedback notes"
        )
        
        # Valid serializer data
        self.serializer_data = {
            'resident': self.resident.id,
            'session_date': timezone.now().date().isoformat(),
            'session_duration': 45,
            'vr_experience': "New VR experience",
            'engagement_level': 5,
            'satisfaction': 4,
            'physical_impact': 4,
            'cognitive_impact': 3,
            'emotional_response': "New emotional response",
            'feedback_notes': "New feedback notes"
        }

    def test_serializer_contains_expected_fields(self):
        """Test the serializer contains expected fields"""
        serializer = FeedbackSerializer(instance=self.feedback)
        self.assertIn('id', serializer.data)
        self.assertIn('resident', serializer.data)
        self.assertIn('session_date', serializer.data)
        self.assertIn('session_duration', serializer.data)
        self.assertIn('vr_experience', serializer.data)
        self.assertIn('engagement_level', serializer.data)
        self.assertIn('satisfaction', serializer.data)
        self.assertIn('physical_impact', serializer.data)
        self.assertIn('cognitive_impact', serializer.data)
        self.assertIn('emotional_response', serializer.data)
        self.assertIn('feedback_notes', serializer.data)
        self.assertIn('created_at', serializer.data)

    def test_serializer_with_valid_data(self):
        """Test serializer with valid data"""
        serializer = FeedbackSerializer(data=self.serializer_data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_with_invalid_data(self):
        """Test serializer with invalid data"""
        # Invalid engagement_level (out of range)
        invalid_data = self.serializer_data.copy()
        invalid_data['engagement_level'] = 6
        serializer = FeedbackSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        
        # Invalid satisfaction (out of range)
        invalid_data = self.serializer_data.copy()
        invalid_data['satisfaction'] = 0
        serializer = FeedbackSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())


class FeedbackAPITest(VirtuAidTestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create users with different roles
        self.superadmin = InterfaceUser.objects.create_superadmin(
            email="superadmin@example.com",
            name="Super Admin",
            password="password123"
        )
        
        self.admin_user = InterfaceUser.objects.create_admin(
            email="admin@example.com",
            name="Admin User",
            password="password123"
        )
        
        self.manager_user = InterfaceUser.objects.create_manager(
            email="manager@example.com",
            name="Manager User",
            password="password123"
        )
        
        self.regular_user = InterfaceUser.objects.create_user(
            email="user@example.com",
            name="Regular User",
            password="password123"
        )
        
        # Create care homes
        self.admin_care_home = CareHomes.objects.create(
            name="Admin's Care Home",
            address="123 Admin Street",
            admin=self.admin_user
        )
        
        self.manager_care_home = CareHomes.objects.create(
            name="Manager's Care Home",
            address="789 Manager Street"
        )
        
        # Create carehome manager relationship
        CarehomeManagers.objects.create(
            carehome=self.manager_care_home,
            manager=self.manager_user
        )
        
        # Create residents
        self.admin_resident = Resident.objects.create(
            name="Admin's Resident",
            age=75,
            care_home=self.admin_care_home
        )
        
        self.manager_resident = Resident.objects.create(
            name="Manager's Resident",
            age=80,
            care_home=self.manager_care_home
        )
        
        # Create feedbacks
        self.admin_feedback = Feedback.objects.create(
            resident=self.admin_resident,
            session_date=timezone.now().date(),
            session_duration=60,
            vr_experience="Admin VR experience",
            engagement_level=4,
            satisfaction=5,
            physical_impact=3,
            cognitive_impact=4,
            emotional_response="Admin emotional response",
            feedback_notes="Admin feedback notes"
        )
        
        self.manager_feedback = Feedback.objects.create(
            resident=self.manager_resident,
            session_date=timezone.now().date() - timedelta(days=1),
            session_duration=45,
            vr_experience="Manager VR experience",
            engagement_level=5,
            satisfaction=4,
            physical_impact=4,
            cognitive_impact=3,
            emotional_response="Manager emotional response",
            feedback_notes="Manager feedback notes"
        )
        
        # URLs
        self.list_url = reverse('feedback-list')
        
    def test_list_feedbacks_superadmin(self):
        """Test that superadmin can see all feedbacks"""
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_list_feedbacks_admin(self):
        """Test that admin can see only their care home's feedbacks"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['resident'], str(self.admin_resident.id))
    
    def test_list_feedbacks_manager(self):
        """Test that manager can see only their managed care home's feedbacks"""
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['resident'], str(self.manager_resident.id))
    
    def test_list_feedbacks_regular_user(self):
        """Test that regular user can't see any feedbacks"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_create_feedback(self):
        """Test creating a new feedback"""
        self.client.force_authenticate(user=self.superadmin)
        data = {
            'resident': self.admin_resident.id,
            'session_date': timezone.now().date().isoformat(),
            'session_duration': 30,
            'vr_experience': "New VR experience",
            'engagement_level': 3,
            'satisfaction': 4,
            'physical_impact': 3,
            'cognitive_impact': 4,
            'emotional_response': "New emotional response",
            'feedback_notes': "New feedback notes"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Feedback.objects.count(), 3)
        
    def test_retrieve_feedback(self):
        """Test retrieving a specific feedback"""
        self.client.force_authenticate(user=self.superadmin)
        url = reverse('feedback-detail', args=[self.admin_feedback.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.admin_feedback.id))
    
    def test_update_feedback(self):
        """Test updating a feedback"""
        self.client.force_authenticate(user=self.superadmin)
        url = reverse('feedback-detail', args=[self.admin_feedback.id])
        data = {
            'resident': self.admin_resident.id,
            'session_date': self.admin_feedback.session_date.isoformat(),
            'session_duration': 75,
            'vr_experience': "Updated VR experience",
            'engagement_level': 5,
            'satisfaction': 5,
            'physical_impact': 5,
            'cognitive_impact': 5,
            'emotional_response': "Updated emotional response",
            'feedback_notes': "Updated feedback notes"
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.admin_feedback.refresh_from_db()
        self.assertEqual(self.admin_feedback.session_duration, 75)
        self.assertEqual(self.admin_feedback.vr_experience, "Updated VR experience")
    
    def test_partial_update_feedback(self):
        """Test partially updating a feedback"""
        self.client.force_authenticate(user=self.superadmin)
        url = reverse('feedback-detail', args=[self.admin_feedback.id])
        data = {
            'engagement_level': 2,
            'satisfaction': 3
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.admin_feedback.refresh_from_db()
        self.assertEqual(self.admin_feedback.engagement_level, 2)
        self.assertEqual(self.admin_feedback.satisfaction, 3)
    
    def test_delete_feedback(self):
        """Test deleting a feedback"""
        self.client.force_authenticate(user=self.superadmin)
        url = reverse('feedback-detail', args=[self.manager_feedback.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Feedback.objects.count(), 1)
    
    def test_filter_by_resident(self):
        """Test filtering feedbacks by resident"""
        self.client.force_authenticate(user=self.superadmin)
        url = f"{self.list_url}?resident={self.admin_resident.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['resident'], str(self.admin_resident.id))
    
    def test_filter_by_date_range(self):
        """Test filtering feedbacks by date range"""
        self.client.force_authenticate(user=self.superadmin)
        today = timezone.now().date().isoformat()
        yesterday = (timezone.now().date() - timedelta(days=1)).isoformat()
        
        # Test start_date filter
        url = f"{self.list_url}?start_date={yesterday}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Test end_date filter
        url = f"{self.list_url}?end_date={yesterday}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test date range
        url = f"{self.list_url}?start_date={yesterday}&end_date={today}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_unauthenticated_access(self):
        """Test unauthenticated access to API"""
        # List
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Create
        data = {
            'resident': self.admin_resident.id,
            'session_date': timezone.now().date().isoformat(),
            'session_duration': 30,
            'vr_experience': "New VR experience",
            'engagement_level': 3,
            'satisfaction': 4,
            'physical_impact': 3,
            'cognitive_impact': 4,
            'emotional_response': "New emotional response",
            'feedback_notes': "New feedback notes"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Detail
        url = reverse('feedback-detail', args=[self.admin_feedback.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
