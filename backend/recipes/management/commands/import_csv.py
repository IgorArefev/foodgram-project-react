import csv
import os

from django.core.management.base import BaseCommand

from foodgram.settings import BASE_DIR
from recipes.models import Ingredient


def get_reader(file_name: str):
    csv_path = os.path.join(BASE_DIR, file_name)
    csv_file = open(csv_path, 'r', encoding='utf-8')
    reader = csv.reader(csv_file, delimiter=',')
    return reader


class Command(BaseCommand):

    def handle(self, *args, **options):
        csv_reader = get_reader('ingredients.csv')
        next(csv_reader, None)
        for row in csv_reader:
            obj, created = Ingredient.objects.get_or_create(
                name=row[0],
                measurement_unit=row[1]
            )
        print('импортировано')
