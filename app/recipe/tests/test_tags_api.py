"""
Test for the tags API.
"""
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.models import (
    Tag,
    Recipe
)
from django.contrib.auth import get_user_model
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')

def create_user(email='user@example.com', password='testpass123'):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email=email, password=password)

def detail_url(tag_id):
    """Create and return a tag detail URL."""
    return reverse('recipe:tag-detail', args=[tag_id])

class PublicTagsApiTests(TestCase):
    """Test the publicly available tags API."""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required to access the API."""
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateTagsApiTests(TestCase):
    """Test the authorized user tags API."""
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving a list of tags."""
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')

        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test that tags returned are for the authenticated user."""
        other_user = create_user(email='user2@example.com', password='testpass123')
        Tag.objects.create(user=other_user, name='Fruity')
        tag = Tag.objects.create(user=self.user, name='Comfort Food')
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_create_tag_successful(self):
        """Test creating a new tag."""
        payload = {'name': 'Test Tag'}
        res = self.client.post(TAGS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        tag = Tag.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(tag, key))
        self.assertEqual(tag.user, self.user)
        self.assertEqual(tag.name, payload['name'])

    def test_create_tag_invalid(self):
        """Test creating a new tag with invalid payload fails."""
        payload = {'name': ''}
        res = self.client.post(TAGS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Tag.objects.count(), 0)
        self.assertEqual(Tag.objects.filter(user=self.user).count(), 0)

    def test_update_tag(self):
        """Test updating a tag."""
        tag = Tag.objects.create(user=self.user, name='Vegan')
        payload = {'name': 'Dessert'}
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])
        self.assertEqual(tag.user, self.user)
        self.assertEqual(tag.id, tag.id)

    def test_delete_tag(self):
        """Test deleting a tag."""
        tag = Tag.objects.create(user=self.user, name='Vegan')
        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())
        self.assertEqual(tags.count(), 0)
        self.assertEqual(res.data, None)

    def test_filter_tags_assigned_to_recipes(self):
        """Test listing tags assigned to recipes."""
        tag1 = Tag.objects.create(user=self.user, name='Breakfast')
        tag2 = Tag.objects.create(user=self.user, name='Lunch')
        recipe = Recipe.objects.create(
            title='Pancakes',
            time_minutes=5,
            price=Decimal('2.50'),
            user=self.user,
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_filter_tags_assigned_unique(self):
        """Test filtering tags by assigned recipes returns unique items."""
        tag = Tag.objects.create(user=self.user, name='Breakfast')
        Tag.objects.create(user=self.user, name='Lunch')
        recipe1 = Recipe.objects.create(
            title='Pancakes',
            time_minutes=5,
            price=Decimal('2.50'),
            user=self.user,
        )
        recipe1.tags.add(tag)
        recipe2 = Recipe.objects.create(
            title='Omelette',
            time_minutes=10,
            price=Decimal('3.00'),
            user=self.user,
        )
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

