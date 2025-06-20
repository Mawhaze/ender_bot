import aiohttp
import asyncio
import ffmpeg
import os
import logging
import tempfile
import traceback
import subprocess
import re

from datetime import datetime
from discord.ext import commands
from discord.ui import Button, View


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
    )

class TranscribeCog(commands.Cog):
    """
    Commands for transcribing video and audio files.
    This requires an api endpoint running the faster-whisper model to handle transcription.
    """
    def __init__(self, bot):
        self.bot = bot
        self.audio_files = os.getenv("SOURCE_PATH")
        self.cuda_api_url = os.getenv("CUDA_API_URL")
        self.completed_files = os.getenv("COMPLETED_PATH")
        self.tmp_dir = os.getenv("TMP_DIR")

    def detect_audio_silence(self, input_file, silence_threshold='-30dB', silence_duration=1):
        """
        Use ffmpeg-python to detect silence in the file
        Returns a list of silence points to split the file for transcription
        """
        cmd = [
            'ffmpeg', '-i', input_file,
            '-af', f'silencedetect=noise={silence_threshold}:d={silence_duration}',
            '-f', 'null', '-'
        ]
        try:
            result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
            output = result.stderr
            logging.debug(f"ffmpeg silence detect output: {output}")
            silence_ends = [float(m.group(1)) for m in re.finditer(r'silence_end: (\d+(\.\d+)?)', output)]
            logging.info(f"Detected silence ends at: {silence_ends}")
            return silence_ends
        except Exception as e:
            logging.error(f"Error detecting silence: {e}")
            raise
    
    def split_audio_silence(self, input_file, silence_ends, ext):
        """
        Splits the audio file at the silent sections to ease transcription
        """
        segment_files = []
        prev_end = 0
        for idx, end in enumerate(silence_ends + [None]):
            start = prev_end
            duration = (end - start) if end else None
            segment_file = tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False, dir=self.tmp_dir)
            segment_file.close
            input_kwargs = {'ss': start}
            if duration:
                input_kwargs['t'] = duration
            try:
                logging.info(f"Creating segment {idx}: start={start}, duration={duration}, file={segment_file.name}")
                (
                    ffmpeg
                    .input(input_file, **input_kwargs)
                    .output(segment_file.name, c='copy')
                    .overwrite_output()
                    .run(quiet=True)
                )
                segment_files.append(segment_file.name)
            except Exception as e:
                logging.error(f"Error creating segment {idx}: {e}")
                raise
            prev_end = end if end else prev_end
        logging.info(f"Creating segments: {segment_files}")
        return segment_files
    
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

    def create_button_callback(self, ctx, video_file_path, file, silence_threshold='-30dB', silence_duration=1):
        async def button_callback(interaction):
            try:
                await interaction.response.send_message(f"Running silence detection on {video_file_path} and transcribing...")

                ext = os.path.splitext(file)[1][1:]
                silence_ends = await asyncio.get_event_loop().run_in_executor(
                    None, self.detect_audio_silence, video_file_path, silence_threshold, silence_duration
                )
                segment_files = await asyncio.get_event_loop().run_in_executor(
                    None, self.split_audio_silence, video_file_path, silence_ends, ext
                )

                results = []
                timeout = aiohttp.ClientTimeout(total=600)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    for idx, segment_path in enumerate(segment_files):
                        form = aiohttp.FormData()
                        with open(segment_path, "rb") as segf:
                            form.add_field('file', segf, filename=f"{file}.part{idx}")
                            form.add_field('language', 'en')
                            form.add_field('model', 'faster-whisper-med-en-gpu')
                            logging.info(f"Uploading segment {idx}: {segment_path}")
                            try:
                                async with session.post(self.cuda_api_url, data=form) as response:
                                    if response.status == 200:
                                        transcription_result = await response.json()
                                        results.append(transcription_result.get("text", ""))
                                        logging.info(f"Segment {idx} transcribed successfully.")
                                    else:
                                        text = await response.text()
                                        logging.info(f"Segment {idx+1} transcription failed: {text}")
                                        await ctx.send(f"Segment {idx+1} transcription failed: {text}")
                            except asyncio.TimeoutError:
                                logging.error(f"Timeout while uploading segment {idx} to CUDA API")
                                await ctx.send(f"Timeout while uploading segment {idx} to CUDA API")
                                continue
                
                # Combine and save results
                combined_text = "\n".join(results)
                date_str = datetime.now().strftime("%Y-%m-%d")
                file_header = os.path.splitext(file)[0]
                output_file_path = os.path.join(self.completed_files, f"{file_header}_{date_str}.txt")
                try:
                    with open(output_file_path, "w") as output_file:
                        output_file.write(combined_text)
                    logging.info(f"Transcription completed! Output saved to {output_file_path}")
                    await ctx.send(f"Transcription completed! Output saved to {output_file_path}")
                except Exception as e:
                    logging.error(f"Error writing transcription output: {e}")
                    await ctx.send("Failed to save transcription output.")

            except Exception as e:
                logging.error(f"Error during transcription: {e}")
                logging.error(traceback.format_exc())
                await ctx.send("An error occurred during transcription.")
            finally:
                if segment_files:
                    for segment_path in segment_files:
                        if os.path.exists(segment_path):
                            try:
                                os.unlink(segment_path)
                                logging.info(f"Deleted temp segment file: {segment_path}")
                            except Exception as e:
                                logging.warning(f"Could not delete temp segment file {segment_path}: {e}")

        return button_callback

async def setup(bot):
    await bot.add_cog(TranscribeCog(bot))
    logging.info("Transcription cog loaded successfully.")
