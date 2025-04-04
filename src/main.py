import asyncio
import discord
import os
import logging

from discord.ext import commands
from dotenv import load_dotenv

handler = logging.StreamHandler()

def main():
    # Load environment variables
    load_dotenv()
    discord_token = os.getenv("DISCORD_TOKEN")

    # Define intents
    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True

    # Create the bot instance
    bot = commands.Bot(command_prefix="!", intents=intents)

    # Load cogs from the src/cogs/ directory
    async def load_cogs():
        cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py"):
                try:
                    await bot.load_extension(f"cogs.{filename[:-3]}")
                    print(f"Loaded cog: {filename}")
                except Exception as e:
                    print(f"Failed to load cog {filename}: {e}")
        print("All cogs loaded.")
        for command in bot.commands:
            print(f"Command: {command.name} - {command.description}")

    @bot.event
    async def on_ready():
        print(f"Logged in as {bot.user}")
        print("Bot is ready!")

    # Run the bot
    async def start_bot():
        try:
            await load_cogs()
            await bot.start(discord_token)
        except Exception as e:
            logger.error(f"Error starting bot: {e}")

    asyncio.run(start_bot())

if __name__ == "__main__":
    main()