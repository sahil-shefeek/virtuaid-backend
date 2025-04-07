from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
import datetime

from .models import Resident
from .serializers import ResidentSerializer, ResidentCreateSerializer
from carehomes.models import CareHomes
from carehome_managers.models import CarehomeManagers


class ResidentModelTests(TestCase):
    """Tests for the Resident model."""
    
    def setUp(self):
        """Set up test data."""
        # Create user groups
        self.superadmin_group = Group.objects.create(name='SuperAdmin')
        self.admin_group = Group.objects.create(name='Admin')
        self.manager_group = Group.objects.create(name='Manager')
        
        # Create users
        self.User = get_user_model()
        self.superadmin = self.User.objects.create_superadmin(
            email='superadmin@example.com',
            name='Super Admin',
            password='password123'
        )
        
        self.admin = self.User.objects.create_admin(
            email='admin@example.com',
            name='Test Admin',
            password='password123',
            created_by=self.superadmin
        )
        
        # Create care home
        self.care_home = CareHomes.objects.create(
            name='Test Care Home',
            admin=self.admin,
            location='Test Location'
        )
        
        # Create resident
        self.resident = Resident.objects.create(
            name='Test Resident',
            date_of_birth=datetime.date(1950, 1, 1),
            care_home=self.care_home,
            created_by=self.admin
        )
    
    def test_resident_creation(self):
        """Test creating a resident."""
        self.assertEqual(self.resident.name, 'Test Resident')
        self.assertEqual(self.resident.date_of_birth, datetime.date(1950, 1, 1))
        self.assertEqual(self.resident.care_home, self.care_home)
        self.assertEqual(self.resident.created_by, self.admin)
    
    def test_string_representation(self):
        """Test the string representation of a resident."""
        resident = Resident.objects.get(name='Test Resident')
        # Assuming the __str__ method returns the resident's name
        # If not, you'll need to adjust this test or implement __str__
        self.assertEqual(str(resident), resident.name)


class ResidentSerializerTests(TestCase):
    """Tests for the Resident serializers."""
    
    def setUp(self):
        """Set up test data."""
        # Create user groups
        self.superadmin_group = Group.objects.create(name='SuperAdmin')
        self.admin_group = Group.objects.create(name='Admin')
        self.manager_group = Group.objects.create(name='Manager')
        
        # Create users
        self.User = get_user_model()
        self.superadmin = self.User.objects.create_superadmin(
            email='superadmin@example.com',
            name='Super Admin',
            password='password123'
        )
        
        self.admin = self.User.objects.create_admin(
            email='admin@example.com',
            name='Test Admin',
            password='password123',
            created_by=self.superadmin
        )
        
        # Create care home
        self.care_home = CareHomes.objects.create(
            name='Test Care Home',
            admin=self.admin,
            location='Test Location'
        )
        
        # Create resident
        self.resident = Resident.objects.create(
            name='Test Resident',
            date_of_birth=datetime.date(1950, 1, 1),
            care_home=self.care_home,
            created_by=self.admin
        )
    
    def test_resident_create_serializer(self):
        """Test the ResidentCreateSerializer."""
        data = {
            'name': 'New Resident',
            'date_of_birth': '1960-02-02',
        }
        serializer = ResidentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Test with invalid data
        invalid_data = {
            'name': 'New Resident',
            # Missing date_of_birth
        }
        serializer = ResidentCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())


