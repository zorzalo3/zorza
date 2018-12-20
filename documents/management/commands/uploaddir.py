import os
from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from documents import models

class Command(BaseCommand):
    help = 'Uploads a directory of files to a category'

    def add_arguments(self, parser):
        parser.add_argument('directory', type=str)
        parser.add_argument('category_id')

        parser.add_argument('-p', '--prefix', metavar='N', dest='prefix',
            type=int, default=0, help=\
'Discard N characters from the beginning of the filename for the Item name')
        parser.add_argument('-s', '--suffix', metavar='N', dest='suffix',
            type=int, default=0, help=\
'Discard N characters from the end of the filename for the Item name')

    def handle(self, *args, **options):
        directory = options['directory']
        pref = options['prefix']
        suff = options['suffix']
        try:
            category_id = int(options['category_id'])
        except:
            category_id = None

        for filename in os.listdir(directory):
            path = os.path.join(directory, filename)
            if os.path.isdir(path):
                continue
            f = File(open(path, 'rb'))

            title = filename[pref:]
            if suff > 0:
                title = title[:-suff]

            obj = models.File(title=title, data=f, category_id=category_id)
            obj.data.save(filename, f)
