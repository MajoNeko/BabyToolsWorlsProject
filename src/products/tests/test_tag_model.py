from django.core.exceptions import ValidationError
from django.test import TestCase

from btw_app.utils import log_execution
from products.models import Tag


class TagTestCase(TestCase):

    @classmethod
    def setUpTestData(self):
        self.test_tag_name = "Test Tag"

    # SUCCESS TEST CASES
    @log_execution
    def test_successful_tag_creation(self):
        # Test the creation of a tag
        tag = Tag.objects.create(name=self.test_tag_name)
        tag.full_clean()
        self.assertEqual(Tag.objects.count(), 1)
        # Ensure name is unique
        self.assertTrue(Tag.objects.filter(name=self.test_tag_name).exists())
        # Ensure created_at is set
        self.assertIsNotNone(Tag.objects.first().created_at)
        # Ensure updated_at is set
        self.assertIsNotNone(Tag.objects.first().updated_at)

    # FAILURE TEST CASES
    @log_execution
    def test_failure_tag_creation_without_name(self):
        # Test the failure of tag creation without a name
        with self.assertRaises(ValidationError) as ctx:
            tag = Tag()
            tag.full_clean()  # Validate before saving
            tag.save()

        self.assertEqual(ctx.exception.message_dict, {"name": ["This field cannot be blank."]})
        self.assertEqual(Tag.objects.count(), 0)

    @log_execution
    def test_failure_tag_creation_with_duplicate_name(self):
        Tag.objects.create(name=self.test_tag_name)
        with self.assertRaises(ValidationError) as ctx:
            duplicate_tag = Tag(name=self.test_tag_name)
            duplicate_tag.full_clean()
            duplicate_tag.save()
        # Ensure only one tag exists
        self.assertEqual(ctx.exception.message_dict, {"name": ["Tag with this Name already exists."]})
        self.assertEqual(Tag.objects.count(), 1)

    @log_execution
    def test_failure_tag_creation_with_too_long_name(self):
        long_name = "a" * 51
        with self.assertRaises(ValidationError) as ctx:
            tag = Tag(name=long_name)
            tag.full_clean()
            tag.save()
        # Ensure no tags were created
        self.assertEqual(
            ctx.exception.message_dict, {"name": ["Ensure this value has at most 50 characters (it has 51)."]}
        )
        self.assertEqual(Tag.objects.count(), 0)

    @log_execution
    def test_tag_string_representation(self):
        tag = Tag.objects.create(name=self.test_tag_name)
        # Ensure __str__ method works correctly
        self.assertEqual(str(tag), self.test_tag_name)
        self.assertEqual(str(tag), self.test_tag_name)
