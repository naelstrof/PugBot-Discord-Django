import asyncio
import collections
import collections.abc
import contextlib
import functools
import heapq
import itertools
import random
import re
import shelve
import os

from discord.ext import commands
import discord
import pendulum

PICKMODES = [
        [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        [0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0],
        [0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        [0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0]]
MAXPLAYERS = len(PICKMODES[0]) + 2
MAXTAGLENGTH = 10
PLASEP = '\N{SMALL ORANGE DIAMOND}'
MODSEP = '\N{SMALL BLUE DIAMOND}'
OKMSG = '\N{OK HAND SIGN}'

DISCORD_MD_CHARS = '*~_`'
DISCORD_MD_ESCAPE_RE = re.compile('[{}]'.format(DISCORD_MD_CHARS))
DISCORD_MD_ESCAPE_DICT = {c: '\\' + c for c in DISCORD_MD_CHARS}

def discord_md_escape(value):
    return DISCORD_MD_ESCAPE_RE.sub(lambda match: DISCORD_MD_ESCAPE_DICT[match.group(0)], value)

def display_name(member):
    return discord_md_escape(member.display_name)


class Mod(collections.abc.MutableSet):
    """Maintains the state for players in a PUG"""
    def __init__(self, name, desc, maxplayers):
        self.name = name
        self.desc = desc
        self.maxplayers = maxplayers
        self.players = []
        self.maps = set()

    def __contains__(self, member):
        return member in self.players

    def __iter__(self):
        return iter(self.players)

    def __len__(self):
        return len(self.players)

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['players']
        return state

    def __setstate__(self, state):
        self.__dict__ = state
        self.players = []

    @property
    def brief(self):
        return '**{}** [{}/{}]'.format(self.name, len(self), self.maxplayers)

    @property
    def full(self):
        return len(self) == self.maxplayers

    @property
    def needed(self):
        return self.maxplayers - len(self)

    @property
    def teamgame(self):
        return False

    def add(self, member):
        if member not in self and not self.full:
            self.players.append(member)
            return True

    def discard(self, member):
        if member in self:
            self.players.remove(member)
            return True

    def fullreset(self):
        self.players = []


class Team(list):
    def __init__(self):
        super().__init__()

    @property
    def captain(self):
        return self[0]


class TeamMod(Mod):
    def __init__(self, name, desc, maxplayers, pickmode):
        super().__init__(name, desc, maxplayers)
        self.teams = (Team(), Team())
        self.pickmode = pickmode
        self.task = None
        self.here = [True, True]

    def __getstate__(self):
        state = super().__getstate__()
        del state['teams']
        del state['task']
        del state['here']
        return state

    def __setstate__(self, state):
        super().__setstate__(state)
        self.teams = (Team(), Team())
        self.task = None
        self.here = [True, True]

    @property
    def teamgame(self):
        return True

    @property
    def hascaptains(self):
        return self.red and self.blue

    @property
    def team(self):
        return PICKMODES[self.pickmode][len(self.red) + len(self.blue) - 2]

    @property
    def captain(self):
        return self.teams[self.team].captain if self.hascaptains else None

    @property
    def teamsready(self):
        return len(self.red) + len(self.blue) == self.maxplayers

    @property
    def red(self):
        return self.teams[0]

    @property
    def blue(self):
        return self.teams[1]

    def __contains__(self, member):
        return member in (self.players + self.red + self.blue)

    def discard(self, member):
        if member in self:
            if self.red:
                self.reset()
            if self.task:
                self.task.cancel()
            self.players.remove(member)
            return True

    def reset(self):
        if self.red:
            self.players += self.red + self.blue
            self.players = list(filter(None, self.players))
            self.red.clear()
            self.blue.clear()
            self.here = [True, True]
            if self.task:
                self.task.cancel()
            return True
        return False

    def fullreset(self):
        self.players = []
        self.red.clear()
        self.blue.clear()
        self.here = [True, True]
        if self.task:
            self.task.cancel()

    def setcaptain(self, player):
        if player in self.players and self.full:
            index = self.players.index(player)
            if not self.red:
                self.red.append(player)
            elif not self.blue:
                self.blue.append(player)
            else:
                return False
            self.players[index] = None
            return True
        return False

    def pick(self, captain, index):
        if captain == self.captain:
            self.here[self.team] = True
            if all(self.here) and self.task:
                self.task.cancel()

            if index < 0 or index >= len(self) or not self.players[index]:
                return False

            player = self.players[index]
            self.teams[self.team].append(player)
            self.players[index] = None

            # check to see if next team has any choice and move them
            index = len(self.red) + len(self.blue) - 2
            remaining = PICKMODES[self.pickmode][index:self.maxplayers - 2]
            if len(set(remaining)) == 1:
                self.teams[remaining[0]].extend(p for p in self.players if p)
            return True


class PUGChannel(collections.abc.MutableMapping):
    def __init__(self):
        self.active = True
        self.server_name = ''
        self.randcaptaintimer = 20
        self.idlecaptaintimer = 60
        self.mods = collections.OrderedDict()

    def __setitem__(self, key: str, mod: Mod):
        self.mods[key.lower()] = mod

    def __getitem__(self, key: str):
        return self.mods[key.lower()]

    def __delitem__(self, key: str):
        del self.mods[key.lower()]

    def __iter__(self):
        return iter(self.mods)

    def __len__(self):
        return len(self.mods)

    @property
    def team_mods(self):
        return (mod for mod in self.values() if mod.teamgame)


class ModStats:
    def __init__(self):
        self.total = 0
        self.timestamp = pendulum.now().timestamp
        self.last_timestamp = self.timestamp

    @property
    def last(self):
        return HistoryItem(self.last_timestamp)

    @property
    def daily(self):
        days = (pendulum.now() - pendulum.from_timestamp(self.timestamp)).days
        return self.total / (days + 1)

    def update(self, timestamp):
        self.total += 1
        self.last_timestamp = timestamp
        return self


class TeamStats(ModStats):
    def __init__(self):
        super().__init__()
        self.picks = 0
        self.captain = 0

    @property
    def average_pick(self):
        total = self.total - self.captain
        return 0 if total == 0 else self.picks / total

    def update(self, timestamp, pick):
        self.picks += pick
        self.captain += 0 if pick else 1
        return super().update(timestamp)


class HistoryItem:
    def __init__(self, timestamp, players=None, modid=None):
        self.timestamp = timestamp
        self.players = '\n' + players if players else ''
        self.modid = modid

    def __str__(self):
        name = '**{}** '.format(self.modid) if self.modid else ''
        when = (pendulum.now() - pendulum.from_timestamp(self.timestamp)).in_words()
        return '{}[{} ago]{}'.format(name, when, self.players)

    def __lt__(self, other):
        return self.timestamp < other.timestamp


class PUGStats:
    def __init__(self):
        self.total = 0
        self.timestamp = pendulum.now().timestamp
        self.history = collections.deque(maxlen=3)

    @property
    def daily(self):
        days = (pendulum.now() - pendulum.from_timestamp(self.timestamp)).days
        return self.total / (days + 1)

    @property
    def last_timestamp(self):
        return self.last.timestamp

    @property
    def last(self):
        return HistoryItem(*self.history[-1])

    @property
    def lastt(self):
        return HistoryItem(*self.history[min(0, len(self.history) - 1)])

    @property
    def lasttt(self):
        return HistoryItem(*self.history[0])

    def update(self, timestamp, players):
        self.total += 1
        self.history.append((timestamp, players))
        return self


class Stats(collections.abc.MutableMapping):
    def __init__(self):
        self.data = dict()

    def __getitem__(self, mod):
        return self.data[mod.name]

    def __setitem__(self, mod, value):
        self.data[mod.name] = value

    def __delitem__(self, mod):
        del self.data[mod.name]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def items(self):
        return self.data.items()

    def values(self):
        return self.data.values()

    @property
    def timestamp(self):
        return min(self.values(), key=lambda x: x.timestamp).timestamp

    @property
    def total(self):
        return sum(mod.total for mod in self.values())

    @property
    def daily(self):
        days = (pendulum.now() - pendulum.from_timestamp(self.timestamp)).days
        return self.total / (days + 1)

    @property
    def last(self):
        modid, stats = max(self.items(), key=lambda x: x[1].last)
        last = stats.last
        last.modid = modid
        return last


class ChannelStats(Stats):
    """Stores the PUG stats for the channel"""
    @property
    def history(self):
        for mod, stats in self.items():
            for timestamp, players in stats.history:
                yield HistoryItem(timestamp, players, modid=mod)

    @property
    def lastt(self):
        history = sorted(self.history, reverse=True)
        return history[min(1, len(history) - 1)]

    @property
    def lasttt(self):
        history = sorted(self.history, reverse=True)
        return history[min(2, len(history) - 1)]


class MemberStats(Stats):
    """Stores the member's stats for a channel"""
    @property
    def team_stats(self):
        return (mod for mod in self.values() if isinstance(mod, TeamStats))

    @property
    def captain(self):
        return sum(mod.captain for mod in self.team_stats)

    @property
    def average_pick(self):
        total, picks = 0, 0
        for mod in self.team_stats:
            total += mod.total - mod.captain
            picks += mod.picks
        return 0 if total == 0 else picks / total


class ChannelStatsView:
    def __init__(self, db, channel):
        self.db = db
        self.channel = channel

    def __iter__(self):
        for member_id, stats in self.db.items():
            member = self.channel.server.get_member(member_id)
            if member and not member.bot and self.channel.id in stats:
                yield member, stats[self.channel.id]


class ModStatsView(ChannelStatsView):
    def __init__(self, db, channel, mod):
        super().__init__(db, channel)
        self.mod = mod

    def __iter__(self):
        return ((member, stats[self.mod]) for member, stats in super().__iter__() if self.mod in stats)


class StatsDB(collections.abc.MutableMapping):
    def __init__(self, db, channel, mod):
        self.db = db
        self.channel = channel
        self.mod = mod

    def __getitem__(self, member):
        stats = self.db[member.id]
        if self.channel.id in stats:
            if self.mod is None:
                return stats[self.channel.id]
            elif self.mod in stats[self.channel.id]:
                return stats[self.channel.id][self.mod]
        raise KeyError

    def __setitem__(self, member, value):
        stats = self.db.get(member.id, dict())
        cls = ChannelStats if member.bot else MemberStats
        channel_stats = stats.setdefault(self.channel.id, cls())
        channel_stats[self.mod] = value
        self.db[member.id] = stats

    def __delitem__(self, member):
        del self.db[member.id]

    def __len__(self):
        return len(self.db)

    def __iter__(self):
        if self.mod is None:
            return iter(ChannelStatsView(self.db, self.channel))
        return iter(ModStatsView(self.db, self.channel, self.mod))


@contextlib.contextmanager
def stats_open(channel, mod, flag='c', writeback=False):
    with shelve.open('data/stats', flag=flag, writeback=writeback) as db:
        yield StatsDB(db, channel, mod)

def clamp(n, low, high):
    return max(low, min(n, high))

def ispugchannel(ctx):
    pugchannel = ctx.bot.get_cog('PUG').channels.get(ctx.message.channel)
    return pugchannel is not None and pugchannel.active


class ModConverter(commands.Converter):
    def convert(self):
        mod = self.ctx.cog.channels[self.ctx.message.channel].get(self.argument)
        if mod is None:
            raise commands.errors.BadArgument('PUG "{}" not found'.format(self.argument))
        return mod


class TeamModConverter(ModConverter):
    def convert(self):
        mod = super().convert()
        if not mod.teamgame:
            raise commands.errors.BadArgument('"{}" is not a team PUG'.format(mod.name))
        return mod


class PUG:
    """PUG related commands"""
    def __init__(self, bot):
        self.bot = bot
        self.last_teams = dict()
        self.tags = collections.defaultdict(lambda: collections.defaultdict(str))
        self.nocaptains = collections.defaultdict(set)
        self.channels = dict()

    async def on_ready(self):
        """Load PUGChannels"""
        with shelve.open('data/pug') as db:
            for (channel_id, pugchannel) in list(db.items()):
                channel = self.bot.get_channel(channel_id)
                if channel is not None:
                    self.channels[channel] = pugchannel
                else:
                    del db[channel_id]

    @commands.command(pass_context=True, no_pm=True)
    @commands.has_permissions(manage_server=True)
    async def pugbot(self, ctx, enable: bool):
        """Enables/Disables PUG commands in the channel"""
        pugchannel = self.channels.get(ctx.message.channel)
        if pugchannel is None:
            if not enable:
                return
            self.channels[ctx.message.channel] = PUGChannel()
        else:
            if pugchannel.active == enable:
                return
            pugchannel.active = enable
        status = ' enabled' if enable else ' disabled'
        await self.bot.say('PUG commands have been' + status)
        with shelve.open('data/pug', 'w') as db:
            db[ctx.message.channel.id] = self.channels[ctx.message.channel]

    @commands.command(no_pm=True, aliases=['pickorders'])
    @commands.check(ispugchannel)
    async def pickmodes(self):
        """Displays the available pickmodes"""
        await self.bot.say('```{}```'.format(
            '\n'.join('{}) {}'.format(i, ', '.join(map(str, pm)))
                for i, pm in enumerate(PICKMODES))))

    @commands.command(pass_context=True, no_pm=True, aliases=['setpickorder'])
    @commands.has_permissions(manage_channels=True)
    @commands.check(ispugchannel)
    async def setpickmode(self, ctx, mod: TeamModConverter, pickmode: int):
        """Set pickmode for mod"""
        if 0 <= pickmode < len(PICKMODES):
            mod.pickmode = pickmode
            await self.bot.say(OKMSG)
            with shelve.open('data/pug', 'w') as db:
                db[ctx.message.channel.id] = self.channels[ctx.message.channel]

    @commands.command(no_pm=True, aliases=['pickorder'])
    @commands.check(ispugchannel)
    async def pickmode(self, mod: TeamModConverter):
        """Displays the pickmode for mod"""
        pickmode = PICKMODES[mod.pickmode][:mod.maxplayers - 2]
        await self.bot.say('```[{}]```'.format(', '.join(map(str, pickmode))))

    @commands.command(pass_context=True, no_pm=True)
    @commands.has_permissions(manage_channels=True)
    @commands.check(ispugchannel)
    async def setlimit(self, ctx, mod: ModConverter, limit: int):
        """Sets number of players required to fill mod"""
        if limt > 1 and not mod.full and (not mod.teamgame or limit <= MAXPLAYERS):
            mod.maxplayers = limit
            await self.bot.say(OKMSG)
            with shelve.open('data/pug') as db:
                db[ctx.message.channel.id] = self.channels[ctx.message.channel]

    @commands.command(pass_context=True, no_pm=True)
    @commands.has_permissions(manage_channels=True)
    @commands.check(ispugchannel)
    async def setrandcaptaintimer(self, ctx, duration: int):
        """Set the amount of time bot waits before setting random captains"""
        pugchannel = self.channels[ctx.message.channel]
        pugchannel.randcaptaintimer = clamp(duration, 10, 99)
        await self.bot.say(OKMSG)
        with shelve.open('data/pug', 'w') as db:
            db[ctx.message.channel.id] = pugchannel

    @commands.command(pass_context=True, no_pm=True)
    @commands.has_permissions(manage_channels=True)
    @commands.check(ispugchannel)
    async def setidlecaptaintimer(self, ctx, duration: int):
        """Set the amount of time bot waits before kicking idle captains"""
        pugchannel = self.channels[ctx.message.channel]
        pugchannel.idlecaptaintimer = clamp(duration, 10, 99)
        await self.bot.say(OKMSG)
        with shelve.open('data/pug', 'w') as db:
            db[ctx.message.channel.id] = pugchannel

    @commands.command(pass_context=True, no_pm=True)
    @commands.has_permissions(manage_channels=True)
    @commands.check(ispugchannel)
    async def setserver(self, ctx, *, server: str):
        """Set the channel's PUG server"""
        pugchannel = self.channels[ctx.message.channel]
        pugchannel.server_name = server
        await self.bot.say(OKMSG)
        with shelve.open('data/pug', 'w') as db:
            db[ctx.message.channel.id] = pugchannel

    @commands.command(pass_context=True, no_pm=True)
    @commands.check(ispugchannel)
    async def server(self, ctx):
        """Displays channel's PUG server"""
        pugchannel = self.channels[ctx.message.channel]
        if pugchannel.server_name:
            await self.bot.say(pugchannel.server_name)
        else:
            await self.bot.say('No server set, use `.setserver` to set the server')

    @commands.command(pass_context=True, no_pm=True)
    @commands.has_permissions(manage_channels=True)
    @commands.check(ispugchannel)
    async def addmod(self, ctx, mod: str, name: str, n: int, teams: bool=True, pickmode: int=1):
        """Adds new mod to the channel"""
        pugchannel = self.channels[ctx.message.channel]
        if n < 2 or mod in pugchannel:
            return

        if n == 2:
            teams = False

        if teams:
            if 4 > n > MAXPLAYERS or n % 2 == 1 or 0 > pickmode >= len(PICKMODES):
                return
            pickmode = 0 if n == 4 else pickmode
            pugchannel[mod] = TeamMod(mod, name, n, pickmode)
        else:
            pugchannel[mod] = Mod(mod, name, n)

        await self.bot.say(OKMSG)
        with shelve.open('data/pug') as db:
            db[ctx.message.channel.id] = pugchannel

    @commands.command(pass_context=True, no_pm=True)
    @commands.has_permissions(manage_channels=True)
    @commands.check(ispugchannel)
    async def delmod(self, ctx, mod: ModConverter):
        """Deletes mod from the channel"""
        pugchannel = self.channels[ctx.message.channel]
        del pugchannel[mod.name]
        await self.bot.say(OKMSG)
        with shelve.open('data/pug', 'w') as db:
            db[ctx.message.channel.id] = pugchannel

    async def on_command_error(self, error, ctx):
        """If a PUG command is used in a channel that doesn't have active
        PUGs send a message display the active channels on the server
        """
        cmds = {'join', 'list', 'last', 'liast', 'lastt', 'liastt', 'lasttt', 'liasttt'}
        if isinstance(error, commands.errors.CheckFailure) and ctx.command.name in cmds:
            server = ctx.message.server
            active_channels = (channel for channel in self.channels if channel.server == server and self.channels[channel].active)
            channel_mentions = [channel.mention for channel in active_channels]
            if channel_mentions:
                await self.bot.send_message(ctx.message.channel, '**Active Channels:** {}'.format(' '.join(channel_mentions)))

    def get_tag(self, member):
        return self.tags[member.server][member]

    def format_players(self, ps, number=False, mention=False, tags=True):
        def name(p):
            return p.mention if mention else display_name(p)
        xs = ((i, name(p), self.get_tag(p)) for i, p in enumerate(ps, 1) if p)
        fmt = '**{0})** {1}' if number else '{1}'
        fmt += '{2}' if tags else ''
        return PLASEP.join(fmt.format(*x) for x in xs)

    def format_mod(self, mod):
        fmt = '**__{0.desc} [{1}/{0.maxplayers}]:__**\n{2}'
        return fmt.format(mod, len(mod), self.format_players(mod, number=mod.full))

    def format_teams(self, mod, mention=False, tags=False):
        teams = '**Red Team:** {}\n**Blue Team:** {}'
        red = self.format_players(mod.red, mention=mention, tags=tags)
        blue = self.format_players(mod.blue, mention=mention, tags=tags)
        return teams.format(red, blue)

    def format_last(self, channel, mod, attr='last'):
        with stats_open(channel, mod, flag='r') as db:
            pugstats = db.get(self.bot.user, None)
            if pugstats is not None:
                history_item = getattr(pugstats, attr)
                return '**{}:** {}'.format(attr.title(), history_item)
        return 'No PUGs recorded'

    def format_list(self, channel, mod):
        if mod is None:
            pugchannel = self.channels[channel]
            return MODSEP.join(mod.brief for mod in pugchannel.values())
        else:
            return self.format_mod(mod)

    def format_liast(self, channel, mod, attr='last'):
        ls = self.format_list(channel, mod)
        la = self.format_last(channel, mod, attr)
        return '{}\n{}'.format(ls, la)

    @commands.command(name='list', pass_context=True, no_pm=True, aliases=['ls'])
    @commands.check(ispugchannel)
    async def _list(self, ctx, mod: ModConverter=None):
        """Displays mods/players in the channel"""
        await self.bot.say(self.format_list(ctx.message.channel, mod))

    @commands.command(pass_context=True, no_pm=True, aliases=['la'])
    @commands.check(ispugchannel)
    async def last(self, ctx, mod: ModConverter=None):
        """Displays players from last PUG"""
        await self.bot.say(self.format_last(ctx.message.channel, mod))

    @commands.command(pass_context=True, no_pm=True, aliases=['lia'])
    @commands.check(ispugchannel)
    async def liast(self, ctx, mod: ModConverter=None):
        """Display mods/players and last PUG"""
        await self.bot.say(self.format_liast(ctx.message.channel, mod))

    @commands.command(pass_context=True, no_pm=True, hidden=True)
    @commands.check(ispugchannel)
    async def lastt(self, ctx, mod: ModConverter=None):
        await self.bot.say(self.format_last(ctx.message.channel, mod, 'lastt'))

    @commands.command(pass_context=True, no_pm=True, hidden=True)
    @commands.check(ispugchannel)
    async def liastt(self, ctx, mod: ModConverter=None):
        await self.bot.say(self.format_liast(ctx.message.channel, mod, 'lastt'))

    @commands.command(pass_context=True, no_pm=True, hidden=True)
    @commands.check(ispugchannel)
    async def lasttt(self, ctx, mod: ModConverter=None):
        await self.bot.say(self.format_last(ctx.message.channel, mod, 'lasttt'))

    @commands.command(pass_context=True, no_pm=True, hidden=True)
    @commands.check(ispugchannel)
    async def liasttt(self, ctx, mod: ModConverter=None):
        await self.bot.say(self.format_liast(ctx.message.channel, mod, 'lasttt'))

    async def addplayers_impl(self, channel, mod, members):
        if not any(list(mod.add(m) for m in members)):
            return
        if not mod.full:
            return await self.bot.say(self.format_mod(mod))
        msg = ['**{}** has been filled'.format(mod.name)]
        msg.append(self.format_players(mod, mention=True, tags=False))
        mods = (other for other in self.channels[channel].values() if other is not mod)
        for other in mods:
            wasfull = other.full
            if any(list(other.discard(p) for p in mod)) and wasfull:
                msg.append('**{}** was reset'.format(other.name))

        await self.bot.say('\n'.join(msg))

        if mod.teamgame:
            mod.task = self.bot.loop.create_task(self.randcaptains(channel, mod))
        else:
            timestamp = pendulum.now().timestamp
            with stats_open(channel, mod) as db:
                for member in mod:
                    db[member] = db.get(member, ModStats()).update(timestamp)
                    self.remove_tags(member)
                players = self.format_players(mod, mention=False, tags=False)
                db[self.bot.user] = db.get(self.bot.user, PUGStats()).update(timestamp, players)
            mod.fullreset()

    @commands.command(pass_context=True, no_pm=True, aliases=['addplayer'])
    @commands.has_permissions(manage_channels=True)
    @commands.check(ispugchannel)
    async def addplayers(self, ctx, mod: ModConverter, *members: discord.Member):
        """Adds players to mod"""
        await self.addplayers_impl(ctx.message.channel, mod, (m for m in members if not m.bot))

    @commands.command(pass_context=True, no_pm=True, aliases=['j'])
    @commands.check(ispugchannel)
    async def join(self, ctx, mod: ModConverter):
        """Joins mod"""
        await self.addplayers_impl(ctx.message.channel, mod, [ctx.message.author])

    async def randcaptains(self, channel, mod):
        """Waits for n seconds before selecting random captains"""
        content = '`Random captains in {:2d} seconds`'
        seconds = self.channels[channel].randcaptaintimer
        message = await self.bot.send_message(channel, content.format(seconds))
        mod.here = [False, False]

        for i in range(seconds - 1, -1, -1):
            try:
                await asyncio.sleep(1)
                if i % 5 == 0 or i < 10:
                    message = await self.bot.edit_message(message, content.format(i))
            except asyncio.CancelledError:
                return await self.bot.edit_message(message, '`Random captains cancelled`')

        if not mod.full or mod.hascaptains:
            return

        candidates = [p for p in mod if p and p not in self.nocaptains[channel.server]]
        if len(candidates) < 2:
            candidates = list(mod)
        random.shuffle(candidates)
        msg, redset = [], False

        if not mod.red:
            redset = mod.setcaptain(candidates.pop(0))
            msg.append(mod.red.captain.mention + ' is captain for the **Red Team**')
        blue_captain = candidates.pop(0)
        mod.setcaptain(blue_captain)
        mod.here = [not redset, False]

        await self.bot.edit_message(message, '`Random captains selected`')
        msg.append(blue_captain.mention + ' is captain for the **Blue Team**')
        msg.append('Type .here to prevent being kicked')
        msg.append('{} to pick'.format(mod.captain.mention))
        msg.append(self.format_players(mod, number=True))
        await self.bot.send_message(channel, '\n'.join(msg))
        mod.task = self.bot.loop.create_task(self.kick_idle(channel, mod))

    async def kick_idle(self, channel, mod):
        """Removes captains if they did not pick or type .here"""
        try:
            await asyncio.sleep(self.channels[channel].idlecaptaintimer)
        except asyncio.CancelledError:
            return

        if mod.hascaptains and not all(mod.here):
            msg = ['**{}** was reset'.format(mod.name)]
            kick = []
            for i in range(2):
                if not mod.here[i]:
                    captain = mod.teams[i].captain
                    kick.append(captain)
                    msg.append('{} was removed for being idle'.format(captain.mention))
            # Send the message before we kick the players, otherwise the task will be cancelled
            await self.bot.send_message(channel, '\n'.join(msg))
            [mod.discard(p) for p in kick]

    @commands.command(pass_context=True, no_pm=True, aliases=['pro'])
    @commands.cooldown(2, 5.0, type=commands.BucketType.channel)
    @commands.check(ispugchannel)
    async def promote(self, ctx, mod: ModConverter):
        """Notify other members in the channel"""
        await self.bot.say('@here Only **{0.needed}** more needed for **{0.name}**'.format(mod))

    async def remove_player(self, channel, mod, player, reason):
        wasfull = mod.full
        name = player.mention if reason == 'was removed' else display_name(player)
        if mod.discard(player):
            if wasfull:
                await self.bot.say('**{}** was reset because **{}** {}'.format(mod.name, name, reason))
            else:
                await self.bot.say('**{}** was removed from **{}** because they {}'.format(name, mod.name, reason))

    @commands.command(pass_context=True, no_pm=True)
    @commands.has_permissions(manage_channels=True)
    @commands.check(ispugchannel)
    async def delplayer(self, ctx, mod: ModConverter, member: discord.Member):
        """Removes player from mod"""
        await self.remove_player(ctx.message.channel, mod, member, 'was removed')

    @commands.command(pass_context=True, no_pm=True, aliases=['l'])
    @commands.check(ispugchannel)
    async def leave(self, ctx, mod: ModConverter):
        """Leave mod"""
        await self.remove_player(ctx.message.channel, mod, ctx.message.author, 'left')

    @commands.command(pass_context=True, no_pm=True, aliases=['lva'])
    @commands.check(ispugchannel)
    async def leaveall(self, ctx):
        """Leaves all mods you have joined, including other channels"""
        for channel in self.channels:
            await self.remove_from_channel(ctx.message.author, channel, 'left')

    async def on_member_update(self, before, after):
        """Remove member from all mods if they go offline"""
        if after.status is discord.Status.offline:
            await self.remove_from_server(before, 'quit')

    def removed_from(self, member, channel):
        pugchannel = self.channels[channel]
        mods = (mod for mod in pugchannel.values() if member in mod)
        for mod in mods:
            yield mod
            mod.discard(member)

    async def remove_from_channel(self, member, channel, reason):
        reset, removed = None, []
        for mod in self.removed_from(member, channel):
            if mod.full:
                reset = mod.name
            else:
                removed.append(mod.name)
        msg, name = [], display_name(member)
        if reset:
            fmt = '**{}** was reset because **{}** {}'
            msg.append(fmt.format(reset, name, reason))
        if removed:
            fmt = '**{}** was removed from **{}** because they {}'
            if len(removed) > 1:
                mods = ', '.join(removed[:-1]) + ' & ' + removed[-1]
            else:
                mods = removed[0]
            msg.append(fmt.format(name, mods, reason))
        if msg:
            await self.bot.send_message(channel, '\n'.join(msg))

    async def remove_from_server(self, member, reason):
        """Removes the member from the server"""
        self.remove_tags(member)
        for channel in self.channels:
            if channel.server == member.server:
                await self.remove_from_channel(member, channel, reason)

    async def on_member_remove(self, member):
        """Remove member from all mods in the server"""
        await self.remove_from_server(member, 'left the server')

    async def on_member_ban(self, member):
        """Remove member from all mods in the server"""
        with shelve.open('data/bans') as db:
            bans = db.get(member.server.id, collections.Counter())
            bans[member.id] += 1
            db[server.id] = bans
        await self.remove_from_server(member, 'was banned')

    async def on_channel_delete(self, channel):
        """Remove PUGChannel if the associated channel was deleted"""
        if channel in self.channels:
            del self.channels[channel]
            with shelve.open('data/pug', 'w') as db:
                del db[channel.id]

    async def on_server_remove(self, server):
        """Remove server tags when server is removed from the bot"""
        self.tags.pop(server)
        self.nocaptains.pop(server)

    @commands.command(pass_context=True, no_pm=True)
    @commands.has_permissions(manage_channels=True)
    @commands.check(ispugchannel)
    async def reset(self, ctx, mod: TeamModConverter=None):
        """Resets teams"""
        if mod is None:
            pugchannel = self.channels[ctx.message.channel]
            mods = [mod for mod in pugchannel.team_mods if mod.red]
            if len(mods) == 1:
                mod = mods[0]
        if mod is not None and mod.reset():
            await self.bot.say('**{}** was reset'.format(mod.name))
            mod.task = self.bot.loop.create_task(self.randcaptains(ctx.message.channel, mod))

    @commands.command(pass_context=True, no_pm=True)
    @commands.has_permissions(manage_channels=True)
    @commands.check(ispugchannel)
    async def fullreset(self, ctx, mod: ModConverter):
        """Resets players in the mod"""
        mod.fullreset()
        await self.bot.say('**{}** was reset'.format(mod.name))

    @commands.command(pass_context=True, no_pm=True)
    @commands.check(ispugchannel)
    async def here(self, ctx):
        """Prevent being kicked when set as random captain"""
        channel = ctx.message.channel
        pugchannel = self.channels[channel]
        captain = ctx.message.author

        for mod in pugchannel.team_mods:
            if mod.red:
                if mod.red.captain == captain:
                    mod.here[0] = True
                    return
                elif mod.blue and mod.blue.captain == captain:
                    if not mod.here[1]:
                        mod.here[1] = True
                        if all(mod.here) and mod.task:
                            mod.task.cancel()
                    return

    async def setcaptain_impl(self, channel, member, mention=False):
        pugchannel = self.channels[channel]
        mod = next((mod for mod in pugchannel.team_mods if mod.setcaptain(member)), None)
        name = member.mention if mention else '**{}**'.format(display_name(member))
        if mod is not None:
            if mod.hascaptains:
                if mod.task is not None:
                    mod.task.cancel()
                msg = [name + ' is captain for the **Blue Team**']
                msg.append('{} to pick'.format(mod.captain.mention))
                msg.append(self.format_players(mod, number=True))
                await self.bot.say('\n'.join(msg))
            else:
                await self.bot.say('**{}** is captain for the **Red Team**'.format(name))

    @commands.command(pass_context=True, no_pm=True)
    @commands.has_permissions(manage_channels=True)
    @commands.check(ispugchannel)
    async def setcaptain(self, ctx, member: discord.Member):
        """Set player as captain"""
        await self.setcaptain_impl(ctx.message.channel, member, mention=True)

    @commands.command(pass_context=True, no_pm=True)
    @commands.check(ispugchannel)
    async def captain(self, ctx):
        """Become captain for mod"""
        await self.setcaptain_impl(ctx.message.channel, ctx.message.author)

    @commands.command(pass_context=True, no_pm=True, aliases=['p'])
    @commands.check(ispugchannel)
    async def pick(self, ctx, *players: int):
        """Pick player by number"""
        channel = ctx.message.channel
        pugchannel = self.channels[channel]
        captain = ctx.message.author
        mod = next((mod for mod in pugchannel.team_mods if mod.captain == captain), None)
        if mod is None:
            return
        picks = list(itertools.takewhile(functools.partial(mod.pick, captain), (x - 1 for x in players)))

        if picks:
            teams = self.format_teams(mod)
            if mod.teamsready:
                self.last_teams[channel] = '**{}**\n{}'.format(mod.desc, teams)
                msg = 'Teams have been selected:\n{}'.format(self.format_teams(mod, mention=True))
                await self.bot.say(msg)
                timestamp = pendulum.now().timestamp
                with stats_open(channel, mod) as db:
                    members = mod.red + mod.blue
                    xs = PICKMODES[mod.pickmode][:mod.maxplayers - 2]
                    picks = [0] + [i + 1 for i, x in enumerate(xs) if x == 0]
                    picks += [0] + [i + 1 for i, x in enumerate(xs) if x == 1]
                    for i in range(mod.maxplayers):
                        member = members[i]
                        db[member] = db.get(member, TeamStats()).update(timestamp, picks[i])
                        self.remove_tags(member)
                    db[self.bot.user] = db.get(self.bot.user, PUGStats()).update(timestamp, teams)
                mod.fullreset()
            else:
                msg = '\n'.join([
                    self.format_players(mod, number=True, tags=True),
                    teams,
                    '{} to pick'.format(mod.captain.mention)])
                await self.bot.say(msg)

    @pick.error
    async def pick_error(self, error, ctx):
        if isinstance(error, commands.errors.BadArgument) and ctx.invoked_with == 'p':
            modid = ctx.message.content.split()[1]
            mod = self.channels[ctx.message.channel].get(modid, None)
            if mod is not None:
                await self.bot.say('@here Only **{0.needed}** more needed for **{0.name}**'.format(mod))

    @commands.command(pass_context=True, no_pm=True)
    @commands.check(ispugchannel)
    async def teams(self, ctx):
        """Displays current teams, or teams from last PUG"""
        pugchannel = self.channels[ctx.message.channel]
        mods = [(mod.desc, self.format_teams(mod, tags=True)) for mod in pugchannel.team_mods if mod.red]
        if mods:
            await self.bot.say('\n'.join('**__{}:__**\n{}'.format(*mod) for mod in mods))
        elif ctx.message.channel in self.last_teams:
            await self.bot.say(self.last_teams[ctx.message.channel])

    @commands.command(pass_context=True, no_pm=True)
    @commands.check(ispugchannel)
    async def turn(self, ctx):
        """Displays captain whose turn it is to pick and current teams"""
        pugchannel = self.channels[ctx.message.channel]
        mods = [(display_name(mod.captain), mod.desc) for mod in pugchannel.team_mods if mod.hascaptains]
        if mods:
            await self.bot.say('\n'.join('**{}** to pick for **{}**'.format(*mod) for mod in mods))

    async def display_stats(self, member, channel, mod):
        with stats_open(channel, mod, flag='r') as db:
            stats = db.get(member)
            if stats is None:
                return await self.bot.say('No stats available')
            out = []
            out.append('**Total:** [{}]'.format(stats.total))
            out.append('**Daily:** [{:.2f}]'.format(stats.daily))

            if hasattr(stats, 'captain') and not member.bot:
                out.append('**Captain:** [{}]'.format(stats.captain))
                mp = '/' + str(mod.maxplayers - 2) if mod is not None else ''
                out.append('**Avg. Pick:** [{:.2f}{}]'.format(stats.average_pick, mp))

            if not member.bot:
                try:
                    db = shelve.open('data/bans', 'r')
                except:
                    out.append('**Bans:** [0]')
                else:
                    bans = db.get(member.server.id, collections.Counter())
                    db.close()
                    out.append('**Bans:** [{}]'.format(bans[member.id]))

            out.append('**Last:** {}'.format(stats.last))
            await self.bot.say(MODSEP.join(out))

    @commands.command(pass_context=True, no_pm=True)
    @commands.check(ispugchannel)
    async def stats(self, ctx, member: discord.Member, mod: ModConverter=None):
        """Display PUG stats for player"""
        await self.display_stats(member, ctx.message.channel, mod)

    @commands.command(pass_context=True, no_pm=True)
    @commands.check(ispugchannel)
    async def mystats(self, ctx, mod: ModConverter=None):
        """Display your PUG stats"""
        await self.display_stats(ctx.message.author, ctx.message.channel, mod)

    @commands.command(pass_context=True, no_pm=True)
    @commands.check(ispugchannel)
    async def pugstats(self, ctx, mod: ModConverter=None):
        """Display channel PUG stats"""
        await self.display_stats(self.bot.user, ctx.message.channel, mod)

    @commands.command(pass_context=True, no_pm=True, aliases=['nocapt'])
    @commands.check(ispugchannel)
    async def nocaptain(self, ctx):
        """Prevent being made captain for next PUG, resets after next PUG"""
        self.nocaptains[ctx.message.server].add(ctx.message.author)

    @commands.command(pass_context=True, no_pm=True)
    @commands.check(ispugchannel)
    async def nomic(self, ctx):
        """Sets tag to 'nomic'"""
        self.tags[ctx.message.server][ctx.message.author] = ' [nomic]'

    @commands.command(pass_context=True, no_pm=True)
    @commands.check(ispugchannel)
    async def tag(self, ctx, *, tag: str):
        """Sets custom tag for all mods"""
        if tag == 'nocapt' or tag == 'nocaptain':
            self.nocaptains[ctx.message.server].add(ctx.message.author)
        else:
            self.tags[ctx.message.server][ctx.message.author] = ' [{}]'.format(discord_md_escape(tag[:MAXTAGLENGTH]))

    def remove_tags(self, member):
        self.nocaptains[member.server].discard(member)
        self.tags[member.server].pop(member, None)

    @commands.command(pass_context=True, no_pm=True)
    @commands.check(ispugchannel)
    async def deltag(self, ctx):
        """Deletes tags"""
        self.remove_tags(ctx.message.author)

    @commands.command(pass_context=True, no_pm=True, hidden=True)
    @commands.has_permissions(manage_server=True)
    async def cleartags(self, ctx):
        """Clear current tags for the server"""
        self.nocaptains.pop(ctx.message.server)
        self.tags.pop(ctx.message.server)

    @commands.command(pass_context=True, no_pm=True)
    @commands.has_permissions(manage_server=True)
    async def numtags(self, ctx):
        """Displays the number tags in use on the server"""
        server = ctx.message.server
        await self.bot.whisper('tags: {}\nnocaptains: {}'.format(len(self.tags[server]), len(self.nocaptains[server])))

    @commands.group(pass_context=True, no_pm=True)
    @commands.check(ispugchannel)
    async def top(self, ctx, n: int):
        """Displays a top n list for the channel"""
        if ctx.invoked_subcommand is not None:
            self.count = n

    @top.command(pass_context=True, no_pm=True)
    async def picks(self, ctx, mod: TeamModConverter=None):
        """Displays top average picks"""
        with stats_open(ctx.message.channel, mod, flag='r') as db:
            ps = ((display_name(p[0]), p[1].average_pick) for p in db if p[1].average_pick)
            topn = heapq.nsmallest(self.count, ps, key=lambda p: p[1])
            if topn:
                entries = ('**{})** {} [{:.2f}]'.format(i, *p) for i, p in enumerate(topn, 1))
                await self.bot.say(PLASEP.join(entries))

    @top.command(pass_context=True, no_pm=True)
    async def puggers(self, ctx, mod: ModConverter=None):
        """Displays top puggers"""
        with stats_open(ctx.message.channel, mod, flag='r') as db:
            ps = ((display_name(p[0]), p[1].total) for p in db)
            topn = heapq.nlargest(self.count, ps, key=lambda p: p[1])
            if topn:
                entries = ('**{})** {} [{}]'.format(i, *p) for i, p in enumerate(topn, 1))
                await self.bot.say(PLASEP.join(entries))

    @top.command(pass_context=True, no_pm=True)
    async def lamers(self, ctx, mod: ModConverter=None):
        """Displays top lamers"""
        with stats_open(ctx.message.channel, mod, flag='r') as db:
            ps = ((display_name(p[0]), p[1].total) for p in db)
            topn = heapq.nsmallest(self.count, ps, key=lambda p: p[1])
            if topn:
                entries = ('**{})** {} [{}]'.format(i, *p) for i, p in enumerate(topn, 1))
                await self.bot.say(PLASEP.join(entries))

    @top.command(pass_context=True, no_pm=True)
    async def captains(self, ctx, mod: TeamModConverter=None):
        """Display top captains"""
        with stats_open(ctx.message.channel, mod, flag='r') as db:
            ps = ((display_name(p[0]), p[1].captain) for p in db if p[1].captain)
            topn = heapq.nlargest(self.count, ps, key=lambda p: p[1])
            if topn:
                entries = ('**{})** {} [{}]'.format(i, *p) for i, p in enumerate(topn, 1))
                await self.bot.say(PLASEP.join(entries))

    @commands.command(pass_context=True, no_pm=True)
    @commands.has_permissions(manage_channels=True)
    @commands.check(ispugchannel)
    async def addmaps(self, ctx, mod: ModConverter, *maps: str):
        """Adds maps to mod"""
        if maps:
            mod.maps.update(maps)
            await self.bot.say(OKMSG)
            with shelve.open('data/pug') as db:
                db[ctx.message.channel.id] = self.channels[ctx.message.channel]

    @commands.command(pass_context=True, no_pm=True)
    @commands.has_permissions(manage_channels=True)
    @commands.check(ispugchannel)
    async def delmaps(self, ctx, mod: ModConverter, *maps: str):
        """Removes maps from mod"""
        if maps:
            mod.maps -= set(maps)
            await self.bot.say(OKMSG)
            with shelve.open('data/pug') as db:
                db[ctx.message.channel.id] = self.channels[ctx.message.channel]

    @commands.command(pass_context=True, no_pm=True, aliases=['maps'])
    @commands.check(ispugchannel)
    async def maplist(self, ctx, mod: ModConverter=None):
        """Displays maps for mod"""
        if mod is not None and mod.maps:
            await self.bot.say('**__{}__:**\n{}'.format(mod.desc, MODSEP.join(sorted(mod.maps))))
        elif mod is None:
            pugchannel = self.channels[ctx.message.channel]
            mods = [mod for mod in pugchannel.values() if mod.maps]
            if mods:
                await self.bot.say('\n'.join('**__{}__:** {}'.format(mod.desc, MODSEP.join(sorted(mod.maps))) for mod in mods))


def setup(bot):
    if not os.path.exists('data'):
        os.makedirs('data')
    shelve.open('data/stats', 'c').close()
    bot.add_cog(PUG(bot))
