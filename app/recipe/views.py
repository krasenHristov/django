''' views for the recipe APIs '''

from drf_spectacular.utils import (
        extend_schema_view,
        extend_schema,
        OpenApiParameter,
        OpenApiTypes,
        )

from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import Recipe, Tag, Ingredient
from recipe import serializers


# extend the schema for the view set
# to add the tags and ingredients parameters for filtering
@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma separated list of IDs to filter',
                ),
            OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description='Comma separated list of ingredient IDs to filter',
                ),
        ])
    )
# the model view set is a class that provides the basic CRUD operations
# for a model in the database
class RecipeViewSet(viewsets.ModelViewSet):
    ''' view for manage recipe API '''

    # serialize the model data
    serializer_class = serializers.RecipeSerializer

    # the queryset variable is the queryset for the model
    queryset = Recipe.objects.all()

    # will require the user to be authenticated to access the API
    authentication_classes = (TokenAuthentication,)

    # require the user to be authenticated to access the API
    permission_classes = (IsAuthenticated,)

    def _params_to_ints(self, qs):
        ''' convert a list of string IDs to a list of integers '''

        # split the query string by the comma
        # and convert the string to an integer
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        ''' return the recipes for the authenticated user '''

        # get the tags parameter from the request
        tags = self.request.query_params.get('tags')

        # get the ingredients parameter from the request
        ingredients = self.request.query_params.get('ingredients')

        # get the queryset for the model
        queryset = self.queryset

        # filter the queryset by the tags and ingredients
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)

        if ingredients:
            ingredient_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredient_ids)

        # filter the queryset by the user and order by the id descending
        return queryset.filter(
                user=self.request.user
                ).order_by('-id').distinct()

    def get_serializer_class(self):
        ''' return the serializer class for request '''

        if self.action == 'list':
            return serializers.RecipeDetailSerializer

        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer

        # default serializer class
        return self.serializer_class

    def perform_create(self, serializer):
        ''' create a new recipe '''

        # modify the behavior of the create method to set the user
        # to the authenticated user before saving the object to the database
        serializer.save(user=self.request.user)

    # create a custom action for the viewset to upload an image
    # we use method POST to upload the image and the detail=True
    # to specify that the action is for a single object
    # the url_path is the url to access the action
    @action(methods=['POST'], detail=True, url_path='upload-image')
    # the pk is the primary key of the object
    # the request is the request object
    # pk is the primary key of the object to upload the image
    def upload_image(self, request, pk=None):
        ''' upload an image to a recipe '''

        # get the recipe object
        recipe = self.get_object()

        # get the serializer class
        serializer = self.get_serializer(
            recipe,
            data=request.data
        )

        if serializer.is_valid():
            # save the serializer
            serializer.save()

            # return the serializer data
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                # the type is integer
                # enum is a list of possible values
                OpenApiTypes.INT, enum=[0, 1],
                description='Filter by items assigned to recipes',
                ),
        ])
    )
class BaseRecipeAttrViewSet(viewsets.GenericViewSet, mixins.ListModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.DestroyModelMixin):
    ''' base view for manage recipe attributes '''

    # will require the user to be authenticated to access the API
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        ''' return the ingredients for the authenticated user '''

        # get the assigned_only parameter from the request
        # if the parameter is not present, the default value is 0
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )

        # get the queryset for the model
        queryset = self.queryset

        # filter the queryset by the tags and ingredients
        if assigned_only:
            # filter the queryset by the tags and ingredients
            queryset = queryset.filter(recipe__isnull=False)

        # else filter the queryset by the user and order by the id descending
        return queryset.filter(
                user=self.request.user).order_by('-name').distinct()


class TagViewSet(BaseRecipeAttrViewSet):

    ''' view for manage tags API '''

    # serialize the model data
    serializer_class = serializers.RecipeTagSerializer

    # the queryset variable is the queryset for the model
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    ''' view for manage ingredients API '''

    # serialize the model data
    serializer_class = serializers.IngredientSerializer

    # the queryset variable is the queryset for the model
    queryset = Ingredient.objects.all()
