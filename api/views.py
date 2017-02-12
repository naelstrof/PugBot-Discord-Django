from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django_tables2 import RequestConfig
from api.models import Player, Mode, Pug, Map, Mutator, Pick_Order 
from rest_framework.decorators import api_view
from api.tables import MapTable, MutatorTable
#import duckduckgo
from pprint import pprint
import json


PLASEP = '\N{SMALL ORANGE DIAMOND}'
MODSEP = '\N{SMALL BLUE DIAMOND}'
OKMSG = '\N{OK HAND SIGN}'

short_modes = {'ctf': '5v5', 'elim': '3v3'}

def get_open(maximum, pug_obj):
    open_spaces = []
    if maximum == 10:
        one = pug_obj.first
        open_spaces.append(one)
        two = pug_obj.second
        open_spaces.append(two)
        third = pug_obj.third
        open_spaces.append(third)
        fourth = pug_obj.fourth
        open_spaces.append(fourth)
        fifth = pug_obj.fifth
        open_spaces.append(fifth)
        sixth = pug_obj.sixth
        open_spaces.append(sixth)
        seventh = pug_obj.seventh
        open_spaces.append(seventh)
        eighth = pug_obj.eighth
        open_spaces.append(eighth)
        ninth = pug_obj.ninth
        open_spaces.append(ninth)
        tenth = pug_obj.tenth
        open_spaces.append(tenth)

    if maximum == 8:
        one = pug_obj.first
        open_spaces.append(one)
        two = pug_obj.second
        open_spaces.append(two)
        third = pug_obj.third
        open_spaces.append(third)
        fourth = pug_obj.fourth
        open_spaces.append(fourth)
        fifth = pug_obj.fifth
        open_spaces.append(fifth)
        sixth = pug_obj.sixth
        open_spaces.append(sixth)
        seventh = pug_obj.seventh
        open_spaces.append(seventh)
        eighth = pug_obj.eighth
        open_spaces.append(eighth)
    
    if maximum == 6:
        one = pug_obj.first
        open_spaces.append(one)
        two = pug_obj.second
        open_spaces.append(two)
        third = pug_obj.third
        open_spaces.append(third)
        fourth = pug_obj.fourth
        open_spaces.append(fourth)
        fifth = pug_obj.fifth
        open_spaces.append(fifth)
        sixth = pug_obj.sixth
        open_spaces.append(sixth)

    if maximum == 4:
        one = pug_obj.first
        open_spaces.append(one)
        two = pug_obj.second
        open_spaces.append(two)
        third = pug_obj.third
        open_spaces.append(third)
        fourth = pug_obj.fourth
        open_spaces.append(fourth)
             
    if maximum == 2:
        one = pug_obj.first
        open_spaces.append(one)
        two = pug_obj.second
        open_spaces.append(two)
        
    open_spaces = [e for e in open_spaces if e != None]    
    return open_spaces


def get_pool(open_spaces):
    player_pool = []
    for player in open_spaces:
        player_pool.append(player.username)
        db_tag = str(player.tag)
        if db_tag == 'None':
            tag = None
        else:
            tag = '[' + str(player.tag) + ']'
            player_pool.append(tag)
        player_pool.append(PLASEP)
    if player_pool[-1] == PLASEP:
        player_pool.pop()
    players = ' '.join(player_pool)
    return players


#@login_required(login_url="/login/")
def redirect(request):
    if request.method == 'GET':
        maps = MapTable(Map.objects.all())
        mutators = MutatorTable(Mutator.objects.all())
        RequestConfig(request).configure(maps)
        RequestConfig(request).configure(mutators) 
        return render(request, "redirect.html", {'maps': maps, 'mutators': mutators})


@login_required(login_url="/login/")
def home(request):
    return render(request,"home.html")


def player_mention(user_id):
    format_id = '<@{}>'.format(user_id)
    return format_id    


