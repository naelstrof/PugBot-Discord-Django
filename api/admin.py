from django.contrib import admin
from api.models import Player, Mode, Pug, Map, Mutator, Pick_Order
admin.site.register(Player)
admin.site.register(Pug)
admin.site.register(Mode)
admin.site.register(Map)
admin.site.register(Mutator)
admin.site.register(Pick_Order)
# Register your models here.
