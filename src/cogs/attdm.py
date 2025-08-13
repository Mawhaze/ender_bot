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

    # Menus
    @commands.command(name="dnd")
    async def dnd(self, ctx):
        """
        The main menu for the dnd bot section.
        Usage: !dnd
        """
        async def init_menu():
            """
            Show the main menu with options for `create_campaign` and `select_campaign`.
            """
            class InitMenuView(View):
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

            await ctx.send("**Campaign Selection Menu:**", view=InitMenuView(run_create_campaign, run_select_campaign))

        # Helper methods to run the commands
        async def run_create_campaign(ctx):
            await self.create_campaign(ctx)
            await self.select_campaign(ctx)

        async def run_select_campaign(ctx):
            await self.select_campaign(ctx)

        await init_menu()

    async def main_menu(self, ctx):
        """
        Show the action menu with options for `roll_loot`, `add_character`, `add_loot_source`, and `list_loot_sources`.
        """
        class MainMenuView(View):
            def __init__(self, cog):
                super().__init__(timeout=None)
                self.cog = cog

                # Rolling loot
                self.roll_loot_button = Button(label="Roll Loot", style=discord.ButtonStyle.primary)
                self.roll_loot_button.callback = self.roll_loot_callback
                self.add_item(self.roll_loot_button)

                # List Party Passive Stats
                self.list_stats_button = Button(label="List Passive Stats", style=discord.ButtonStyle.primary)
                self.list_stats_button.callback = self.list_stats_callback
                self.add_item(self.list_stats_button)

                # NPC and Location Menu
                self.lore_menu_button = Button(label="NPC & Locations Menu", style=discord.ButtonStyle.primary)
                self.lore_menu_button.callback = self.lore_menu_callback
                self.add_item(self.lore_menu_button)

                # Campaign Management Menu
                self.mgmt_menu_button = Button(label="Campaign Management Menu", style=discord.ButtonStyle.primary)
                self.mgmt_menu_button.callback = self.mgmt_menu_callback
                self.add_item(self.mgmt_menu_button)

                # End the Session
                self.quit_button = Button(label="Quit", style=discord.ButtonStyle.danger)
                self.quit_button.callback = self.quit_callback
                self.add_item(self.quit_button)

            async def roll_loot_callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                await self.cog.roll_loot(ctx)
                await self.cog.main_menu(ctx)

            async def list_stats_callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                await self.cog.list_passive_stats(ctx)
                await self.cog.main_menu(ctx)

            async def lore_menu_callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                await self.cog.campaign_lore_menu(ctx)

            async def mgmt_menu_callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                await self.cog.campaign_mgmt_menu(ctx)
            
            async def quit_callback(self, interaction: discord.Interaction):
                await interaction.response.send_message("Ending the dnd session.", ephemeral=True)
                self.stop()

        await ctx.send("**Main Menu:**", view=MainMenuView(self))

    async def campaign_lore_menu(self, ctx):
        """
        This menu is for managing a campaigns lore items. At this time, NPCs and Locations
        """
        class LoreMenuView(View):
            def __init__(self, cog):
                super().__init__(timeout=None)
                self.cog = cog

                # NPC Buttons
                self.add_npc_button = Button(label="Add NPC", style=discord.ButtonStyle.primary)
                self.add_npc_button.callback = self.add_npc_callback
                self.add_item(self.add_npc_button)

                self.edit_npc_button = Button(label="Edit NPC details", style=discord.ButtonStyle.primary)
                self.edit_npc_button.callback = self.edit_npc_callback
                self.add_item(self.edit_npc_button)

                self.delete_npc_button = Button(label="Delete NPC", style=discord.ButtonStyle.primary)
                self.delete_npc_button.callback = self.delete_npc_callback
                self.add_item(self.delete_npc_button)

                # Location Buttons
                self.add_location_button = Button(label="Add Location", style=discord.ButtonStyle.primary)
                self.add_location_button.callback = self.add_location_callback
                self.add_item(self.add_location_button)

                self.edit_location_button = Button(label="Edit Location", style=discord.ButtonStyle.primary)
                self.edit_location_button.callback = self.edit_location_callback
                self.add_item(self.edit_location_button)

                self.delete_location_button = Button(label="Delete Location", style=discord.ButtonStyle.primary)
                self.delete_location_button.callback = self.delete_location_callback
                self.add_item(self.delete_location_button)

                # Previous Menu
                self.menu_back_button = Button(label="Previous Menu", style=discord.ButtonStyle.danger)
                self.menu_back_button.callback = self.menu_back_callback
                self.add_item(self.menu_back_button)

            async def add_npc_callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                await self.cog.add_lore_item(ctx, "npcs")
                await self.cog.campaign_lore_menu(ctx)

            async def edit_npc_callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                await self.cog.edit_lore_item(ctx, "npcs")
                await self.cog.campaign_lore_menu(ctx)

            async def delete_npc_callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                await self.cog.delete_lore_item(ctx, "npcs")
                await self.cog.campaign_lore_menu(ctx)
            
            async def add_location_callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                await self.cog.add_lore_item(ctx, "locations")
                await self.cog.campaign_lore_menu(ctx)

            async def edit_location_callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                await self.cog.edit_lore_item(ctx, "locations")
                await self.cog.campaign_lore_menu(ctx)

            async def delete_location_callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                await self.cog.delete_lore_item(ctx, "locations")
                await self.cog.campaign_lore_menu(ctx)

            async def menu_back_callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                self.stop()
                await self.cog.main_menu(ctx)

        await ctx.send("**NPC & Location Menu:**", view=LoreMenuView(self))

    async def campaign_mgmt_menu(self, ctx):
        class MgmtMenuView(View):
            def __init__(self, cog):
                super().__init__(timeout=None)
                self.cog = cog

                # Loot Buttons
                self.add_loot_source_button = Button(label="Add Loot Source", style=discord.ButtonStyle.primary)
                self.add_loot_source_button.callback = self.add_loot_source_callback
                self.add_item(self.add_loot_source_button)

                self.list_loot_sources_button = Button(label="List Loot Sources", style=discord.ButtonStyle.primary)
                self.list_loot_sources_button.callback = self.list_loot_sources_callback
                self.add_item(self.list_loot_sources_button)

                # Player Character Buttons
                self.add_character_button = Button(label="Add Character", style=discord.ButtonStyle.primary)
                self.add_character_button.callback = self.add_character_callback
                self.add_item(self.add_character_button)

                self.list_party_button = Button(label="List Party Members", style=discord.ButtonStyle.primary)
                self.list_party_button.callback = self.list_party_callback
                self.add_item(self.list_party_button)

                self.update_character_info_button = Button(label="Update Party Character Sheets", style=discord.ButtonStyle.primary)
                self.update_character_info_button.callback = self.update_character_info_callback
                self.add_item(self.update_character_info_button)

                self.delete_character_button = Button(label="Delete Character", style=discord.ButtonStyle.danger)
                self.delete_character_button.callback = self.delete_character_callback
                self.add_item(self.delete_character_button)
                
                # Previous Menu
                self.menu_back_button = Button(label="Previous Menu", style=discord.ButtonStyle.danger)
                self.menu_back_button.callback = self.menu_back_callback
                self.add_item(self.menu_back_button)

            async def add_loot_source_callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                await self.cog.add_loot_source(ctx)
                await self.cog.campaign_mgmt_menu(ctx)

            async def list_loot_sources_callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                await self.cog.list_loot_sources(ctx)
                await self.cog.campaign_mgmt_menu(ctx)
            
            async def add_character_callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                await self.cog.add_character(ctx)
                await self.cog.campaign_mgmt_menu(ctx)
            
            async def list_party_callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                await self.cog.list_pc(ctx)
                await self.cog.campaign_mgmt_menu(ctx)

            async def update_character_info_callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                await self.cog.update_party_sheets(ctx)
                await self.cog.main_menu(ctx)

            async def delete_character_callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                await self.cog.delete_pc(ctx)
                await self.cog.campaign_mgmt_menu(ctx)
            
            async def menu_back_callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                self.stop()
                await self.cog.main_menu(ctx)

        await ctx.send("**Campaign Management Menu:**", view=MgmtMenuView(self))


    # Campaign Cogs
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
            "loot_books": []
        }

        try:
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
                            self.cog = cog
                            self.selected_campaign = None

                            for campaign in campaigns:
                                campaign_id, campaign_name, dm_name, _ = campaign
                                button = Button(label=f"{campaign_name} (DM: {dm_name})", style=discord.ButtonStyle.primary)

                                async def button_callback(interaction: discord.Interaction, campaign_id=campaign_id, campaign_name=campaign_name):
                                    self.cog.user_sessions[ctx.author.id] = int(campaign_id)
                                    self.selected_campaign = campaign_id
                                    await interaction.response.send_message(
                                        f"Campaign '{campaign_name}' selected! (ID: {campaign_id})", ephemeral=True
                                    )
                                    logging.info(f"Campaign '{campaign_name}' selected with ID: {campaign_id}")
                                    self.stop()

                                button.callback = button_callback
                                self.add_item(button)

                    # Create the view and send the campaign selection message
                    view = SelectCampaignView(self)
                    await ctx.send("**Select a campaign:**", view=view)

                    await view.wait()

                    # Check if a campaign was selected
                    if view.selected_campaign:
                        await self.main_menu(ctx)
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


    # Player Character Cogs
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

                        async def button_callback(interaction: discord.Interaction, pc_name=pc_name, character_id=character_id):
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
            logging.warning("No campaign selected")
        await self.select_player(ctx)
        character_id = self.user_sessions.get("character_id")
        url = f"{self.api_base_url}/players/{campaign_id}/delete/?character_id={character_id}"
        try:
            response = requests.delete(url)
            if response.status_code == 200:
                logging.info(f"{character_id} deleted")
                await ctx.send(f"Delete {character_id}")
                del self.user_sessions["character_id"]
            else:
                logging.info(f"Failed to delete {character_id}")
                await ctx.send(f"Failed to delete {character_id}")
        except Exception as e:
            logging.error(f"An error occurred while deleting {character_id}: {e}")
            await ctx.send(f"An error occurred: {e}")

    @commands.command(name="list_pc")
    async def list_pc(self, ctx):
        """
        List the current part characters.
        Later this will be updated to reflect only living party characters, with an additional solution for the rest
        """
        campaign_id = self.user_sessions.get(ctx.author.id)
        if not campaign_id:
            logging.warning("No campaign selected")
        
        url = f"{self.api_base_url}/players/{campaign_id}/"

        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data:
                    formatted = "\n".join([f"- {row[0]} (ID: {row[1]}, Class: {row[2]})" for row in data])
                    await ctx.send(f"**Party Member:**\n{formatted}")
                else:
                    await ctx.send("No party members found")
        except Exception as e:
            logging.error(f"An error occurred while list party members for {campaign_id}: {e}")
            await ctx.send(f"An error occurred: {e}")

    @commands.command(name="list_passive_stats")
    async def list_passive_stats(self, ctx):
        """
        List the party's passive stats for either Perception, Investigation, or Insight
        """
        campaign_id = self.user_sessions.get(ctx.author.id)
        if not campaign_id:
            logging.warning("No campaign selected")
        
        class PassiveStatSelectView(View):
            def __init__(self):
                super().__init__(timeout=30)
                self.selected_passive = None

                for stat in ["perception", "investigation", "insight"]:
                    button = Button(label=stat.capitalize(), style=discord.ButtonStyle.primary)
                    button.callback = self.selection_callback(stat)
                    self.add_item(button)
                
            def selection_callback(self, stat):
                async def callback(interaction: discord.Interaction):
                    self.selected_passive = stat
                    await interaction.response.defer()
                    self.stop()
                return callback
            
        view = PassiveStatSelectView()
        await ctx.send("Select the passive stat:", view=view)
        await view.wait()

        selected_passive = view.selected_passive
        if not selected_passive:
            await ctx.send("No passive stat selected.")
            logging.warning("No passive stat selected, aborting.")
            return
        
        url = f"{self.api_base_url}/players/{campaign_id}/passive-stats/?stat_name={selected_passive}"

        try:
            response = requests.get(url)
            if response.status_code == 200:
                stats = response.json()
                if stats:
                    formatted_stats = "\n".join([f"- {row[0]}: {row[1]}" for row in stats])
                    await ctx.send(f"**Party {selected_passive.capitalize()} Stats:**\n{formatted_stats}")
                else:
                    await ctx.send(f"No stats found for {selected_passive}.")
            else:
                error_detail = response.json().get("detail", "Unknown error")
                await ctx.send(f"Failed to list stats: {error_detail}")
                logging.error(f"Failed to list stats: {error_detail}")
        except Exception as e:
            logging.error(f"An error occurred while listing passive stats: {e}")
            await ctx.send(f"Error: {e}")

    @commands.command(name="update_party_sheets")
    async def update_party_sheets(self, ctx):
        """
        Update the character sheet information for the entire party. 
        This is helpful after leveling up to correct any changes.
        """
        campaign_id = self.user_sessions.get(ctx.author.id)
        if not campaign_id:
            logging.warning(f"Command attempted in incorrect channel: {ctx.channel.id}")
            await ctx.send("This command can only be run in the designated DM channel.")
            return
        
        url = f"{self.api_base_url}/players/{campaign_id}/update/"

        try:
            response = requests.put(url)
            if response.status_code == 200:
                await ctx.send("Updating the party's character info.")
                return
            else:
                await ctx.send("Error updating the party.")
                logging.error(f"Error updating party sheets. {response.status_code}: {response.json}")
        except Exception as e:
            logging.error(f"An error occurred updating character sheets. {e}")
            await ctx.send(f"Error: {e}")

    # Loot Cogs
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

        campaign_id = self.user_sessions.get(ctx.author.id)
        if not campaign_id:
            logging.warning(f"User {ctx.author.id} attempted to roll loot without selecting a campaign.")
            await ctx.send("You have not selected a campaign yet. Use !select_campaign to select one.")
            return

        await ctx.send("Select a character to roll loot for.")
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

                view = View()
                loot_selected = False
                for item in loot:
                    button = Button(label=item, style=discord.ButtonStyle.primary)

                    # Define the callback for the button
                    async def button_callback(interaction: discord.Interaction, item=item):
                        self.user_sessions["selected_loot"] = item
                        logging.info(f"User {ctx.author.id} selected loot item: {item}.")
                        await interaction.response.send_message(f"You selected: {item}", ephemeral=True)
                        nonlocal loot_selected
                        loot_selected = True
                        view.stop()

                    button.callback = button_callback
                    view.add_item(button)

                urls_message = "\n".join([f"- <{url}>" for url in item_urls])
                await ctx.send("**Select a loot item:**", view=view)
                await ctx.send(f"**Loot URLs:**\n{urls_message}")
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
                player_channel_id = os.getenv("PLAYER_CHANNEL")
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

        available_sources = ["DMG'24", "PHB'24", "ERLW", "TCE", "XGE"]

        class LootSourceButtonView(View):
            def __init__(self, api_base_url, campaign_id, available_sources):
                super().__init__(timeout=60)
                self.api_base_url = api_base_url
                self.campaign_id = campaign_id
                self.selected_sources = []

                for source in available_sources:
                    button = Button(label=source, style=discord.ButtonStyle.primary)
                    button.callback = self.create_button_callback(source)
                    self.add_item(button)

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
                await ctx.send("Adding loot sources, this can take a minute.")

                if not self.selected_sources:
                    logging.warning(f"User {ctx.author.id} submitted without selecting any loot sources.")
                    await interaction.followup.send("No loot sources selected. Please select at least one.", ephemeral=True)
                    return

                url = f"{self.api_base_url}/loot/{self.campaign_id}/sources/"
                payload = self.selected_sources

                try:
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

                self.stop()

        view = LootSourceButtonView(self.api_base_url, campaign_id, available_sources)
        await ctx.send("Click on the buttons to select loot sources. Click 'Submit' when done:", view=view)
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

        url = f"{self.api_base_url}/loot/{campaign_id}/sources/"

        try:
            logging.info(f"Fetching loot sources for campaign {campaign_id} from {url}.")
            response = requests.get(url)
            if response.status_code == 200:
                loot_sources = response.json()
                if loot_sources:
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


    # NPC/Location/Lore Cogs
    @commands.command(name="add_lore_item")
    async def add_lore_item(self, ctx, lore_category):
        """
        Add a new lore item, either Location or NPC
        """
        campaign_id = self.user_sessions.get(ctx.author.id)
        if not campaign_id:
            logging.warning("No campaign selected")
            await ctx.send("No campaign selected")
            return
        
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel
        
        # Prompt for the Lore item name and description
        await ctx.send(f"Please enter the {lore_category} name:")
        try:
            lore_item_name_msg = await self.bot.wait_for("message", timeout=60.0, check=check)
            lore_item_name = lore_item_name_msg.content
        except asyncio.TimeoutError:
            await ctx.send(f"You took too long to respond. {lore_category} creation canceled.")
            logging.warning("Creation timed out.")
            return
        await ctx.send(f"Please enter the {lore_category} description:")
        try:
            lore_item_desc_msg = await self.bot.wait_for("message", timeout=60.0, check=check)
            lore_item_desc = lore_item_desc_msg.content
        except asyncio.TimeoutError:
            await ctx.send(f"You took too long to respond. {lore_category} creation canceled.")
            logging.warning("Creation timed out.")
            return
        
        url = f"{self.api_base_url}/{lore_category}/"
        payload = {
            "campaign_id": campaign_id,
            "name": lore_item_name,
            "species": lore_item_desc
        }
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                logging.info(f"{lore_item_name} created successfully")
                await ctx.send(f"{lore_item_name} created successfully")
            else:
                logging.warning(f"Creating item: {lore_item_name} failed. {response.status_code}")
                await ctx.send(f"Creating item: {lore_item_name} failed")
        except Exception as e:
            logging.error(f"An error has occurred creating {lore_item_name}: {e}")
            await ctx.send(f"An error has occurred creating {lore_item_name}: {e}")

    @commands.command(name="edit_lore_item")
    async def edit_lore_item(self, ctx, lore_category):
        """
        Edit current campaign lore items
        """
        campaign_id = self.user_sessions.get(ctx.author.id)
        if not campaign_id:
            logging.warning("No campaign selected")
            await ctx.send("No campaign selected")
            return
        
        url = f"{self.api_base_url}/{lore_category}/{campaign_id}/"

        try:
            logging.info(f"Listing {lore_category} entries")
            response = requests.get(url)
            if response.status_code == 200:
                lore_items = response.json()
                formatted_item = "\n".join(f"- {item}" for item in lore_items)
                await ctx.send(f"**{lore_category} entries for {campaign_id}:**\n{formatted_item}")
            else:
                logging.info(f"No {lore_category} found")
                await ctx.send(f"No {lore_category} found")
        except Exception as e:
            logging.error(f"An error occurred while listing loot sources for campaign {campaign_id}: {e}")
            await ctx.send(f"An error occurred while listing loot sources: {e}")

async def setup(bot):
    await bot.add_cog(AttdmCog(bot))
    logging.info("AttdmCog loaded successfully.")