@api_view(['POST'])
def verify(request):
    if request.user.is_authenticated():
        incoming_message = json.loads(request.body.decode('utf-8'))
        pprint(incoming_message)
        for k,v  in incoming_message.items():
            if k == 'registration':
                username = v['username']
                print(username)
                user_id = v['user_id']
                role = v['role']
                try:
                    player = Player.objects.get(user_id=user_id)
                    mention = player_mention(player.user_id)
                    player.username = username
                    player.user_id = user_id
                    player.role = role
                    player.save()
                    return HttpResponse(json.dumps({'message': '{}, friend you have already registered, but any changes were noted.'.format(mention)}))
                except:
                    username = username
                    player = Player(user_id=user_id, username=username, role=role)
                    mention = player_mention(user_id)
                    player.save()                
                    return HttpResponse(json.dumps({'message': 'Welcome ' + mention + ' you have {} Liandri Denarii'.format(player.liandri_denarii)}))
            else:
 
                return HttpResponse()

#@method_decorator(csrf_exempt)
@api_view(['POST'])
def set_tag(request):
    if request.user.is_authenticated():
        incoming_message = json.loads(request.body.decode('utf-8'))
        pprint(incoming_message)
        for k,v  in incoming_message.items():
            try:
                player_obj = Player.objects.get(user_id=k)
                msg = v
                if msg == '.notag' or msg == '.deltag':
                    player_obj.tag = None
                    player_obj.save()
                    return HttpResponse(json.dumps({'message': player_obj.username + ' your tag was removed.'}))
                elif msg == '.nomic':
                    player_obj.tag = 'noMic'
                    player_obj.save()
                    return HttpResponse(json.dumps({'message': 'Starting a GoFundMe for ' + player_obj.username + '...jk tag updated.'}))
                else:
                    tag = v[5:]
                    player_obj.tag = tag  
                    player_obj.save()
                    return HttpResponse(json.dumps({'message': player_obj.username + ' your tag was updated.'}))

            except:
                return HttpResponse(json.dumps({'message': 'Please use the register command first. (.register/.r)'}))        

@api_view(['POST'])
def list_maps(request):
    if request.user.is_authenticated():
        incoming_message = json.loads(request.body.decode('utf-8'))
        pprint(incoming_message)
        for k,v  in incoming_message.items():   
            term = v.split()
            msg = term[-1]
            if msg.upper() == 'DM':
                maps = Map.objects.filter(mode='DM') 
            elif msg.upper() == 'CTF':
                maps = Map.objects.filter(mode='CTF')
            map_list = []
            for m in maps:
                map_list.append(m.name)
                map_list.append(MODSEP)
                response = ' '.join(map_list)
            return HttpResponse(json.dumps({'message': response}))

def handle_leaving(index, pug):
    if index == 0:
        pug.first = pug.second
        pug.second = pug.third
        pug.third = pug.fourth
        pug.fourth = pug.fifth
        pug.fifth = pug.sixth
        pug.sixth = pug.seventh
        pug.seventh = pug.eighth
        pug.eighth = pug.ninth
        pug.ninth = pug.tenth 
        pug.tenth = None

    if index == 1:
        pug.second = pug.third
        pug.third = pug.fourth
        pug.fourth = pug.fifth
        pug.fifth = pug.sixth
        pug.sixth = pug.seventh
        pug.seventh = pug.eighth
        pug.eighth = pug.ninth
        pug.ninth = pug.tenth
        pug.tenth = None 

    if index == 2:
        pug.third = pug.fourth
        pug.fourth = pug.fifth
        pug.fifth = pug.sixth
        pug.sixth = pug.seventh
        pug.seventh = pug.eighth
        pug.eighth = pug.ninth
        pug.ninth = pug.tenth
        pug.tenth = None

    if index == 3:
        pug.fourth = pug.fifth
        pug.fifth = pug.sixth
        pug.sixth = pug.seventh
        pug.seventh = pug.eighth
        pug.eighth = pug.ninth
        pug.ninth = pug.tenth
        pug.tenth = None

    if index == 4: 
        pug.fifth = pug.sixth
        pug.sixth = pug.seventh
        pug.seventh = pug.eighth
        pug.eighth = pug.ninth
        pug.ninth = pug.tenth
        pug.tenth = None

    if index == 5:
        pug.sixth = pug.seventh
        pug.seventh = pug.eighth
        pug.eighth = pug.ninth
        pug.ninth = pug.tenth
        pug.tenth = None    

    if index == 6:
        pug.seventh = pug.eighth
        pug.eighth = pug.ninth
        pug.ninth = pug.tenth
        pug.tenth = None

    if index == 7:
        pug.eighth = pug.ninth
        pug.ninth = pug.tenth
        pug.tenth = None  

    if index == 8:
        pug.ninth = pug.tenth
        pug.tenth = None
    
    if index == 9:
        pug.tenth = None
    pug.save()
    return pug 

