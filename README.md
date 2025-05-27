# Project Ender Discord Bot

## Overview

**Project Ender Discord Bot** A Python based Discord bot built to be a central user interface for 

---

**Modular Cog System**
  - Each major feature is implemented as a Discord cog for easy extension and maintenance.

## Features

- **Audio/Video Transcription**
    - `!transcribe_audio` provides a list of files in the transcription source folder.
    - Runs ffmpeg to detect silence in the audio file and split into smaller files
    - Requires API endpoint running the faster-whisper model for transcription

- **Assistant to the Dungeon Manager Integration**
    - `!dnd` and related commands provide campaign management features for DnD 5e.
    - Create, list, and update campaigns directly from Discord.
    - Manage player characters, loot, and session notes.
    - Integrates with a PostgreSQL backend for persistent campaign data storage.