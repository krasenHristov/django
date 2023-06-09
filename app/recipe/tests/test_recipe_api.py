''' test for recipe api '''

import tempfile
import os

from PIL import Image

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

# url for the recipe API
RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    ''' return the recipe detail url '''

    # return the url for the recipe detail
    return reverse('recipe:recipe-detail', args=[recipe_id])


def image_upload_url(recipe_id):
    ''' return the url for uploading an image to a recipe '''

    # return the url for uploading an image
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def create_recipe(user, **params):
    ''' create and return a recipe '''

    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'description': 'Sample description',
        'link': 'http://test.com/recipe.pdf',
        'instructions': 'Sample instructions',
    }

    # update the defaults with the params
    defaults.update(params)

    # create the Recipe
    recipe = Recipe.objects.create(user=user, **defaults)

    return recipe


class PublicRecipeApiTests(TestCase):
    ''' test unauthenticated API requests '''

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        ''' test that authentication is required '''

        # get the recipes url
        res = self.client.get(RECIPES_URL)

        # assert that the status code is 401
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    ''' test authenticated API requests '''

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().object.create_user(
            'test@test.com',
            'testpass'
        )

        # authenticate the user
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        ''' test retrieving a list of recipes '''

        # create recipes
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        # get the recipes url
        res = self.client.get(RECIPES_URL)

        # get the recipes
        recipes = Recipe.objects.all().order_by('-id')

        # serialize the recipes
        serializer = RecipeSerializer(recipes, many=True)

        # assert that the status code is 200
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # assert that the response data is the same as the serialized data
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        ''' test retrieving recipes for user '''

        # create a user
        user2 = get_user_model().object.create_user(
            'test2@test.com',
            'testpass'
        )

        # create a recipe for the user
        create_recipe(user=user2)

        # create a recipe for the user
        create_recipe(user=self.user)

        # get the recipes url
        res = self.client.get(RECIPES_URL)

        # get the Recipe
        recipes = Recipe.objects.filter(user=self.user)

        # serialize the Recipe
        serializer = RecipeSerializer(recipes, many=True)

        # assert that the status code is 200
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # assert that the response data is the same as the serialized data
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        ''' test retrieving a recipe detail '''

        # create a recipe
        recipe = create_recipe(user=self.user)

        # get the recipe detail url
        url = detail_url(recipe.id)

        # get the recipe detail url
        res = self.client.get(url)

        # serialize the recipe
        serializer = RecipeDetailSerializer(recipe)

        # assert that the status code is 200
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # assert that the response data is the same as the serialized data
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        ''' test creating a recipe '''

        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'description': 'Delicious cheesecake',
            'link': 'http://test.com/recipe.pdf',
            'instructions': 'Sample instructions',
        }

        # post the payload to the recipes url
        res = self.client.post(RECIPES_URL, payload)

        # assert that the status code is 201
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # get the Recipe
        recipe = Recipe.objects.get(id=res.data['id'])

        # assert that each field is the same as the payload
        for k, v in payload.items():

            # getattr() returns the value of the named attribute of an object
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(recipe.user, self.user)

    def test_create_recipe_with_tags(self):
        ''' test creating a recipe with tags '''

        # create a Tag
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')

        payload = {
            'title': 'Avocado lime cheesecake',
            'time_minutes': 60,
            'description': 'Delicious cheesecake',
            'link': 'http://test.com/recipe.pdf',
            'tags': [{'name': 'Vegan'}, {'name': 'Dessert'}],
        }

        # post the payload to the recipes url
        res = self.client.post(RECIPES_URL, payload, format='json')

        # assert that the status code is 201
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # get the Recipe
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)

        # assert that the tags are the same as the payload
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                user=self.user,
                name=tag['name']
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        ''' test creating a recipe with existing tags '''

        # create a Tag
        tag = Tag.objects.create(user=self.user, name='Vegan')

        payload = {
            'title': 'Avocado lime cheesecake',
            'time_minutes': 60,
            'description': 'Delicious cheesecake',
            'link': 'http://test.com/recipe.pdf',
            'tags': [{'name': 'Vegan'}, {'name': 'Dessert'}],
        }

        # post the payload to the recipes url
        res = self.client.post(RECIPES_URL, payload, format='json')

        # assert that the status code is 201
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # get the Recipe
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)

        # assert that the tags are the same as the payload
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                user=self.user,
                name=tag['name']
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        ''' test creating a new tag on update '''

        # create a recipe
        recipe = create_recipe(user=self.user)

        payload = {'tags': [{'name': 'Vegan'}, {'name': 'Dessert'}]}

        # get the recipe detail url
        url = detail_url(recipe.id)

        # patch the payload to the recipe detail url
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_tag = Tag.objects.get(user=self.user, name='Dessert')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assing_tags(self):
        ''' test assigning an existing tag when creating a recipe'''

        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')

        # create a Recipe
        recipe = create_recipe(user=self.user)

        # add a tag to the Recipe
        recipe.tags.add(tag_breakfast)

        # create a new tag
        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')

        payload = {'tags': [{'name': 'Lunch'}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        ''' test clearing a recipe tags '''

        tag = Tag.objects.create(user=self.user, name='Breakfast')

        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}

        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        ''' test creating a recipe with new ingredients '''

        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'description': 'Delicious cheesecake',
            'link': 'http://test.com/recipe.pdf',
            'ingredients': [{'name': 'Chocolate'}, {'name': 'Cheese'}],
        }

        # post the payload to the recipes url
        res = self.client.post(RECIPES_URL, payload, format='json')

        # assert that the status code is 201
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # get the Recipe
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)

        # assert that the ingredients are the same as the payload
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                user=self.user,
                name=ingredient['name']
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self):
        ''' test creating a recipe with existing ingredients '''

        # create an Ingredient
        ingredient = Ingredient.objects.create(
                user=self.user, name='Chocolate')

        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'description': 'Delicious cheesecake',
            'link': 'http://test.com/recipe.pdf',
            'ingredients': [{'name': 'Chocolate'}, {'name': 'Cheese'}],
        }

        # post the payload to the recipes url
        res = self.client.post(RECIPES_URL, payload, format='json')

        # assert that the status code is 201
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # get the Recipe
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)

        # assert that the ingredients are the same as the payload
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                user=self.user,
                name=ingredient['name']
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        ''' test creating a new ingredient on update '''

        # create a Recipe
        recipe = create_recipe(user=self.user)

        payload = {'ingredients': [{'name': 'Chocolat'}, {'name': 'Cheese'}]}

        url = detail_url(recipe.id)

        # patch the payload to the recipe detail url
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # get the new ingredient
        new_ingredient = Ingredient.objects.get(user=self.user, name='Cheese')

        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredients(self):
        ''' test assigning an existing ingredient when creating a recipe'''

        ingredient1 = Ingredient.objects.create(
            user=self.user, name='Chocolate')

        # create a Recipe
        recipe = create_recipe(user=self.user)

        ingredient2 = Ingredient.objects.create(
            user=self.user, name='Cheese')

        payload = {'ingredients': [{'name': 'Cheese'}]}
        url = detail_url(recipe.id)

        # patch the payload to the recipe detail url
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        ''' test clearing a recipe ingredients '''

        ingredient = Ingredient.objects.create(
            user=self.user, name='Chocolate')

        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {'ingredients': []}

        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)

    def test_filter_by_tags(self):
        ''' test returning recipes with specific tags '''

        # create recipes
        recipe1 = create_recipe(user=self.user, title='Thai vegetable curry')
        recipe2 = create_recipe(user=self.user, title='Aubergine with tahini')

        # create tags
        tag1 = Tag.objects.create(user=self.user, name='Vegan')
        tag2 = Tag.objects.create(user=self.user, name='Vegetarian')

        # assign tags to recipes
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)

        # create a Recipe without tags
        recipe3 = create_recipe(user=self.user, title='Fish and chips')

        # get the recipes with the Vegan Tag
        res = self.client.get(
            RECIPES_URL,
            {'tags': f'{tag1.id},{tag2.id}'}
        )

        # serialize the Recipes
        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        # test that the recipes with Tags are in the response
        # and the recipe without Tags is not in the response
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_by_ingredients(self):
        ''' test returning recipes with specific ingredients '''

        # create Recipes
        recipe1 = create_recipe(user=self.user, title='Posh beans on toast')
        recipe2 = create_recipe(user=self.user, title='Chicken cacciatore')

        # create Ingredients
        ingredient1 = Ingredient.objects.create(
            user=self.user, name='Feta cheese')
        ingredient2 = Ingredient.objects.create(
            user=self.user, name='Chicken')

        # assign Ingredients to Recipes
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)

        # create a Recipe without Ingredients
        recipe3 = create_recipe(user=self.user, title='Steak and mushrooms')

        # get the recipes with the Ingredients
        res = self.client.get(
            RECIPES_URL,
            {'ingredients': f'{ingredient1.id},{ingredient2.id}'}
        )

        # serialize the Recipes
        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        # test that the recipes with Ingredients are in the response
        # and the recipe without Ingredients is not in the response
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)


class RecipeImageUploadTests(TestCase):
    ''' test uploading images to recipes '''

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().object.create_user(
            'test@test.com',
            'testpass'
        )

        # authenticate the User
        self.client.force_authenticate(self.user)

        # create a Recipe
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):

        # delete the image file after the test is done
        # this is to avoid cluttering the file system
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        ''' test uploading an image to a recipe '''

        # create a temporary image File
        url = image_upload_url(self.recipe.id)

        # create a temporary image File
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:

            # create an image object
            img = Image.new('RGB', (10, 10))

            # save the image to the temporary file
            img.save(image_file, format='JPEG')

            # check if image exists in the file system
            image_file.seek(0)

            payload = {'image': image_file}

            # post the image to the recipe image upload url
            res = self.client.post(
                    url, payload, format='multipart')

        # refresh the Recipe from the database
        self.recipe.refresh_from_db()

        # assert that the status code is 200
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # assert that the image is not empty
        self.assertIn('image', res.data)

        # assert that the image is the same as the one uploaded
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        ''' test uploading an invalid image '''

        # create a temporary image File
        url = image_upload_url(self.recipe.id)

        payload = {'image': 'notimagebutastring'}

        # post the image to the recipe image upload url
        res = self.client.post(
                url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
