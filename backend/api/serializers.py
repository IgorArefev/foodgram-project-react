from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (
    Favorite,
    Follow,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingList,
    Tag
)

User = get_user_model()


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return user.is_authenticated and Follow.objects.filter(
            user=user,
            author=obj.id
        ).exists()


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientRecipeSerializer(
        source='ingredient_amounts',
        many=True,
        read_only=True
    )
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        return self._obj_exists(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        return self._obj_exists(obj, ShoppingList)

    def _obj_exists(self, recipe, name_class):
        request = self.context.get('request')
        return (request
                and request.user.is_authenticated
                and name_class.objects.filter(
                    user=request.user,
                    recipe=recipe
                ).exists())


class AddIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    ingredients = AddIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'ingredients', 'tags', 'image', 'name',
                  'text', 'cooking_time',)

    def validate(self, data):
        tags = data['tags']
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Тег обязателен для заполнения!'
            })
        tags_set = set()
        for tag in tags:
            if tag in tags_set:
                raise serializers.ValidationError({
                    'tags': f'Тег {tag} существует, измените тег!'
                })
            tags_set.add(tag)
        ingredients = data['ingredients']
        ingredients_set = set()
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Ингредиенты обязателены для заполнения!'
            })
        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            if ingredient_id in ingredients_set:
                raise serializers.ValidationError({
                    'ingredients': f'Ингредиент {ingredient} существует,'
                                   ' измените ингредиент!'
                })
            ingredients_set.add(ingredient_id)
            amount = ingredient['amount']
            if int(amount) < 1:
                raise serializers.ValidationError({
                    'amount': 'Количество должно быть больше 0!'
                })
        cooking_time = data['cooking_time']
        if int(cooking_time) < 1:
            raise serializers.ValidationError({
                'cooking_time': 'Время приготовления должно быть больше 0!'
            })
        return data

    def add_ingredients(self, ingredients, recipe):
        new_ingredients = [IngredientRecipe(
            recipe=recipe,
            ingredient=ingredient['id'],
            amount=ingredient['amount'],
        ) for ingredient in ingredients]
        IngredientRecipe.objects.bulk_create(new_ingredients)

    def add_tags(self, tags, recipe):
        for tag in tags:
            recipe.tags.add(tag)

    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=author, **validated_data)
        self.add_tags(tags, recipe)
        self.add_ingredients(ingredients, recipe)
        return recipe

    def to_representation(self, instance):
        return representation(self.context, instance, RecipeSerializer)

    def update(self, recipe, validated_data):
        recipe.tags.clear()
        IngredientRecipe.objects.filter(recipe=recipe).delete()
        self.add_tags(validated_data.pop('tags'), recipe)
        self.add_ingredients(validated_data.pop('ingredients'), recipe)
        return super().update(recipe, validated_data)


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count',)

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeShortSerializer(recipes, many=True).data

    @staticmethod
    def get_recipes_count(obj):
        return obj.recipes.count()


class FavoriteSerializer(RecipeShortSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        return representation(
            self.context,
            instance.recipe,
            RecipeShortSerializer)


class ShoppingListSerializer(RecipeShortSerializer):
    class Meta:
        model = ShoppingList
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        return representation(
            self.context,
            instance.recipe,
            RecipeShortSerializer)


def representation(context, instance, serializer):
    request = context.get('request')
    new_context = {'request': request}
    return serializer(instance, context=new_context).data
