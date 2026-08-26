import json
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from .models import Consumer, Item, Scan, skuPost

class SkuFeedTests(TestCase):
    def setUp(self):
        self.item = Item.objects.create(sku='BD-001', name='Denim Jacket')
        self.owner = User.objects.create_user('owner', password='password')
        self.other_user = User.objects.create_user('other', password='password')
        Consumer.objects.create(user_id=self.owner, sku=self.item)
        self.url = reverse('sku_feed', kwargs={'sku': self.item.sku})

    def test_only_registered_user_can_access_feed(self):
        self.client.force_login(self.other_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_registered_user_comment_is_pending_and_not_displayed(self):
        self.client.force_login(self.owner)

        response = self.client.post(self.url, {'text': 'Great jacket!'}, follow=True)

        post = skuPost.objects.get()
        self.assertFalse(post.is_approved)
        self.assertContains(response, 'será publicado')
        self.assertNotContains(response, 'Great jacket!')

    def test_only_approved_comments_are_displayed(self):
        skuPost.objects.create(sku=self.item, user_id=self.owner, text='Pending comment')
        skuPost.objects.create(
            sku=self.item,
            user_id=self.owner,
            text='Approved comment',
            is_approved=True,
        )
        self.client.force_login(self.owner)

        response = self.client.get(self.url)

        self.assertContains(response, 'Approved comment')
        self.assertNotContains(response, 'Pending comment')

    @patch('britishdenim.views.upload_sku_feed_images')
    def test_image_urls_are_stored_with_pending_post(self, upload_images):
        upload_images.return_value = ['https://ketengostorage.com/sku-feed-images/1/test.jpg']
        image = SimpleUploadedFile(
            'jacket.jpg',
            b'\xff\xd8\xff\xe0' + b'0' * 20,
            content_type='image/jpeg',
        )
        self.client.force_login(self.owner)

        self.client.post(self.url, {'text': 'My jacket', 'images': image})

        post = skuPost.objects.get()
        self.assertEqual(
            post.imageList,
            '["https://ketengostorage.com/sku-feed-images/1/test.jpg"]',
        )
        upload_images.assert_called_once()

    def test_registered_user_can_like_an_approved_post_once(self):
        post = skuPost.objects.create(
            sku=self.item,
            user_id=self.owner,
            text='Approved comment',
            is_approved=True,
        )
        self.client.force_login(self.owner)

        self.client.post(self.url, {'action': 'like', 'post_id': post.id})
        self.client.post(self.url, {'action': 'like', 'post_id': post.id})

        self.assertEqual(post.likepost_set.count(), 1)


class StatsTests(TestCase):
    def test_stats_uses_aggregated_scan_data(self):
        staff_user = User.objects.create_superuser('admin', 'admin@example.com', 'password')
        item = Item.objects.create(sku='BD-100', name='Jeans')
        second_item = Item.objects.create(sku='BD-200', name='Jacket')
        Scan.objects.create(sku=item, country='PA')
        Scan.objects.create(sku=item, country='PA')
        Scan.objects.create(sku=second_item, country='CO')
        self.client.force_login(staff_user)

        response = self.client.get(reverse('stats'))

        self.assertEqual(response.context['totalScans'], 3)
        self.assertEqual(response.context['totalItems'], 2)
        self.assertEqual(response.context['scansByItem']['BD-100'], 2)
        self.assertEqual(response.context['scansByItem']['BD-200'], 1)


class ChartsTests(TestCase):
    def test_charts_calculates_all_datasets_from_valid_scans(self):
        staff_user = User.objects.create_superuser('charts-admin', 'charts@example.com', 'password')
        item = Item.objects.create(sku='BD-300', name='Shirt')
        Scan.objects.create(sku=item, when=str(datetime.now()))
        Scan.objects.create(sku=item, when=str(datetime.now() - timedelta(days=1)))
        Scan.objects.create(sku=item, when='not a date')
        self.client.force_login(staff_user)

        response = self.client.get(reverse('charts'))

        self.assertEqual(sum(json.loads(response.context['values'])), 2)
        self.assertEqual(sum(json.loads(response.context['day_values'])), 2)
        self.assertIn('BD-300', response.context['itemList'])


class ConsumerTests(TestCase):
    def test_consumer_view_groups_registered_skus_by_user(self):
        staff_user = User.objects.create_superuser('consumer-admin', 'consumer@example.com', 'password')
        customer = User.objects.create_user('customer', password='password')
        first_item = Item.objects.create(sku='BD-400', name='Jeans')
        second_item = Item.objects.create(sku='BD-401', name='Shirt')
        Consumer.objects.create(user_id=customer, sku=first_item, country='PA')
        Consumer.objects.create(user_id=customer, sku=second_item, country='PA')
        self.client.force_login(staff_user)

        response = self.client.get(reverse('consumer'))

        self.assertEqual(response.context['count'], 1)
        self.assertEqual(response.context['consumers'][0]['username'], 'customer')
        self.assertEqual(response.context['consumers'][0]['skus'], ['BD-400', 'BD-401'])
