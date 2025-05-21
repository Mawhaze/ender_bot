import aiohttp
import ffmpeg
import json
import os
import logging
import tempfile

from datetime import datetime
from discord.ext import commands
from discord.ui import Button, View


# Configure logging
logging.basicConfig(
    filename=os.getenv("LOG_FILE", "tmp/logs/ender-bot.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
    )

class TranscribeCog(commands.Cog):
    """
    Commands for transcribing video and audio files.
    """
    def __init__(self, bot):
        self.bot = bot
        self.audio_files = os.getenv("SOURCE_PATH")
        self.cuda_api_url = os.getenv("CUDA_API_URL")
        self.completed_files = os.getenv("COMPLETED_PATH")

    @commands.command(name="transcribe_audio")
    async def transcribe_audio(self, ctx):
        try:
            files = os.listdir(self.audio_files)
            if not files:
                await ctx.send("No audio files found in the specified directory.")
                return
            
            view = View(timeout=300)
            for file in files:
                audio_file_path = os.path.join(self.audio_files, file)
                if os.path.isfile(audio_file_path):
                    label = file[:80]
                    custom_id = file[:100]
                    button = Button(label=label, custom_id=custom_id)
                    button.callback = self.create_button_callback(ctx, audio_file_path, file)
                    view.add_item(button)
                else:
                    await ctx.send(f"{file} is not a valid file.")
            await ctx.send(content= "Select the file to transcribe", view=view)

        except Exception as e:
            logging.error(f"Error listing audio files: {e}")
            await ctx.send("An error occurred while listing audio files.")

    def create_button_callback(self, ctx, video_file_path, file, segment_length=120, overlap=15):
        async def button_callback(interaction):
            try:
                await interaction.response.send_message(f"Transcribing {video_file_path} in 120s segments with 15s overlap...")

                # Probe video duration
                probe = ffmpeg.probe(video_file_path)
                duration = float(probe['format']['duration'])
                results = []
                ext = os.path.splitext(file)[1][1:]  # e.g., 'mp4'
                segment_idx = 0
                start = 0

                async with aiohttp.ClientSession() as session:
                    while start < duration:
                        actual_length = min(segment_length, duration - start)
                        segment_file = tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False)
                        segment_file.close()

                        (
                            ffmpeg
                            .input(video_file_path, ss=start, t=actual_length)
                            .output(segment_file.name, c='copy')
                            .overwrite_output()
                            .run(quiet=True)
                        )

                        # Send segments to transcription API
                        form = aiohttp.FormData()
                        with open(segment_file.name, "rb") as segf:
                            form.add_field('file', segf, filename=f"{file}.part{segment_idx}")
                            form.add_field('language', 'en')
                            form.add_field('model', 'faster-whisper-med-en-gpu')
                            async with session.post(self.cuda_api_url, data=form) as response:
                                if response.status == 200:
                                    transcription_result = await response.json()
                                    results.append(transcription_result.get("text", ""))
                                else:
                                    text = await response.text()
                                    await ctx.send(f"Segment {segment_idx+1} transcription failed: {text}")

                        os.unlink(segment_file.name)
                        segment_idx += 1
                        start += (segment_length - overlap)

                dedeuped_results = []
                checked_text = ""
                window = 300

                for idx, text in enumerate(results):
                    text = text.strip()
                    if not text:
                        continue
                    if checked_text:
                        max_overlap = min(window, len(checked_text), len(text))
                        for i in range(max_overlap, 0, -1):
                            if checked_text[-i:] == text[:i]:
                                overlap_found = i
                                break
                        text = text[overlap_found:]
                    dedeuped_results.append(text)
                    checked_text += text

                # Combine and save results
                combined_text = "\n".join(dedeuped_results)
                date_str = datetime.now().strftime("%Y-%m-%d")
                file_header = os.path.splitext(file)[0]
                output_file_path = os.path.join(self.completed_files, f"{file_header}_{date_str}.txt")
                with open(output_file_path, "w") as output_file:
                    output_file.write(combined_text)
                await ctx.send(f"Transcription completed! Output saved to {output_file_path}")

            except Exception as e:
                logging.error(f"Error during transcription: {e}")
                await ctx.send("An error occurred during transcription.")

        return button_callback

async def setup(bot):
    await bot.add_cog(TranscribeCog(bot))
    logging.info("Transcription cog loaded successfully.")
