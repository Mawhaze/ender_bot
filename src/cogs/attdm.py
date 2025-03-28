import asyncio
import discord
import json
import logging
import os
import requests
from discord.ext import commands
from discord.ui import Button, Select, View

logging.basicConfig(level=logging.INFO)

class AttdmCog(commands.Cog):
    """
    A simple cog for testing the bot.
    """

    def __init__(self, bot):
        self.bot = bot
        self.api_base_url = os.getenv("API_URL")
        self.user_sessions = {}

    @commands.command(name="dnd")
    async def dnd(self, ctx):
        """
        The main menu for the dnd bot section.
        Usage: !dnd
        """
        async def show_main_menu():
            """
            Show the main menu with options for `create_campaign` and `select_campaign`.
            """
            class MainMenuView(View):
                def __init__(self, run_create_campaign, run_select_campaign):
                    super().__init__(timeout=60)
                    self.run_create_campaign = run_create_campaign
                    self.run_select_campaign = run_select_campaign

                    # Button for creating a campaign
                    self.create_campaign_button = Button(label="Create Campaign", style=discord.ButtonStyle.primary)
                    self.create_campaign_button.callback = self.create_campaign_callback
                    self.add_item(self.create_campaign_button)

                    # Button for selecting a campaign
                    self.select_campaign_button = Button(label="Select Campaign", style=discord.ButtonStyle.primary)
                    self.select_campaign_button.callback = self.select_campaign_callback
                    self.add_item(self.select_campaign_button)

                async def create_campaign_callback(self, interaction: discord.Interaction):
                    await interaction.response.defer()
                    self.stop()
                    await self.run_create_campaign(ctx)

                async def select_campaign_callback(self, interaction: discord.Interaction):
                    await interaction.response.defer()
                    self.stop()
                    await self.run_select_campaign(ctx)

            await ctx.send("**Main Menu:**", view=MainMenuView(run_create_campaign, run_select_campaign))

        async def show_action_menu():
            """
            Show the action menu with options for `roll_loot`, `add_character`, `add_loot_source`, and `list_loot_sources`.
            """
            class ActionMenuView(View):
                def __init__(self):
                    super().__init__(timeout=60)

                    # Button for rolling loot
                    self.roll_loot_button = Button(label="Roll Loot", style=discord.ButtonStyle.primary)
                    self.roll_loot_button.callback = self.roll_loot_callback
                    self.add_item(self.roll_loot_button)

                    # Button for adding a character
                    self.add_character_button = Button(label="Add Character", style=discord.ButtonStyle.primary)
                    self.add_character_button.callback = self.add_character_callback
                    self.add_item(self.add_character_button)

                    # Button for adding loot sources
                    self.add_loot_source_button = Button(label="Add Loot Source", style=discord.ButtonStyle.primary)
                    self.add_loot_source_button.callback = self.add_loot_source_callback
                    self.add_item(self.add_loot_source_button)

                    # Button for listing loot sources
                    self.list_loot_sources_button = Button(label="List Loot Sources", style=discord.ButtonStyle.primary)
                    self.list_loot_sources_button.callback = self.list_loot_sources_callback
                    self.add_item(self.list_loot_sources_button)

                async def roll_loot_callback(self, interaction: discord.Interaction):
                    await interaction.response.defer()
                    await self.stop()
                    await self.run_roll_loot(ctx)

                async def add_character_callback(self, interaction: discord.Interaction):
                    await interaction.response.defer()
                    await self.stop()
                    await self.run_add_character(ctx)

                async def add_loot_source_callback(self, interaction: discord.Interaction):
                    await interaction.response.defer()
                    await self.stop()
                    await self.run_add_loot_source(ctx)

                async def list_loot_sources_callback(self, interaction: discord.Interaction):
                    await interaction.response.defer()
                    await self.stop()
                    await self.run_list_loot_sources(ctx)

            await ctx.send("**Action Menu:**", view=ActionMenuView())

        # Helper methods to run the commands
        async def run_create_campaign(ctx):
            await self.create_campaign(ctx)
            await show_action_menu()

        async def run_select_campaign(ctx):
            await self.select_campaign(ctx)
            await show_action_menu()

        async def run_roll_loot(ctx):
            await self.roll_loot(ctx)
            await show_action_menu()

        async def run_add_character(ctx):
            await self.add_character(ctx)
            await show_action_menu()

        async def run_add_loot_source(ctx):
            await self.add_loot_source(ctx)
            await show_action_menu()

        async def run_list_loot_sources(ctx):
            await self.list_loot_sources(ctx)
            await show_action_menu()

        # Start by showing the main menu
        await show_main_menu()

    @commands.command(name="create_campaign")
    async def create_campaign(self, ctx):
        """
        Create a new campaign by prompting the user for the campaign name and DM name.
        Usage: !create_campaign
        """
        # Prompt for the campaign name
        await ctx.send("Please enter the campaign name:")

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        try:
            campaign_name_msg = await self.bot.wait_for("message", timeout=60.0, check=check)
            campaign_name = campaign_name_msg.content
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Campaign creation canceled.")
            return

        # Prompt for the DM name
        await ctx.send("Please enter the DM name:")

        try:
            dm_name_msg = await self.bot.wait_for("message", timeout=60.0, check=check)
            dm_name = dm_name_msg.content
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Campaign creation canceled.")
            return

        # Prepare the API URL and payload
        url = f"{self.api_base_url}/campaigns/"
        payload = {
            "name": campaign_name,
            "dm": dm_name,
            "loot_books": []  # Optional field, can be extended later
        }

        try:
            # Send the POST request to the API
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                campaign_id = data.get("campaign_id")
                self.user_sessions[ctx.author.id] = int(campaign_id)
                await ctx.send(f"Campaign '{campaign_name}' created successfully! (ID: {campaign_id})")
            else:
                error_detail = response.json().get("detail", "Unknown error")
                await ctx.send(f"Failed to create campaign: {error_detail}")
        except Exception as e:
            await ctx.send(f"An error occurred while creating the campaign: {e}")

    @commands.command(name="select_campaign")
    async def select_campaign(self, ctx):
        """
        List all campaigns.
        Usage: !select_campaign
        """
        url = f"{self.api_base_url}/campaigns/"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                campaigns = response.json()
                if campaigns:
                    # Create a view with buttons for each campaign
                    view = View()
                    for campaign in campaigns:
                        campaign_id, campaign_name, dm_name, _ = campaign
                        button = Button(label=f"{campaign_name} (DM: {dm_name})", style=discord.ButtonStyle.primary)

                        # Define the callback for the button
                        async def button_callback(interaction: discord.Interaction, campaign_id=campaign_id):
                            self.user_sessions[ctx.author.id] = int(campaign_id)
                            await interaction.response.send_message(f"Campaign '{campaign_name}' selected! (ID: {campaign_id})", ephemeral=True)

                        button.callback = button_callback
                        view.add_item(button)

                    # Send the message with the buttons
                    await ctx.send("**Select a campaign:**", view=view)
                else:
                    await ctx.send("No campaigns found.")
            else:
                await ctx.send(f"Failed to list campaigns: {response.json().get('detail', 'Unknown error')}")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command(name="current_campaign")
    async def current_campaign(self, ctx):
        """
        Display the currently selected campaign for the user.
        Usage: !current_campaign
        """
        campaign_id = int(self.user_sessions.get(ctx.author.id))
        if campaign_id:
            await ctx.send(f"Your current campaign ID is: {campaign_id}")
        else:
            await ctx.send("You have not selected a campaign yet. Use !select_campaign to select one.")

    @commands.command(name="add_character")
    async def add_character(self, ctx):
        """
        Add a player character to a campaign by hitting the /players/ API endpoint.
        Checks if a campaign is already selected.
        Usage: !add_character
        """
        # Check if the user has already selected a campaign
        campaign_id = self.user_sessions.get(ctx.author.id)
        if not campaign_id:
            await ctx.send("You have not selected a campaign yet. Use !select_campaign to select one.")
            return

        # Prompt for the character ID
        await ctx.send("Please enter the character ID:")

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        try:
            character_id_msg = await self.bot.wait_for("message", timeout=60.0, check=check)
            character_id = character_id_msg.content
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Adding character to campaign canceled.")
            return

        # Prepare the API URL and payload
        url = f"{self.api_base_url}/players/"
        payload = {
            "character_id": character_id,
            "campaign_id": campaign_id
        }

        try:
            # Send the POST request to the API
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                await ctx.send(f"Character '{character_id}' added to campaign '{campaign_id}' successfully!")
            else:
                error_detail = response.json().get("detail", "Unknown error")
                await ctx.send(f"Failed to add character to campaign: {error_detail}")
        except Exception as e:
            await ctx.send(f"An error occurred while adding the character to the campaign: {e}")

    @commands.command(name="select_player")
    async def select_player(self, ctx):
        """
        List all players in the currently selected campaign and allow the user to select one.
        Usage: !select_player
        """
        # Get the currently selected campaign ID for the user
        campaign_id = self.user_sessions.get(ctx.author.id)
        if not campaign_id:
            await ctx.send("You have not selected a campaign yet. Use !select_campaign to select one.")
            return

        url = f"{self.api_base_url}/players/{campaign_id}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                pcs = response.json()
                if pcs:
                    # Create a view with buttons for each player
                    view = View(timeout=60)  # Set a timeout for the view
                    player_selected = False  # Flag to track if a player is selected

                    for pc in pcs:
                        pc_name, character_id, class_level = pc
                        button = Button(label=f"{pc_name} ({class_level})", style=discord.ButtonStyle.primary)

                        # Define the callback for the button
                        async def button_callback(interaction: discord.Interaction, pc_name=pc_name):
                            self.user_sessions["character_name"] = pc_name
                            await interaction.response.send_message(f"Player '{pc_name}' selected!", ephemeral=True)
                            nonlocal player_selected
                            player_selected = True  # Set the flag to True
                            view.stop()  # Stop the view to continue execution

                        button.callback = button_callback
                        view.add_item(button)

                    # Send the message with the buttons
                    await ctx.send("**Select a player character:**", view=view)

                    # Wait for the user to interact with the buttons
                    await view.wait()

                    # Check if a player was selected
                    selected_pc = self.user_sessions.get("character_name")
                    if not player_selected:
                        await ctx.send("No player character selected.")
                        return
                else:
                    await ctx.send("No players found in the selected campaign.")
                    return
            else:
                await ctx.send(f"Failed to list players: {response.json().get('detail', 'Unknown error')}")
                return
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
            return

    @commands.command(name="roll_loot")
    async def roll_loot(self, ctx):
        """
        Roll loot for the currently selected player in the selected campaign.
        Usage: !roll_loot
        """
        # Check if the command is being run in the correct channel
        dm_channel_id = os.getenv("DM_CHANNEL")  # Get the DM channel ID from the environment variable
        if not dm_channel_id:
            await ctx.send("DM_CHANNEL environment variable is not set.")
            return

        if str(ctx.channel.id) != dm_channel_id:
            await ctx.send("This command can only be run in the designated DM channel.")
            return

        # Get the currently selected campaign ID for the user
        campaign_id = self.user_sessions.get(ctx.author.id)
        if not campaign_id:
            await ctx.send("You have not selected a campaign yet. Use !select_campaign to select one.")
            return

        # Get the currently selected player character for the user
        selected_pc = self.user_sessions.get("character_name")
        if not selected_pc:
            await ctx.send("You have not selected a player character yet.")
            # Run the select_player command
            await self.select_player(ctx)
            # Recheck if a player has been selected
            selected_pc = self.user_sessions.get("character_name")
            if not selected_pc:
                await ctx.send("No player character selected. Aborting loot roll.")
                return

        # Call the roll loot API
        url = f"{self.api_base_url}/loot/{campaign_id}/roll/?character_name={selected_pc}"
        try:
            response = requests.post(url)
            if response.status_code == 200:
                loot, item_urls = response.json()
                if not loot:
                    await ctx.send("No loot was rolled.")
                    return

                # Create a view with buttons for each loot item
                view = View()
                loot_selected = False  # Flag to track if loot was selected

                for item in loot:
                    button = Button(label=item, style=discord.ButtonStyle.primary)

                    # Define the callback for the button
                    async def button_callback(interaction: discord.Interaction, item=item):
                        self.user_sessions["selected_loot"] = item  # Save the selected loot item
                        await interaction.response.send_message(f"You selected: {item}", ephemeral=True)
                        nonlocal loot_selected
                        loot_selected = True  # Set the flag to True
                        view.stop()  # Stop the view to continue execution

                    button.callback = button_callback
                    view.add_item(button)

                # Send the message with the buttons
                urls_message = "\n".join([f"- <{url}>" for url in item_urls])
                await ctx.send("**Select a loot item:**", view=view)
                await ctx.send(f"**Loot URLs:**\n{urls_message}")

                # Wait for the user to interact with the buttons
                await view.wait()

                # Check if loot was selected
                selected_loot = self.user_sessions.get("selected_loot")
                if not loot_selected:
                    await ctx.send("No loot item selected.")
                    return

                # Confirm the selected loot
                await ctx.send(f"You selected the loot item: {selected_loot}")
                # Send the selected loot to the player channel
                player_channel_id = os.getenv("PLAYER_CHANNEL")  # Get the player channel ID from the environment variable
                if player_channel_id:
                    player_channel = self.bot.get_channel(int(player_channel_id))
                    if player_channel:
                        await player_channel.send(f"- {selected_pc} | {selected_loot}")
                    else:
                        await ctx.send("Player channel not found.")
            else:
                await ctx.send(f"Failed to roll loot: {response.json().get('detail', 'Unknown error')}")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command(name="add_loot_source")
    async def add_loot_source(self, ctx):
        """
        Add loot sources to a campaign by hitting the /loot/{campaign_id}/sources/ API endpoint.
        Usage: !add_loot_source
        """
        # Check if the user has already selected a campaign
        campaign_id = self.user_sessions.get(ctx.author.id)
        if not campaign_id:
            await ctx.send("You have not selected a campaign yet. Use !select_campaign to select one.")
            return

        # Ensure campaign_id is an integer
        campaign_id = int(campaign_id)

        # Define available loot sources
        available_sources = ["DMG'24", "PHB'24", "ERLW", "TCE", "XGE"]

        # Create a view with a Select dropdown and a Button
        class LootSourceView(View):
            def __init__(self, api_base_url, campaign_id):
                super().__init__(timeout=60)
                self.campaign_id = campaign_id
                self.api_base_url = api_base_url
                self.selected_sources = []

                # Add a Select dropdown for loot sources
                self.select = Select(
                    placeholder="Select loot sources...",
                    options=[
                        discord.SelectOption(label=source, value=source) for source in available_sources
                    ],
                    min_values=1,  # Minimum number of selections
                    max_values=len(available_sources),  # Maximum number of selections
                )
                self.add_item(self.select)

                # Add a Button to submit the selected sources
                self.action_button = Button(label="Select", style=discord.ButtonStyle.primary)
                self.action_button.callback = self.select_callback
                self.add_item(self.action_button)

            async def select_callback(self, interaction: discord.Interaction):
                # Store the selected loot sources
                self.selected_sources = self.select.values
                if not self.selected_sources:
                    await interaction.response.send_message(
                        "No loot sources selected. Please select at least one.", ephemeral=True
                    )
                    return

                # Update the button to say "Add" and change its functionality
                self.action_button.label = "Add"
                self.action_button.callback = self.add_callback
                await interaction.response.edit_message(
                    content=f"Selected loot sources: {', '.join(self.selected_sources)}",
                    view=self
                )

            async def add_callback(self, interaction: discord.Interaction):
                if not self.selected_sources:
                    await interaction.response.send_message(
                        "No loot sources selected. Please select at least one.", ephemeral=True
                    )
                    return

                # Prepare the API URL and payload
                url = f"{self.api_base_url}/loot/{self.campaign_id}/sources/"
                payload = self.selected_sources  # Send the list directly as the payload

                # Log the payload for debugging
                logging.info(f"Payload for adding loot sources: {payload}")

                try:
                    # Send the POST request to the API
                    response = requests.post(url, json=payload)
                    logging.info(f"API Response: {response.status_code} - {response.text}")

                    if response.status_code == 200:
                        await interaction.response.send_message(
                            f"Loot sources added successfully to campaign '{self.campaign_id}'!", ephemeral=True
                        )
                    else:
                        error_detail = response.json().get("detail", "Unknown error")
                        await interaction.response.send_message(
                            f"Failed to add loot sources: {error_detail}", ephemeral=True
                        )
                except Exception as e:
                    await interaction.response.send_message(
                        f"An error occurred while adding loot sources: {e}", ephemeral=True
                    )
                    logging.exception("Exception occurred while adding loot sources")

                # Stop the view after the button is clicked
                self.stop()

        # Pass the api_base_url to the LootSourceView
        view = LootSourceView(self.api_base_url, campaign_id)
        await ctx.send("Select loot sources to add to the campaign:", view=view)

        # Wait for the view to timeout or be stopped
        await view.wait()
        if not view.is_finished():
            await ctx.send("You took too long to respond. Adding loot sources canceled.")

    @commands.command(name="list_loot_sources")
    async def list_loot_sources(self, ctx):
        """
        List all loot sources for the currently selected campaign.
        Usage: !list_loot_sources
        """
        # Check if the user has already selected a campaign
        campaign_id = self.user_sessions.get(ctx.author.id)
        if not campaign_id:
            await ctx.send("You have not selected a campaign yet. Use !select_campaign to select one.")
            return

        # Prepare the API URL
        url = f"{self.api_base_url}/loot/{campaign_id}/sources/"

        try:
            # Send the GET request to the API
            response = requests.get(url)
            if response.status_code == 200:
                loot_sources = response.json()
                if loot_sources:
                    # Format the loot sources into a readable list
                    formatted_sources = "\n".join(f"- {source}" for source in loot_sources)
                    await ctx.send(f"**Loot Sources for Campaign {campaign_id}:**\n{formatted_sources}")
                else:
                    await ctx.send(f"No loot sources found for campaign {campaign_id}.")
            else:
                error_detail = response.json().get("detail", "Unknown error")
                await ctx.send(f"Failed to list loot sources: {error_detail}")
        except Exception as e:
            await ctx.send(f"An error occurred while listing loot sources: {e}")

async def setup(bot):
    await bot.add_cog(AttdmCog(bot))