from discord.ext import commands
import aiohttp
import json
import discord
import asyncio
import duckduckgo
import random

PLASEP = '\N{SMALL ORANGE DIAMOND}'
MODSEP = '\N{SMALL BLUE DIAMOND}'
OKMSG = '\N{OK HAND SIGN}'
BASEURL = 'https://ut4pugs.us'
#BASEURL = 'http://localhost:8080'

class register:
    """Unreal Tournament 4 related commands"""
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()       
        self.token = 'Token ' 
        self.headers = {'content-type': 'application/json', 'Authorization': self.token}

    @commands.group(pass_context=True, no_pm=False, aliases=['r'])
    async def register(self,ctx):
        self.user_name = ctx.message.author
        self.user_msg = ctx.message.content
        self.user_id = ctx.message.author.id
        self.url = BASEURL + '/discord'
        self.payload = {'registration': {'username': '{}'.format(self.user_name), 'user_id': str(self.user_id), 'role': ctx.message.author.top_role.name, 'message': str(self.user_msg)}}
        async with self.session.post(self.url, data=json.dumps(self.payload), headers=self.headers) as resp:
            try:
                response = await resp.json()
                for k,v in response.items():
                    if k == 'message':
                        await self.bot.say(response['message'])
            except:
                response = await resp.text()
                f = open('loggg', 'w')
                f.write(response)
                f.close()
                await self.bot.say("Sorry, I failed to register you!")
            print(response)
        await resp.release()
    
    @commands.group(pass_context=True, no_pm=False)
    async def search(self,ctx):
        self.user_name = ctx.message.author
        self.user_msg = ctx.message.content
        self.user_id = ctx.message.author.id
        msg = self.user_msg
        term = msg[8:]
        response = duckduckgo.get_zci(term)
        await self.bot.say(response)
   
    @commands.group(pass_context=True, no_pm=True, aliases=['t'])
    async def tag(self,ctx):
        self.user_name = ctx.message.author
        self.user_msg = ctx.message.content
        self.user_id = ctx.message.author.id
        self.url = BASEURL + '/tag'
        self.payload = {self.user_id: self.user_msg}
        async with self.session.post(self.url, data=json.dumps(self.payload), headers=self.headers) as resp:
            response = await resp.json()
            print(response)
            for k,v in response.items():
                if k == 'message':
                    await self.bot.say(response['message'])
        await resp.release() 
       
    @commands.group(pass_context=True, no_pm=True, aliases=['notag'])
    async def deltag(self,ctx):
        self.user_name = ctx.message.author
        self.user_msg = ctx.message.content
        self.user_id = ctx.message.author.id
        self.url = BASEURL + '/tag'
        self.payload = {self.user_id: self.user_msg}
        async with self.session.post(self.url, data=json.dumps(self.payload), headers=self.headers) as resp:
            response = await resp.json()
            print(response)
            for k,v in response.items():
                if k == 'message':
                    await self.bot.say(response['message'])
        await resp.release() 
    
    @commands.group(pass_context=True, no_pm=True)
    async def nomic(self,ctx):
        self.user_name = ctx.message.author
        self.user_msg = ctx.message.content
        self.user_id = ctx.message.author.id
        self.url = BASEURL + '/tag'
        self.payload = {self.user_id: self.user_msg}
        async with self.session.post(self.url, data=json.dumps(self.payload), headers=self.headers) as resp:
            response = await resp.json()
            print(response)
            for k,v in response.items():
                if k == 'message':
                    await self.bot.say(response['message'])
        await resp.release()

    async def on_member_update(self, before, after):
        if after.status is discord.Status.offline: 
            self.url = BASEURL + '/leave'
            self.payload = {after.id: 'quit'}
            async with self.session.post(self.url, data=json.dumps(self.payload), headers=self.headers) as resp:
                response = await resp.json()
                for k,v in response.items():
                    if k == 'message':
                        await self.bot.send_message(after.server, response['message'])
            await resp.release()

        elif after.game.type is not None:
                if after.game.type == 1:
                    response = '<@{}>'.format(str(after.id)) +  ' is now live streaming: {}'.format(str(after.game) + '\n{}'.format(after.game.url))
                    await self.bot.send_message(after.server, response)
  
    @commands.group(pass_context=True, no_pm=False)
    async def map(self,ctx):
        self.user_name = ctx.message.author
        self.user_msg = ctx.message.content
        self.user_id = ctx.message.author.id
        self.url = BASEURL + '/map'
        self.payload = {'map': self.user_msg}
        async with self.session.post(self.url, data=json.dumps(self.payload), headers=self.headers) as resp:
            response = await resp.json()
            print(response)
            for k,v in response.items():
                if k == 'message':
                    await self.bot.say(response['message'])
        await resp.release()     

    @commands.group(pass_context=True, no_pm=False)
    async def maps(self,ctx):
        self.user_name = ctx.message.author
        self.user_msg = ctx.message.content
        self.user_id = ctx.message.author.id
        self.url = BASEURL + '/list_maps'
        self.payload = {'maps': self.user_msg}
        async with self.session.post(self.url, data=json.dumps(self.payload), headers=self.headers) as resp:
            response = await resp.json()
            print(response)
            for k,v in response.items():
                if k == 'message':
                    await self.bot.say(response['message'])
        await resp.release() 

    @commands.group(pass_context=True, no_pm=False)
    async def mutator(self,ctx):
        self.user_name = ctx.message.author
        self.user_msg = ctx.message.content
        self.user_id = ctx.message.author.id
        self.url = BASEURL + '/get_mutator'
        self.payload = {'mutator': self.user_msg}
        async with self.session.post(self.url, data=json.dumps(self.payload), headers=self.headers) as resp:
            response = await resp.json()
            print(response)
            for k,v in response.items():
                if k == 'message':
                    await self.bot.say(response['message'])
        await resp.release()  

    @commands.group(pass_context=True, no_pm=True, aliases=['ls'])
    async def list(self,ctx):
        self.user_name = ctx.message.author
        self.user_msg = ctx.message.content
        self.user_id = ctx.message.author.id
        print(self.user_msg)
        if len(self.user_msg) < 6:
            self.url = BASEURL + '/pug_all'
            self.payload = {'list_all': self.user_msg}
        else:
            self.url = BASEURL + '/list_mode' 
            self.payload = {'list_mode': self.user_msg}   
        async with self.session.post(self.url, data=json.dumps(self.payload), headers=self.headers) as resp: 
            response = await resp.json() 
            print(response)
            for k,v in response.items():
                if k == 'message_specific':
                    await self.bot.say(response['message_specific'] + PLASEP)      
                elif k == 'message_general':
                    await self.bot.say(response['message_general'])
        await resp.release()

    async def handle_response(self,response):
            for k,v in response.items():
                if k == 'filled':
           
                    self.count = int(v['count'])
                    #self.players = []
                    self.mode = v['mode']
                    self.pug_id = v['pug']
                    self.players_list = v['players'] 
                    print(self.players_list) 
                    self.players = []
                    for player_dict in self.players_list:
                        for player, tag in player_dict.items():
                            self.players.append(player)                  
                    return self.players, self.pug_id, self.mode, self.players_list                               

    async def picking(self, players, pug_id, mode, channel, players_list):
        print(pug_id, mode)
        content = '`Random captains in {:2d} seconds`'
        randcaptsecs = 10
        message = await self.bot.send_message(channel, content.format(randcaptsecs))
        for i in range(randcaptsecs - 1, -1, -1):
            try:
                await asyncio.sleep(1)
                if i % 5 == 0 or i < 10:
                    message = await self.bot.edit_message(message, content.format(i))
            except asyncio.CancelledError:
                return await self.bot.edit_message(message, '`Random captains cancelled`') 
        candidates = []
        for player_dict in players_list:
            for player, tag in player_dict.items():
                if str(tag) == 'nocapt':
                    pass 
                else:
                    candidates.append(player)
        redrand = len(candidates) - 1
        redcapt = candidates[random.randint(0, redrand)]
        candidates.remove(redcapt) 
        bluerand = len(candidates) - 1
        bluecapt = candidates[random.randint(0, bluerand)]
        picks = players
        picks.remove(redcapt)
        picks.remove(bluecapt)
        formatted_picks = []
        redcapt_json = redcapt[2:]
        redcapt_json = redcapt_json[:-1]
        bluecapt_json = bluecapt[2:]
        bluecapt_json = bluecapt_json[:-1]
        print(redcapt_json, bluecapt_json)

        for item in picks:
            number = int(picks.index(item)) + 1
            formatted_picks.append('**' +str(number) + ')** {}'.format(item))

        formatted_picks_str = ' '.join(formatted_picks)
        self.url = BASEURL + '/picking'
        self.payload = {'captains': {'redcapt': redcapt_json, 'bluecapt': bluecapt_json, 'pug_id': pug_id}}
        async with self.session.post(self.url, data=json.dumps(self.payload), headers=self.headers) as resp:
            response = await resp.text()
            r = open('captain_response', 'w')
            r.write(response)
            r.close()
        await resp.release()

        await self.bot.send_message(channel, '{} is captain for the **Red team**'.format(redcapt) + '\n {} is captain for the **Blue team**'.format(bluecapt) + '\n **Type .here** to prevent being kicked.' + '\n {} to pick'.format(redcapt) + '\n {}'.format(formatted_picks_str))
        await asyncio.sleep(45)

        attendance_payload = {'verify': {'redcapt': redcapt_json, 'bluecapt': bluecapt_json, 'pug_id': pug_id}}
        async with self.session.post(self.url, data=json.dumps(attendance_payload), headers=self.headers) as attend_resp: 
            attend_response = await attend_resp.json()

            for k, v in attend_response.items():
                if len(v) > 0:  
                    for player_id in v:
                        print(player_id)
                        url = BASEURL + '/leave'   
                        idle_payload = {player_id: 'idle'}

                        async with self.session.post(url, data=json.dumps(idle_payload), headers=self.headers) as idle:
                            idle_resp = await idle.json() 
                            for k,v in idle_resp.items():
                                if k == 'message':
                                    await self.bot.send_message(channel, v)
                        await idle.release()

        await attend_resp.release()  

    @commands.group(pass_context=True, no_pm=True, aliases=['p'])
    async def pick(self,ctx):
        self.user_name = ctx.message.author
        self.user_msg = ctx.message.content
        self.channel = ctx.message.channel
        self.user_id = ctx.message.author.id
        self.url = BASEURL + '/picking'
        self.payload = {self.user_id: self.user_msg}
        async with self.session.post(self.url, data=json.dumps(self.payload), headers=self.headers) as resp:
            response = await resp.json() 
        

    @commands.group(pass_context=True, no_pm=True, aliases=['j'])
    async def join(self,ctx):
        self.user_name = ctx.message.author
        self.user_msg = ctx.message.content
        self.channel = ctx.message.channel
        print(self.channel)
        self.user_id = ctx.message.author.id   
        self.url = BASEURL + '/join'
        self.payload = {self.user_id: self.user_msg}
        async with self.session.post(self.url, data=json.dumps(self.payload), headers=self.headers) as resp:
            response = await resp.json()
            for k,v in response.items():
                if k == 'message':
                    await self.bot.say(v)
                else:
                    self.players, self.pug_id, self.mode, self.players_list = await self.handle_response(response) 
                    self.players_str = ' '.join(self.players)
                    await self.bot.say('**' + self.mode + '** has been filled. \n ' + self.players_str)
                    timer = await self.picking(self.players, self.pug_id, self.mode, self.channel, self.players_list)
        await resp.release()  

    @commands.group(pass_context=True, no_pm=True, aliases=['l'])
    async def leave(self,ctx):
        self.user_name = ctx.message.author
        self.user_msg = ctx.message.content
        self.user_id = ctx.message.author.id
        self.url = BASEURL + '/leave'
        self.payload = {self.user_id: self.user_msg}
        async with self.session.post(self.url, data=json.dumps(self.payload), headers=self.headers) as resp:
            response = await resp.json()
            print(response)
            for k,v in response.items():
                if k == 'message':
                    await self.bot.say(response['message'])

        await resp.release() 
 
    @commands.group(pass_context=True, no_pm=True, aliases=['pro'])
    async def promote(self,ctx):
        self.user_name = ctx.message.author
        self.user_msg = ctx.message.content
        self.user_id = ctx.message.author.id
        self.url = BASEURL + '/list_mode'
        self.payload = {'list_mode': self.user_msg}
        async with self.session.post(self.url, data=json.dumps(self.payload), headers=self.headers) as resp:
            response = await resp.json()
            for k,v in response.items():
                if k == 'message_specific':
                    await self.bot.say('@here '+ response['message_specific'])

        await resp.release()
    
    @commands.group(pass_context=True, no_pm=True)
    async def lva(self,ctx):
        self.user_name = ctx.message.author
        self.user_msg = ctx.message.content
        self.user_id = ctx.message.author.id
        self.url = BASEURL + '/leave'
        self.payload = {self.user_id: self.user_msg}
        async with self.session.post(self.url, data=json.dumps(self.payload), headers=self.headers) as resp:
            response = await resp.json()
            print(response)
            for k,v in response.items():
                if k == 'message':
                    await self.bot.say(response['message'])

        await resp.release() 

    @commands.group(pass_context=True, no_pm=False, description='Usage: .setid [username] {EpicID}\nExample: .setid 1bc258e3a2194fa88fac3d06bc6da28a\nAssociates an Epic ID with a discord user. Allows for more informative print-outs for .stats.')
    async def setid(self,ctx):
        self.user_name = ctx.message.author
        self.user_msg = ctx.message.content
        self.user_id = ctx.message.author.id
        self.url = BASEURL + '/setid'
        self.payload = {self.user_id: self.user_msg}
        async with self.session.post(self.url, data=json.dumps(self.payload), headers=self.headers) as resp:
            response = await resp.json()
            print(response)
            for k,v in response.items():
                if k == 'message':
                    await self.bot.say(response['message'])
        await resp.release()     
  
    @register.command()
    async def changelog(self):
        await self.bot.say('https://wiki.unrealengine.com/Version_Notes')

def setup(bot):
    bot.add_cog(register(bot))