@api_view(['POST'])
def leave(request):
    if request.user.is_authenticated():
        incoming_message = json.loads(request.body.decode('utf-8'))
        pprint(incoming_message)
        for k,v  in incoming_message.items():
            if v == '.lva' or v == '.leave' or v == 'quit' or v == 'idle':
                player = Player.objects.get(user_id=k)
                pugs = Pug.objects.filter(leaveable=True) 
                full_response = [] 
                for pug in pugs:
                    mode = pug.mode
                    name = str(mode)
                    maximum = int(name[:1]) * 2
                    open_spaces = get_open(maximum, pug)
                    if player in open_spaces:
                        index = int(open_spaces.index(player))
                        if index == 0:
                            if len(open_spaces) == 1:
                                pug.first = None
                                pug.save()
                                full_response.append(str(pug.mode))
                            else:
                                pug_obj = handle_leaving(index, pug)
                                pug_obj.save()
                                full_response.append(str(pug.mode))
                        else:
                            pug_obj = handle_leaving(index, pug)
                            if pug_obj.red_captain == player:
                                pug_obj.red_captain = None
                            elif pug_obj.blue_captain == player:
                                pug_obj.blue_captain = None
                            pug_obj.isfull = False
                            pug_obj.save()
                            full_response.append(str(pug.mode))
                if len(full_response) < 1:
                    return HttpResponse(json.dumps({'None': 'None'})) 
                if v == 'quit':
                    response = '**' + player.username + '** left the following pug(s): ' + MODSEP.join(full_response) + ' because they quit.'
                elif v == 'idle':
                    response = '**' + player.username + '** left the following pug(s): ' + MODSEP.join(full_response) + ' because they were idle.' 
                else:
                    response = '**' + player.username + '** left the following pug(s): ' + MODSEP.join(full_response)  
                return HttpResponse(json.dumps({'message': response}))        
             
            else:
                 msg = v.split()
                 mode = msg[-1]
                 maximum = int(mode[:1]) * 2
                 player = Player.objects.get(user_id=k)
                 pugs = Pug.objects.filter(leaveable=True, mode=mode) 
                 for pug in pugs:
                     open_spaces = get_open(maximum, pug)
                     if player in open_spaces:
                         print(player)
                         index = int(open_spaces.index(player))
                         if index == 0:
                             if len(open_spaces) == 1: 
                                 pug.first = None
                                 print(pug.first)
                                 pug.save()
                                 return HttpResponse(json.dumps({'message': '**' + player.username + '** was removed from **' + str(pug.mode).upper() + '** because they left.'}))
                             else:
                                 pug_obj = handle_leaving(index, pug)        
                                 pug_obj.save()
                                 return HttpResponse(json.dumps({'message': '**' + player.username + '** was removed from **' + str(pug_obj.mode) + '** because they left.'}))
                         else:
                             pug_obj = handle_leaving(index, pug)
                             pug_obj.save()
                             return HttpResponse(json.dumps({'message': '**' + player.username + '** was removed from **' + str(pug_obj.mode) + '** because they left.'}))                    
                     else:
                         return HttpResponse(json.dumps({'message': player.username + ' is trying to leave a mode they did not join.'}))     
                
                
            
            
