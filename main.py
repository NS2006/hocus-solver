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
        self.current_direction = None
        self.last_direction = None
        self.move_delay = 2  # Delay between moves in seconds
        
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
        self.root.geometry("450x400")

    def create_folders(self):
        for folder in ["direction_screenshots", "stage_screenshots", "directions"]:
            if not os.path.exists(folder):
                os.makedirs(folder)

    def setup_gui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status label (initialize this first)
        self.status_label = ttk.Label(main_frame, text="Press Start to begin detection")
        self.status_label.pack(pady=5)
        
        # Region display
        ttk.Label(main_frame, text="Region Configuration:").pack()
        ttk.Label(main_frame, text=f"Direction: {self.direction_region}").pack()
        ttk.Label(main_frame, text=f"Stage: {self.stage_region}").pack(pady=(0,10))
        
        # Controls
        self.start_button = ttk.Button(main_frame, text="Start", command=self.toggle_detection)
        self.start_button.pack(pady=5, fill=tk.X)
        
        # Settings
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding=10)
        settings_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(settings_frame, text="Move Delay (s):").grid(row=0, column=0, sticky="w")
        self.delay_entry = ttk.Entry(settings_frame, width=5)
        self.delay_entry.insert(0, "2")
        self.delay_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(settings_frame, text="Detection Threshold:").grid(row=1, column=0, sticky="w")
        self.threshold_entry = ttk.Entry(settings_frame, width=5)
        self.threshold_entry.insert(0, "0.8")
        self.threshold_entry.grid(row=1, column=1, padx=5)
        
        # Status displays
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.direction_label = ttk.Label(status_frame, text="Available Directions: None")
        self.direction_label.pack(anchor="w")
        
        self.action_label = ttk.Label(status_frame, text="Last Action: None")
        self.action_label.pack(anchor="w")
        
        self.counter_label = ttk.Label(status_frame, text="Detections: 0")
        self.counter_label.pack(anchor="w")

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
        direction_img = pyautogui.screenshot(region=(
            self.direction_region[0],
            self.direction_region[1],
            self.direction_region[2] - self.direction_region[0],
            self.direction_region[3] - self.direction_region[1]
        ))
        
        stage_img = pyautogui.screenshot(region=(
            self.stage_region[0],
            self.stage_region[1],
            self.stage_region[2] - self.stage_region[0],
            self.stage_region[3] - self.stage_region[1]
        ))
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        direction_img.save(f"direction_screenshots/direction_{timestamp}.png")
        stage_img.save(f"stage_screenshots/stage_{timestamp}.png")
        
        return direction_img, stage_img

    def match_direction(self, direction_img):
        """Match the direction image against templates"""
        gray_img = cv2.cvtColor(np.array(direction_img), cv2.COLOR_RGB2GRAY)
        best_match, best_score = None, -1
        
        for direction, template in self.direction_templates.items():
            res = cv2.matchTemplate(gray_img, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            if max_val > best_score:
                best_score, best_match = max_val, direction
                
        return best_match if best_score > 0.8 else None

    def perform_move(self, direction):
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        distance = 200
        duration = 0.2
        
        if direction == 'up':
            pyautogui.moveTo(center_x, center_y + distance//2)
            pyautogui.dragTo(center_x, center_y - distance//2, duration, button='left')
        elif direction == 'down':
            pyautogui.moveTo(center_x, center_y - distance//2)
            pyautogui.dragTo(center_x, center_y + distance//2, duration, button='left')
        elif direction == 'left':
            pyautogui.moveTo(center_x + distance//2, center_y)
            pyautogui.dragTo(center_x - distance//2, center_y, duration, button='left')
        elif direction == 'right':
            pyautogui.moveTo(center_x - distance//2, center_y)
            pyautogui.dragTo(center_x + distance//2, center_y, duration, button='left')
        elif direction == 'up-left':
            pyautogui.moveTo(center_x + distance//3, center_y + distance//3)
            pyautogui.dragTo(center_x - distance//3, center_y - distance//3, duration, button='left')
        elif direction == 'up-right':
            pyautogui.moveTo(center_x - distance//3, center_y + distance//3)
            pyautogui.dragTo(center_x + distance//3, center_y - distance//3, duration, button='left')
        elif direction == 'down-left':
            pyautogui.moveTo(center_x + distance//3, center_y - distance//3)
            pyautogui.dragTo(center_x - distance//3, center_y + distance//3, duration, button='left')
        elif direction == 'down-right':
            pyautogui.moveTo(center_x - distance//3, center_y - distance//3)
            pyautogui.dragTo(center_x + distance//3, center_y + distance//3, duration, button='left')
        
        self.action_label.config(text=f"Last Action: Swiped {direction}")

    def toggle_detection(self):
        if not self.is_running:
            self.is_running = True
            self.move_delay = float(self.delay_entry.get() or 0.5)
            self.start_button.config(text="Stop")
            self.status_label.config(text="Detecting and moving...")
            threading.Thread(target=self.run_detection, daemon=True).start()
        else:
            self.is_running = False
            self.start_button.config(text="Start")
            self.status_label.config(text="Detection stopped.")

    def run_detection(self):
        """Main detection loop"""
        direction_count = 0
        stage_count = 0
        
        while self.is_running:
            try:
                direction_img, stage_img = self.capture_regions()
                
                # Detect direction
                direction = self.match_direction(direction_img)
                if direction and direction != 'nothing':
                    self.current_direction = direction
                    self.direction_label.config(text=f"Direction: {direction}")
                    direction_count += 1
                    
                    # Only perform move if direction changed
                    if direction != self.last_direction:
                        self.perform_move(direction)
                        self.last_direction = direction
                        time.sleep(self.move_delay)  # Delay after movement
                
                stage_count += 1
                self.counter_label.config(
                    text=f"Captures: {direction_count} directions, {stage_count} stages"
                )
                
                time.sleep(0.1)  # Short delay between detections
                
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1)

def clear_screenshots():
    """Empty the screenshot directories"""
    screenshot_dirs = ["direction_screenshots", "stage_screenshots"]
    
    for dir_name in screenshot_dirs:
        try:
            # Remove the entire directory and recreate it
            shutil.rmtree(dir_name)
            os.makedirs(dir_name)
            print(f"Cleared directory: {dir_name}")
        except Exception as e:
            print(f"Error clearing {dir_name}: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppSolver(root)

    clear_screenshots()
    root.mainloop()