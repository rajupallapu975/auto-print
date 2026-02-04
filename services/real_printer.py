import subprocess
import os

class RealPrinter:
    def __init__(self, printer_name=None):
        """
        Initialize with printer name. If None, uses default printer.
        Find printer name with: lpstat -p -d
        """
        self.printer_name = printer_name
        
    def print_job(self, file_paths, settings):
        """
        Sends files to the actual printer using CUPS (lp command).
        """
        print("\n" + "="*40)
        print("🖨️  REAL PRINT JOB STARTING  🖨️")
        print("="*40)
        
        if not file_paths:
            print("❌ No files provided for printing.")
            return False

        print(f"📄 Files to print: {len(file_paths)}")
        
        for item in file_paths:
            file_path = item if isinstance(item, str) else item.get('path')
            file_settings = {} if isinstance(item, str) else item.get('settings', {})
            
            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                continue
                
            print(f"\n📄 Printing: {os.path.basename(file_path)}")
            
            # Build lp command
            cmd = ['lp']
            
            # Printer name
            if self.printer_name:
                cmd.extend(['-d', self.printer_name])
            
            # Number of copies
            copies = file_settings.get('copies', settings.get('copies', 1))
            cmd.extend(['-n', str(copies)])
            
            # Color vs BW
            color_mode = file_settings.get('color', settings.get('color', 'BW'))
            if color_mode == 'BW':
                cmd.extend(['-o', 'ColorModel=Gray'])
            else:
                cmd.extend(['-o', 'ColorModel=RGB'])
            
            # Duplex (two-sided)
            duplex = settings.get('duplex', False)
            if duplex:
                cmd.extend(['-o', 'sides=two-sided-long-edge'])
            
            # Orientation
            orientation = file_settings.get('orientation', 'PORTRAIT')
            if orientation == 'LANDSCAPE':
                cmd.extend(['-o', 'landscape'])
            
            # File path
            cmd.append(file_path)
            
            # Execute print command
            try:
                print(f"🔧 Command: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ Print job submitted successfully!")
                    print(f"   Job ID: {result.stdout.strip()}")
                else:
                    print(f"❌ Print failed: {result.stderr}")
                    return False
                    
            except Exception as e:
                print(f"❌ Print error: {e}")
                return False
        
        print("\n" + "="*40)
        print("✅ ALL PRINT JOBS COMPLETED")
        print("="*40 + "\n")
        return True
