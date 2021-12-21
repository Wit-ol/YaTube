from http import HTTPStatus

from django.test import TestCase, Client


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_author(self):
        guest_client = Client()
        response = guest_client.get('/about/author/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_tech(self):
        guest_client = Client()
        response = guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
