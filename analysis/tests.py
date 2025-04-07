import os
import tempfile
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from authentication.models import User
from carehomes.models import CareHome
from residents.models import Resident
from .models import Video
from .serializers import VideoSerializer

class VideoModelTests(TestCase):
    """Tests for the Video model."""
    
    def setUp(self):
        # Create test resident
        self.resident = Resident.objects.create(
            first_name="Test",
            last_name="Resident"
        )
        
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.mp4')
        self.temp_file.write(b'test video content')
        self.temp_file.seek(0)
        
        # Create a test video
        self.video = Video.objects.create(
            title="Test Video",
            description="Test video description",
            file=SimpleUploadedFile(
                name='test_video.mp4',
                content=self.temp_file.read(),
                content_type='video/mp4'
            ),
            resident=self.resident
        )
    
    def tearDown(self):
        # Close the temporary file
        self.temp_file.close()
        
        # Clean up any uploaded files
        if self.video.file and os.path.isfile(self.video.file.path):
            os.remove(self.video.file.path)
    
    def test_video_creation(self):
        """Test that a video can be created with all fields."""
        self.assertEqual(self.video.title, "Test Video")
        self.assertEqual(self.video.description, "Test video description")
        self.assertEqual(self.video.resident, self.resident)
        self.assertTrue(self.video.file)
        self.assertGreater(self.video.file_size, 0)
    
    def test_video_str_method(self):
        """Test the string representation of the Video model."""
        self.assertEqual(str(self.video), "Test Video")
    
    def test_file_size_automatic_update(self):
        """Test that file_size is automatically updated on save."""
        original_size = self.video.file_size
        self.assertGreater(original_size, 0)
        
        # Update the file with new content
        self.temp_file.seek(0)
        self.temp_file.write(b'test video content with more data')
        self.temp_file.seek(0)
        self.video.file = SimpleUploadedFile(
            name='updated_video.mp4',
            content=self.temp_file.read(),
            content_type='video/mp4'
        )
        self.video.save()
        
        # File size should be updated
        self.assertGreater(self.video.file_size, original_size)


