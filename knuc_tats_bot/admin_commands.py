from discord.ext import commands
from time import time
from knuc_tats_cog import KnucTatsCog


class Admin(KnucTatsCog):

    @commands.command(name="max", help='Use to change max number of hand sets',
                      usage='(num_hand_sets) to change max number of hand sets, no parameters to check current max. '
                            'Only members with permissions to manage server may use.')
    @commands.has_permissions(manage_guild=True)
    async def max(self, ctx, *args):
        if len(args) == 0:
            mx = self.cache.get_server_max_hands(ctx.guild.id)
            await ctx.send(f"Maximum sets of hands is currently {mx}.{self.looks_like(mx)}")
            return
        try:
            amount = int(args[0])
            if 0 < amount < 100:
                self.cache.set_server_max_hands(ctx.guild.id, amount)
                await ctx.send(f"Maximum sets of hands changed to {amount}.{self.looks_like(amount)}")
            else:
                await ctx.send("invalid number of hands")
        except ValueError:
            await ctx.send("invalid number of hands")

    @commands.command(name="mute", help='Mute bot in channel or server wide for period of time or until unmuted',
                      usage='(minutes) or %mute #y#w#d#h#m#s, '
                            'leave blank to mute indefinitely. -server to mute server-wide, '
                            '-stop to unmute, -check to see how long a channel or server is muted for. '
                            'Only people with permission to manage channels may use this command to modify mute times.')
    async def mute(self, ctx, *args):
        admin = ctx.author.guild_permissions.manage_channels
        args = list(args)
        try:
            args.remove("-check")
            check = True
        except ValueError:
            check = False
        try:
            args.remove("-server")
            server = True
        except ValueError:
            server = False
        try:
            args.remove("-stop")
            stop = True
        except ValueError:
            stop = False

        amount = to_seconds("".join(args))
        if amount is None:
            await ctx.send("invalid amount of time.")
            return

        if not server:
            ID = ctx.channel.id
        else:
            ID = ctx.guild.id

        left = self.cache.time_left(ctx.guild.id, ID)
        s_left = self.cache.time_left(ctx.guild.id, ctx.guild.id)

        if check and stop:
            await ctx.send("Cannot both check and stop mute.")

        entity = ctx.guild.name if server else f"<#{ctx.channel.id}>"

        if left is None and (check or stop):
            if s_left is None:
                await ctx.send(f"{entity} is not muted.")
                return
            else:
                left = s_left
                entity = ctx.guild.name
                server = True

        if check:
            if left < 0:
                await ctx.send(f"{entity} is muted indefinitely. %mute -stop to unmute.")
                return

            await ctx.send(f"{entity} will be muted for {time_string(int(left))} longer.")
            return

        if not admin:
            await ctx.send("You do not have permissions to mute.")
            return

        if stop:
            self.cache.enable(ctx.guild.id, ctx.channel.id if not server else None)
            await ctx.send(f"{entity} has been unmuted.")
            return

        if amount > 0:
            until = time() + amount
        else:
            until = -1

        self.cache.disable(ctx.guild.id, ID, until)

        if amount < 0:
            await ctx.send(f"{entity} has been muted indefinitely. %mute -stop to unmute.")
            return

        await ctx.send(f"{entity} has been muted for {time_string(amount)}.")


