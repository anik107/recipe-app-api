"""
Serializers for the Recipe API Views.
"""
from rest_framework import serializers
from core.models import Recipe, Tag, Ingredient

class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag objects."""
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']

class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredient objects."""
    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_fields = ['id']

class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipe objects."""
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)
    class Meta:
        model = Recipe
        fields = [
            'id',
            'title',
            'time_minutes',
            'price',
            'link',
            'tags',
            'ingredients',
        ]
        read_only_fields = ['id']

    def _get_or_create_tags(self, tags, recipe):
        """Handle getting or creating tags as needed."""
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(user=auth_user, **tag)
            recipe.tags.add(tag_obj)

    def _get_or_create_ingredients(self, ingredients, recipe):
        """Handle getting or creating ingredients as needed."""
        auth_user = self.context['request'].user
        for ingredient in ingredients:
            ingredient_obj, created = Ingredient.objects.get_or_create(user=auth_user, **ingredient)
            recipe.ingredients.add(ingredient_obj)

    def create(self, validated_data):
        """Create a recipe with tags."""
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags, recipe)
        self._get_or_create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Update a recipe with tags."""
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        if ingredients is not None:
            # Clear existing ingredients
            instance.ingredients.clear()
            self._get_or_create_ingredients(ingredients, instance)
        if tags is not None:
            # Clear existing tags
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail view."""
    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']
        # read_only_fields = RecipeSerializer.Meta.read_only_fields + ['description']

class RecipeImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to recipes."""
    class Meta:
        model = Recipe
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': True}}
