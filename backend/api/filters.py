from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe

FILTER_USER = {'favorites': 'favorites__user',
               'shop_list': 'shop_list__user'}


class IngredientSearchFilter(FilterSet):
    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name', )


class RecipeFilter(FilterSet):
    tags = filters.AllValuesMultipleFilter(method='filter')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('author', )

    def filter(self, queryset, *args, **kwargs):
        queryset = super().filter(queryset, *args, **kwargs)
        tags = kwargs.get('tags')
        if not tags:
            return queryset.none()
        return queryset

    def _get_queryset(self, queryset, name, value, model):
        if value:
            return queryset.filter(**{FILTER_USER[model]: self.request.user})
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        return self._get_queryset(queryset, name, value, 'favorites')

    def filter_is_in_shopping_cart(self, queryset, name, value):
        return self._get_queryset(queryset, name, value, 'shop_list')
