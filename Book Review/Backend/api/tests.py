from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from api.models import User, Book
from api.helpers import generate_token
import os
import shutil

class BookReviewAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create users
        self.primary_admin = User.objects.create_superuser(
            email='admin@example.com',
            username='primary_admin',
            password='password123'
        )
        self.other_admin = User.objects.create_superuser(
            email='otheradmin@example.com',
            username='other_admin',
            password='password123'
        )
        self.normal_user = User.objects.create_user(
            email='user@example.com',
            username='normal_user',
            password='password123'
        )
        
        # Generate tokens
        self.primary_admin_token = generate_token(self.primary_admin)
        self.other_admin_token = generate_token(self.other_admin)
        self.normal_user_token = generate_token(self.normal_user)

    def tearDown(self):
        # Clean up any uploaded test files
        media_path = os.path.join(settings.MEDIA_ROOT, 'book_covers')
        if os.path.exists(media_path):
            shutil.rmtree(media_path)

    def test_book_creation_with_file_upload(self):
        # Create a dummy image file
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00'
            b'\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b'
        )
        uploaded_file = SimpleUploadedFile('test_cover.gif', small_gif, content_type='image/gif')
        
        # Send multipart post request
        response = self.client.post(
            '/api/books/',
            {
                'title': 'The AI Chronicles',
                'author': 'Antigravity',
                'genre': 'Science Fiction',
                'published_date': '2026-06-20',
                'description': 'A fantastic book',
                'cover_image': uploaded_file
            },
            HTTP_AUTHORIZATION=f'Bearer {self.primary_admin_token}'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verify book exists in database
        book = Book.objects.get(title='The AI Chronicles')
        self.assertEqual(book.author, 'Antigravity')
        self.assertEqual(book.genre, 'Science Fiction')
        self.assertTrue('test_cover' in book.cover_url)
        self.assertTrue(book.cover_url.startswith('http://testserver/media/book_covers/'))

    def test_user_promotion_restrictions(self):
        # 1. Normal user tries to promote -> forbidden
        response = self.client.post(
            f'/api/admin/users/{self.normal_user.id}/make-admin/',
            HTTP_AUTHORIZATION=f'Bearer {self.normal_user_token}'
        )
        self.assertEqual(response.status_code, 403)
        
        # 2. Other admin tries to promote -> success (since any admin can now promote)
        response = self.client.post(
            f'/api/admin/users/{self.normal_user.id}/make-admin/',
            HTTP_AUTHORIZATION=f'Bearer {self.other_admin_token}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        # Verify role has updated in database
        self.normal_user.refresh_from_db()
        self.assertEqual(self.normal_user.role, 'admin')
        
        # Demote back to user using other admin to prepare for primary admin test
        response = self.client.post(
            f'/api/admin/users/{self.normal_user.id}/demote-to-user/',
            HTTP_AUTHORIZATION=f'Bearer {self.other_admin_token}'
        )
        self.assertEqual(response.status_code, 200)
        self.normal_user.refresh_from_db()
        self.assertEqual(self.normal_user.role, 'user')
        
        # 3. Primary admin (admin@example.com) promotes normal user -> success
        response = self.client.post(
            f'/api/admin/users/{self.normal_user.id}/make-admin/',
            HTTP_AUTHORIZATION=f'Bearer {self.primary_admin_token}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        # Verify role has updated in database
        self.normal_user.refresh_from_db()
        self.assertEqual(self.normal_user.role, 'admin')
        
        # 4. Primary admin tries to promote an already admin user -> error
        response = self.client.post(
            f'/api/admin/users/{self.normal_user.id}/make-admin/',
            HTTP_AUTHORIZATION=f'Bearer {self.primary_admin_token}'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], 'User is already an Admin.')