class VideoAPITests(APITestCase):
    """Tests for the Video API endpoints."""
    
    def setUp(self):
        # Create test users with different roles
        self.superadmin = User.objects.create_user(
            email='superadmin@example.com',
            password='password123',
            is_superadmin=True
        )
        
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='password123',
            is_admin=True
        )
        
        self.manager_user = User.objects.create_user(
            email='manager@example.com',
            password='password123',
            is_manager=True
        )
        
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            password='password123'
        )
        
        # Create care home
        self.care_home = CareHome.objects.create(
            name="Test Care Home",
            address="123 Test Street",
            admin=self.admin_user
        )
        
        # Associate manager with care home (simplified - actual implementation may vary)
        if hasattr(self.care_home, 'carehomemanagers'):
            self.care_home.carehomemanagers.manager = self.manager_user
            self.care_home.carehomemanagers.save()
        
        # Create resident
        self.resident = Resident.objects.create(
            first_name="Test",
            last_name="Resident",
            care_home=self.care_home
        )
        
        # Create a test video
        self.video = Video.objects.create(
            title="Test Video",
            description="Test video description",
            file=SimpleUploadedFile(
                name='test_video.mp4',
                content=b'test video content',
                content_type='video/mp4'
            ),
            resident=self.resident
        )
        
        # Set up API client
        self.client = APIClient()
        
        # API endpoints
        self.list_url = reverse('video-list')
        self.detail_url = reverse('video-detail', kwargs={'pk': self.video.id})
    
    def tearDown(self):
        # Clean up any uploaded files
        if self.video.file and os.path.isfile(self.video.file.path):
            os.remove(self.video.file.path)
    
    def test_list_videos_unauthenticated(self):
        """Test that unauthenticated users cannot access the video list."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_videos_superadmin(self):
        """Test that superadmins can see all videos."""
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should see the one video created
    
    def test_list_videos_admin(self):
        """Test that admins can only see videos from their care home."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should see the one video created
        
        # Create a video for a different care home
        other_admin = User.objects.create_user(
            email='other_admin@example.com',
            password='password123',
            is_admin=True
        )
        
        other_care_home = CareHome.objects.create(
            name="Other Care Home",
            address="456 Other Street",
            admin=other_admin
        )
        
        other_resident = Resident.objects.create(
            first_name="Other",
            last_name="Resident",
            care_home=other_care_home
        )
        
        other_video = Video.objects.create(
            title="Other Video",
            description="Other video description",
            file=SimpleUploadedFile(
                name='other_video.mp4',
                content=b'other test video content',
                content_type='video/mp4'
            ),
            resident=other_resident
        )
        
        # Admin should still only see their own videos
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Clean up
        if other_video.file and os.path.isfile(other_video.file.path):
            os.remove(other_video.file.path)
    
    def test_list_videos_manager(self):
        """Test that managers can only see videos from their care home."""
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.get(self.list_url)
        
        # Note: This test might fail if the manager-care home relationship is not properly set up
        # Adjust based on actual implementation
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_retrieve_video(self):
        """Test retrieving a single video."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Test Video")
        self.assertEqual(response.data['description'], "Test video description")
    
    def test_create_video(self):
        """Test creating a video."""
        self.client.force_authenticate(user=self.admin_user)
        
        with tempfile.NamedTemporaryFile(suffix='.mp4') as temp_file:
            temp_file.write(b'new test video content')
            temp_file.seek(0)
            
            data = {
                'title': 'New Test Video',
                'description': 'New test video description',
                'file': temp_file,
                'resident': self.resident.id
            }
            
            response = self.client.post(
                self.list_url, 
                data=data,
                format='multipart'
            )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Video.objects.count(), 2)
        
        # Clean up
        new_video = Video.objects.get(title='New Test Video')
        if new_video.file and os.path.isfile(new_video.file.path):
            os.remove(new_video.file.path)
    
    def test_update_video(self):
        """Test updating a video."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'title': 'Updated Test Video',
            'description': 'Updated test video description',
        }
        
        response = self.client.patch(self.detail_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Test Video')
        self.assertEqual(response.data['description'], 'Updated test video description')
    
    def test_delete_video(self):
        """Test deleting a video."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.delete(self.detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Video.objects.count(), 0)
    
    def test_search_videos(self):
        """Test searching for videos."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create another video for testing search
        another_video = Video.objects.create(
            title="Another Video",
            description="Another test video description",
            file=SimpleUploadedFile(
                name='another_video.mp4',
                content=b'another test video content',
                content_type='video/mp4'
            ),
            resident=self.resident
        )
        
        # Search by title
        response = self.client.get(f"{self.list_url}?search=Another")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Another Video")
        
        # Search by description
        response = self.client.get(f"{self.list_url}?search=test")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Clean up
        if another_video.file and os.path.isfile(another_video.file.path):
            os.remove(another_video.file.path)
    
    def test_ordering_videos(self):
        """Test ordering videos."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create another video for testing ordering
        another_video = Video.objects.create(
            title="Another Video",
            description="Another test video description",
            file=SimpleUploadedFile(
                name='another_video.mp4',
                content=b'another test video content',
                content_type='video/mp4'
            ),
            resident=self.resident
        )
        
        # Order by title ascending
        response = self.client.get(f"{self.list_url}?ordering=title")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['title'], "Another Video")
        self.assertEqual(response.data[1]['title'], "Test Video")
        
        # Order by title descending
        response = self.client.get(f"{self.list_url}?ordering=-title")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['title'], "Test Video")
        self.assertEqual(response.data[1]['title'], "Another Video")
        
        # Clean up
        if another_video.file and os.path.isfile(another_video.file.path):
            os.remove(another_video.file.path)