def return_players(pug_obj, count):
    pug_obj = pug_obj
    count = count
    #list of dicts 
    players = []
    print(count, pug_obj, 'hi')
    if count == 3:
        players.append({player_mention(pug_obj.first.user_id): pug_obj.first.tag})
        f = pug_obj.first
        f.activity = pug_obj.pug_id
        f.save()
        players.append({player_mention(pug_obj.second.user_id): pug_obj.second.tag})
        s = pug_obj.second
        s.activity = pug_obj.pug_id
        s.save()
        players.append({player_mention(pug_obj.third.user_id): pug_obj.third.tag})
        t = pug_obj.third
        t.activity = pug_obj.pug_id
        t.save()
        players.append({player_mention(pug_obj.fourth.user_id): pug_obj.fourth.tag})
        fth = pug_obj.fourth
        fth.activity = pug_obj.pug_id
        fth.save()

    if count == 5:
        players.append({player_mention(pug_obj.first.user_id): pug_obj.first.tag})
        players.append({player_mention(pug_obj.second.user_id): pug_obj.second.tag})
        players.append({player_mention(pug_obj.third.user_id): pug_obj.third.tag})
        players.append({player_mention(pug_obj.fourth.user_id): pug_obj.fourth.tag})
        players.append({player_mention(pug_obj.fifth.user_id): pug_obj.fifth.tag})
        players.append({player_mention(pug_obj.sixth.user_id): pug_obj.sixth.tag})                    
        f = pug_obj.first
        f.activity = pug_obj.pug_id
        f.save()
        s = pug_obj.second
        s.activity = pug_obj.pug_id
        s.save() 
        t = pug_obj.third
        t.activity = pug_obj.pug_id
        t.save()
        fth = pug_obj.fourth
        fth.activity = pug_obj.pug_id
        fth.save() 
        fif = pug_obj.fifth
        fif.activity = pug_obj.pug_id
        six = pug_obj.sixth
        six.activity = pug_obj.pug_id
        six.save()

    if count == 7:
        players.append({player_mention(pug_obj.first.user_id): pug_obj.first.tag})
        players.append({player_mention(pug_obj.second.user_id): pug_obj.second.tag})
        players.append({player_mention(pug_obj.third.user_id): pug_obj.third.tag})
        players.append({player_mention(pug_obj.fourth.user_id): pug_obj.fourth.tag})
        players.append({player_mention(pug_obj.fifth.user_id): pug_obj.fifth.tag})
        players.append({player_mention(pug_obj.sixth.user_id): pug_obj.sixth.tag})
        players.append({player_mention(pug_obj.seventh.user_id): pug_obj.seventh.tag})
        players.append({player_mention(pug_obj.eighth.user_id): pug_obj.eighth.tag})
        f = pug_obj.first
        f.activity = pug_obj.pug_id
        f.save()
        s = pug_obj.second
        s.activity = pug_obj.pug_id
        s.save()
        t = pug_obj.third
        t.activity = pug_obj.pug_id
        t.save()
        fth = pug_obj.fourth
        fth.activity = pug_obj.pug_id
        fth.save()
        fif = pug_obj.fifth
        fif.activity = pug_obj.pug_id
        six = pug_obj.sixth
        six.activity = pug_obj.pug_id
        six.save()
        sev = pug_obj.seventh
        sev.activity = pug_obj.pug_id
        sev.save()
        eig = pug_obj.eighth
        eig.activity = pug_obj.pug_id
        eig.save()
         
    if count == 9:                
        players.append({player_mention(pug_obj.first.user_id): pug_obj.first.tag})
        players.append({player_mention(pug_obj.second.user_id): pug_obj.second.tag})
        players.append({player_mention(pug_obj.third.user_id): pug_obj.third.tag})
        players.append({player_mention(pug_obj.fourth.user_id): pug_obj.fourth.tag})
        players.append({player_mention(pug_obj.fifth.user_id): pug_obj.fifth.tag})
        players.append({player_mention(pug_obj.sixth.user_id): pug_obj.sixth.tag})
        players.append({player_mention(pug_obj.seventh.user_id): pug_obj.seventh.tag})
        players.append({player_mention(pug_obj.eighth.user_id): pug_obj.eighth.tag})
        players.append({player_mention(pug_obj.ninth.user_id): pug_obj.ninth})
        players.append({player_mention(pug_obj.tenth.user_id): pug_obj.tenth})
        f = pug_obj.first
        f.activity = pug_obj.pug_id
        f.save()
        s = pug_obj.second
        s.activity = pug_obj.pug_id
        s.save()
        t = pug_obj.third
        t.activity = pug_obj.pug_id
        t.save()
        fth = pug_obj.fourth
        fth.activity = pug_obj.pug_id
        fth.save()
        fif = pug_obj.fifth
        fif.activity = pug_obj.pug_id
        six = pug_obj.sixth
        six.activity = pug_obj.pug_id
        six.save()
        sev = pug_obj.seventh
        sev.activity = pug_obj.pug_id
        sev.save()
        eig = pug_obj.eighth
        eig.activity = pug_obj.pug_id
        eig.save()
        nin = pug_obj.ninth
        nin.activity = pug_obj.pug_id
        nin.save()
        ten = pug_obj.tenth
        ten.activity = pug_obj.pug_id
        ten.save()

    return players
                

                       
