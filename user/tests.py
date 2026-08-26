from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from .models import Profile


class ProfileImageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('fan', password='password')
        self.profile = Profile.objects.create(user=self.user)
        self.client.force_login(self.user)

    @patch('user.views.upload_profile_image')
    def test_profile_image_url_is_saved_after_upload(self, upload_profile_image):
        upload_profile_image.return_value = (
            'https://www.ketengostorage.com/profile-images/1/profile.jpg'
        )
        image = SimpleUploadedFile('profile.jpg', b'\xff\xd8\xff\xe0' + b'0' * 20)

        self.client.post(
            reverse('profile'),
            {
                'edit': '1',
                'username': 'fan',
                'email': '',
                'password': '',
                'password1': '',
                'first_name': '',
                'last_name': '',
                'telephone': '',
                'movil': '',
                'direccion': '',
                'pais': 'Selecciona...',
                'profile_image': image,
            },
        )

        self.profile.refresh_from_db()
        self.assertEqual(
            self.profile.image_url,
            'https://www.ketengostorage.com/profile-images/1/profile.jpg',
        )
        upload_profile_image.assert_called_once()

    def test_social_links_are_saved_from_profile_form(self):
        self.client.post(
            reverse('profile'),
            {
                'edit': '1',
                'username': 'fan',
                'email': '',
                'password': '',
                'password1': '',
                'first_name': '',
                'last_name': '',
                'telephone': '',
                'movil': '',
                'direccion': '',
                'pais': 'Selecciona...',
                'ig_link': 'https://instagram.com/britishdenim',
                'fb_link': 'https://facebook.com/britishdenim',
                'tw_link': 'https://twitter.com/britishdenim',
            },
        )

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.ig_link, 'https://instagram.com/britishdenim')
        self.assertEqual(self.profile.fb_link, 'https://facebook.com/britishdenim')
        self.assertEqual(self.profile.tw_link, 'https://twitter.com/britishdenim')
