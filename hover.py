import win32gui
import win32con
import win32api
import time
import tkinter as tk
from tkinter import ttk, messagebox
import threading

# Version information
__version__ = "1.0.0"
__title__ = "Hover"

def set_window_always_on_top(hwnd, always_on_top):
    """Set the window to always stay on top."""
    if always_on_top:
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
    else:
        win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

def set_window_transparent(hwnd, transparency):
    """Set the window transparency."""
    extended_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, extended_style | win32con.WS_EX_LAYERED)
    
    # Set the window transparency based on the specified value
    win32gui.SetLayeredWindowAttributes(hwnd, 0, transparency, win32con.LWA_ALPHA)

def is_mouse_over_window(hwnd):
    """Check if the mouse is over the window."""
    mouse_x, mouse_y = win32api.GetCursorPos()
    window_rect = win32gui.GetWindowRect(hwnd)
    return window_rect[0] <= mouse_x <= window_rect[2] and window_rect[1] <= mouse_y <= window_rect[3]

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

def create_ui():
    """Create the UI window using tkinter."""
    selected_hwnd = None
    
    def on_window_select():
        """Handle window selection from dropdown."""
        nonlocal selected_hwnd
        selection = window_var.get()
        if selection and selection != "Select a window...":
            # Extract hwnd from the selection string
            hwnd_str = selection.split(" - ")[0]
            selected_hwnd = int(hwnd_str)
            
            # Enable the control buttons
            topmost_checkbox.config(state='normal')
            hover_effect_checkbox.config(state='normal')
        else:
            selected_hwnd = None
            # Disable the control buttons
            topmost_checkbox.config(state='disabled')
            hover_effect_checkbox.config(state='disabled')
    
    def refresh_windows():
        """Refresh the list of available windows."""
        windows = get_all_windows()
        window_options = ["Select a window..."]
        for hwnd, title in windows:
            # Limit title length for better display
            display_title = title[:50] + "..." if len(title) > 50 else title
            window_options.append(f"{hwnd} - {display_title}")
        
        window_dropdown['values'] = window_options
        window_var.set("Select a window...")
        
        # Reset selection and disable controls
        nonlocal selected_hwnd
        selected_hwnd = None
        topmost_checkbox.config(state='disabled')
        hover_effect_checkbox.config(state='disabled')
        always_on_top_var.set(False)
        hover_effect_var.set(False)

    def on_toggle_topmost():
        """Toggle the always-on-top state of the selected window."""
        if selected_hwnd:
            current_topmost = always_on_top_var.get()
            set_window_always_on_top(selected_hwnd, current_topmost)

    def on_toggle_hover_effect():
        """Toggle the hover effect (show/hide based on mouse hover)."""
        if not selected_hwnd:
            return
            
        if hover_effect_var.get():
            # Start the hover effect in a separate thread
            hover_thread = threading.Thread(target=start_hover_effect, args=(selected_hwnd,))
            hover_thread.daemon = True
            hover_thread.start()
        else:
            # Stop the hover effect and set window to fully visible
            stop_hover_effect(selected_hwnd)

    def start_hover_effect(hwnd):
        """Start the hover effect: make the window visible on hover."""
        while hover_effect_var.get() and hwnd == selected_hwnd:
            check_hover_and_update(hwnd, 255)  # Full opacity when hovered
            time.sleep(0.1)

    def stop_hover_effect(hwnd):
        """Stop the hover effect and set window to fully visible."""
        set_window_transparent(hwnd, 255)  # Make the window fully visible when hover effect is stopped

    def on_close():
        """Handle window close event to disable all effects and reset the selected window."""
        if selected_hwnd:
            # Disable all effects
            always_on_top_var.set(False)
            hover_effect_var.set(False)
            set_window_always_on_top(selected_hwnd, False)
            stop_hover_effect(selected_hwnd)
            set_window_transparent(selected_hwnd, 255)  # Make the window fully visible before closing
        root.destroy()

    # Create the main UI window
    root = tk.Tk()
    root.title(f"{__title__} v{__version__}")

    # Resize the window to make it more spacious
    root.geometry("400x250")  # Adjust the size to fit the content better

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

    # Instructions
    instructions = tk.Label(root, text="Select a window from the dropdown above to enable controls.", 
                           fg="gray", wraplength=350)
    instructions.pack(padx=20, pady=10)

    # Bind the close button event to disable effects and reset the selected window
    root.protocol("WM_DELETE_WINDOW", on_close)

    # Initialize with available windows
    refresh_windows()

    # Start the UI loop
    root.mainloop()

def main():
    """Main function to run the application."""
    print("Starting Window Control application...")
    print("Use the GUI to select a window and apply effects.")
    
    # Start the UI - it now handles everything
    create_ui()

if __name__ == "__main__":
    main()