@api_view(['POST'])
def picking(request):
    if request.user.is_authenticated():
        incoming_message = json.loads(request.body.decode('utf-8'))
        for k,v  in incoming_message.items():
            if k == 'captains':
                pug_id = v['pug_id']
                pug_obj = Pug.objects.get(pk=pug_id)
                red = Player.objects.get(pk=v['redcapt'])
                red.activity = pug_id
                red.save()
                pug_obj.red_captain = red
                blue = Player.objects.get(pk=v['bluecapt'])
                blue.activity = pug_id
                blue.save()
                pug_obj.blue_captain = blue
                pug_obj.save()
                return HttpResponse(json.dumps({'message': 'Awaiting captains response'}))                 
            elif k == 'verify':
                pug_id = v['pug_id']
                pug_obj = Pug.objects.get(pk=pug_id)
                not_here = []
                if pug_obj.red_here == False:
                    not_here.append(pug_obj.red_captain.user_id)
                if pug_obj.blue_here == False:
                    not_here.append(pug_obj.blue_captain.user_id)
                return HttpResponse(json.dumps({'absentees': not_here}))
                
         
@api_view(['POST'])
def here(request):       
    if request.user.is_authenticated():
        incoming_message = json.loads(request.body.decode('utf-8'))
        for k,v  in incoming_message.items():        
            user_id = k
            player = Player.objects.get(pk=user_id)
            pug_id = player.activity
            pug_obj = Pug.objects.get(pk=pug_id)
            if pug_obj.red_captain.user_id == user_id:
                pug_obj.red_here = True
                pug_obj.save()  
                if pug_obj.red_here == True and pug_obj.blue_here == True:
                    return HttpResponse(json.dumps({'message': 'Captains have checked in, leaving is no longer permitted.'}))
                    pug_obj.leaveable = False
                    pug_obj.save()
                else:
                    return HttpResponse(json.dumps({'message': 'Red captain has checked in.'})) 
            if pug_obj.blue_captain.user_id == user_id:  
                pug_obj.blue_here = True
                pug_obj.save()
                if pug_obj.red_here == True and pug_obj.blue_here == True: 
                    return HttpResponse(json.dumps({'message': 'Captains have checked in, leaving is no longer permitted.'}))
                    pug_obj.leaveable = False
                    pug_obj.save()
                else:
                    return HttpResponse(json.dumps({'message': 'Blue captain has checked in.'}))
           

@api_view(['POST'])
def captain(request):
    if request.user.is_authenticated():
        incoming_message = json.loads(request.body.decode('utf-8'))
        for k,v  in incoming_message.items(): 
            user_id = k
            volunteer = Players.objects.get(pk=user_id)
            pug_id = volunteer.activity
            pug_obj = Pug.objects.get(pk=pug_id) 
            if pug_obj.red_captain == None:
                pug_obj.red_captain = volunteer 
                pug_obj.save()
                return HttpResponse(json.dumps({'message': '{} is captain for red.'.format(red_volunteer.username)})) 
            if pug_obj.blue_captain == None:
                if volunteer is not pug_obj.red_captain:
                    pug_obj.blue_captain = volunteer
                    pug_obj.save() 
                    return HttpResponse(json.dumps({'message': '{} is captain for red.'.format(blue_volunteer.username)}))  

@api_view(['POST'])
def check_captains(request):
    if request.user.is_authenticated():
        incoming_message = json.loads(request.body.decode('utf-8'))
        for k,v  in incoming_message.items(): 
            pug_id = v
            pug_obj = Pug.objects.get(pk=pug_id)
            if pug_obj.red_captain is not None and pug_obj.blue_captain is not None:
                return HttpResponse(json.dumps({'skip': {'red_capt': pug_obj.red_captain, 'blue_capt': pug_obj.blue_captain}}))
            else:
                return HttpResponse(json.dumps({'message': 'random'}))
           

