import os
from django.conf import settings
from django.db import models
from django.forms import ModelForm
from django.contrib.auth.models import User
from django import forms
from django.contrib import admin
from django.db.models.signals import post_save
import hashlib
# Create your models here.

Position_Choices = [
    ('Defender', 'Defender'),
    ('Mid', 'Mid'),
    ('Offense', 'Offense'),
]

Day_Choices = [
    ('Friday', 'Friday'),
    ('Saturday', 'Saturday'),
    ('Sunday', 'Sunday'),
]

Time_Choices = [
    ('Evenings', 'Evenings'),
    ('Afternoons', 'Afternoons'),
    ('Mornings', 'Mornings'),
]

Region_Choices = [
    ('North America', 'North America'),
    ('Europe', 'Europe'),
    ('South America', 'South America'),
    ('Central America', 'Central America'),
]
  
Map_Size = [
    ('1v1', '1v1'),
    ('2v2', '2v2'),
    ('3v3', '3v3'),
    ('4v4', '4v4'),
    ('5v5', '5v5'),
    ('6v6', '6v6'),
    ('7v7', '7v7'),
    ('8v8', '8v8'),
]

Modes = [
    ('DM', 'DM'),
    ('CTF', 'CTF'),
    ('AS', 'AS'),
]

Captain_Colors = [
    ('red', 'red'),
    ('blue', 'blue'),
    ('None', 'None'),
]
    

class Player(models.Model):
    user_id = models.CharField(max_length=30, primary_key=True, unique=True)
    epic_id = models.CharField(max_length=32, null=True, blank=True) 
    username = models.CharField(max_length=45)
    role = models.CharField(max_length=19, null=True, blank=True) 
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    win_loss_ratio = models.DecimalField(default=0, max_digits=5, decimal_places=2)
    position = models.CharField(max_length=10, default='Offense',choices=Position_Choices)
    liandri_denarii = models.DecimalField(max_digits=15, decimal_places=2, default=700) 
    average_pick = models.DecimalField(default=0, max_digits=3, decimal_places=2) 
    times_captained = models.PositiveIntegerField(default=0)
    tag = models.CharField(max_length=12, null=True, blank=True)    
    can_captain = models.BooleanField(default=False)
    current = models.CharField(max_length=11, null=True, blank=True)
    def __str__(self):
        return '{}'.format(self.username)
    class Meta:
        verbose_name_plural = 'Players'



class Attachment(models.Model):
    file = models.FileField(null=False)

class Game_ini(models.Model):
    file = models.FileField(null=False)

class Map(models.Model):
    name = models.CharField(max_length=75, primary_key=True)
    map_size = models.CharField(max_length=4, choices=Map_Size)
    mode = models.CharField(max_length=7, choices=Modes) 
    file = models.FileField(null=False, blank=False, default='')
    MD5 = models.CharField(max_length=32, null=True, blank=True)
    ini = models.CharField(max_length=300, null=True, blank=True) 
    def __str__(self):
        return '{}'.format(self.name)
    class Meta:
        verbose_name_plural = 'Maps' 

def create_MD5(instance=None, new_MD5=None):
    MD5 = hashlib.md5(open((os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT)+'{}').format(instance.file),'rb').read()).hexdigest()

    if new_MD5 is not None:
        MD5 = new_MD5
    instance.MD5 = MD5
    instance.save()  
    name = "\"" + instance.name[:-4] + "\""
    file_location = '/' + str(instance.file) 
    ini_md5 = "\"" + MD5 + "\""
    url = "\"ut4pugs.us/media{}".format(file_location) + "\""
    instance.ini = "RedirectReferences=(PackageName={}".format(name) + ',' + 'PackageURLProtocol=' + "\"" + "https" + "\"" + ',PackageURL={}'.format(url) + ',PackageChecksum={})'.format(ini_md5)  
    instance.save()
    return MD5

def post_save_receiver(sender, instance, *args, **kwargs):
    if not instance.MD5:
        instance.MD5 = create_MD5(instance)

post_save.connect(post_save_receiver, sender=Map)



class SignUp(models.Model):
    display_name = models.CharField(max_length=21, primary_key=True, unique=True)
    epicID = models.CharField(max_length=32, unique=True)
    position = models.CharField(max_length=10, default='Offense',choices=Position_Choices) 
    day_most_available = models.CharField(max_length=8, default='Saturday', choices=Day_Choices)
    time_most_available = models.CharField(max_length=13, default='Evenings', choices=Time_Choices)
    region = models.CharField(max_length=17, default='North America', choices=Region_Choices)
    email = models.EmailField(max_length=70, blank=False)
    Availability_Explained = models.CharField(max_length=40, blank=True)
    def __str__(self):
        return '{}'.format(self.display_name)
    class Meta:
        verbose_name_plural = 'Signups'
    
    


class Mutator(models.Model):
    name = models.CharField(max_length=75, primary_key=True, unique=True)
    description = models.CharField(max_length=50)
    file = models.FileField(null=False, blank=False, default='')
    MD5 = models.CharField(max_length=32, null=True, blank=True)
    ini = models.CharField(max_length=300, null=True, blank=True)
    def __str__(self):
        return '{}'.format(self.name)
    class Meta:
        verbose_name_plural = 'Mutators' 

post_save.connect(post_save_receiver, sender=Mutator)


class Mode(models.Model):
    name = models.CharField(max_length=12, primary_key=True, unique=True)
    count = models.PositiveIntegerField(default=8)
    def __str__(self):
        return '{}'.format(self.name)
    class Meta:
        verbose_name_plural = 'Modes'


