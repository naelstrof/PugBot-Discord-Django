import django_tables2 as tables
from api.models import Map, Mutator, SignUp

class MapTable(tables.Table):
    class Meta:
        model = Map
        attrs = {"class": "w3-table-all w3-responsive", "id": "myTable"}
        exclude = ("link", "mode", "name", "map_size")

class MutatorTable(tables.Table):
     class Meta:
        model = Mutator
        attrs = {"class": "w3-table-all w3-responsive", "id": "myTable"}
        exclude = ("link", "name", "description")

class SignUpTable(tables.Table):
     class Meta:
         model = SignUp
         attrs = {"class": "w3-table-all w3-responsive", "id": "myTable"}
         exclude = ('email',)
