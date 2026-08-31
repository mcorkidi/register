import json
from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from .models import Consumer, Item, PostInviteCampaign, Scan, skuPost
from .views import _post_invitation_token
from user.models import Profile

class SkuFeedTests(TestCase):
    def setUp(self):
        self.item = Item.objects.create(sku='BD-001', name='Denim Jacket')
        self.owner = User.objects.create_user('owner', password='password')
        self.other_user = User.objects.create_user('other', password='password')
        Profile.objects.create(user=self.owner, location='PA')
        Consumer.objects.create(user_id=self.owner, sku=self.item)
        self.url = reverse('sku_feed', kwargs={'sku': self.item.sku})

    def test_public_can_access_feed_but_unregistered_user_cannot_post(self):
        anonymous_response = self.client.get(self.url)
        self.client.force_login(self.other_user)

        response = self.client.get(self.url)
        post_response = self.client.post(self.url, {'text': 'Not registered'})

        self.assertEqual(anonymous_response.status_code, 200)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(post_response.status_code, 403)
        self.assertEqual(skuPost.objects.count(), 0)

    @patch('britishdenim.views.send_post_review_email')
    def test_registered_user_comment_is_pending_and_not_displayed(self, review_email_mock):
        self.client.force_login(self.owner)

        response = self.client.post(
            self.url,
            {'text': 'Great jacket!'},
            follow=True,
        )

        post = skuPost.objects.get()
        self.assertFalse(post.is_approved)
        self.assertEqual(post.location, 'PA')
        review_email_mock.assert_called_once()
        self.assertEqual(review_email_mock.call_args.args[1], post)
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

    @patch('britishdenim.views.send_post_review_email')
    @patch('britishdenim.views.upload_sku_feed_images')
    def test_image_urls_are_stored_with_pending_post(self, upload_images, review_email_mock):
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
        review_email_mock.assert_called_once()

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

    @patch('britishdenim.views.send_post_review_email')
    def test_email_invitation_allows_guest_to_post_as_registered_user(self, review_email_mock):
        registration = Consumer.objects.get(user_id=self.owner, sku=self.item)
        invitation_url = '{}?{}'.format(
            self.url,
            urlencode({'invite': _post_invitation_token(registration)}),
        )

        response = self.client.post(invitation_url, {'text': 'Posted from my invitation link'})

        post = skuPost.objects.get()
        self.assertRedirects(response, invitation_url)
        self.assertEqual(post.user_id, self.owner)
        self.assertEqual(post.location, 'PA')
        review_email_mock.assert_called_once()

    def test_invitation_token_cannot_be_used_for_another_sku(self):
        other_item = Item.objects.create(sku='BD-002', name='Denim Shirt')
        registration = Consumer.objects.get(user_id=self.owner, sku=self.item)
        other_url = '{}?{}'.format(
            reverse('sku_feed', kwargs={'sku': other_item.sku}),
            urlencode({'invite': _post_invitation_token(registration)}),
        )

        response = self.client.post(other_url, {'text': 'Wrong product'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(skuPost.objects.count(), 0)

    @patch('britishdenim.admin.send_post_approval_email', return_value=True)
    def test_bulk_approval_sends_approval_email_once(self, approval_email_mock):
        from britishdenim.admin import approve_comments

        post = skuPost.objects.create(sku=self.item, user_id=self.owner, text='Pending')
        request = self.client.request().wsgi_request

        approve_comments(None, request, skuPost.objects.filter(pk=post.pk))

        post.refresh_from_db()
        self.assertTrue(post.is_approved)
        self.assertTrue(post.approval_email_sent)
        approval_email_mock.assert_called_once()


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
        self.assertEqual(json.loads(response.context['consumer_country_labels']), ['Panama'])
        self.assertEqual(json.loads(response.context['consumer_country_values']), [1])

    @patch('britishdenim.views.EmailMultiAlternatives')
    def test_staff_can_email_review_invitation_for_registered_sku(self, email_mock):
        staff_user = User.objects.create_superuser('invite-admin', 'invite@example.com', 'password')
        customer = User.objects.create_user('reviewer', 'reviewer@example.com', 'password')
        item = Item.objects.create(sku='BD-500', name='Denim Jacket')
        registration = Consumer.objects.create(user_id=customer, sku=item)
        self.client.force_login(staff_user)

        response = self.client.post(
            reverse('invite_consumer_to_post', kwargs={'consumer_id': registration.id}),
        )

        self.assertRedirects(response, reverse('consumer'))
        subject, message, sender, recipients = email_mock.call_args.args
        self.assertIn('Denim Jacket', subject)
        self.assertIn('http://testserver/sku_feed/BD-500', message)
        self.assertEqual(sender, 'noreply@britishdenimlatam.com')
        self.assertEqual(recipients, ['reviewer@example.com'])
        email_mock.return_value.attach_alternative.assert_called_once()
        email_mock.return_value.send.assert_called_once()

    @patch('britishdenim.views.EmailMultiAlternatives')
    @patch(
        'britishdenim.views.ipInfo',
        return_value={'city': 'Panama City', 'region': 'Panama', 'country': 'PA'},
    )
    def test_sku_registration_sends_review_invitation(self, ip_info_mock, email_mock):
        user = User.objects.create_user('registered-user', 'registered@example.com', 'password')
        item = Item.objects.create(sku='BD-600', name='Denim Shirt')
        self.client.force_login(user)

        response = self.client.post(
            reverse('register', kwargs={'sku': item.sku}),
            {'regProd': '1', 'inputSku': item.sku},
        )

        self.assertRedirects(response, reverse('sku_feed', kwargs={'sku': item.sku}))
        self.assertTrue(Consumer.objects.filter(user_id=user, sku=item).exists())
        email_mock.return_value.send.assert_called_once()

    @patch('britishdenim.views.send_sku_post_invitation', return_value=True)
    def test_campaign_sends_one_pending_invitation_and_records_it(self, invitation_mock):
        staff_user = User.objects.create_superuser('campaign-admin', 'campaign@example.com', 'password')
        customer = User.objects.create_user('campaign-user', 'campaign-user@example.com', 'password')
        item = Item.objects.create(sku='BD-700', name='Denim Jeans')
        registration = Consumer.objects.create(user_id=customer, sku=item)
        self.client.force_login(staff_user)

        start_response = self.client.post(reverse('start_post_invite_campaign'))
        campaign_id = start_response.json()['campaign_id']
        response = self.client.post(
            reverse('process_next_post_invite', kwargs={'campaign_id': campaign_id}),
        )

        registration.refresh_from_db()
        self.assertEqual(response.json()['sent'], 1)
        self.assertIsNotNone(registration.post_invitation_sent_at)
        self.assertEqual(PostInviteCampaign.objects.get(pk=campaign_id).status, 'active')
        invitation_mock.assert_called_once()


class PrivacyPolicyTests(TestCase):
    def test_privacy_policy_is_publicly_available(self):
        response = self.client.get(reverse('privacy_policy'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Política de Privacidad')

    def test_terms_and_conditions_are_publicly_available(self):
        response = self.client.get(reverse('terms_and_conditions'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Términos y Condiciones de Uso')
