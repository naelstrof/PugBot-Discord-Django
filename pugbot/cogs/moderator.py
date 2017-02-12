from discord.ext import commands
import discord


class Moderator:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(no_pm=True)
    @commands.has_permissions(kick_members=True)
    async def kick(self, member: discord.Member):
        """Kicks member from the server

        Requires `Kick Members` permissions
        member can still join the server if they have an invite
        """
        try:
            await self.bot.kick(member)
        except discord.Forbidden:
            await self.bot.say('I do not have the proper permissions')
        except discord.HTTPException:
            await self.bot.say('Kicking failed')
        else:
            await self.bot.say('\N{OK HAND SIGN}')

    @commands.command(no_pm=True)
    @commands.has_permissions(ban_members=True)
    async def ban(self, member: discord.Member, delete_message_days: int=1):
        """Bans member from the server

        Requires `Ban Members` permissions

        delete_message_days - The number of days worth of messages to delete
        from the user in the server. The minimum is 0 and the maximum is 7.
        """
        try:
            await self.bot.ban(member, delete_message_days)
        except discord.Forbidden:
            await self.bot.say('I do not have the proper permissions')
        except discord.HTTPException:
            await self.bot.say('Banning failed')
        else:
            await self.bot.say('\N{OK HAND SIGN}')

    @commands.command(pass_context=True, no_pm=True)
    @commands.has_permissions(ban_members=True)
    async def bans(self, ctx):
        """Displays a list of names that have been banned

        Requires `Ban Members` permissions
        """
        try:
            bans = await self.bot.get_bans(ctx.message.server)
        except discord.Forbidden:
            await self.bot.say('I do not have the proper permissions')
        except discord.HTTPException:
            await self.bot.say('Getting bans failed')
        else:
            await self.bot.say('\N{SMALL ORANGE DIAMOND}'.join(user.name for user in bans))

    @commands.command(pass_context=True, no_pm=True)
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, name: str):
        """Unbans user from the server

        Requires `Ban Members` permissions

        name - name of the banned user
        """
        try:
            bans = await self.bot.get_bans(ctx.message.server)
            user = discord.utils.get(bans, name=name)
            if user is not None:
                await self.bot.unban(ctx.message.server, user)
        except discord.Forbidden:
            await self.bot.say('I do not have the proper permissions')
        except discord.HTTPException:
            await self.bot.say('Unbanning failed')
        else:
            await self.bot.say('\N{OK HAND SIGN}')


def setup(bot):
    bot.add_cog(Moderator(bot))
