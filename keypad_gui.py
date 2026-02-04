import tkinter as tk
from tkinter import messagebox, font
from firebase_service import FirebaseService
from backend_service import BackendService
from smart_printer import SmartPrinter
import threading


class KeypadGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto-Print Pickup Code Entry")
        self.root.geometry("480x600")
        self.root.configure(bg="#1a1a2e")
        
        # Make window always on top (optional)
        # self.root.attributes('-topmost', True)
        
        # Initialize services
        self.BACKEND_BASE_URL = "http://localhost:5000"
        self.PRINTER_NAME = None
        
        self.fb_service = FirebaseService()
        self.backend = BackendService(base_url=self.BACKEND_BASE_URL)
        self.printer = SmartPrinter(printer_name=self.PRINTER_NAME)
        
        # Current code entry
        self.current_code = ""
        
        # Setup UI
        self.setup_ui()
        
        # Check printer on startup
        self.check_printer_status()
    
    def setup_ui(self):
        """Create the user interface"""
        
        # Title Label
        title_label = tk.Label(
            self.root,
            text="🖨️ Auto-Print System",
            font=("Arial", 24, "bold"),
            bg="#1a1a2e",
            fg="#00d4ff"
        )
        title_label.pack(pady=20)
        
        # Display Frame
        display_frame = tk.Frame(self.root, bg="#16213e", bd=2, relief=tk.SUNKEN)
        display_frame.pack(pady=10, padx=20, fill=tk.X)
        
        # Display Label
        self.display_label = tk.Label(
            display_frame,
            text="Enter Pickup Code",
            font=("Courier New", 20, "bold"),
            bg="#0f3460",
            fg="#ffffff",
            height=2,
            anchor="center"
        )
        self.display_label.pack(fill=tk.BOTH, padx=5, pady=5)
        
        # Keypad Frame
        keypad_frame = tk.Frame(self.root, bg="#1a1a2e")
        keypad_frame.pack(pady=20)
        
        # Button style
        button_font = font.Font(family="Arial", size=18, weight="bold")
        
        # Number buttons (1-9)
        buttons = [
            ['1', '2', '3'],
            ['4', '5', '6'],
            ['7', '8', '9'],
            ['C', '0', '⌫']
        ]
        
        for row_idx, row in enumerate(buttons):
            for col_idx, btn_text in enumerate(row):
                if btn_text == 'C':
                    # Clear button
                    btn = tk.Button(
                        keypad_frame,
                        text=btn_text,
                        font=button_font,
                        width=5,
                        height=2,
                        bg="#e74c3c",
                        fg="white",
                        activebackground="#c0392b",
                        command=self.clear_code
                    )
                elif btn_text == '⌫':
                    # Backspace button
                    btn = tk.Button(
                        keypad_frame,
                        text=btn_text,
                        font=button_font,
                        width=5,
                        height=2,
                        bg="#f39c12",
                        fg="white",
                        activebackground="#e67e22",
                        command=self.backspace
                    )
                else:
                    # Number buttons
                    btn = tk.Button(
                        keypad_frame,
                        text=btn_text,
                        font=button_font,
                        width=5,
                        height=2,
                        bg="#00d4ff",
                        fg="#1a1a2e",
                        activebackground="#0096c7",
                        command=lambda x=btn_text: self.add_digit(x)
                    )
                
                btn.grid(row=row_idx, column=col_idx, padx=5, pady=5)
        
        # Action Buttons Frame
        action_frame = tk.Frame(self.root, bg="#1a1a2e")
        action_frame.pack(pady=20)
        
        # Submit Button
        self.submit_btn = tk.Button(
            action_frame,
            text="✓ SUBMIT",
            font=("Arial", 16, "bold"),
            width=15,
            height=2,
            bg="#27ae60",
            fg="white",
            activebackground="#229954",
            command=self.submit_code
        )
        self.submit_btn.grid(row=0, column=0, padx=10)
        
        # Exit Button
        exit_btn = tk.Button(
            action_frame,
            text="✕ EXIT",
            font=("Arial", 16, "bold"),
            width=15,
            height=2,
            bg="#95a5a6",
            fg="white",
            activebackground="#7f8c8d",
            command=self.exit_app
        )
        exit_btn.grid(row=0, column=1, padx=10)
        
        # Status Label
        self.status_label = tk.Label(
            self.root,
            text="Ready",
            font=("Arial", 12),
            bg="#1a1a2e",
            fg="#95a5a6"
        )
        self.status_label.pack(pady=10)
    
    def add_digit(self, digit):
        """Add a digit to the current code"""
        self.current_code += digit
        self.update_display()
    
    def backspace(self):
        """Remove last digit"""
        self.current_code = self.current_code[:-1]
        self.update_display()
    
    def clear_code(self):
        """Clear the entire code"""
        self.current_code = ""
        self.update_display()
    
    def update_display(self):
        """Update the display label"""
        if self.current_code:
            self.display_label.config(text=self.current_code)
        else:
            self.display_label.config(text="Enter Pickup Code")
    
    def check_printer_status(self):
        """Check if printer is available"""
        is_available, message = self.printer.check_printer_available()
        if not is_available:
            self.status_label.config(text=f"⚠️ {message}", fg="#f39c12")
        else:
            self.status_label.config(text="✓ Printer Ready", fg="#27ae60")
    
    def submit_code(self):
        """Process the pickup code"""
        if not self.current_code:
            messagebox.showwarning("No Code", "Please enter a pickup code first!")
            return
        
        pickup_code = self.current_code
        self.status_label.config(text=f"Processing code: {pickup_code}...", fg="#00d4ff")
        self.submit_btn.config(state=tk.DISABLED)
        
        # Run in separate thread to avoid freezing UI
        thread = threading.Thread(target=self.process_order, args=(pickup_code,))
        thread.daemon = True
        thread.start()
    
    def process_order(self, pickup_code):
        """Process the order in background thread"""
        try:
            # 1️⃣ Get order using pickup code (Firestore)
            print(f"\n{'='*40}")
            print(f"🔍 Looking up order with code: {pickup_code}")
            print(f"{'='*40}\n")
            
            order_data = self.fb_service.get_order_by_pickup_code(pickup_code)
            if not order_data:
                self.root.after(0, lambda: self.show_error("Order not found!"))
                return
            
            # 2️⃣ Download files using Order ID (Node backend)
            downloaded_items = self.backend.download_files(order_data)
            if not downloaded_items:
                self.root.after(0, lambda: self.show_error("No files downloaded!"))
                return
            
            # 3️⃣ Print files with actual settings
            print(f"\n📑 Preparing {len(downloaded_items)} files for printing...\n")
            
            # Get global settings from order
            print_settings = order_data.get('printSettings', {})
            global_duplex = print_settings.get('doubleSide', False)
            
            for item in downloaded_items:
                file_path = item["path"]
                file_settings = item.get("settings", {})
                
                # Combine global and per-file settings
                final_settings = {
                    "copies": file_settings.get('copies', 1),
                    "color": file_settings.get('color', 'BW'),
                    "duplex": global_duplex,
                    "orientation": file_settings.get('orientation', 'PORTRAIT'),
                }
                
                self.printer.print_job([item], final_settings)
            
            print("✅ PRINT JOBS COMPLETED\n")
            
            # Success!
            self.root.after(0, lambda: self.show_success())
            
        except Exception as e:
            print(f"❌ Error processing order: {e}")
            self.root.after(0, lambda: self.show_error(f"Error: {str(e)}"))
    
    def show_success(self):
        """Show success message and reset"""
        self.status_label.config(text="✅ Print job completed!", fg="#27ae60")
        messagebox.showinfo("Success", f"Order {self.current_code} printed successfully!")
        self.clear_code()
        self.submit_btn.config(state=tk.NORMAL)
    
    def show_error(self, message):
        """Show error message and reset"""
        self.status_label.config(text=f"❌ {message}", fg="#e74c3c")
        messagebox.showerror("Error", message)
        self.submit_btn.config(state=tk.NORMAL)
    
    def exit_app(self):
        """Exit the application"""
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            self.root.quit()


def main():
    root = tk.Tk()
    app = KeypadGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