class ResidentAPITests(APITestCase):
    """Tests for Resident API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create user groups
        self.superadmin_group = Group.objects.create(name='SuperAdmin')
        self.admin_group = Group.objects.create(name='Admin')
        self.manager_group = Group.objects.create(name='Manager')
        
        # Create users
        self.User = get_user_model()
        self.superadmin = self.User.objects.create_superadmin(
            email='superadmin@example.com',
            name='Super Admin',
            password='password123'
        )
        
        self.admin1 = self.User.objects.create_admin(
            email='admin1@example.com',
            name='Admin 1',
            password='password123',
            created_by=self.superadmin
        )
        
        self.admin2 = self.User.objects.create_admin(
            email='admin2@example.com',
            name='Admin 2',
            password='password123',
            created_by=self.superadmin
        )
        
        self.manager = self.User.objects.create_manager(
            email='manager@example.com',
            name='Test Manager',
            password='password123',
            created_by=self.admin1
        )
        
        # Create care homes
        self.care_home1 = CareHomes.objects.create(
            name='Care Home 1',
            admin=self.admin1,
            location='Location 1'
        )
        
        self.care_home2 = CareHomes.objects.create(
            name='Care Home 2',
            admin=self.admin2,
            location='Location 2'
        )
        
        # Link manager to care home
        self.carehome_manager = CarehomeManagers.objects.create(
            carehome=self.care_home1,
            manager=self.manager
        )
        
        # Create residents
        self.resident1 = Resident.objects.create(
            name='Resident 1',
            date_of_birth=datetime.date(1950, 1, 1),
            care_home=self.care_home1,
            created_by=self.admin1
        )
        
        self.resident2 = Resident.objects.create(
            name='Resident 2',
            date_of_birth=datetime.date(1955, 5, 5),
            care_home=self.care_home2,
            created_by=self.admin2
        )
        
        # Create client and URLs
        self.client = APIClient()
        self.residents_list_url = reverse('residents-list')
        self.resident1_detail_url = reverse('residents-detail', kwargs={'pk': self.resident1.id})
        self.resident2_detail_url = reverse('residents-detail', kwargs={'pk': self.resident2.id})
    
    def authenticate_as(self, user):
        """Helper method to authenticate as a specific user."""
        self.client.force_authenticate(user=user)
    
    def test_list_residents_superadmin(self):
        """Test that superadmins can see all residents."""
        self.authenticate_as(self.superadmin)
        
        response = self.client.get(self.residents_list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Should see both residents
    
    def test_list_residents_admin(self):
        """Test that admins can only see residents from their care home."""
        self.authenticate_as(self.admin1)
        
        response = self.client.get(self.residents_list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should only see resident1
        self.assertEqual(response.data[0]['name'], 'Resident 1')
    
    def test_list_residents_manager(self):
        """Test that managers can only see residents from their assigned care home."""
        self.authenticate_as(self.manager)
        
        response = self.client.get(self.residents_list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should only see resident1
        self.assertEqual(response.data[0]['name'], 'Resident 1')
    
    def test_retrieve_resident(self):
        """Test retrieving a single resident."""
        self.authenticate_as(self.admin1)
        
        response = self.client.get(self.resident1_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Resident 1')
    
    def test_retrieve_unauthorized_resident(self):
        """Test attempting to retrieve a resident not in user's care home."""
        self.authenticate_as(self.admin1)
        
        response = self.client.get(self.resident2_detail_url)
        
        # Should not be able to access
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_create_resident(self):
        """Test creating a new resident."""
        self.authenticate_as(self.admin1)
        
        data = {
            'name': 'New Resident',
            'date_of_birth': '1965-03-03'
        }
        
        response = self.client.post(self.residents_list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Resident')
        
        # Check that it was created in the database with correct relationships
        new_resident = Resident.objects.get(name='New Resident')
        self.assertEqual(new_resident.care_home, self.care_home1)
        self.assertEqual(new_resident.created_by, self.admin1)
    
    def test_create_resident_as_manager(self):
        """Test creating a new resident as a manager."""
        self.authenticate_as(self.manager)
        
        data = {
            'name': 'Manager Created Resident',
            'date_of_birth': '1970-04-04'
        }
        
        response = self.client.post(self.residents_list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that it was created in the database with correct relationships
        new_resident = Resident.objects.get(name='Manager Created Resident')
        self.assertEqual(new_resident.care_home, self.care_home1)
        self.assertEqual(new_resident.created_by, self.manager)
    
    def test_update_resident(self):
        """Test updating a resident."""
        self.authenticate_as(self.admin1)
        
        data = {
            'name': 'Updated Resident Name'
        }
        
        response = self.client.patch(self.resident1_detail_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Resident Name')
        
        # Check that it was updated in the database
        updated_resident = Resident.objects.get(pk=self.resident1.id)
        self.assertEqual(updated_resident.name, 'Updated Resident Name')
    
    def test_delete_resident(self):
        """Test deleting a resident."""
        self.authenticate_as(self.admin1)
        
        response = self.client.delete(self.resident1_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Check that it was deleted from the database
        self.assertFalse(Resident.objects.filter(pk=self.resident1.id).exists())
    
    def test_unauthorized_delete(self):
        """Test that a user cannot delete a resident not in their care home."""
        self.authenticate_as(self.admin1)
        
        response = self.client.delete(self.resident2_detail_url)
        
        # Should not be able to access
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Resident should still exist in the database
        self.assertTrue(Resident.objects.filter(pk=self.resident2.id).exists())
    
    def test_search_residents(self):
        """Test searching for residents by name."""
        self.authenticate_as(self.superadmin)
        
        response = self.client.get(f"{self.residents_list_url}?search=Resident 1")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Resident 1')
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access residents."""
        # No authentication
        response = self.client.get(self.residents_list_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
