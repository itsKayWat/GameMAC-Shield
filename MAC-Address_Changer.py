import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import winreg
import re
import random
import json
import os
from elevate import elevate
import sys
from pathlib import Path
import ctypes
import time
from colorama import init, Fore, Back, Style

# Initialize colorama
init()

class MACChangerGUI:
    def __init__(self, root):
        try:
            self.root = root
            self.root.title("Gaming MAC Address Changer")
            self.root.geometry("600x400")
            
            # Create StringVar for comboboxes
            self.adapter_var = tk.StringVar()
            self.platform_var = tk.StringVar()
            
            # Load or create settings
            self.settings_file = Path.home() / "gaming_mac_settings.json"
            self.load_settings()
            
            # Initialize adapters dictionary
            self.adapters_dict = {}
            
            self.create_gui()
            
            # Populate the adapters list and comboboxes
            self.refresh_adapters()
            
            # Populate platform combobox
            self.platform_combo['values'] = list(self.settings['platforms'].keys())
            
            # Bind events
            self.adapter_combo.bind('<<ComboboxSelected>>', lambda e: self.update_current_mac())
            
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to initialize: {str(e)}")
            raise
        
    def load_settings(self):
        """Load saved MAC addresses and settings"""
        if self.settings_file.exists():
            with open(self.settings_file, 'r') as f:
                self.settings = json.load(f)
        else:
            self.settings = {
                'saved_macs': {},
                'last_adapter': '',
                'platforms': {
                    'Epic Games': 'XX:XX:XX:XX:XX:XX',
                    'Steam': 'YY:YY:YY:YY:YY:YY',
                    'Battle.net': 'ZZ:ZZ:ZZ:ZZ:ZZ:ZZ',
                    'Origin': 'AA:AA:AA:AA:AA:AA',
                    'Custom': 'BB:BB:BB:BB:BB:BB'
                }
            }
            
    def save_settings(self):
        """Save current settings to file"""
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f)

    def create_gui(self):
        # Create main frame with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Style configuration
        style = ttk.Style()
        style.configure('Header.TLabel', font=('Arial', 10, 'bold'))
        style.configure('Info.TLabel', font=('Consolas', 10))
        
        # Network Adapter selection
        ttk.Label(main_frame, text="Network Adapter:", style='Header.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(0,5))
        self.adapter_combo = ttk.Combobox(main_frame, width=50, textvariable=self.adapter_var)
        self.adapter_combo.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(0,5))
        
        # Gaming Platform selection
        ttk.Label(main_frame, text="Gaming Platform:", style='Header.TLabel').grid(row=1, column=0, sticky=tk.W, pady=(0,5))
        self.platform_combo = ttk.Combobox(main_frame, width=50, textvariable=self.platform_var)
        self.platform_combo.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(0,5))
        
        # MAC Address displays
        ttk.Label(main_frame, text="Current MAC:", style='Header.TLabel').grid(row=2, column=0, sticky=tk.W, pady=(0,5))
        self.current_mac_label = ttk.Label(main_frame, style='Info.TLabel')
        self.current_mac_label.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=(0,5))
        
        ttk.Label(main_frame, text="Generated MAC:", style='Header.TLabel').grid(row=3, column=0, sticky=tk.W, pady=(0,5))
        self.generated_mac_label = ttk.Label(main_frame, style='Info.TLabel')
        self.generated_mac_label.grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=(0,5))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Generate Random MAC", command=self.generate_random_mac).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Save Current MAC", command=self.save_current_mac).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Change MAC", command=self.change_mac).grid(row=0, column=2, padx=5)
        
        # Adapters List
        ttk.Label(main_frame, text="Available Network Adapters:", style='Header.TLabel').grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=(10,5))
        
        # Create a frame for the text widget with a border
        text_frame = ttk.Frame(main_frame, relief='solid', borderwidth=1)
        text_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        self.adapters_list = tk.Text(text_frame, height=10, width=60, font=('Consolas', 9))
        self.adapters_list.pack(padx=1, pady=1)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)

    def refresh_adapters(self):
        """Refresh the list of network adapters"""
        try:
            self.adapters_dict = self.get_network_adapters()
            
            # Clear and update the adapters list text widget
            self.adapters_list.delete(1.0, tk.END)
            
            # Format each adapter's information
            for name, info in self.adapters_dict.items():
                formatted_text = (
                    f"Adapter: {name}\n"
                    f"   MAC Address: {info['mac']}\n"
                    f"   Hardware: {info['adapter']}\n"
                    f"{'_' * 50}\n\n"
                )
                self.adapters_list.insert(tk.END, formatted_text)
            
            # Update adapter combobox values
            self.adapter_combo['values'] = list(self.adapters_dict.keys())
            
            # Set last used adapter if available
            if self.settings['last_adapter'] in self.adapters_dict:
                self.adapter_var.set(self.settings['last_adapter'])
            elif self.adapters_dict:
                self.adapter_var.set(list(self.adapters_dict.keys())[0])
                
            # Update current MAC display
            self.update_current_mac()
            
        except Exception as e:
            print(f"Error refreshing adapters: {e}")
            messagebox.showerror("Error", f"Failed to refresh adapters: {str(e)}")

    def get_network_adapters(self):
        """Get list of active network adapters with their MAC addresses"""
        adapters_with_mac = {}
        try:
            # Get all adapters with their MAC addresses using getmac command
            output = subprocess.check_output("getmac /v /fo csv", shell=True).decode()
            for line in output.splitlines()[1:]:  # Skip header row
                try:
                    parts = line.strip('"').split('","')
                    if len(parts) >= 3:
                        connection_name = parts[0]  # Connection name
                        adapter_name = parts[1]     # Physical adapter name
                        mac_address = parts[2].rstrip('"')  # MAC address
                        if mac_address and mac_address.lower() != 'n/a':
                            adapters_with_mac[connection_name] = {
                                'mac': mac_address,
                                'adapter': adapter_name
                            }
                except:
                    continue
                    
            return adapters_with_mac
            
        except Exception as e:
            print(f"Error getting adapters: {e}")
            return {}

    def generate_random_mac(self):
        """Generate a random MAC address without saving"""
        # Generate random MAC
        mac = [random.randint(0x00, 0xff) for _ in range(6)]
        mac[0] = mac[0] & 0xfe  # ensure unicast
        mac_address = ':'.join([f"{x:02x}" for x in mac])
        
        # Only display the generated MAC
        self.generated_mac_label.config(text=mac_address)
        self.status_label.config(text="New MAC generated - use 'Save Current MAC' to save it for this platform")

    def save_current_mac(self):
        """Save either current adapter MAC or generated MAC for selected platform"""
        platform = self.platform_var.get()
        if not platform:
            messagebox.showerror("Error", "Please select a platform first")
            return
        
        # If there's a generated MAC, save that, otherwise save the current adapter's MAC
        generated_mac = self.generated_mac_label.cget("text")
        if generated_mac and generated_mac != "":
            mac_to_save = generated_mac
            source = "generated"
        else:
            mac_to_save = self.get_current_mac()
            source = "current adapter"
            
        if mac_to_save:
            self.settings['platforms'][platform] = mac_to_save
            self.save_settings()
            messagebox.showinfo("Success", 
                f"Saved {source} MAC address for {platform}\n\n"
                "Click 'Change MAC' to apply this MAC address to your adapter.")
        else:
            messagebox.showerror("Error", "No MAC address available to save")

    def load_platform_mac(self, *args):
        """Load saved MAC address when platform is selected"""
        platform = self.platform_var.get()
        if platform:
            saved_mac = self.settings['platforms'].get(platform, '')
            self.generated_mac_label.config(text=saved_mac)

    def get_current_mac(self):
        """Get current MAC address of selected adapter"""
        adapter = self.adapter_var.get()
        # Extract MAC from the display name if it exists
        if "(" in adapter and ")" in adapter:
            return adapter.split("(")[1].strip(")")
        return self.adapters_dict.get(adapter)

    def update_current_mac(self):
        """Update the current MAC address display"""
        adapter = self.adapter_var.get()
        if adapter and adapter in self.adapters_dict:
            mac = self.adapters_dict[adapter]['mac']
            self.current_mac_label.config(text=mac)
        else:
            self.current_mac_label.config(text="No adapter selected")

    def change_mac(self):
        """Change MAC address for selected adapter"""
        try:
            if not self.platform_var.get():
                messagebox.showerror("Error", "Please select a platform")
                return
                
            new_mac = self.settings['platforms'][self.platform_var.get()]
            if not new_mac:
                messagebox.showerror("Error", "No MAC address saved for this platform")
                return
                
            adapter_name = self.adapter_var.get()
            print(f"\n{Fore.CYAN}Changing MAC address:{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Adapter: {Fore.YELLOW}{adapter_name}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}New MAC: {Fore.YELLOW}{new_mac}{Style.RESET_ALL}")
            
            if not self.change_mac_address(adapter_name, new_mac):
                raise Exception("Failed to change MAC address")
                
            self.settings['last_adapter'] = adapter_name
            self.save_settings()
            
            print(f"{Fore.GREEN}Refreshing adapter list...{Style.RESET_ALL}")
            self.refresh_adapters()
            
            messagebox.showinfo("Success", 
                "MAC address changed successfully!\n\n"
                "The new MAC address is now active.")
                
        except Exception as e:
            error_msg = str(e)
            print(f"{Fore.RED}Error: {error_msg}{Style.RESET_ALL}")
            messagebox.showerror("Error", f"Failed to change MAC address: {error_msg}")

    def change_mac_address(self, connection_name, new_mac):
        """Change MAC address in Windows registry and refresh adapter"""
        try:
            # Get the physical adapter name from our stored dictionary
            adapter_info = self.adapters_dict.get(connection_name)
            if not adapter_info:
                raise Exception(f"Could not find adapter info for {connection_name}")
                
            adapter_name = adapter_info['adapter']
            print(f"{Fore.CYAN}Physical adapter name: {Fore.YELLOW}{adapter_name}{Style.RESET_ALL}")
            
            # Change MAC in registry
            key_path = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}"
            print(f"{Fore.CYAN}Opening registry key: {Fore.WHITE}{key_path}{Style.RESET_ALL}")
            
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_ALL_ACCESS)
            
            found = False
            for i in range(50):
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name, 0, winreg.KEY_ALL_ACCESS)
                    
                    try:
                        driver_desc = winreg.QueryValueEx(subkey, "DriverDesc")[0]
                        print(f"{Fore.BLUE}Checking adapter: {Fore.WHITE}{driver_desc}{Style.RESET_ALL}")
                        
                        if driver_desc == adapter_name:
                            print(f"{Fore.GREEN}Found matching adapter: {Fore.YELLOW}{adapter_name}{Style.RESET_ALL}")
                            clean_mac = new_mac.replace(':', '').upper()
                            print(f"{Fore.GREEN}Setting MAC to: {Fore.YELLOW}{clean_mac}{Style.RESET_ALL}")
                            
                            winreg.SetValueEx(subkey, "NetworkAddress", 0, winreg.REG_SZ, clean_mac)
                            found = True
                            
                            print(f"{Fore.YELLOW}Disabling {connection_name}...{Style.RESET_ALL}")
                            subprocess.run(["netsh", "interface", "set", "interface", 
                                         connection_name, "admin=disabled"], 
                                         capture_output=True, text=True, check=True)
                            
                            time.sleep(2)
                            
                            print(f"{Fore.GREEN}Enabling {connection_name}...{Style.RESET_ALL}")
                            subprocess.run(["netsh", "interface", "set", "interface", 
                                         connection_name, "admin=enabled"], 
                                         capture_output=True, text=True, check=True)
                            
                            return True
                    finally:
                        winreg.CloseKey(subkey)
                except WindowsError:
                    break
            
            if not found:
                raise Exception(f"Physical adapter '{adapter_name}' not found in registry")
                
        except Exception as e:
            print(f"{Fore.RED}Error changing MAC: {str(e)}{Style.RESET_ALL}")
            raise Exception(f"Failed to change MAC address: {str(e)}")
        finally:
            try:
                winreg.CloseKey(key)
            except:
                pass
        return False

    def on_adapter_select(self, *args):
        """Called whenever the adapter selection changes"""
        self.update_current_mac()

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":
    try:
        if not is_admin():
            # Re-run the program with admin rights
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
        else:
            # Continue with normal execution
            root = tk.Tk()
            app = MACChangerGUI(root)
            root.mainloop()
    except Exception as e:
        # Write error to a file for debugging
        with open("error_log.txt", "w") as f:
            f.write(f"Error: {str(e)}")
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
    finally:
        sys.exit()