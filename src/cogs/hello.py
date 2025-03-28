from discord.ext import commands

class HelloCog(commands.Cog):
    """
    A simple cog for testing the bot.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="hello")
    async def hello(self, ctx):
        """
        A simple command that says Hello World.
        Usage: !hello
        """
        await ctx.send("Hello!")

async def setup(bot):
    await bot.add_cog(HelloCog(bot))