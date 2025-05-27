import asyncio
import discord
import json
import logging
import os
import requests
from discord.ext import commands
from discord.ui import Button, View

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
    )

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
                    super().__init__(timeout=300)
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

        # Helper methods to run the commands
        async def run_create_campaign(ctx):
            await self.create_campaign(ctx)
            await self.select_campaign(ctx)

        async def run_select_campaign(ctx):
            await self.select_campaign(ctx)

        # Start by showing the main menu
        await show_main_menu()

    async def show_action_menu(self, ctx):
        """
        Show the action menu with options for `roll_loot`, `add_character`, `add_loot_source`, and `list_loot_sources`.
        """
        class ActionMenuView(View):
            def __init__(self, cog):
                super().__init__(timeout=None)
                self.cog = cog

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

                # Button for quitting the action menu
                self.quit_button = Button(label="Quit", style=discord.ButtonStyle.danger)
                self.quit_button.callback = self.quit_callback
                self.add_item(self.quit_button)

            async def roll_loot_callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                await self.cog.roll_loot(ctx)
                await self.cog.show_action_menu(ctx)

            async def add_character_callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                await self.cog.add_character(ctx)
                await self.cog.show_action_menu(ctx)

            async def add_loot_source_callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                await self.cog.add_loot_source(ctx)
                await self.cog.show_action_menu(ctx)

            async def list_loot_sources_callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                await self.cog.list_loot_sources(ctx)
                await self.cog.show_action_menu(ctx)

            async def quit_callback(self, interaction: discord.Interaction):
                await interaction.response.send_message("Ending the dnd session.", ephemeral=True)
                self.stop()

        await ctx.send("**Action Menu:**", view=ActionMenuView(self))

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
            logging.warning("Campaign creation timed out.")
            return

        # Prompt for the DM name
        await ctx.send("Please enter the DM name:")

        try:
            dm_name_msg = await self.bot.wait_for("message", timeout=60.0, check=check)
            dm_name = dm_name_msg.content
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Campaign creation canceled.")
            logging.warning("DM name input timed out.")
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
            logging.info(f"Sending POST request to {url} with payload: {payload}")
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                campaign_id = data.get("campaign_id")
                self.user_sessions[ctx.author.id] = int(campaign_id)
                await ctx.send(f"Campaign '{campaign_name}' created successfully! (ID: {campaign_id})")
                logging.info(f"Campaign '{campaign_name}' created successfully with ID: {campaign_id}")
            else:
                error_detail = response.json().get("detail", "Unknown error")
                await ctx.send(f"Failed to create campaign: {error_detail}")
                logging.error(f"Failed to create campaign: {error_detail}")
        except Exception as e:
            await ctx.send(f"An error occurred while creating the campaign: {e}")
            logging.error(f"An error occurred while creating the campaign: {e}")

    @commands.command(name="select_campaign")
    async def select_campaign(self, ctx):
        """
        List all campaigns.
        Usage: !select_campaign
        """
        url = f"{self.api_base_url}/campaigns/"
        try:
            logging.info(f"Fetching campaigns from {url}")
            response = requests.get(url)
            if response.status_code == 200:
                campaigns = response.json()
                if campaigns:
                    class SelectCampaignView(View):
                        def __init__(self, cog):
                            super().__init__(timeout=60)
                            self.cog = cog  # Reference to the AttdmCog instance
                            self.selected_campaign = None  # Store the selected campaign

                            for campaign in campaigns:
                                campaign_id, campaign_name, dm_name, _ = campaign
                                button = Button(label=f"{campaign_name} (DM: {dm_name})", style=discord.ButtonStyle.primary)

                                # Define the callback for the button
                                async def button_callback(interaction: discord.Interaction, campaign_id=campaign_id):
                                    self.cog.user_sessions[ctx.author.id] = int(campaign_id)
                                    self.selected_campaign = campaign_id
                                    await interaction.response.send_message(
                                        f"Campaign '{campaign_name}' selected! (ID: {campaign_id})", ephemeral=True
                                    )
                                    logging.info(f"Campaign '{campaign_name}' selected with ID: {campaign_id}")
                                    self.stop()  # Stop the view to continue execution

                                button.callback = button_callback
                                self.add_item(button)

                    # Create the view and send the campaign selection message
                    view = SelectCampaignView(self)
                    await ctx.send("**Select a campaign:**", view=view)

                    # Wait for the user to make a selection or for the view to timeout
                    await view.wait()

                    # Check if a campaign was selected
                    if view.selected_campaign:
                        # Transition to the action menu after a campaign is selected
                        await self.show_action_menu(ctx)
                    else:
                        await ctx.send("No campaign selected. Returning to the main menu.")
                        logging.warning("No campaign selected.")
                else:
                    await ctx.send("No campaigns found.")
                    logging.warning("No campaigns found.")
            else:
                error_detail = response.json().get("detail", "Unknown error")
                await ctx.send(f"Failed to list campaigns: {error_detail}")
                logging.error(f"Failed to list campaigns: {error_detail}")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
            logging.error(f"An error occurred while listing campaigns: {e}")

    @commands.command(name="current_campaign")
    async def current_campaign(self, ctx):
        """
        Display the currently selected campaign for the user.
        Usage: !current_campaign
        """
        campaign_id = self.user_sessions.get(ctx.author.id)
        if campaign_id:
            logging.info(f"User {ctx.author.id} is currently in campaign {campaign_id}.")
            await ctx.send(f"Your current campaign ID is: {campaign_id}")
        else:
            logging.warning(f"User {ctx.author.id} has not selected a campaign.")
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
            logging.warning(f"User {ctx.author.id} attempted to add a character without selecting a campaign.")
            await ctx.send("You have not selected a campaign yet. Use !select_campaign to select one.")
            return

        # Prompt for the character ID
        await ctx.send("Please enter the character ID:")

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        try:
            character_id_msg = await self.bot.wait_for("message", timeout=60.0, check=check)
            character_id = character_id_msg.content
            logging.info(f"User {ctx.author.id} provided character ID: {character_id}.")
        except asyncio.TimeoutError:
            logging.warning(f"User {ctx.author.id} took too long to provide a character ID.")
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
            logging.info(f"Sending POST request to {url} with payload: {payload}")
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                logging.info(f"Character '{character_id}' added to campaign '{campaign_id}' successfully.")
                await ctx.send(f"Character '{character_id}' added to campaign '{campaign_id}' successfully!")
            else:
                error_detail = response.json().get("detail", "Unknown error")
                logging.error(f"Failed to add character to campaign: {error_detail}")
                await ctx.send(f"Failed to add character to campaign: {error_detail}")
        except Exception as e:
            logging.error(f"An error occurred while adding the character to the campaign: {e}")
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
            logging.warning(f"User {ctx.author.id} attempted to select a player without selecting a campaign.")
            await ctx.send("You have not selected a campaign yet. Use !select_campaign to select one.")
            return

        url = f"{self.api_base_url}/players/{campaign_id}/"
        try:
            logging.info(f"Fetching players for campaign {campaign_id} from {url}.")
            response = requests.get(url)
            if response.status_code == 200:
                pcs = response.json()
                if pcs:
                    logging.info(f"Players found for campaign {campaign_id}: {pcs}.")
                    view = View(timeout=60)
                    player_selected = False
                    for pc in pcs:
                        pc_name, character_id, class_level = pc
                        button = Button(label=f"{pc_name} ({class_level})", style=discord.ButtonStyle.primary)

                        async def button_callback(interaction: discord.Interaction, pc_name=pc_name):
                            self.user_sessions["character_name"] = pc_name
                            self.user_sessions["character_id"] = character_id
                            logging.info(f"User {ctx.author.id} selected player '{pc_name}'.")
                            await interaction.response.send_message(f"Player '{pc_name}' selected!", ephemeral=True)
                            nonlocal player_selected
                            player_selected = True
                            view.stop()
                        button.callback = button_callback
                        view.add_item(button)

                    await ctx.send("**Select a player character:**", view=view)
                    await view.wait()

                    # Check if a player was selected
                    selected_pc = self.user_sessions.get("character_name")
                    if not player_selected:
                        logging.warning(f"User {ctx.author.id} did not select a player.")
                        await ctx.send("No player character selected.")
                        return
                else:
                    logging.warning(f"No players found for campaign {campaign_id}.")
                    await ctx.send("No players found in the selected campaign.")
                    return
            else:
                error_detail = response.json().get("detail", "Unknown error")
                logging.error(f"Failed to list players for campaign {campaign_id}: {error_detail}")
                await ctx.send(f"Failed to list players: {error_detail}")
                return
        except Exception as e:
            logging.error(f"An error occurred while listing players for campaign {campaign_id}: {e}")
            await ctx.send(f"An error occurred: {e}")
            return

    @commands.command(name="delete_pc")
    async def delete_pc(self, ctx):
        """
        Delete a player character. Requires the same character id used to import a character
        """
        campaign_id = self.user_sessions.get(ctx.author.id)
        if not campaign_id:
            logging.warning(f"No campaign selected")
        await self.select_player(ctx)
        character_id = self.user_sessions.get("character_id")
        url = f"{self.api_base_url}/player/{campaign_id}/delete/?character_id={character_id}"
        try:
            response = requests.post(url)
            if response.status_code == 200:
                logging.info(f"{character_id} deleted")
                await ctx.send(f"Delete {character_id}")
            else:
                logging.info(f"Failed to delete {character_id}")
                await ctx.send(f"Failed to delete {character_id}")
        except Exception as e:
            logging.error(f"An error occurred while deleting {character_id}: {e}")
            await ctx.send(f"An error occurred: {e}")

    @commands.command(name="roll_loot")
    async def roll_loot(self, ctx):
        """
        Roll loot for the currently selected player in the selected campaign.
        Usage: !roll_loot
        """
        # Check if the command is being run in the correct channel
        dm_channel_id = os.getenv("DM_CHANNEL")
        if not dm_channel_id:
            logging.error("DM_CHANNEL environment variable is not set.")
            await ctx.send("DM_CHANNEL environment variable is not set.")
            return

        if str(ctx.channel.id) != dm_channel_id:
            logging.warning(f"Command attempted in incorrect channel: {ctx.channel.id}")
            await ctx.send("This command can only be run in the designated DM channel.")
            return

        # Get the currently selected campaign ID for the user
        campaign_id = self.user_sessions.get(ctx.author.id)
        if not campaign_id:
            logging.warning(f"User {ctx.author.id} attempted to roll loot without selecting a campaign.")
            await ctx.send("You have not selected a campaign yet. Use !select_campaign to select one.")
            return

        # Get the currently selected player character for the user
        selected_pc = self.user_sessions.get("character_name")
        if not selected_pc:
            logging.warning(f"User {ctx.author.id} attempted to roll loot without selecting a player.")
            await ctx.send("You have not selected a player character yet.")
            await self.select_player(ctx)
            selected_pc = self.user_sessions.get("character_name")
            if not selected_pc:
                logging.warning(f"User {ctx.author.id} did not select a player after being prompted.")
                await ctx.send("No player character selected. Aborting loot roll.")
                return

        # Call the roll loot API
        await ctx.send(f"Rolling loot for {selected_pc}")
        url = f"{self.api_base_url}/loot/{campaign_id}/roll/?character_name={selected_pc}"
        try:
            logging.info(f"Rolling loot for campaign {campaign_id} and player {selected_pc} via {url}.")
            response = requests.post(url)
            if response.status_code == 200:
                loot, item_urls = response.json()
                if not loot:
                    logging.info(f"No loot rolled for campaign {campaign_id} and player {selected_pc}.")
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
                        logging.info(f"User {ctx.author.id} selected loot item: {item}.")
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
                    logging.warning(f"User {ctx.author.id} did not select any loot item.")
                    await ctx.send("No loot item selected.")
                    return

                # Confirm the selected loot
                logging.info(f"User {ctx.author.id} confirmed loot item: {selected_loot}.")
                await ctx.send(f"You selected the loot item: {selected_loot}")
                # Send the selected loot to the player channel
                player_channel_id = os.getenv("PLAYER_CHANNEL")  # Get the player channel ID from the environment variable
                if player_channel_id:
                    player_channel = self.bot.get_channel(int(player_channel_id))
                    if player_channel:
                        await player_channel.send(f"- {selected_pc} | {selected_loot}")
                        logging.info(f"Loot item '{selected_loot}' sent to player channel for player {selected_pc}.")
                        del self.user_sessions["selected_loot"]
                        del self.user_sessions["character_name"]
                    else:
                        logging.error("Player channel not found.")
                        await ctx.send("Player channel not found.")
            else:
                error_detail = response.json().get("detail", "Unknown error")
                logging.error(f"Failed to roll loot: {error_detail}")
                await ctx.send(f"Failed to roll loot: {error_detail}")
        except Exception as e:
            logging.error(f"An error occurred while rolling loot: {e}")
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
            logging.warning(f"User {ctx.author.id} attempted to add loot sources without selecting a campaign.")
            await ctx.send("You have not selected a campaign yet. Use !select_campaign to select one.")
            return

        # Define available loot sources
        available_sources = ["DMG'24", "PHB'24", "ERLW", "TCE", "XGE"]

        # Create a view with buttons for each loot source
        class LootSourceButtonView(View):
            def __init__(self, api_base_url, campaign_id, available_sources):
                super().__init__(timeout=60)
                self.api_base_url = api_base_url
                self.campaign_id = campaign_id
                self.selected_sources = []

                # Add a button for each loot source
                for source in available_sources:
                    button = Button(label=source, style=discord.ButtonStyle.primary)
                    button.callback = self.create_button_callback(source)
                    self.add_item(button)

                # Add a submit button
                self.submit_button = Button(label="Submit", style=discord.ButtonStyle.success)
                self.submit_button.callback = self.submit_callback
                self.add_item(self.submit_button)

            def create_button_callback(self, source):
                async def button_callback(interaction: discord.Interaction):
                    if source in self.selected_sources:
                        self.selected_sources.remove(source)
                        logging.info(f"User {ctx.author.id} removed loot source: {source}.")
                        await interaction.response.send_message(f"Removed {source} from selection.", ephemeral=True)
                    else:
                        self.selected_sources.append(source)
                        logging.info(f"User {ctx.author.id} added loot source: {source}.")
                        await interaction.response.send_message(f"Added {source} to selection.", ephemeral=True)

                return button_callback

            async def submit_callback(self, interaction: discord.Interaction):
                await interaction.response.defer(ephemeral=True)

                if not self.selected_sources:
                    logging.warning(f"User {ctx.author.id} submitted without selecting any loot sources.")
                    await interaction.followup.send("No loot sources selected. Please select at least one.", ephemeral=True)
                    return

                # Prepare the API URL and payload
                url = f"{self.api_base_url}/loot/{self.campaign_id}/sources/"
                payload = self.selected_sources

                try:
                    # Send the POST request to the API
                    logging.info(f"Sending POST request to {url} with payload: {payload}")
                    response = requests.post(url, json=payload)
                    if response.status_code == 200:
                        logging.info(f"Loot sources added successfully to campaign '{self.campaign_id}'.")
                        await interaction.followup.send(
                            f"Loot sources added successfully to campaign '{self.campaign_id}'!", ephemeral=True
                        )
                    else:
                        error_detail = response.json().get("detail", "Unknown error")
                        logging.error(f"Failed to add loot sources: {error_detail}")
                        await interaction.followup.send(
                            f"Failed to add loot sources: {error_detail}", ephemeral=True
                        )
                except Exception as e:
                    logging.error(f"An error occurred while adding loot sources: {e}")
                    await interaction.followup.send(
                        f"An error occurred while adding loot sources: {e}", ephemeral=True
                    )

                # Stop the view after submission
                self.stop()

        # Create the view and send the message
        view = LootSourceButtonView(self.api_base_url, campaign_id, available_sources)
        await ctx.send("Click on the buttons to select loot sources. Click 'Submit' when done:", view=view)

        # Wait for the view to timeout or be stopped
        await view.wait()
        if not view.is_finished():
            logging.warning(f"User {ctx.author.id} took too long to respond for adding loot sources.")
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
            logging.warning(f"User {ctx.author.id} attempted to list loot sources without selecting a campaign.")
            await ctx.send("You have not selected a campaign yet. Use !select_campaign to select one.")
            return

        # Prepare the API URL
        url = f"{self.api_base_url}/loot/{campaign_id}/sources/"

        try:
            # Send the GET request to the API
            logging.info(f"Fetching loot sources for campaign {campaign_id} from {url}.")
            response = requests.get(url)
            if response.status_code == 200:
                loot_sources = response.json()
                if loot_sources:
                    # Format the loot sources into a readable list
                    formatted_sources = "\n".join(f"- {source}" for source in loot_sources)
                    logging.info(f"Loot sources for campaign {campaign_id}: {formatted_sources}")
                    await ctx.send(f"**Loot Sources for Campaign {campaign_id}:**\n{formatted_sources}")
                else:
                    logging.info(f"No loot sources found for campaign {campaign_id}.")
                    await ctx.send(f"No loot sources found for campaign {campaign_id}.")
            else:
                error_detail = response.json().get("detail", "Unknown error")
                logging.error(f"Failed to list loot sources for campaign {campaign_id}: {error_detail}")
                await ctx.send(f"Failed to list loot sources: {error_detail}")
        except Exception as e:
            logging.error(f"An error occurred while listing loot sources for campaign {campaign_id}: {e}")
            await ctx.send(f"An error occurred while listing loot sources: {e}")

async def setup(bot):
    await bot.add_cog(AttdmCog(bot))
    logging.info("AttdmCog loaded successfully.")
