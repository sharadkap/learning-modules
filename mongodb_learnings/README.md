# MongoDB with Python

This project contains advanced use cases and examples for using MongoDB with Python (`pymongo`).

## Prerequisites
- Python 3.8+
- A MongoDB instance (e.g., Railway, Atlas, or Local)
- `pymongo` and `python-dotenv`

## Music Industry Use Cases
1. **[01_music_crud.py](./01_music_crud.py)**: Tracking songs with **ISRC codes**, unique indexing, and atomic play-count increments (`$inc`).
2. **[02_music_aggregation.py](./02_music_aggregation.py)**: Building a **Trending Dashboard**. Calculate top genres and artist reach using `$group` and `$addToSet`.
3. **[03_music_modeling.py](./03_music_modeling.py)**: The **Album vs. Playlist** dilemma. Learn when to embed (Tracks in an Album) vs. reference (Songs in a Playlist).
4. **[04_music_bulk_ops.py](./04_music_bulk_ops.py)**: Mass-syncing **Trending Scores** from external APIs using `bulk_write`.

## Setup
1. **Create a Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your Railway MongoDB URI.
3. **Initialize the Database**:
   Run the setup script to create collections, indexes, and sample data automatically:
   ```bash
   python setup_db.py
   ```
