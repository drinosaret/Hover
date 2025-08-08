import win32gui
import win32con
import win32api
import time
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import sys
import pystray
import signal
import atexit
from PIL import Image, ImageDraw
from version import __version__, __title__

def set_window_always_on_top(hwnd, always_on_top):
    """Set the window to always stay on top."""
    try:
        # Check if the window handle is still valid
        if not win32gui.IsWindow(hwnd):
            return False
        
        # Try multiple approaches for better reliability
        attempts = 0
        max_attempts = 3
        
        while attempts < max_attempts:
            try:
                if always_on_top:
                    # First attempt: Standard topmost setting
                    result = win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                                                 win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
                    
                    # Verify it worked by checking the extended style
                    time.sleep(0.1)  # Small delay to let the change take effect
                    extended_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                    is_topmost = bool(extended_style & win32con.WS_EX_TOPMOST)
                    
                    if result != 0 and is_topmost:
                        return True
                    
                    # If verification failed, try alternative approach
                    if attempts == 1:
                        # Force refresh by setting to not topmost first, then topmost
                        win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, 
                                            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
                        time.sleep(0.05)
                        result = win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                                                     win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
                else:
                    result = win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, 
                                                 win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
                    
                    # For removing topmost, we don't need as strict verification
                    if result != 0:
                        return True
                
                attempts += 1
                if attempts < max_attempts:
                    time.sleep(0.1)  # Wait before retry
                    
            except Exception as inner_e:
                print(f"Attempt {attempts + 1} failed: {inner_e}")
                attempts += 1
                if attempts < max_attempts:
                    time.sleep(0.1)
                
        return False
        
    except Exception as e:
        print(f"Error setting window always on top: {e}")
        return False

def set_window_transparent(hwnd, transparency):
    """Set the window transparency."""
    try:
        # Check if the window handle is still valid
        if not win32gui.IsWindow(hwnd):
            return False
            
        extended_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, extended_style | win32con.WS_EX_LAYERED)
        
        # Set the window transparency based on the specified value
        result = win32gui.SetLayeredWindowAttributes(hwnd, 0, transparency, win32con.LWA_ALPHA)
        return result != 0
    except Exception as e:
        print(f"Error setting window transparency: {e}")
        return False

def restore_window_to_normal(hwnd):
    """Force restore a window to normal state (full opacity, not topmost)."""
    try:
        if not win32gui.IsWindow(hwnd):
            return False
            
        # Remove topmost status
        win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, 
                             win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
        
        # Remove layered window style to restore normal transparency
        extended_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, extended_style & ~win32con.WS_EX_LAYERED)
        
        print(f"Force restored window {hwnd} to normal state")
        return True
    except Exception as e:
        print(f"Error restoring window to normal: {e}")
        return False

def is_mouse_over_window(hwnd):
    """Check if the mouse is over the window."""
    try:
        # Check if the window handle is still valid
        if not win32gui.IsWindow(hwnd):
            return False
            
        mouse_x, mouse_y = win32api.GetCursorPos()
        window_rect = win32gui.GetWindowRect(hwnd)
        
        # Validate window rect
        if len(window_rect) != 4:
            return False
            
        return window_rect[0] <= mouse_x <= window_rect[2] and window_rect[1] <= mouse_y <= window_rect[3]
    except Exception as e:
        print(f"Error checking mouse position: {e}")
        return False

def check_hover_and_update(hwnd, transparency):
    """Check mouse hover and adjust window transparency."""
    if is_mouse_over_window(hwnd):
        set_window_transparent(hwnd, transparency)  # Fully opaque when hovered
    else:
        set_window_transparent(hwnd, 0)  # Fully invisible when not hovered

def get_all_windows():
    """Get all visible windows with their hwnd and title."""
    def enum_windows_callback(hwnd, lparam):
        if win32gui.IsWindowVisible(hwnd):
            window_title = win32gui.GetWindowText(hwnd)
            if window_title:  # Only include windows with titles
                lparam.append((hwnd, window_title))

    hwnd_list = []
    win32gui.EnumWindows(enum_windows_callback, hwnd_list)
    return hwnd_list

