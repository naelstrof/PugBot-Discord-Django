import django_tables2 as tables
from api.models import Map, Mutator

class MapTable(tables.Table):
    class Meta:
        model = Map
        attrs = {"class": "paleblue"}
        exclude = ("link", "mode")

class MutatorTable(tables.Table):
     class Meta:
        model = Mutator
        attrs = {"class": "paleblue"}
        exclude = ("link")

