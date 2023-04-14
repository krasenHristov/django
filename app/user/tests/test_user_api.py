''' tests for user api '''

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')


def create_user(**params):

    # create a user with the given parameters and return it
    return get_user_model().object.create_user(**params)


class PublicUserApiTests(TestCase):
    ''' test the users api (public) '''

    def setUp(self):

        # create a test client to make requests to the api
        self.client = APIClient()

    def test_create_user_success(self):
        ''' test creating user with valid payload is successful '''

        # create a payload with the required fields for a user object
        payload = {
            'email': 'test@email.test',
            'password': 'testpass',
            'name': 'Test name',
        }

        # make a post request to the create user url with the payload
        res = self.client.post(CREATE_USER_URL, payload)

        # check that the request was successful
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # check that the user was created
        user = get_user_model().object.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_with_email_exist_error(self):
        ''' test creating a user that already exists fails '''

        # create a payload with the required fields for a user object
        payload = {
            'email': 'test@email.test',
            'password': 'testpass',
            'name': 'Test name',
        }

        # create a user with the payload
        create_user(**payload)

        # make a post request to the create user url with the payload
        res = self.client.post(CREATE_USER_URL, payload)

        # check that the request was unsuccessful
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        ''' test that the password must be more than 5 characters '''

        # create a payload with the required fields for a user object
        payload = {
            'email': 'test@email.com',
            'password': 'pw',
            'name': 'Test name',
        }

        # make a post request to the create user url with the payload
        res = self.client.post(CREATE_USER_URL, payload)

        # check that the request was unsuccessful
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # check that the user was not created
        user_exists = get_user_model().object.filter(
            email=payload['email']).exists()

        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        ''' test that a token is created for the user '''

        user_details = {
            'email': 'test@email.com',
            'password': 'testpass',
            'name': 'Test name',
        }

        # create a user with the payload
        create_user(**user_details)

        # create a payload with the required fields for a user object
        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }

        # make a post request to the create user url with the payload
        res = self.client.post(TOKEN_URL, payload)

        # check that the request was successful
        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        ''' test that token is not created if invalid credentials are given '''

        # create a user with the payload
        create_user(
                email='test@email.com',
                password='testpass',
                )

        # create a payload with the required fields for a user object
        payload = {'email': '', 'password': 'badpass'}

        # make a post request to the create user url with the payload
        res = self.client.post(TOKEN_URL, payload)

        # check that the request was unsuccessful
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_password(self):
        ''' test that email and password are required '''

        # create a user with the payload
        payload = {'email': 'test@email.com', 'password': ''}

        # make a post request to the create user url with the payload
        res = self.client.post(TOKEN_URL, payload)

        # check that the request was unsuccessful
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)