def create_tray_icon():
    """Create a system tray icon."""
    # Create a simple icon if the file doesn't exist
    def create_default_icon():
        # Create a simple 64x64 icon
        width = 64
        height = 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw a simple window icon
        draw.rectangle([8, 16, 56, 48], fill=(70, 130, 180, 255), outline=(25, 25, 112, 255), width=2)
        draw.rectangle([12, 20, 24, 32], fill=(173, 216, 230, 255))
        draw.rectangle([28, 20, 40, 32], fill=(173, 216, 230, 255))
        draw.rectangle([44, 20, 52, 32], fill=(173, 216, 230, 255))
        draw.rectangle([12, 36, 24, 44], fill=(173, 216, 230, 255))
        draw.rectangle([28, 36, 40, 44], fill=(173, 216, 230, 255))
        draw.rectangle([44, 36, 52, 44], fill=(173, 216, 230, 255))
        
        return image

    def get_tray_icon():
        """Get the icon for the system tray."""
        icon_path = None
        
        if getattr(sys, 'frozen', False):
            # Running as executable
            icon_path = os.path.join(sys._MEIPASS, 'hover_icon.ico')
        else:
            # Running as script
            icon_path = 'hover_icon.ico'
        
        if icon_path and os.path.exists(icon_path):
            try:
                return Image.open(icon_path)
            except Exception as e:
                print(f"Could not load tray icon: {e}")
        
        # Fallback to default icon
        return create_default_icon()

    return get_tray_icon()

