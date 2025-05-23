import os
os.environ['TK_SILENCE_DEPRECATION'] = '1'

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import queue
import random
from moviepy.editor import VideoFileClip, concatenate_videoclips, ColorClip, CompositeVideoClip
from PIL import Image, ImageTk
import sys
import argparse  # FIX: Needed for terminal mode

# Monkey patch moviepy's resize method to use the new constant
def patch_resize():
    try:
        from moviepy.video.fx.resize import resize
        resize.old_resize = resize.resize
        def new_resize(clip, newsize=None, height=None, width=None, apply_to_mask=True):
            return resize.old_resize(clip, newsize, height, width, apply_to_mask)
        resize.resize = new_resize
    except:
        pass

patch_resize()

def get_video_files(directory, sort_by="name"):
    """Recursively find video files in the selected directory and sort them."""
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv']
    video_files = []
    for root_dir, _, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in video_extensions):
                video_files.append(os.path.join(root_dir, file))
    if sort_by == "name":
        return sorted(video_files)
    elif sort_by == "date":
        return sorted(video_files, key=os.path.getmtime)
    else:
        return video_files  # Unsorted fallback

def process_videos(selected_videos, output_file, progress_queue=None, use_messagebox=False):
    """Process videos: extract random seconds, resize, concatenate, and save."""
    if not selected_videos:
        msg = "No videos found in the specified directory."
        print(msg)
        if use_messagebox:
            messagebox.showerror("Error", msg)
        return

    try:
        print("Starting video processing...")
        # Get target resolution from the first video
        first_clip = VideoFileClip(selected_videos[0])
        target_w, target_h = first_clip.w, first_clip.h
        first_clip.close()

        clips = []
        for i, video_path in enumerate(selected_videos):
            try:
                print(f"\nProcessing video {i+1}/{len(selected_videos)}: {video_path}")
                clip = VideoFileClip(video_path)
                duration = clip.duration
                if duration < 1:
                    print("Video is too short, skipping...")
                    clip.close()
                    continue

                # Select a random start time
                start_time = random.uniform(0, duration - 1)
                subclip = clip.subclip(start_time, start_time + 1)

                # Resize subclip to match target resolution, maintaining aspect ratio
                scaling_factor = min(target_w / subclip.w, target_h / subclip.h)
                new_subclip = subclip.resize(scaling_factor)

                # Create black background
                bg = ColorClip(size=(target_w, target_h), color=(0, 0, 0))
                bg = bg.set_duration(1)

                # Position the subclip
                pos_x = (target_w - new_subclip.w) / 2
                pos_y = (target_h - new_subclip.h) / 2

                # Create composite
                positioned_clip = new_subclip.set_position((pos_x, pos_y))
                composite = CompositeVideoClip([bg, positioned_clip])
                composite = composite.set_duration(1)

                # Write the clip directly instead of storing in memory
                temp_file = f"temp_clip_{i}.mp4"
                composite.write_videofile(
                    temp_file,
                    fps=30,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile=f'temp_audio_{i}.m4a',
                    remove_temp=True,
                    preset='ultrafast',
                    threads=4,
                    ffmpeg_params=[
                        '-pix_fmt', 'yuv420p',
                        '-movflags', '+faststart'
                    ],
                    verbose=False,
                    logger=None
                )
                clips.append(temp_file)

                # Clean up
                composite.close()
                positioned_clip.close()
                new_subclip.close()
                subclip.close()
                clip.close()
                print("Clip processed successfully")
                if progress_queue:
                    progress_queue.put(i + 1)  # Update progress
            except Exception as e:
                print(f"Error processing video: {str(e)}")
                continue

        if not clips:
            msg = "No valid clips were processed"
            print(msg)
            if use_messagebox:
                messagebox.showerror("Error", msg)
            return

        # Concatenate the temporary files
        print("\nConcatenating clips...")
        final_clips = []
        for temp_file in clips:
            try:
                clip = VideoFileClip(temp_file)
                if clip is not None:
                    final_clips.append(clip)
                else:
                    print(f"Warning: Could not load temporary file {temp_file}")
            except Exception as e:
                print(f"Warning: Error loading temporary file {temp_file}: {str(e)}")
                continue

        if not final_clips:
            print("No valid clips to concatenate.")
            return

        if progress_queue:
            progress_queue.put("writing")

        final_clip = concatenate_videoclips(final_clips)
        print("Writing final video...")
        final_clip.write_videofile(
            output_file,
            fps=30,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            preset='ultrafast',
            threads=4,
            ffmpeg_params=[
                '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart'
            ],
            verbose=False,
            logger=None
        )

        # Clean up
        for clip in final_clips:
            clip.close()
        final_clip.close()
        for temp_file in clips:
            try:
                os.remove(temp_file)
            except:
                pass

        print("Video generation completed successfully.")
        if progress_queue:
            progress_queue.put("done")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        if use_messagebox:
            messagebox.showerror("Error", f"Fatal error: {str(e)}")

