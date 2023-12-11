# CS 308 Term Project - Musicee (Back-End)

## Project Overview

This project aims to develop an online system for collecting liked-song information from various sources and providing users with analyses and recommendations based on their musical preferences. 
The system focuses on user interaction and personalized music choice analysis without involving music streaming.

### ALL Functionalities

### Data Format

- **Basic Data Format:**
  
  - Collects song information, including track name, performer(s), album/media details, and user ratings.
  - Handles challenges like multiple performers and different versions of the same song.

### Data Collection

- **User Input:**
  - Allows manual song input through a user-friendly web/mobile interface.
  - Supports batch input via file uploads (.json).
  - Permits data transfer from a self-hosted or cloud database.
  - Enables users to rate non-rated songs/albums/performers and modify ratings over time.

### Analysis of Musical Choices

- **Statistical Information:**
  - Provides users with statistical insights into their preferences, filterable by date constraints.
- **Tables and Charts:**
  - Displays tables showing how many like the singers' songs received over time.

### Recommendations

- **Music Recommendations:**
  - Suggests songs based on user ratings.
  - Considers temporal properties and recommends less active but highly-rated items.
  - Recommends based on friendship activity.

### Additional Features

- **Authentication:**
  - Supports password-based authentication.
- **Friends and Friendship:**
  - Enables users to add friends.
- **Result Sharing:**
  - Permits sharing analysis results on social media platforms.
- **Data Exporting:**
  - Facilitates exporting song ratings with filtering options.
 
## How to Start Application on Your Local:

### 1) Please download Python 3 on your local:

### 2) Create a virtual environment named "venv" directory in the project root directory:
mkdir venv
python3 -m venv venv

### 3) Configure Run/Debug Configurations on your local:
Set interpreter as "module" to run Python module, give module name "uvicorn" and add the run script as "app.main:app --host 0.0.0.0 --port 8080 --reload"

### 4) After activating the virtual environment, download the required packages on venv:
pip install -U -r requirements.txt
