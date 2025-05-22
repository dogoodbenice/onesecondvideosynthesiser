import os
os.environ['TK_SILENCE_DEPRECATION'] = '1'

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import queue
import random
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips, ColorClip, CompositeVideoClip
from PIL import Image, ImageTk

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
        
        # Generate button
        self.generate_btn = tk.Button(main_frame, text="Generate", 
                                    command=self.generate_video, 
                                    bg='#4CAF50', fg='white')
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
            videos = self.get_video_files(directory, sort_by)
            self.add_videos(videos)

    def get_video_files(self, directory, sort_by="name"):
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

    def generate_video(self):
        """Start the video generation process."""
        if not self.selected_videos:
            messagebox.showerror("Error", "No videos selected")
            return

        # Let user choose output file name
        output_file = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4")])
        if not output_file:
            return  # User cancelled

        # Initialize progress bar
        self.progress_bar['maximum'] = len(self.selected_videos)
        self.progress_bar['value'] = 0
        self.status_label.config(text="Starting...")

        # Start processing in a separate thread
        worker = threading.Thread(target=self.process_videos, args=(self.selected_videos, output_file))
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

    def process_videos(self, selected_videos, output_file):
        """Process videos: extract random seconds, resize, concatenate, and save."""
        try:
            print("Starting video processing...")
            # Get target resolution from the first video
            try:
                print(f"Attempting to load first video: {selected_videos[0]}")
                first_clip = VideoFileClip(selected_videos[0])
                if first_clip is None:
                    raise Exception("First video clip is None")
                print(f"First video loaded successfully. Resolution: {first_clip.w}x{first_clip.h}")
                target_w, target_h = first_clip.w, first_clip.h
                first_clip.close()
            except Exception as e:
                messagebox.showerror("Error", f"Could not read the first video: {selected_videos[0]}\nError: {str(e)}")
                return

            clips = []
            for i, video_path in enumerate(selected_videos):
                try:
                    print(f"\nProcessing video {i+1}/{len(selected_videos)}: {video_path}")
                    # Load video
                    clip = VideoFileClip(video_path)
                    if clip is None:
                        raise Exception("Failed to load video")
                    print(f"Video loaded. Duration: {clip.duration} seconds")
                        
                    duration = clip.duration
                    if duration is None:
                        raise Exception("Could not determine video duration")

                    # Skip videos shorter than 1 second
                    if duration < 1:
                        print("Video is too short, skipping...")
                        clip.close()
                        continue

                    # Select a random start time
                    start_time = random.uniform(0, duration - 1)
                    print(f"Extracting clip from {start_time:.2f} to {start_time + 1:.2f}")
                    subclip = clip.subclip(start_time, start_time + 1)

                    # Verify subclip
                    try:
                        test_frame = subclip.get_frame(0)
                        if test_frame is None:
                            raise Exception("Could not get frame from subclip")
                        print("Subclip verified successfully")
                    except Exception as e:
                        raise Exception(f"Error testing subclip: {str(e)}")

                    # Resize subclip to match target resolution, maintaining aspect ratio
                    scaling_factor = min(target_w / subclip.w, target_h / subclip.h)
                    print(f"Resizing with scaling factor: {scaling_factor}")
                    new_subclip = subclip.resize(scaling_factor)

                    # Create black background
                    print("Creating background...")
                    bg = ColorClip(size=(target_w, target_h), color=(0, 0, 0))
                    bg = bg.set_duration(1)
                    
                    # Position the subclip
                    pos_x = (target_w - new_subclip.w) / 2
                    pos_y = (target_h - new_subclip.h) / 2
                    print(f"Positioning clip at ({pos_x}, {pos_y})")
                    
                    # Create composite
                    print("Creating composite...")
                    positioned_clip = new_subclip.set_position((pos_x, pos_y))
                    composite = CompositeVideoClip([bg, positioned_clip])
                    composite = composite.set_duration(1)  # Ensure duration is set

                    # Verify composite
                    try:
                        print("Testing composite...")
                        test_frame = composite.get_frame(0)
                        if test_frame is None:
                            raise Exception("Could not get frame from composite")
                        print("Composite verified successfully")
                    except Exception as e:
                        raise Exception(f"Error testing composite: {str(e)}")

                    # Write the clip directly instead of storing in memory
                    temp_file = f"temp_clip_{i}.mp4"
                    print(f"Writing clip {i+1}/{len(selected_videos)}...")
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
                        ]
                    )
                    clips.append(temp_file)
                    
                    # Clean up
                    composite.close()
                    positioned_clip.close()
                    new_subclip.close()
                    subclip.close()
                    clip.close()
                    print("Clip processed successfully")
                    self.progress_queue.put(i + 1)  # Update progress
                except Exception as e:
                    print(f"Error processing video: {str(e)}")
                    messagebox.showwarning("Warning", f"Could not process video {video_path}\nError: {str(e)}")
                    continue

            if not clips:
                messagebox.showerror("Error", "No valid clips were processed")
                return

            # Concatenate the temporary files
            print("\nConcatenating clips...")
            try:
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
                    raise Exception("No valid clips to concatenate")

                final_clip = concatenate_videoclips(final_clips)
                if final_clip is None:
                    raise Exception("Failed to concatenate clips")

                print("Writing final video...")
                self.progress_queue.put("writing")
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
                    ]
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

                print("Video generation completed successfully")
                self.progress_queue.put("done")
            except Exception as e:
                print(f"Error during final video writing: {str(e)}")
                # Clean up temporary files
                for temp_file in clips:
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                self.progress_queue.put("done")
                messagebox.showerror("Error", f"Failed to write final video: {str(e)}")
                return

        except Exception as e:
            print(f"Fatal error: {str(e)}")
            self.progress_queue.put("done")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = OneSecondVideoSynthesiser(root)
    root.mainloop()