def create_ui():
    """Create the UI window using tkinter."""
    selected_hwnd = None
    topmost_monitor_thread = None
    tray_icon = None
    
    def show_window():
        """Show the main window."""
        root.deiconify()
        root.lift()
        root.focus_force()

    def hide_to_tray():
        """Hide the window to system tray."""
        root.withdraw()

    def on_tray_click(icon, item):
        """Handle tray icon click."""
        show_window()

    def quit_application():
        """Quit the application completely."""
        if tray_icon:
            tray_icon.stop()
        on_close()

    def setup_tray():
        """Set up the system tray icon."""
        nonlocal tray_icon
        
        try:
            icon_image = create_tray_icon()
            
            # Create tray menu
            menu = pystray.Menu(
                pystray.MenuItem("Show Window", on_tray_click, default=True),
                pystray.MenuItem("Quit", quit_application)
            )
            
            # Create tray icon
            tray_icon = pystray.Icon(
                name=f"{__title__}",
                icon=icon_image,
                title=f"{__title__} v{__version__}",
                menu=menu
            )
            
            # Run tray in separate thread
            tray_thread = threading.Thread(target=tray_icon.run, daemon=True)
            tray_thread.start()
            
            return True
        except Exception as e:
            print(f"Failed to create system tray icon: {e}")
            return False
    
    def on_window_select():
        """Handle window selection from dropdown."""
        nonlocal selected_hwnd
        global _global_selected_hwnd
        selection = window_var.get()
        
        if selection and selection != "Select a window...":
            # Extract hwnd from the selection string
            try:
                hwnd_str = selection.split(" - ")[0]
                new_hwnd = int(hwnd_str)
                
                # Check if the window is still valid
                if not win32gui.IsWindow(new_hwnd):
                    messagebox.showwarning("Invalid Window", "The selected window is no longer available. Please refresh the window list.")
                    refresh_windows()
                    return
                
                # Reset any effects on the previously selected window
                if selected_hwnd and selected_hwnd != new_hwnd:
                    try:
                        if win32gui.IsWindow(selected_hwnd):
                            # Stop all effects and restore normal state
                            always_on_top_var.set(False)
                            hover_effect_var.set(False)
                            stop_topmost_monitoring()
                            set_window_always_on_top(selected_hwnd, False)
                            stop_hover_effect(selected_hwnd)
                            set_window_transparent(selected_hwnd, 255)  # Reset transparency to fully opaque
                            print(f"Reset previous window {selected_hwnd} to normal state")
                    except Exception as e:
                        print(f"Error resetting previous window: {e}")
                
                selected_hwnd = new_hwnd
                # Update global tracking variable
                _global_selected_hwnd = new_hwnd
                
                # Enable the control buttons
                topmost_checkbox.config(state='normal')
                hover_effect_checkbox.config(state='normal')
                transparency_slider.config(state='normal')
                
                # Reset the control states for the new window
                always_on_top_var.set(False)
                hover_effect_var.set(False)
                transparency_var.set(255)  # Reset to fully opaque
                transparency_percent_label.config(text="100%")
                
                # Ensure the new window starts with full opacity
                set_window_transparent(selected_hwnd, 255)
                print(f"Selected window {selected_hwnd}: {selection}")
                
            except (ValueError, IndexError) as e:
                print(f"Error parsing window selection: {e}")
                messagebox.showerror("Error", "Invalid window selection format.")
                refresh_windows()
            except Exception as e:
                print(f"Unexpected error in window selection: {e}")
                messagebox.showerror("Error", f"Failed to select window: {e}")
                refresh_windows()
        else:
            # No window selected - disable controls
            if selected_hwnd:
                try:
                    # Clean up current window if valid
                    if win32gui.IsWindow(selected_hwnd):
                        set_window_transparent(selected_hwnd, 255)
                        set_window_always_on_top(selected_hwnd, False)
                        stop_topmost_monitoring()
                except Exception as e:
                    print(f"Error cleaning up on deselection: {e}")
            
            selected_hwnd = None
            # Clear global tracking variable
            _global_selected_hwnd = None
            # Disable the control buttons
            topmost_checkbox.config(state='disabled')
            hover_effect_checkbox.config(state='disabled')
            transparency_slider.config(state='disabled')
            always_on_top_var.set(False)
            hover_effect_var.set(False)
            transparency_var.set(255)
            transparency_percent_label.config(text="100%")
    
    def refresh_windows():
        """Refresh the list of available windows."""
        global _global_selected_hwnd
        try:
            windows = get_all_windows()
            window_options = ["Select a window..."]
            
            # Filter out invalid windows and sort by title
            valid_windows = []
            for hwnd, title in windows:
                if win32gui.IsWindow(hwnd) and title.strip():
                    valid_windows.append((hwnd, title))
            
            # Sort by title for better user experience
            valid_windows.sort(key=lambda x: x[1].lower())
            
            for hwnd, title in valid_windows:
                # Limit title length for better display
                display_title = title[:50] + "..." if len(title) > 50 else title
                window_options.append(f"{hwnd} - {display_title}")
            
            window_dropdown['values'] = window_options
            window_var.set("Select a window...")
            
            # Reset selection and disable controls
            nonlocal selected_hwnd
            if selected_hwnd:
                # Clean up previous window state
                try:
                    if win32gui.IsWindow(selected_hwnd):
                        set_window_transparent(selected_hwnd, 255)  # Restore full opacity
                        set_window_always_on_top(selected_hwnd, False)  # Remove topmost
                except Exception as e:
                    print(f"Error cleaning up previous window: {e}")
                stop_topmost_monitoring()
                
            selected_hwnd = None
            # Clear global tracking variable
            _global_selected_hwnd = None
            topmost_checkbox.config(state='disabled')
            hover_effect_checkbox.config(state='disabled')
            transparency_slider.config(state='disabled')
            always_on_top_var.set(False)
            hover_effect_var.set(False)
            transparency_var.set(255)
            transparency_percent_label.config(text="100%")
            
        except Exception as e:
            print(f"Error refreshing windows: {e}")
            messagebox.showerror("Error", f"Failed to refresh window list: {e}")

    def on_toggle_topmost():
        """Toggle the always-on-top state of the selected window."""
        if selected_hwnd:
            current_topmost = always_on_top_var.get()
            
            if current_topmost:
                # Enable always-on-top with monitoring
                success = set_window_always_on_top(selected_hwnd, True)
                if success:
                    # Start continuous monitoring
                    start_topmost_monitoring(selected_hwnd)
                    print(f"Enabled always-on-top with monitoring for window {selected_hwnd}")
                else:
                    # If setting failed, revert the checkbox state
                    always_on_top_var.set(False)
                    messagebox.showerror("Error", "Failed to set window always on top. The window may have been closed.")
            else:
                # Disable always-on-top and stop monitoring
                stop_topmost_monitoring()
                success = set_window_always_on_top(selected_hwnd, False)
                if not success:
                    messagebox.showwarning("Warning", "Failed to remove always-on-top state. The window may have been closed.")
                print(f"Disabled always-on-top for window {selected_hwnd}")

    def on_toggle_hover_effect():
        """Toggle the hover effect (show/hide based on mouse hover)."""
        if not selected_hwnd:
            return
            
        try:
            # Verify window is still valid
            if not win32gui.IsWindow(selected_hwnd):
                messagebox.showwarning("Invalid Window", "The selected window is no longer available.")
                hover_effect_var.set(False)
                refresh_windows()
                return
                
            if hover_effect_var.get():
                # Start the hover effect in a separate thread
                hover_thread = threading.Thread(target=start_hover_effect, args=(selected_hwnd,))
                hover_thread.daemon = True
                hover_thread.start()
                print(f"Started hover effect for window {selected_hwnd}")
            else:
                # Stop the hover effect and restore current transparency
                stop_hover_effect(selected_hwnd)
                print(f"Stopped hover effect for window {selected_hwnd}")
                
        except Exception as e:
            print(f"Error toggling hover effect: {e}")
            hover_effect_var.set(False)
            messagebox.showerror("Error", f"Failed to toggle hover effect: {e}")

    def on_transparency_change():
        """Handle transparency slider changes."""
        if not selected_hwnd:
            return
        
        try:
            # Get current transparency value (0-255)
            transparency_value = transparency_var.get()
            
            # Update percentage label
            percentage = int((transparency_value / 255) * 100)
            transparency_percent_label.config(text=f"{percentage}%")
            
            # Apply transparency only if hover effect is not active
            # and window is still valid
            if not hover_effect_var.get() and win32gui.IsWindow(selected_hwnd):
                set_window_transparent(selected_hwnd, transparency_value)
                
        except Exception as e:
            print(f"Error in transparency change: {e}")
            # Reset percentage label on error
            transparency_percent_label.config(text="Error")

    def start_hover_effect(hwnd):
        """Start the hover effect: make the window visible on hover."""
        last_state = None
        error_count = 0
        max_errors = 5
        
        while hover_effect_var.get() and hwnd == selected_hwnd and error_count < max_errors:
            try:
                # Check if the window is still valid
                if not win32gui.IsWindow(hwnd):
                    print(f"Window {hwnd} no longer valid, stopping hover effect")
                    break
                
                # Check current mouse state
                is_hovering = is_mouse_over_window(hwnd)
                
                # Only update transparency if state changed (performance optimization)
                if is_hovering != last_state:
                    if is_hovering:
                        # Use current transparency slider value when hovered
                        hover_transparency = transparency_var.get()
                        set_window_transparent(hwnd, hover_transparency)
                    else:
                        # Make window invisible when not hovered
                        set_window_transparent(hwnd, 0)
                    last_state = is_hovering
                
                error_count = 0  # Reset error count on successful operation
                time.sleep(0.05)  # Reduced from 0.1 for better responsiveness
                
            except Exception as e:
                error_count += 1
                print(f"Error in hover effect (attempt {error_count}/{max_errors}): {e}")
                time.sleep(0.2)  # Wait longer after errors
        
        if error_count >= max_errors:
            print(f"Too many errors in hover effect for window {hwnd}, stopping")
            # Try to restore window transparency before stopping
            try:
                current_transparency = transparency_var.get()
                set_window_transparent(hwnd, current_transparency)
            except:
                pass

    def stop_hover_effect(hwnd):
        """Stop the hover effect and restore current transparency setting."""
        try:
            if win32gui.IsWindow(hwnd):
                current_transparency = transparency_var.get()
                set_window_transparent(hwnd, current_transparency)  # Restore current transparency slider value
                print(f"Stopped hover effect for window {hwnd}, restored transparency to {current_transparency}")
        except Exception as e:
            print(f"Error stopping hover effect: {e}")
            # Force restore to full opacity as fallback
            try:
                set_window_transparent(hwnd, 255)
                print(f"Force restored window {hwnd} to full opacity")
            except:
                pass

    def is_window_topmost(hwnd):
        """Check if a window is currently set as topmost."""
        try:
            if not win32gui.IsWindow(hwnd):
                return False
            
            extended_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            return bool(extended_style & win32con.WS_EX_TOPMOST)
        except Exception as e:
            print(f"Error checking topmost status: {e}")
            return False

    def monitor_topmost_status(hwnd):
        """Continuously monitor and maintain the topmost status of a window."""
        last_check_time = time.time()
        consecutive_failures = 0
        max_failures = 3
        
        while always_on_top_var.get() and hwnd == selected_hwnd:
            try:
                # Check if the window is still valid
                if not win32gui.IsWindow(hwnd):
                    print(f"Window {hwnd} is no longer valid, stopping topmost monitoring")
                    break
                
                # Check current topmost status
                current_status = is_window_topmost(hwnd)
                
                # If the window should be topmost but isn't, try to fix it
                if always_on_top_var.get() and not current_status:
                    print(f"Window {hwnd} lost topmost status, attempting to restore...")
                    success = set_window_always_on_top(hwnd, True)
                    
                    if success:
                        consecutive_failures = 0
                        print(f"Successfully restored topmost status for window {hwnd}")
                    else:
                        consecutive_failures += 1
                        print(f"Failed to restore topmost status (attempt {consecutive_failures}/{max_failures})")
                        
                        if consecutive_failures >= max_failures:
                            print(f"Too many consecutive failures, window may be unresponsive")
                            # Optionally notify user via UI
                            root.after(0, lambda: messagebox.showwarning(
                                "Topmost Monitor", 
                                f"Unable to maintain always-on-top for the selected window. "
                                f"The window may be unresponsive or have been closed."
                            ))
                            break
                else:
                    consecutive_failures = 0
                
                # Adaptive monitoring frequency
                current_time = time.time()
                if current_time - last_check_time > 30:  # Every 30 seconds, do a more thorough check
                    # Force refresh the topmost state
                    if always_on_top_var.get():
                        set_window_always_on_top(hwnd, True)
                    last_check_time = current_time
                
                # Sleep for a short interval before next check
                time.sleep(0.5)  # Check every 500ms
                
            except Exception as e:
                print(f"Error in topmost monitoring: {e}")
                consecutive_failures += 1
                if consecutive_failures >= max_failures:
                    break
                time.sleep(1)  # Wait longer after errors

    def start_topmost_monitoring(hwnd):
        """Start monitoring the topmost status in a separate thread."""
        nonlocal topmost_monitor_thread
        
        # Stop any existing monitoring thread
        stop_topmost_monitoring()
        
        if always_on_top_var.get():
            topmost_monitor_thread = threading.Thread(target=monitor_topmost_status, args=(hwnd,))
            topmost_monitor_thread.daemon = True
            topmost_monitor_thread.start()
            print(f"Started topmost monitoring for window {hwnd}")

    def stop_topmost_monitoring():
        """Stop the topmost monitoring thread."""
        nonlocal topmost_monitor_thread
        
        if topmost_monitor_thread and topmost_monitor_thread.is_alive():
            # The thread will stop when always_on_top_var becomes False
            # or when selected_hwnd changes
            print("Stopping topmost monitoring...")
            topmost_monitor_thread = None

    def on_close():
        """Handle window close event to disable all effects and reset the selected window."""
        print("Application closing, cleaning up...")
        
        try:
            if selected_hwnd and win32gui.IsWindow(selected_hwnd):
                # First, disable all effects to stop any active threads
                always_on_top_var.set(False)
                hover_effect_var.set(False)
                stop_topmost_monitoring()
                
                # Give threads a moment to stop, especially hover effect
                time.sleep(0.2)
                
                # Force restore window to normal state regardless of current settings
                try:
                    set_window_always_on_top(selected_hwnd, False)
                except Exception as e:
                    print(f"Error removing topmost: {e}")
                
                try:
                    # Use the dedicated restoration function
                    restore_window_to_normal(selected_hwnd)
                except Exception as e:
                    print(f"Error restoring window: {e}")
                    # Fallback: try to set full opacity
                    try:
                        set_window_transparent(selected_hwnd, 255)
                        print(f"Fallback: Set window {selected_hwnd} to full opacity")
                    except Exception as e2:
                        print(f"Fallback also failed: {e2}")
                
                print(f"Restored window {selected_hwnd} to normal state")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
        
        try:
            # Stop tray icon if it exists
            if tray_icon:
                tray_icon.stop()
        except Exception as e:
            print(f"Error stopping tray icon: {e}")
        
        print("Application cleanup complete")
        root.destroy()

    def on_minimize_to_tray():
        """Minimize the window to system tray."""
        hide_to_tray()

    # Create the main UI window
    root = tk.Tk()
    root.title(f"{__title__} v{__version__}")
    
    # Set the window icon for taskbar
    def get_icon_path():
        """Get the correct path to the icon file."""
        if getattr(sys, 'frozen', False):
            # Running as executable
            return os.path.join(sys._MEIPASS, 'hover_icon.ico')
        else:
            # Running as script
            return 'hover_icon.ico'
    
    try:
        icon_path = get_icon_path()
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception as e:
        # If icon loading fails, continue without icon
        print(f"Could not load icon: {e}")

    # Resize the window to make it more spacious
    root.geometry("400x320")  # Increased height to fit the transparency slider

    # Window selection frame
    selection_frame = tk.Frame(root)
    selection_frame.pack(padx=20, pady=10, fill='x')
    
    tk.Label(selection_frame, text="Select Window:").pack(anchor='w')
    
    window_var = tk.StringVar()
    window_dropdown = ttk.Combobox(selection_frame, textvariable=window_var, state='readonly', width=50)
    window_dropdown.pack(fill='x', pady=(5, 0))
    window_dropdown.bind('<<ComboboxSelected>>', lambda e: on_window_select())
    
    # Refresh button
    refresh_button = tk.Button(selection_frame, text="Refresh Window List", command=refresh_windows)
    refresh_button.pack(pady=(5, 0))

    # Minimize to tray button
    tray_button = tk.Button(selection_frame, text="Minimize to Tray", command=on_minimize_to_tray)
    tray_button.pack(pady=(5, 0))

    # Controls frame
    controls_frame = tk.Frame(root)
    controls_frame.pack(padx=20, pady=10, fill='x')

    # Set up Always on Top checkbox (default off, initially disabled)
    always_on_top_var = tk.BooleanVar(value=False)
    topmost_checkbox = tk.Checkbutton(controls_frame, text="Always on Top", variable=always_on_top_var, 
                                     command=on_toggle_topmost, state='disabled')
    topmost_checkbox.pack(padx=20, pady=5, anchor='w')

    # Set up Hover Effect checkbox (default off, initially disabled)
    hover_effect_var = tk.BooleanVar(value=False)
    hover_effect_checkbox = tk.Checkbutton(controls_frame, text="Enable Hover Effect", variable=hover_effect_var, 
                                          command=on_toggle_hover_effect, state='disabled')
    hover_effect_checkbox.pack(padx=20, pady=5, anchor='w')

    # Transparency slider frame
    transparency_frame = tk.Frame(controls_frame)
    transparency_frame.pack(padx=20, pady=5, fill='x')
    
    # Transparency label and slider
    transparency_label = tk.Label(transparency_frame, text="Window Transparency:")
    transparency_label.pack(anchor='w')
    
    # Create transparency variable (255 = fully opaque, 0 = fully transparent)
    transparency_var = tk.IntVar(value=255)
    
    transparency_slider = tk.Scale(transparency_frame, from_=0, to=255, orient='horizontal', 
                                  variable=transparency_var, command=lambda x: on_transparency_change(),
                                  state='disabled', length=300)
    transparency_slider.pack(fill='x', pady=(2, 0))
    
    # Add percentage label
    transparency_percent_label = tk.Label(transparency_frame, text="100%", fg="gray")
    transparency_percent_label.pack(anchor='w')

    # Instructions
    instructions = tk.Label(root, text="Select a window from the dropdown above to enable controls.", 
                           fg="gray", wraplength=350)
    instructions.pack(padx=20, pady=10)

    # Bind the close button event to disable effects and reset the selected window
    root.protocol("WM_DELETE_WINDOW", on_close)

    # Initialize with available windows
    refresh_windows()

    # Set up system tray
    tray_available = setup_tray()
    if not tray_available:
        # If tray setup failed, disable the minimize to tray button
        tray_button.config(state='disabled', text="Tray Unavailable")

    # Start the UI loop
    root.mainloop()

# Global variable to track the selected window for cleanup
_global_selected_hwnd = None

def cleanup_on_exit():
    """Global cleanup function called when the application exits."""
    global _global_selected_hwnd
    if _global_selected_hwnd and win32gui.IsWindow(_global_selected_hwnd):
        try:
            print("Global cleanup: Restoring window to normal state...")
            restore_window_to_normal(_global_selected_hwnd)
        except Exception as e:
            print(f"Global cleanup error: {e}")

def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown."""
    print(f"Received signal {signum}, cleaning up...")
    cleanup_on_exit()
    sys.exit(0)

def main():
    """Main function to run the application."""
    print("Starting Window Control application...")
    print("Use the GUI to select a window and apply effects.")
    
    # Register cleanup handlers
    atexit.register(cleanup_on_exit)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the UI - it now handles everything
    create_ui()

if __name__ == "__main__":
    main()