class OneSecondVideoSynthesiser:
    def __init__(self, root):
        self.root = root
        self.root.title("One Second Video Synthesiser")
        self.root.geometry("800x600")
        
        # Create main frame
        main_frame = tk.Frame(root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header = tk.Label(main_frame, text="One Second Video Synthesiser", 
                         font=('Helvetica', 12, 'bold'), bg='#f0f0f0')
        header.pack(pady=10)
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill=tk.X, pady=5)
        
        # Create GUI widgets
        self.select_videos_btn = tk.Button(button_frame, text="Select Videos", 
                                         command=self.select_videos)
        self.select_videos_btn.pack(side=tk.LEFT, padx=5)
        
        # Directory sorting options
        sort_frame = tk.LabelFrame(button_frame, text="Directory Sorting Options", bg='#f0f0f0')
        sort_frame.pack(side=tk.LEFT, padx=5)
        self.sort_option = tk.StringVar(value="name")
        tk.Radiobutton(sort_frame, text="Sort by Name", 
                      variable=self.sort_option, value="name", bg='#f0f0f0').pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(sort_frame, text="Sort by Date", 
                      variable=self.sort_option, value="date", bg='#f0f0f0').pack(side=tk.LEFT, padx=5)
        
        self.select_dir_btn = tk.Button(button_frame, text="Select Directory", 
                                      command=self.select_directory)
        self.select_dir_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_list_btn = tk.Button(button_frame, text="Clear List", 
                                      command=self.clear_list)
        self.clear_list_btn.pack(side=tk.LEFT, padx=5)
        
        # Create text widget with scrollbar
        text_frame = tk.Frame(main_frame, bg='white', bd=2, relief=tk.SUNKEN)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create scrollbar
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create text widget
        self.text_widget = tk.Text(text_frame, yscrollcommand=scrollbar.set,
                                 font=('Helvetica', 10), wrap=tk.NONE,
                                 height=20, width=80, bg='white', bd=0)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbar
        scrollbar.config(command=self.text_widget.yview)
        
        # Make text widget read-only
        self.text_widget.config(state=tk.DISABLED)
        
        # Add a placeholder item
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, "No videos selected")
        self.text_widget.config(state=tk.DISABLED)
        
        # Progress frame
        progress_frame = tk.Frame(main_frame, bg='#f0f0f0')
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", 
                                          length=300, mode="determinate")
        self.progress_bar.pack(side=tk.LEFT, padx=5)
        
        self.status_label = tk.Label(progress_frame, text="", bg='#f0f0f0')
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Generate button (FIX: green with white text)
        self.generate_btn = tk.Button(main_frame, text="Generate", 
                                    command=self.generate_video, 
                                    bg='#4CAF50', fg='black', activebackground='#388E3C', activeforeground='black')
        self.generate_btn.pack(pady=10)
        
        # List to store selected video paths
        self.selected_videos = []
        # Queue for progress updates
        self.progress_queue = queue.Queue()

    def format_size(self, size_bytes):
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def add_videos(self, videos):
        """Add selected videos to the text widget, avoiding duplicates."""
        print(f"Adding videos: {videos}")
        # Enable text widget for editing
        self.text_widget.config(state=tk.NORMAL)
        
        # Clear the placeholder if it exists
        if self.text_widget.get("1.0", tk.END).strip() == "No videos selected":
            print("Clearing placeholder...")
            self.text_widget.delete("1.0", tk.END)
            
        for video in videos:
            if video not in self.selected_videos:
                print(f"Adding video: {video}")
                self.selected_videos.append(video)
                # Just show the filename in the text widget
                self.text_widget.insert(tk.END, os.path.basename(video) + "\n")
                print(f"Current text contents: {self.text_widget.get('1.0', tk.END)}")
        
        # Disable text widget again
        self.text_widget.config(state=tk.DISABLED)
        # Force update the display
        self.root.update_idletasks()

    def clear_list(self):
        """Clear the selected videos list and the text widget."""
        print("Clearing list...")
        self.selected_videos.clear()
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete("1.0", tk.END)
        # Add placeholder back
        self.text_widget.insert(tk.END, "No videos selected")
        self.text_widget.config(state=tk.DISABLED)
        print("List cleared")
        # Force update the display
        self.root.update_idletasks()

    def select_videos(self):
        """Open file dialog to select multiple video files."""
        print("Opening file dialog...")
        videos = filedialog.askopenfilenames(filetypes=[("Video files", "*.mp4 *.mov *.avi *.mkv")])
        print(f"Selected videos: {videos}")
        self.add_videos(videos)

    def select_directory(self):
        """Open directory dialog and find all video files recursively, sorted by user choice."""
        directory = filedialog.askdirectory()
        if directory:
            sort_by = self.sort_option.get()
            videos = get_video_files(directory, sort_by)
            self.add_videos(videos)

    def generate_video(self):
        """Start the video generation process."""
        if not self.selected_videos:
            messagebox.showerror("Error", "No videos selected")
            return

        # Let user choose output file name
        output_file = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4")])
        if not output_file:
            return  # User cancelled

        # Warn if file exists
        if os.path.exists(output_file):
            if not messagebox.askyesno("Overwrite", f"File '{output_file}' exists. Overwrite?"):
                return

        # Initialize progress bar
        self.progress_bar['maximum'] = len(self.selected_videos)
        self.progress_bar['value'] = 0
        self.status_label.config(text="Starting...")

        # Start processing in a separate thread
        worker = threading.Thread(target=process_videos, args=(self.selected_videos, output_file, self.progress_queue, True))
        worker.start()
        self.check_queue()

    def check_queue(self):
        """Check the progress queue and update the GUI."""
        try:
            while True:
                msg = self.progress_queue.get_nowait()
                if msg == "writing":
                    self.status_label.config(text="Writing final video...")
                elif msg == "done":
                    self.progress_bar.stop()
                    self.status_label.config(text="Video generated successfully!")
                else:
                    self.progress_bar['value'] = msg
                    self.status_label.config(text=f"Processing video {msg} of {len(self.selected_videos)}")
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)  # Check again after 100ms

class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write(f"synthesis.py: error: {message}\n")
        if "argument -s/--sort" in message:
            sys.stderr.write("For example: -s date\n")
        self.print_help()
        sys.exit(2)

def main():
    parser = CustomArgumentParser(description="One Second Video Synthesiser (Terminal Version)")
    parser.add_argument("directory", help="Directory containing videos")
    parser.add_argument("-s", "--sort", choices=["name", "date"], default="name", help="Sort videos by name or date (e.g., -s date)")
    parser.add_argument("-o", "--output", required=True, help="Output video file name (e.g., output.mp4)")
    parser.add_argument("--output-dir", help="Directory to save the output video file")
    args = parser.parse_args()

    videos = get_video_files(args.directory, args.sort)
    print(f"Found {len(videos)} videos.")

    # Determine output path
    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
        output_path = os.path.join(args.output_dir, args.output)
    else:
        output_path = args.output

    process_videos(videos, output_path)

if __name__ == "__main__":
    # If only the script name is present, launch GUI. Otherwise, use terminal mode.
    if len(sys.argv) > 1 and not sys.argv[1].endswith(".py"):
        main()
    else:
        root = tk.Tk()
        app = OneSecondVideoSynthesiser(root)
        root.mainloop()