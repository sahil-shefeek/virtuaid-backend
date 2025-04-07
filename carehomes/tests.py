from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from .models import CareHomes
from .serializers import CareHomeSerializer
from carehome_managers.models import CarehomeManagers

User = get_user_model()

class CareHomeModelTest(TestCase):
    def setUp(self):
        # Create a user for the admin field
        self.user = User.objects.create(
            username="testadmin",
            email="testadmin@example.com",
            is_admin=True
        )
        
        # Create a care home
        self.care_home = CareHomes.objects.create(
            name="Test Care Home",
            address="123 Test Street",
            admin=self.user
        )

    def test_carehome_creation(self):
        """Test the care home model creation"""
        self.assertTrue(isinstance(self.care_home, CareHomes))
        self.assertEqual(self.care_home.name, "Test Care Home")
        self.assertEqual(self.care_home.address, "123 Test Street")
        self.assertEqual(self.care_home.admin, self.user)
        self.assertIsNotNone(self.care_home.code)
        self.assertIsNotNone(self.care_home.created_at)
        self.assertIsNotNone(self.care_home.updated_at)

    def test_homes_count_property(self):
        """Test the homes_count property"""
        self.assertEqual(self.care_home.homes_count, 1)
        
        # Create another care home
        CareHomes.objects.create(
            name="Another Care Home",
            address="456 Test Avenue",
            admin=self.user
        )
        
        # Check the homes_count property reflects the change
        self.assertEqual(self.care_home.homes_count, 2)


class CareHomeSerializerTest(TestCase):
    def setUp(self):
        # Create a user for the admin field
        self.user = User.objects.create(
            username="testadmin",
            email="testadmin@example.com",
            is_admin=True
        )
        
        # Create a care home
        self.care_home = CareHomes.objects.create(
            name="Test Care Home",
            address="123 Test Street",
            admin=self.user
        )
        
        self.serializer_data = {
            'name': 'New Care Home',
            'address': '789 New Street',
            'admin': self.user.id
        }

    def test_serializer_contains_expected_fields(self):
        """Test the serializer contains expected fields"""
        serializer = CareHomeSerializer(instance=self.care_home)
        self.assertIn('id', serializer.data)
        self.assertIn('name', serializer.data)
        self.assertIn('code', serializer.data)
        self.assertIn('address', serializer.data)
        self.assertIn('admin', serializer.data)

    def test_serializer_with_valid_data(self):
        """Test serializer with valid data"""
        serializer = CareHomeSerializer(data=self.serializer_data)
        self.assertTrue(serializer.is_valid())

    def test_code_generation_on_save(self):
        """Test code is generated on save"""
        serializer = CareHomeSerializer(data=self.serializer_data)
        self.assertTrue(serializer.is_valid())
        care_home = serializer.save()
        self.assertIsNotNone(care_home.code)
        self.assertTrue(care_home.code.startswith('New'))
        self.assertEqual(len(care_home.code), 6)  # 3 chars from name + 3 from UUID


class CareHomeAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create users with different roles
        self.superadmin = User.objects.create_user(
            username="superadmin", 
            email="superadmin@example.com", 
            password="password123",
            is_superadmin=True
        )
        
        self.admin_user = User.objects.create_user(
            username="admin", 
            email="admin@example.com", 
            password="password123",
            is_admin=True
        )
        
        self.manager_user = User.objects.create_user(
            username="manager", 
            email="manager@example.com", 
            password="password123",
            is_manager=True
        )
        
        self.regular_user = User.objects.create_user(
            username="regular", 
            email="regular@example.com", 
            password="password123"
        )
        
        # Create care homes
        self.admin_care_home = CareHomes.objects.create(
            name="Admin's Care Home",
            address="123 Admin Street",
            admin=self.admin_user
        )
        
        self.another_care_home = CareHomes.objects.create(
            name="Another Care Home",
            address="456 Test Avenue"
        )
        
        # Create carehome manager relationship
        self.manager_care_home = CareHomes.objects.create(
            name="Manager's Care Home",
            address="789 Manager Street"
        )
        
        CarehomeManagers.objects.create(
            carehome=self.manager_care_home,
            manager=self.manager_user
        )
        
        # URLs
        self.list_url = reverse('carehomes-list')
        
    def test_list_carehomes_superadmin(self):
        """Test that superadmin can see all care homes"""
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
    
    def test_list_carehomes_admin(self):
        """Test that admin can see only their care homes"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Admin's Care Home")
    
    def test_list_carehomes_manager(self):
        """Test that manager can see only their managed care homes"""
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Manager's Care Home")
    
    def test_list_carehomes_regular_user(self):
        """Test that regular user can't see any care homes"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_create_carehome(self):
        """Test creating a new care home"""
        self.client.force_authenticate(user=self.superadmin)
        data = {
            'name': 'New Test Care Home',
            'address': '123 New Test Street'
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CareHomes.objects.count(), 4)
        self.assertEqual(CareHomes.objects.latest('created_at').name, 'New Test Care Home')
    
    def test_create_duplicate_carehome(self):
        """Test creating a care home with same name and address"""
        self.client.force_authenticate(user=self.superadmin)
        data = {
            'name': "Admin's Care Home",
            'address': "123 Admin Street"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_retrieve_carehome(self):
        """Test retrieving a specific care home"""
        self.client.force_authenticate(user=self.superadmin)
        url = reverse('carehomes-detail', args=[self.admin_care_home.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Admin's Care Home")
    
    def test_update_carehome(self):
        """Test updating a care home"""
        self.client.force_authenticate(user=self.superadmin)
        url = reverse('carehomes-detail', args=[self.admin_care_home.id])
        data = {
            'name': "Updated Care Home",
            'address': "123 Admin Street",
            'admin': self.admin_user.id
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.admin_care_home.refresh_from_db()
        self.assertEqual(self.admin_care_home.name, "Updated Care Home")
    
    def test_delete_carehome(self):
        """Test deleting a care home"""
        self.client.force_authenticate(user=self.superadmin)
        url = reverse('carehomes-detail', args=[self.another_care_home.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(CareHomes.objects.count(), 2)
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users can't access API"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