@api_view(['POST'])
def join(request):
    if request.user.is_authenticated():
        incoming_message = json.loads(request.body.decode('utf-8'))
        pprint(incoming_message)
        for k,v  in incoming_message.items():
            if k: 
                msg = v 
                msg = msg.split()
                try:  
                    string_match = msg[-1]
                    pug = short_modes[string_match.lower()]
                    maximum = int(pug[:1]) * 2 
                except: 
                    pug = msg[-1]
                    maximum = int(pug[:1]) * 2
                pug_obj = Pug.objects.get(mode__name__icontains=pug, isfull=False)
                open_spaces = get_open(maximum, pug_obj)
                count = len(open_spaces)
                try: 
                    player_obj = Player.objects.get(user_id=k)
                except: 
                    return HttpResponse(json.dumps({'message': 'Please use the .register command before joining a pug.'}))
                for player in open_spaces:
                    if str(player.user_id) == str(player_obj.user_id):
                        return HttpResponse(json.dumps({'message': 'You have already joined this pug.'}))
                else:
                    if count < maximum:
                        if count == 0:
                            pug_obj.first = player_obj
                            pug_obj.save()
                            open_spaces.append(player_obj)
                        elif count == 1:
                            pug_obj.second = player_obj
                            if maximum == 2:
                                pug_obj.isfull = True
                                pug_obj.save() 
                            else:
                                pug_obj.save() 
                            open_spaces.append(player_obj) 
                        elif count == 2:
                            pug_obj.third = player_obj
                            pug_obj.save()   
                            open_spaces.append(player_obj)
                        elif count == 3:
                            pug_obj.fourth = player_obj
                            if maximum == 4:
                                pug_obj.isfull = True
                                pug_obj.save()
                            else:
                                pug_obj.save()
                            open_spaces.append(player_obj)
                        elif count == 4:
                            pug_obj.fifth = player_obj
                            pug_obj.save() 
                            open_spaces.append(player_obj)
                        elif count == 5:
                            pug_obj.sixth = player_obj
                            if maximum == 6:
                                pug_obj.isfull = True
                                pug_obj.save()
                            else: 
                                pug_obj.save()
                            open_spaces.append(player_obj)
                        elif count == 6:
                            pug_obj.seventh = player_obj
                            pug_obj.save()
                            open_spaces.append(player_obj)
                        elif count == 7:
                            pug_obj.eighth = player_obj
                            if maximum == 8:
                                pug_obj.isfull = True
                                pug_obj.save()
                            else:
                                pug_obj.save()
                            open_spaces.append(player_obj)  
                        elif count == 8:
                            pug_obj.ninth = player_obj
                            pug_obj.save()
                            open_spaces.append(player_obj) 
                        elif count == 9:
                            pug_obj.tenth = player_obj
                            pug_obj.isfull = True
                            open_spaces.append(player_obj)
                            pug_obj.save()
                        if pug_obj.isfull == True:
                            if pug_obj.mode.name.upper() == '1V1DUEL':
                                return HttpResponse(json.dumps({'message': pug_obj.pug_id + ' has filled.'}))
                            else:
                                players = return_players(pug_obj, count)  
                                return HttpResponse(json.dumps({'filled': {'count': count, 'pug': pug_obj.pug_id, 'mode': pug_obj.mode.name, 'players': players}}))
                        else:
                            players = get_pool(open_spaces)
                            print(players)
                            return HttpResponse(json.dumps({'message': '**' + str(pug_obj.mode).upper() + ': ' + ' [' + str(len(open_spaces)) + '/' + str(maximum) + ']**\n' + players}))  


@api_view(['POST'])
def get_map(request):
    if request.user.is_authenticated():
        incoming_message = json.loads(request.body.decode('utf-8'))
        pprint(incoming_message)
        for k,v  in incoming_message.items():
            if k == 'map':
                msg = v
                msg_list = msg.split()
                map_name = msg_list[1]
                print(map_name)
                try:
                    map_obj = Map.objects.get(name__icontains=map_name)
                    map_link = map_obj.link
                    return HttpResponse(json.dumps({'message': map_link})) 
                except:
                    return HttpResponse(json.dumps({'message': 'Map not found: Check spelling or ask admin to add it!'}))
                         

