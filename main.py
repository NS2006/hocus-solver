import shutil
import tkinter as tk
from tkinter import ttk
import pyautogui
import time
import threading
import cv2
import numpy as np
import os
from PIL import Image
from datetime import datetime

class AppSolver:
    def __init__(self, root):
        self.root = root
        self.root.title("Hocus Solver")
        self.is_running = False
        self.direction_templates = {}
        self.current_directions = []
        self.last_direction = None
        self.move_delay = 3
        self.all_directions = {}
        
        # Initialize regions
        self.screen_width, self.screen_height = pyautogui.size()
        self.direction_region = (
            self.screen_width // 2 - 100,
            20,
            self.screen_width // 2 + 100,
            200
        )
        self.stage_region = (
            self.screen_width // 3,
            self.screen_height // 6,
            self.screen_width // 2 + 350,
            self.screen_height
        )
        
        self.configure_window()
        self.create_folders()
        self.load_direction_templates()
        self.setup_gui()

    def configure_window(self):
        self.root.attributes('-topmost', True)
        self.root.resizable(False, False)
        self.root.geometry("500x800")
        
        # Set minimum window size
        self.root.minsize(500, 800)

    def create_folders(self):
        for folder in ["direction_screenshots", "stage_screenshots", "directions"]:
            if not os.path.exists(folder):
                os.makedirs(folder)

    def setup_gui(self):
        # Main container with scrollbar
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a canvas
        canvas = tk.Canvas(main_frame)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure the canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Create another frame inside the canvas
        content_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        # Title
        title_label = ttk.Label(content_frame, 
                              text="Hocus Game Solver", 
                              font=("Helvetica", 16, "bold"))
        title_label.pack(pady=20)
        
        # Status label
        self.status_label = ttk.Label(content_frame, 
                                    text="Press Start to begin detection",
                                    font=("Helvetica", 12))
        self.status_label.pack(pady=10)
        
        # Region display
        # region_frame = ttk.LabelFrame(content_frame, text="Region Configuration", padding=15)
        # region_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # ttk.Label(region_frame, text="Direction Region:", font=("Helvetica", 10)).pack(anchor="w")
        # ttk.Label(region_frame, 
        #          text=f"{self.direction_region}", 
        #          font=("Helvetica", 10, "bold")).pack(anchor="w", pady=5)
        
        # ttk.Label(region_frame, text="Stage Region:", font=("Helvetica", 10)).pack(anchor="w")
        # ttk.Label(region_frame, 
        #          text=f"{self.stage_region}", 
        #          font=("Helvetica", 10, "bold")).pack(anchor="w", pady=5)
        
        # Controls
        self.start_button = ttk.Button(content_frame, 
                                     text="Start Detection", 
                                     command=self.toggle_detection,
                                     style="Large.TButton")
        self.start_button.pack(pady=20, fill=tk.X, padx=30)
        
        # Status displays
        status_frame = ttk.LabelFrame(content_frame, text="Detection Status", padding=15)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Directions
        direction_display = ttk.LabelFrame(status_frame, text="Available Directions", padding=10)
        direction_display.pack(fill=tk.X, pady=5)
        self.direction_label = ttk.Label(direction_display, 
                                       text="None detected yet",
                                       font=("Helvetica", 11))
        self.direction_label.pack(anchor="w")
        
        # Actions
        action_display = ttk.LabelFrame(status_frame, text="Last Action", padding=10)
        action_display.pack(fill=tk.X, pady=5)
        self.action_label = ttk.Label(action_display, 
                                    text="No actions performed yet",
                                    font=("Helvetica", 11))
        self.action_label.pack(anchor="w")
        
        # Counter
        counter_display = ttk.LabelFrame(status_frame, text="Statistics", padding=10)
        counter_display.pack(fill=tk.X, pady=5)
        self.counter_label = ttk.Label(counter_display, 
                                     text="Detections: 0",
                                     font=("Helvetica", 11))
        self.counter_label.pack(anchor="w")
        
        # Configure style for larger widgets
        style = ttk.Style()
        style.configure("Large.TButton", font=("Helvetica", 14), padding=10)
        
        # Status bar at bottom
        self.status_bar = ttk.Label(content_frame, 
                                  text="Ready", 
                                  relief=tk.SUNKEN,
                                  anchor=tk.W)
        self.status_bar.pack(fill=tk.X, pady=10)

    def load_direction_templates(self):
        directions = ['up', 'down', 'left', 'right', 
                     'up-left', 'up-right', 'down-left', 'down-right']
        for direction in directions:
            path = f"directions/{direction}.png"
            if os.path.exists(path):
                template = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                if template is not None:
                    self.direction_templates[direction] = template

    def capture_regions(self):
        # Capture direction region
        direction_img = pyautogui.screenshot(region=(
            self.direction_region[0],
            self.direction_region[1],
            self.direction_region[2] - self.direction_region[0],
            self.direction_region[3] - self.direction_region[1]
        ))

        # Save and immediately delete direction screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        direction_path = f"direction_screenshots/direction_{timestamp}.png"
        direction_img.save(direction_path)
        if os.path.exists(direction_path):
            os.remove(direction_path)

        # Capture stage region
        stage_img = pyautogui.screenshot(region=(
            self.stage_region[0],
            self.stage_region[1],
            self.stage_region[2] - self.stage_region[0],
            self.stage_region[3] - self.stage_region[1]
        ))

        # Handle stage screenshot rotation
        current_path = "stage_screenshots/stage_current.png"
        previous_path = "stage_screenshots/stage_previous.png"

        if os.path.exists(current_path):
            if os.path.exists(previous_path):
                os.remove(previous_path)
            os.rename(current_path, previous_path)

        stage_img.save(current_path)

        return direction_img, stage_img

    def match_direction(self, direction_img):
        enhanced_img = self.enhance_image(direction_img)
        threshold = 0.97  # fixed value
        matches = []

        for direction, template in self.direction_templates.items():
            res = cv2.matchTemplate(enhanced_img, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            if max_val > threshold:
                matches.append((direction, max_val))

        return matches

    def enhance_image(self, img):
        # Convert image to grayscale
        gray_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)

        # Apply GaussianBlur to reduce noise
        blurred_img = cv2.GaussianBlur(gray_img, (5, 5), 0)

        # Increase contrast by using adaptive histogram equalization (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced_img = clahe.apply(blurred_img)

        return enhanced_img

    def get_best_available_move(self, matches):
        if not matches:
            return None

        # Check if there is exactly one direction with a high confidence score
        if matches[0][1] >= 0.99:
            return matches[0][0]
        
        # Otherwise, follow the current logic to return a direction different from last_direction
        available_directions = [direction for direction, score in matches]
        
        if not hasattr(self, 'last_direction') or len(available_directions) == 1:
            return available_directions[0]
        
        for direction in available_directions:
            if direction != self.last_direction:
                return direction
        
        return available_directions[0]


    def perform_move(self, direction):
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        distance = 200
        duration = 0.3
        
        if direction == 'up':
            self.last_direction = 'down'
            pyautogui.moveTo(center_x, center_y + distance)
            pyautogui.dragTo(center_x, center_y - distance, duration, button='left')
        elif direction == 'down':
            self.last_direction = 'up'
            pyautogui.moveTo(center_x, center_y - distance)
            pyautogui.dragTo(center_x, center_y + distance, duration, button='left')
        elif direction == 'up-left':
            self.last_direction = 'down-right'
            pyautogui.moveTo(center_x + distance, center_y + distance)
            pyautogui.dragTo(center_x - distance, center_y - distance, duration, button='left')
        elif direction == 'up-right':
            self.last_direction = 'down-left'
            pyautogui.moveTo(center_x - distance, center_y + distance)
            pyautogui.dragTo(center_x + distance, center_y - distance, duration, button='left')
        elif direction == 'down-left':
            self.last_direction = 'up-right'
            pyautogui.moveTo(center_x + distance, center_y - distance)
            pyautogui.dragTo(center_x - distance, center_y + distance, duration, button='left')
        elif direction == 'down-right':
            self.last_direction = 'up-left'
            pyautogui.moveTo(center_x - distance, center_y - distance)
            pyautogui.dragTo(center_x + distance, center_y + distance, duration, button='left')
        
        self.action_label.config(text=f"Last Action: Swiped {direction}")
        self.status_bar.config(text=f"Performed {direction} swipe")

    def toggle_detection(self):
        if not self.is_running:
            self.clear_screenshots()
            self.is_running = True
            self.start_button.config(text="Stop Detection")
            self.status_label.config(text="Detection running...", foreground="green")
            self.status_bar.config(text="Detection started")
            threading.Thread(target=self.run_detection, daemon=True).start()
        else:
            self.is_running = False
            self.start_button.config(text="Start Detection")
            self.status_label.config(text="Detection stopped", foreground="red")
            self.status_bar.config(text="Detection stopped")

    def clear_screenshots(self):
        screenshot_dirs = ["direction_screenshots", "stage_screenshots"]
        for dir_name in screenshot_dirs:
            try:
                shutil.rmtree(dir_name)
                os.makedirs(dir_name)
                self.status_bar.config(text=f"Cleared {dir_name} directory")
            except Exception as e:
                self.status_bar.config(text=f"Error clearing {dir_name}: {str(e)}")

    def run_detection(self):
        detection_count = 0

        while self.is_running:
            try:
                screenshots = []
                matches_list = []

                # Take 3 fast screenshots
                for _ in range(2):
                    direction_img, _ = self.capture_regions()
                    screenshots.append(direction_img)
                    matches = self.match_direction(direction_img)
                    matches_list.append(matches)
                    time.sleep(0.3)  # short delay between shots

                # Determine the best match across all
                direction_counter = {}
                direction_scores = {}

                for matches in matches_list:
                    for direction, score in matches:
                        if score >= 0.80:  # Only consider strong matches
                            direction_counter[direction] = direction_counter.get(direction, 0) + 1
                            direction_scores[direction] = direction_scores.get(direction, 0) + score

                # Filter directions that appear in at least 2 screenshots
                consistent_directions = {
                    direction: direction_scores[direction] / direction_counter[direction]
                    for direction in direction_counter
                    if direction_counter[direction] >= 2
                }

                if consistent_directions:
                    # Sort by average score
                    sorted_consistent = sorted(consistent_directions.items(), key=lambda x: x[1], reverse=True)
                    best_matches = [(d, consistent_directions[d]) for d, _ in sorted_consistent]

                    directions_info = [f"{d} ({s:.2f})" for d, s in best_matches]
                    self.direction_label.config(text="\n".join(directions_info))

                    best_move = self.get_best_available_move(best_matches)
                    if best_move:
                        self.perform_move(best_move)
                        time.sleep(self.move_delay)


                # Clean up: delete all direction screenshots
                for file in os.listdir("direction_screenshots"):
                    if file.startswith("direction_") and file.endswith(".png"):
                        os.remove(os.path.join("direction_screenshots", file))


                detection_count += 1
                self.counter_label.config(text=f"Detections: {detection_count}")
                time.sleep(0.1)

            except Exception as e:
                self.status_bar.config(text=f"Error: {str(e)}")
                time.sleep(1)


if __name__ == "__main__":
    root = tk.Tk()
    app = AppSolver(root)
    root.mainloop()