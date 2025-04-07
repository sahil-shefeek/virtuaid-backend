from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
import json

from .models import InterfaceUser


class InterfaceUserModelTests(TestCase):
    """Tests for the InterfaceUser model."""
    
    def setUp(self):
        # Create necessary groups
        self.admin_group = Group.objects.create(name='Admin')
        self.superadmin_group = Group.objects.create(name='SuperAdmin')
        self.manager_group = Group.objects.create(name='Manager')
        
        # Create test users
        self.superadmin = InterfaceUser.objects.create_superadmin(
            email='superadmin@example.com',
            name='Super Admin',
            password='password123'
        )
        
        self.admin = InterfaceUser.objects.create_admin(
            email='admin@example.com',
            name='Test Admin',
            password='password123',
            created_by=self.superadmin
        )
        
        self.manager = InterfaceUser.objects.create_manager(
            email='manager@example.com',
            name='Test Manager',
            password='password123',
            created_by=self.admin
        )
    
    def test_user_creation(self):
        """Test that users are created with correct attributes."""
        self.assertEqual(self.superadmin.email, 'superadmin@example.com')
        self.assertEqual(self.superadmin.name, 'Super Admin')
        self.assertTrue(self.superadmin.check_password('password123'))
        
        self.assertEqual(self.admin.email, 'admin@example.com')
        self.assertEqual(self.admin.created_by, self.superadmin)
        
        self.assertEqual(self.manager.email, 'manager@example.com')
        self.assertEqual(self.manager.created_by, self.admin)
    
    def test_user_string_representation(self):
        """Test the string representation of users."""
        self.assertEqual(str(self.admin), 'Test Admin')
        self.assertEqual(str(self.superadmin), 'Super Admin')
        self.assertEqual(str(self.manager), 'Test Manager')
    
    def test_user_roles(self):
        """Test user role properties."""
        self.assertTrue(self.superadmin.is_superadmin)
        self.assertFalse(self.superadmin.is_admin)
        self.assertFalse(self.superadmin.is_manager)
        
        self.assertTrue(self.admin.is_admin)
        self.assertFalse(self.admin.is_superadmin)
        self.assertFalse(self.admin.is_manager)
        
        self.assertTrue(self.manager.is_manager)
        self.assertFalse(self.manager.is_admin)
        self.assertFalse(self.manager.is_superadmin)
    
    def test_username_generation(self):
        """Test that usernames are generated correctly."""
        self.assertIsNotNone(self.admin.username)
        self.assertIn('admin', self.admin.username)
        
        # Test unique username generation
        another_admin = InterfaceUser.objects.create_admin(
            email='another_admin@example.com',
            name='Another Admin',
            password='password123',
            created_by=self.superadmin
        )
        self.assertIsNotNone(another_admin.username)
        self.assertIn('another_admin', another_admin.username)
        self.assertNotEqual(self.admin.username, another_admin.username)
    
    def test_has_perm(self):
        """Test permission checks for different user types."""
        # Superadmin should have all permissions
        self.assertTrue(self.superadmin.has_perm('auth.add_user'))
        self.assertTrue(self.superadmin.has_perm('auth.change_user'))
        self.assertTrue(self.superadmin.has_perm('auth.delete_user'))
        
        # Other users depend on group permissions and should be tested accordingly
        # This would require setting up specific permissions for testing