class Pug(models.Model):
    pug_id = models.CharField(max_length=11, primary_key=True, unique=True)
    mode = models.ForeignKey(Mode, null=True, on_delete=models.CASCADE)
    red_captain = models.ForeignKey(Player, null=True,blank=True, related_name='captain1')
    blue_captain = models.ForeignKey(Player, null=True, blank=True,related_name='captain2')
    first = models.ForeignKey(Player, null=True, blank=True, related_name='slot1')
    second = models.ForeignKey(Player, null=True, blank=True,related_name='slot2')
    third = models.ForeignKey(Player, null=True, blank=True, related_name='slot3')
    fourth = models.ForeignKey(Player, null=True, blank=True, related_name='slot4')
    fifth = models.ForeignKey(Player, null=True, blank=True, related_name='slot5')
    sixth = models.ForeignKey(Player, null=True, blank=True, related_name='slot6')
    seventh = models.ForeignKey(Player, null=True, blank=True, related_name='slot7')
    eighth = models.ForeignKey(Player, null=True, blank=True, related_name='slot8')
    ninth = models.ForeignKey(Player, null=True, blank=True, related_name='slot9') 
    tenth = models.ForeignKey(Player, null=True, blank=True, related_name='slot10')
    max_players = models.PositiveIntegerField(default=10)
    red_here = models.BooleanField(default=False)
    blue_here = models.BooleanField(default=False)
    isfull = models.BooleanField(default=False)
    leaveable = models.BooleanField(default=True)
    can_be_reset = models.BooleanField(default=True)
    date = models.DateField(auto_now=True)
    def __str__(self):
        return '{}'.format(self.pug_id)
    class Meta:
        verbose_name_plural = 'Pugs'

class Pick_Order(models.Model):
    pick_id  = models.AutoField(primary_key=True)
    pug = models.ForeignKey(Pug, null=True, on_delete=models.CASCADE) 
    opt_1 = models.ForeignKey(Player, null=True, blank=True, related_name='opt1')
    opt_2 = models.ForeignKey(Player, null=True, blank=True, related_name='opt2')
    opt_3 = models.ForeignKey(Player, null=True, blank=True, related_name='opt3')
    opt_4 = models.ForeignKey(Player, null=True, blank=True, related_name='opt4')
    opt_5 = models.ForeignKey(Player, null=True, blank=True, related_name='opt5')
    opt_6 = models.ForeignKey(Player, null=True, blank=True, related_name='opt6')
    opt_7 = models.ForeignKey(Player, null=True, blank=True, related_name='opt7')
    opt_8 = models.ForeignKey(Player, null=True, blank=True, related_name='opt8')
    pick_1 = models.ForeignKey(Player, null=True, blank=True, related_name='pick1')
    pick_2 = models.ForeignKey(Player, null=True, blank=True, related_name='pick2')
    pick_3 = models.ForeignKey(Player, null=True, blank=True, related_name='pick3')
    pick_4 = models.ForeignKey(Player, null=True, blank=True, related_name='pick4')
    pick_5 = models.ForeignKey(Player, null=True, blank=True, related_name='pick5')
    pick_6 = models.ForeignKey(Player, null=True, blank=True, related_name='pick6')
    pick_7 = models.ForeignKey(Player, null=True, blank=True, related_name='pick7')
    pick_8 = models.ForeignKey(Player, null=True, blank=True, related_name='pick8')
     

"""
class Match_5v5(models.Model):
    match_id = models.AutoField(primary_key=True)
    pug_id = models.ForeignKey(Pug, null=True, on_delete=models.CASCADE)
    mode = models.ForeignKey(Mode, null=True, on_delete=models.CASCADE) 
    red_captain = models.ForeignKey(Player, null=True, blank=True, related_name='red') 
    blue_captain = models.ForeignKey(Player, null=True, blank=True, related_name='blue') 
    pick_1 = models.ForeignKey(Player, null=True, blank=True, related_name='pick1')
    pick_2 = models.ForeignKey(Player, null=True, blank=True, related_name='pick2')
    pick_3 = models.ForeignKey(Player, null=True, blank=True, related_name='pick3')
    pick_4 = models.ForeignKey(Player, null=True, blank=True, related_name='pick4')
    pick_5 = models.ForeignKey(Player, null=True, blank=True, related_name='pick5')
    pick_6 = models.ForeignKey(Player, null=True, blank=True, related_name='pick6')
    pick_7 = models.ForeignKey(Player, null=True, blank=True, related_name='pick7')
    pick_8 = models.ForeignKey(Player, null=True, blank=True, related_name='pick8')
    def __str__(self):
        return '{}'.format(self.match_id)
    class Meta:
        verbose_name_plural = '5v5 Matches'

class Match_3v3(models.Model):
    match_id = models.AutoField(primary_key=True)
    pug_id = models.ForeignKey(Pug, null=True, on_delete=models.CASCADE)
    mode = models.ForeignKey(Mode, null=True, on_delete=models.CASCADE)
    red_captain = models.ForeignKey(Player, null=True, blank=True, related_name='red')
    blue_captain = models.ForeignKey(Player, null=True, blank=True, related_name='blue')
    pick_1 = models.ForeignKey(Player, null=True, blank=True, related_name='pick1')
    pick_2 = models.ForeignKey(Player, null=True, blank=True, related_name='pick2')
    pick_3 = models.ForeignKey(Player, null=True, blank=True, related_name='pick3')
    pick_4 = models.ForeignKey(Player, null=True, blank=True, related_name='pick4')
     def __str__(self):
        return '{}'.format(self.match_id)
    class Meta:
        verbose_name_plural = '5v5 Matches'
""" 
