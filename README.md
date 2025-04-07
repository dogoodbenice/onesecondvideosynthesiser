# OneSecondVideoSynthesiser

OneSecondVideoSynthesiser is a Python application that allows you to select multiple videos via a graphical user interface (GUI), extract a random one-second clip from each, and synthesise them into a single output video! The clips are combined in the order of selection, and the process can be rerun to generate new random selections. It supports over 1000 videos and various formats like MP4, MOV, AVI, and MKV.

## Features
- Select individual video files or an entire directory of videos.
- Option to sort directory videos by name (alphabetical) or date modified.
- Extracts a random one-second clip from each video.
- Combines clips into a single MP4 video, maintaining the order of selection.
- Displays progress with a progress bar and status updates.
- Handles large numbers of videos efficiently (tested with over 1000).
- Supports multiple video formats via FFmpeg.

## Prerequisites
- **Python 3.6+**: Ensure Python is installed on your system.
- **FFmpeg**: Required for video processing. Install it on your system:
  - **Windows**: Download from [FFmpeg's official site](https://ffmpeg.org/download.html) and add to PATH.
  - **macOS**: `brew install ffmpeg` (with Homebrew).
  - **Linux**: `sudo apt-get install ffmpeg` (Ubuntu/Debian) or equivalent.
- **Python Libraries**: Install the required libraries with pip (see Installation section).

## Installation
1. Clone the Repository:
```bash
git clone https://github.com/yourusername/onesecondvideosynthesiser.git
cd onesecondvideosynthesiser
```

2. Install Dependencies:
```bash
pip install -r requirements.txt
```
or install the required packages manually:
```bash
pip install moviepy==1.0.3 numpy>=1.20.0 Pillow>=9.0.0 decorator>=4.4.2 proglog>=0.1.10 requests>=2.27.0 tqdm>=4.65.0 imageio-ffmpeg>=0.4.8
```

Ensure FFmpeg is installed and accessible in your system PATH.

3. Save the Script: The main application script is synthesis.py, included in this repository. No additional steps are needed if cloned.

## Usage
Follow these steps to use OneSecondVideoSynthesiser:

Step 1: Run the Application
Launch the script from your terminal or command prompt:

```bash
python synthesis.py
```

A GUI window titled "One Second Video Synthesiser" will appear.

Step 2: Select Videos
You have two options to add videos:

Select Videos:
- Click the "Select Videos" button.
- In the file dialog, choose one or more video files (e.g., .mp4, .mov, .avi, .mkv).
- Selected video paths will appear in the listbox.

Select Directory:
- Choose a sorting option under "Directory Sorting Options":
- "Sort by Name" (default): Orders videos alphabetically.
- "Sort by Date Modified": Orders videos by modification date (oldest first).
- Click the "Select Directory" button.
- Pick a folder containing video files. All supported videos in the folder (and subfolders) will be added to the listbox in the chosen order.

Step 3: Review and Clear (Optional)
Review the list of videos in the listbox.
To start over, click "Clear List" to remove all selected videos.

Step 4: Generate the Video
Click the "Generate" button.
In the save dialog, choose a location and name for the output file (e.g., output.mp4).
Watch the progress bar and status label:
The progress bar fills as each video is processed.
Status updates show the current video number or "Writing final video...".
When complete, the status will read "Video generated successfully!"

Step 5: Rerun (Optional)
To create a new video with different random clips:
1. Keep the same video list or modify it.
2. Click "Generate" again and choose a new output file name.
3. Each run generates a fresh random selection of one-second clips.

### Notes
Supported Formats: MP4, MOV, AVI, MKV, and others supported by FFmpeg.
Video Requirements: Videos must be at least 1 second long; shorter videos are skipped.
Resolution: The output matches the resolution of the first video, with other clips resized and centered on a black background.
Performance: Processing time depends on video size and count, but memory usage is optimized for large batches.

### Troubleshooting
FFmpeg Not Found: Ensure FFmpeg is installed and in your PATH. Test with ffmpeg -version in your terminal.
Errors During Processing: Check the error message in the popup. Common issues include corrupted videos or unsupported codecs.
GUI Freezes: The app uses threading to stay responsive, but very large files may slow processing—wait for completion.
Contributing
Feel free to fork this repository, submit issues, or create pull requests with improvements!

### License
This project is licensed under the MIT License—see the  file for details.