@api_view(['POST'])
def get_mutator(request):
    if request.user.is_authenticated():
        incoming_message = json.loads(request.body.decode('utf-8'))
        pprint(incoming_message)
        for k,v  in incoming_message.items():
            if k == 'mutator':
                msg = v
                msg_list = msg.split()
                mutator_name = msg_list[1]
                try:
                    mut_obj = Mutator.objects.get(name__icontains=mutator_name)
                    mut_link = mut_obj.link
                    return HttpResponse(json.dumps({'message': mut_link}))
                except:
                    return HttpResponse(json.dumps({'message': 'Mutator not found: Check spelling or ask admin to add it!'}))


@api_view(['POST'])
def list_all(request):
    if request.user.is_authenticated():
        incoming_message = json.loads(request.body.decode('utf-8'))
        pprint(incoming_message)
        for key,value  in incoming_message.items():       
            if key == 'list_all':
                msg = value  
                pugs_query = Pug.objects.filter(leaveable='True').values_list('mode', flat=True)
                print(pugs_query)
                pugs_list = []
                for i, c in enumerate(pugs_query):
                    pugs_list.append(c)
                mode_statuses = {}
                for pug in pugs_list:
                    maximum = int(pug[:1]) * 2
                    pug_obj = Pug.objects.get(mode=pug, leaveable=True)
                    open_spaces = get_open(maximum, pug_obj)
                    count = len(open_spaces) 
                    ratio = str(count) + '/' + str(maximum)
                    mode_statuses[pug] = ratio
                    pug_response = []
                    for k,v in mode_statuses.items():
                        elem = '**' + k.upper() + ' [' +v + ']** ' + MODSEP
                        pug_response.append(elem)
                    if pug_response[-1] == MODSEP:
                        pug_response.pop()
                    resp = ' '.join(pug_response) 
                
                return HttpResponse(json.dumps({'message_general': resp}))    
                    
                         

@api_view(['POST'])
def listing(request):
    if request.user.is_authenticated():
        incoming_message = json.loads(request.body.decode('utf-8'))
        pprint(incoming_message)
        for key,value  in incoming_message.items():
            if key:
               message = value
               try:
                   msg  = message.split()
                   orig_message = msg[1]
               except:
                   pass
               orig_message = str(orig_message)
               gametype = str(orig_message[:1])
               maximum = int(gametype) * 2
               message = orig_message[3:]
               pugs_query = Pug.objects.values_list('mode', flat=True)
               pugs_list = [] 
               for i, c in enumerate(pugs_query):
                   pugs_list.append(c.upper())
               if orig_message.upper() in pugs_list:
                   pug_obj = Pug.objects.get(mode__name__icontains=orig_message, leaveable=True)
                   open_spaces = get_open(maximum, pug_obj)
                   count = len(open_spaces)
                   needed = str(int(maximum)-int(count))
                   if count:
                       players = get_pool(open_spaces)
                       if msg[0] == '.ls' or msg[0] == '.list':
                           return HttpResponse(json.dumps({'message_specific': '**' + str(pug_obj.mode).upper() + ': ' + ' [' + str(count) + '/' + str(maximum) + ']**\n' + players}))
                       elif msg[0] == '.pro' or msg[0] == '.promote':
                           return HttpResponse(json.dumps({'message_specific': '** @here Only {} needed for '.format(needed) + str(pug_obj.mode).upper() + '**' })) 
                   else:
                       if msg[0] == '.ls' or msg[0] == '.list': 
                           return HttpResponse(json.dumps({'message_specific': '**' + str(pug_obj.mode).upper() +  ': ' + '[0/' + str(maximum) + ']**'}))
                       elif msg[0] == '.pro' or msg[0] == '.promote':
                           return HttpResponse(json.dumps({'message_specific': '**@here Only {} needed for '.format(needed) + str(pug_obj.mode).upper() + '**' })) 
               else:
                   return HttpResponse(json.dumps({'message_specific': 'Check your syntax friend, it seems you entered a nonexistent mode.'}))   



