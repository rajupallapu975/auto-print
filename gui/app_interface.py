import tkinter as tk
from tkinter import font
import threading
import time

class AutoPrintUI:
    def __init__(self, root, on_code_complete):
        self.root = root
        self.on_code_complete = on_code_complete # Logic to run after 4 digits
        self.code = ""
        
        # Setup Window
        self.root.title("Auto-Print Kiosk")
        self.root.attributes('-fullscreen', True) # Fullscreen for Pi
        self.root.configure(bg="#0f172a") # Dark Slate background
        
        self.setup_styles()
        self.create_widgets()
        
    def setup_styles(self):
        self.title_font = font.Font(family="Helvetica", size=32, weight="bold")
        self.code_font = font.Font(family="Courier New", size=72, weight="bold")
        self.status_font = font.Font(family="Helvetica", size=24)
        self.instruction_font = font.Font(family="Helvetica", size=18)

    def create_widgets(self):
        # Main Container
        self.main_frame = tk.Frame(self.root, bg="#0f172a")
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Header
        tk.Label(self.main_frame, text="🖨️ AUTO-PRINT STATION", font=self.title_font, 
                 fg="#38bdf8", bg="#0f172a").pack(pady=20)

        # Code Display Box
        self.display_frame = tk.Frame(self.main_frame, bg="#1e293b", padx=30, pady=20, 
                                     highlightbackground="#38bdf8", highlightthickness=2)
        self.display_frame.pack(pady=40)

        # The 4 Slots for the code
        self.code_label = tk.Label(self.display_frame, text="_ _ _ _", font=self.code_font, 
                                  fg="#f8fafc", bg="#1e293b")
        self.code_label.pack()

        # Instruction / Status Label
        self.status_label = tk.Label(self.main_frame, text="Please enter your 4-digit Pickup Code", 
                                    font=self.instruction_font, fg="#94a3b8", bg="#0f172a")
        self.status_label.pack(pady=10)

        # Large Detail Status (Visible during actions)
        self.detail_label = tk.Label(self.main_frame, text="", font=self.status_font, 
                                    fg="#fbbf24", bg="#0f172a")
        self.detail_label.pack(pady=30)

        # Last Key Indicator
        self.last_key_frame = tk.Frame(self.main_frame, bg="#1e293b", padx=10, pady=5)
        self.last_key_frame.pack(pady=10)
        self.last_key_label = tk.Label(self.last_key_frame, text="Last Key: None", 
                                      font=("Helvetica", 14), fg="#94a3b8", bg="#1e293b")
        self.last_key_label.pack()

        # Exit Instructions (Bottom Left)
        tk.Label(self.root, text="Press 'Esc' to exit kiosk mode", font=("Helvetica", 10), 
                 fg="#475569", bg="#0f172a").place(relx=0.02, rely=0.95)

        # Bind Escape key
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))

    def handle_key_input(self, char):
        """Update code display when a key is pressed to the physical keypad."""
        # Update Last Key Indicator
        display_char = char
        if char == "CLEAR": display_char = "🗑️ (Clear)"
        if char == "BACKSPACE": display_char = "⌫ (Back)"
        
        self.last_key_label.config(text=f"Last Key: {display_char}", fg="#38bdf8")
        
        if char == "CLEAR":
            self.code = ""
            self.show_normal("Cleared. Please enter your 4-digit code")
        elif char == "BACKSPACE":
            if len(self.code) > 0:
                self.code = self.code[:-1]
            self.show_normal("Please enter your 4-digit Pickup Code")
        elif len(self.code) < 4:
            self.code += char
            
        self.update_code_display()

        # AUTO VERIFY AT 4 DIGITS
        if len(self.code) == 4:
            self.start_verification()

    def update_code_display(self):
        # Format code with underscores for empty slots
        display_text = ""
        for i in range(4):
            if i < len(self.code):
                display_text += self.code[i] + " "
            else:
                display_text += "_ "
        self.code_label.config(text=display_text.strip())

    def show_normal(self, message):
        self.status_label.config(text=message, fg="#94a3b8")
        self.detail_label.config(text="", fg="#fbbf24")
        self.display_frame.config(highlightbackground="#38bdf8")

    def start_verification(self):
        """Called when exactly 4 digits are entered."""
        self.status_label.config(text="Verifying code...", fg="#38bdf8")
        self.detail_label.config(text="Checking database...", fg="#fbbf24")
        self.display_frame.config(highlightbackground="#fbbf24")
        
        # Trigger the logic passed from main
        # We use a thread to keep the UI responsive while checking Firebase
        threading.Thread(target=self.run_logic, daemon=True).start()

    def run_logic(self):
        # Small delay for visual effect
        time.sleep(0.5)
        self.on_code_complete(self.code)

    def show_error(self, message):
        """Display error on the interface."""
        self.status_label.config(text="❌ FAILED", fg="#ef4444")
        self.detail_label.config(text=message, fg="#ef4444")
        self.display_frame.config(highlightbackground="#ef4444")
        
        # Reset after 3 seconds
        self.root.after(3000, lambda: self.reset_ui("Ready for new code"))

    def show_success(self, message):
        """Display success/printing status."""
        self.status_label.config(text="✅ VERIFIED", fg="#22c55e")
        self.detail_label.config(text=message, fg="#22c55e")
        self.display_frame.config(highlightbackground="#22c55e")

    def update_printing_status(self, current, total):
        self.detail_label.config(text=f"🖨️ Printing file {current} of {total}...", fg="#38bdf8")

    def reset_ui(self, message="Ready"):
        self.code = ""
        self.update_code_display()
        self.show_normal(message)