class AuthenticationAPITests(APITestCase):
    """Tests for authentication API endpoints."""
    
    def setUp(self):
        # Create necessary groups
        self.admin_group = Group.objects.create(name='Admin')
        self.superadmin_group = Group.objects.create(name='SuperAdmin')
        self.manager_group = Group.objects.create(name='Manager')
        
        # Create test users
        self.superadmin = InterfaceUser.objects.create_superadmin(
            email='superadmin@example.com',
            name='Super Admin',
            password='password123'
        )
        
        self.admin = InterfaceUser.objects.create_admin(
            email='admin@example.com',
            name='Test Admin',
            password='password123',
            created_by=self.superadmin
        )
        
        self.manager = InterfaceUser.objects.create_manager(
            email='manager@example.com',
            name='Test Manager',
            password='password123',
            created_by=self.admin
        )
        
        # Setup API client
        self.client = APIClient()
        
        # API endpoints
        self.token_url = reverse('token_obtain_pair')
        self.refresh_url = reverse('token_refresh')
        self.verify_url = reverse('token_verify')
        self.logout_url = reverse('logout')
        self.user_detail_url = reverse('user_details')
        self.users_list_url = reverse('interfaceuser-list')
    
    def get_tokens_for_user(self, email, password):
        """Helper method to get tokens for a user."""
        response = self.client.post(
            self.token_url, 
            {'email': email, 'password': password},
            format='json'
        )
        return response.data
    
    def test_token_obtain(self):
        """Test obtaining JWT tokens."""
        response = self.client.post(
            self.token_url, 
            {'email': 'admin@example.com', 'password': 'password123'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertTrue(response.cookies.get('jwt'))  # Check if cookie is set
        
        # Check that user info is included
        self.assertEqual(response.data['name'], 'Test Admin')
        self.assertTrue(response.data['is_admin'])
        self.assertFalse(response.data['is_superadmin'])
        self.assertFalse(response.data['is_manager'])
    
    def test_token_refresh(self):
        """Test refreshing JWT tokens."""
        # First get tokens
        tokens = self.get_tokens_for_user('admin@example.com', 'password123')
        
        # Test refresh with token in body
        response = self.client.post(
            self.refresh_url, 
            {'refresh': tokens['refresh']},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        
        # Test refresh with token in cookie
        self.client.cookies['jwt'] = tokens['refresh']
        response = self.client.post(self.refresh_url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_token_verify(self):
        """Test verifying JWT tokens."""
        tokens = self.get_tokens_for_user('admin@example.com', 'password123')
        
        # Test verify with token in body
        response = self.client.post(
            self.verify_url, 
            {'token': tokens['access']},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test verify with invalid token
        response = self.client.post(
            self.verify_url, 
            {'token': 'invalid_token'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_logout(self):
        """Test logging out (blacklisting tokens)."""
        tokens = self.get_tokens_for_user('admin@example.com', 'password123')
        
        # Test logout with token in body
        response = self.client.post(
            self.logout_url, 
            {'refresh': tokens['refresh']},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        
        # Test that cookie is cleared
        self.assertNotIn('jwt', response.cookies)
        
        # Test that token is actually blacklisted by trying to use it again
        response = self.client.post(
            self.refresh_url, 
            {'refresh': tokens['refresh']},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_detail(self):
        """Test retrieving current user details."""
        tokens = self.get_tokens_for_user('admin@example.com', 'password123')
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        
        response = self.client.get(self.user_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'admin@example.com')
        self.assertEqual(response.data['name'], 'Test Admin')
        self.assertTrue(response.data['is_admin'])
    
    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access protected endpoints."""
        response = self.client.get(self.user_detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.client.get(self.users_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class InterfaceUserViewSetTests(APITestCase):
    """Tests for the InterfaceUserViewSet."""
    
    def setUp(self):
        # Create necessary groups
        self.admin_group = Group.objects.create(name='Admin')
        self.superadmin_group = Group.objects.create(name='SuperAdmin')
        self.manager_group = Group.objects.create(name='Manager')
        
        # Create test users
        self.superadmin = InterfaceUser.objects.create_superadmin(
            email='superadmin@example.com',
            name='Super Admin',
            password='password123'
        )
        
        self.admin = InterfaceUser.objects.create_admin(
            email='admin@example.com',
            name='Test Admin',
            password='password123',
            created_by=self.superadmin
        )
        
        # Setup API client
        self.client = APIClient()
        
        # API endpoints
        self.users_list_url = reverse('interfaceuser-list')
        self.admin_detail_url = reverse('interfaceuser-detail', kwargs={'pk': self.admin.pk})
    
    def authenticate_as(self, user):
        """Helper method to authenticate as a specific user."""
        self.client.force_authenticate(user=user)
    
    def test_list_users_superadmin(self):
        """Test that superadmins can see all users."""
        self.authenticate_as(self.superadmin)
        
        response = self.client.get(self.users_list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # 2 users created in setUp
    
    def test_list_users_admin(self):
        """Test that admins can only see users they created."""
        # Create an admin-created user
        manager = InterfaceUser.objects.create_manager(
            email='manager@example.com',
            name='Test Manager',
            password='password123',
            created_by=self.admin
        )
        
        self.authenticate_as(self.admin)
        
        response = self.client.get(self.users_list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only the manager they created
        self.assertEqual(response.data[0]['email'], 'manager@example.com')
    
    def test_create_user_admin(self):
        """Test creating admin user"""
        admin = InterfaceUser.objects.create_admin(
            email="testadmin@example.com",
            name="Test Admin",
            password="testpassword123"
        )
        self.assertTrue(admin.is_admin)
        self.assertFalse(admin.is_superadmin)
        self.assertFalse(admin.is_manager)
        self.assertEqual(admin.name, "Test Admin")
    
    def test_retrieve_user(self):
        """Test retrieving a user."""
        self.authenticate_as(self.superadmin)
        
        response = self.client.get(self.admin_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'admin@example.com')
        self.assertEqual(response.data['name'], 'Test Admin')
        self.assertTrue(response.data['is_admin'])
    
    def test_update_user(self):
        """Test updating a user."""
        self.authenticate_as(self.superadmin)
        
        data = {
            'name': 'Updated Admin Name'
        }
        
        response = self.client.patch(
            self.admin_detail_url,
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Admin Name')
        
        # Verify the user was updated in the database
        updated_admin = InterfaceUser.objects.get(pk=self.admin.pk)
        self.assertEqual(updated_admin.name, 'Updated Admin Name')
    
    def test_delete_user(self):
        """Test deleting a user."""
        self.authenticate_as(self.superadmin)
        
        response = self.client.delete(self.admin_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify the user was deleted from the database
        self.assertFalse(
            InterfaceUser.objects.filter(pk=self.admin.pk).exists()
        )
    
    def test_filter_users_by_type(self):
        """Test filtering users by type."""
        # Create a manager
        manager = InterfaceUser.objects.create_manager(
            email='manager@example.com',
            name='Test Manager',
            password='password123',
            created_by=self.superadmin
        )
        
        self.authenticate_as(self.superadmin)
        
        # Filter for admins
        response = self.client.get(f"{self.users_list_url}?type=admin")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['email'], 'admin@example.com')
        
        # Filter for managers
        response = self.client.get(f"{self.users_list_url}?type=manager")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['email'], 'manager@example.com')
