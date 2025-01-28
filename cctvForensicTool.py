import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
import requests
from googlesearch import search
import webbrowser
import socket
import time  # To add delay


class CameraDorkingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenEye: Public CCTV Forensic Tool")
        self.root.geometry("1000x750")
        self.root.resizable(True, True)  # Allow window resizing

        # Define color scheme
        self.dark_blue_grey = "#2E3440"  # Dark blue-grey for boxes
        self.light_blue_grey = "#4C566A"  # Light blue-grey for other boxes
        self.text_color = "#D8DEE9"  # Light text color for contrast
        self.highlight_color = "#81A1C1"  # Highlight color for selections
        self.dark_green = "#006400"

        # Load the animated GIF
        self.bg_gif = Image.open("background5.gif")  # Replace with your GIF file
        self.bg_frames = []
        try:
            while True:
                frame = self.bg_gif.copy()
                self.bg_frames.append(frame)
                self.bg_gif.seek(len(self.bg_frames))  # Go to the next frame
        except EOFError:
            pass  # End of GIF frames

        # Create a canvas for the animated background
        self.bg_canvas = tk.Canvas(root, highlightthickness=0, bg=self.dark_blue_grey)
        self.bg_canvas.place(relwidth=1, relheight=1, x=0, y=0)

        # Start the animation
        self.bg_frame_index = 0
        self.bg_photo = None  # To hold the resized image
        self.animate_gif()

        # Bind window resize to dynamically adjust canvas size
        self.root.bind("<Configure>", self.resize_gif)

        # Dork selection
        tk.Label(root, text="Public CCTV Dork Queries:", bg=self.dark_blue_grey, fg=self.text_color).pack(pady=5)
        self.dork_var = tk.StringVar()
        self.dork_combobox = ttk.Combobox(root, textvariable=self.dork_var, width=70)
        self.dork_combobox['values'] = [
            'inurl:"CgiStart?page="',
            'inurl:/view.shtml',
            'intitle:"Live View / - AXIS"'
        ]
        self.dork_combobox.pack(pady=5)

        # Apply custom style to the Combobox
        self.style = ttk.Style()
        self.style.configure("Highlight.TCombobox", background=self.light_blue_grey, fieldbackground=self.light_blue_grey,
                             foreground=self.text_color, bordercolor="#000000", relief=tk.GROOVE)
        self.dork_combobox.config(style="Highlight.TCombobox")  # Apply the custom style

        # Results display
        self.result_label = tk.Label(root, text="Public CCTV List:", bg=self.dark_blue_grey, fg=self.text_color)
        self.result_label.pack(pady=5)
        self.result_box = tk.Listbox(root, height=15, width=100, bg=self.light_blue_grey, fg=self.text_color, selectbackground=self.highlight_color)
        self.result_box.bind("<<ListboxSelect>>", self.on_result_select)
        self.result_box.pack(pady=5)
        self.result_box.config(relief=tk.GROOVE, bd=3)  # Highlight the Listbox

        # Metadata display
        self.metadata_label = tk.Label(root, text="Metadata of the Selected CCTV:", bg=self.dark_blue_grey, fg=self.text_color)
        self.metadata_label.pack(pady=5)
        self.metadata_box = tk.Text(root, height=15, width=50, state=tk.DISABLED, bg=self.light_blue_grey, fg=self.text_color)
        self.metadata_box.pack(pady=5)
        self.metadata_box.config(relief=tk.GROOVE, bd=3)  # Highlight the Metadata Box

        # Progress bar and status label
        self.progress_label = tk.Label(root, text="", font=("Arial", 10), fg=self.text_color, bg=self.dark_blue_grey)
        self.progress_bar = ttk.Progressbar(root, orient="horizontal", mode="determinate", length=300)

        # Button Frame to hold buttons side by side
        self.button_frame = tk.Frame(root, bg=self.dark_blue_grey)
        self.button_frame.pack(pady=5)

        # Buttons
        self.search_button = tk.Button(root, text="Execute Queries", command=self.start_search_with_delay, bg=self.dark_green, fg=self.text_color)
        self.search_button.pack(pady=5)
        self.test_button = tk.Button(self.button_frame, text="Check Links for Public CCTV",
                                     command=self.start_test_links, state=tk.DISABLED, bg=self.dark_green, fg=self.text_color)
        self.test_button.pack(side=tk.LEFT, padx=5)
        self.open_button = tk.Button(self.button_frame, text="Open in Browser", command=self.open_in_browser,
                                     state=tk.DISABLED, bg=self.dark_green, fg=self.text_color)
        self.open_button.pack(side=tk.LEFT, padx=5)

        # Status bar
        self.status_var = tk.StringVar(value="Ready. Select a query and click 'Execute Queries' to begin.")
        self.status_label = tk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w", bg=self.dark_blue_grey, fg=self.text_color)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)

        # Data storage
        self.search_results = []
        self.tested_links = []
        self.selected_link = None

    def animate_gif(self):
        """Animate the GIF background."""
        if self.bg_frames:
            # Resize the current frame to fit the window dynamically
            frame = self.bg_frames[self.bg_frame_index]
            resized_frame = frame.resize((self.root.winfo_width(), self.root.winfo_height()), Image.Resampling.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(resized_frame)
            self.bg_canvas.create_image(0, 0, anchor="nw", image=self.bg_photo)
            self.bg_frame_index = (self.bg_frame_index + 1) % len(self.bg_frames)
            self.root.after(100, self.animate_gif)  # Adjust timing for smoother animation

    def resize_gif(self, event):
        """Resize the GIF dynamically when the window size changes."""
        self.bg_canvas.config(width=self.root.winfo_width(), height=self.root.winfo_height())

    def start_search_with_delay(self):
        """Start the search process with a delay and loading bar."""
        dork = self.dork_var.get()
        if not dork:
            messagebox.showerror("Error", "Please select a dork.")
            return
        self.update_status("Searching for live public CCTV feeds... Please wait.")
        self.progress_label.config(text="Searching for live public CCTV feeds...")
        self.progress_label.pack(pady=5)
        self.progress_bar.pack(pady=5)
        self.search_button.config(state=tk.DISABLED)  # Disable Execute Queries button
        threading.Thread(target=self.search_with_loading_bar, args=(dork,)).start()

    def search_with_loading_bar(self, dork):
        """Show a loading bar for 3 seconds before performing the search."""
        self.progress_bar["value"] = 0
        for i in range(30):  # Simulate loading for 3 seconds
            time.sleep(0.1)
            self.progress_bar["value"] += 3.33  # Increment progress bar
            self.root.update_idletasks()
        self.progress_label.config(text="Search completed")
        self.perform_search(dork)

    def update_status(self, message):
        """Update the status bar."""
        self.status_var.set(message)

    def perform_search(self, dork):
        """Perform Google Dork search."""
        try:
            self.search_results = [result for result in search(dork, num_results=10)]
            self.update_results()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.update_status("Search completed. Click 'Check Links' to verify public camera feeds.")
            self.test_button.config(state=tk.NORMAL)  # Enable Test Links button

    def update_results(self):
        """Update the results Listbox."""
        self.result_box.delete(0, tk.END)
        for idx, result in enumerate(self.search_results, start=1):
            self.result_box.insert(tk.END, f"{idx}: {result}")
        self.result_label.config(text="Live Public Camera Feed Links Found:")
        self.result_box.pack(pady=5)

    def start_test_links(self):
        """Test the links for public camera feeds."""
        self.update_status("Testing links... Please wait.")
        self.test_button.config(state=tk.DISABLED)  # Disable Test Links button
        threading.Thread(target=self.test_camera_links).start()

    def test_camera_links(self):
        """Filter and return links that match public CCTV patterns."""
        self.tested_links = []
        total_links = len(self.search_results)
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = total_links

        for idx, link in enumerate(self.search_results, start=1):
            self.progress_label.config(text=f"Checking link {idx}/{total_links}...")
            if self.check_camera_link(link):
                self.tested_links.append(link)
            self.progress_bar["value"] += 1
            self.root.update_idletasks()

        self.update_tested_links()

    def update_tested_links(self):
        """Update the results with tested links."""
        self.result_box.delete(0, tk.END)
        for idx, link in enumerate(self.tested_links, start=1):
            self.result_box.insert(tk.END, f"{idx}: {link}")

        # Update status and provide instructions
        self.update_status("Testing completed. Click on a link to view metadata.")
        self.progress_label.config(text="All links tested.")

        # Enable Open in Browser button if links are available
        self.open_button.config(state=tk.NORMAL if self.tested_links else tk.DISABLED)

        # Add a visual cue near the Listbox
        self.result_label.config(text="Live Public Camera Feed Links Found: (Click on a link to view metadata)",
                                 fg=self.highlight_color, font=("Arial", 10, "bold"))

        # Highlight the Listbox
        self.result_box.config(bg=self.light_blue_grey, relief=tk.GROOVE, bd=3)

        # Show a pop-up message
        messagebox.showinfo("Action Required", "Click on a link to view METADATA and Click on the OPEN IN BROWSER button below.")

    def check_camera_link(self, link):
        """Check if the link is a public camera feed."""
        print(f"Testing link: {link}")
        cctv_patterns = [
            "CgiStart", "view/view.shtml", "video.mjpg", "imagePath",
            "/view.shtml", "?id=", "size="
        ]
        if not any(pattern in link for pattern in cctv_patterns):
            print(f"[-] URL does not match public CCTV patterns: {link}")
            return False

        print(f"[+] URL matches public CCTV patterns: {link}")
        try:
            response = requests.get(link, timeout=10, headers={"User-Agent": "Mozilla/5.0"}, verify=False)
            if response.status_code == 200:
                print(f"[+] URL is accessible: {link}")
            else:
                print(f"[-] URL responded with status code {response.status_code}: {link}")
        except requests.RequestException as e:
            print(f"[-] Error accessing link: {e}")
            return False
        return True

    def on_result_select(self, event):
        """Fetch metadata for the selected link."""
        try:
            selected_idx = self.result_box.curselection()[0]
            self.selected_link = self.tested_links[selected_idx]
            self.update_status(f"Fetching metadata for: {self.selected_link}")
            threading.Thread(target=self.get_camera_metadata, args=(self.selected_link,)).start()
        except IndexError:
            pass

    def get_camera_metadata(self, link):
        """Fetch metadata for the selected link and display it in the metadata box."""
        try:
            # Extract the domain from the URL
            domain = link.split("//")[1].split("/")[0]
            ip = socket.gethostbyname(domain)

            # Fetch WHOIS data
            whois_url = f"https://api.ip2whois.com/v2?key=<IP2LOCATION API KEY>&domain={domain}"
            whois_response = requests.get(whois_url, timeout=10).json()

            # Fetch Geolocation data
            geo_url = f"https://api.ip2location.io/?key=<IP2LOCATION API KEY>&ip={ip}"
            geo_response = requests.get(geo_url, timeout=10).json()

            # Clear the metadata box
            self.metadata_box.config(state=tk.NORMAL)
            self.metadata_box.delete(1.0, tk.END)

            # WHOIS Information
            self.metadata_box.insert(tk.END, "\t    === WHOIS Information ===\n\n")
            self.metadata_box.insert(tk.END, f"Domain: {domain}\n")
            self.metadata_box.insert(tk.END, f"IP Address: {ip}\n")
            self.metadata_box.insert(tk.END, f"WHOIS Status: {whois_response.get('status', 'N/A')}\n")
            self.metadata_box.insert(tk.END, f"Registrar: {whois_response.get('registrar', {}).get('name', 'N/A')}\n")
            self.metadata_box.insert(tk.END, f"Domain Age: {whois_response.get('domain_age', 'N/A')} days\n\n")

            # Geolocation Information
            self.metadata_box.insert(tk.END, "\t    === Geolocation Information ===\n\n")
            self.metadata_box.insert(tk.END, f"Country: {geo_response.get('country_name', 'N/A')}\n")
            self.metadata_box.insert(tk.END, f"City: {geo_response.get('city_name', 'N/A')}\n")
            self.metadata_box.insert(tk.END, f"Latitude: {geo_response.get('latitude', 'N/A')}\n")
            self.metadata_box.insert(tk.END, f"Longitude: {geo_response.get('longitude', 'N/A')}\n")

            # Disable editing of the metadata box
            self.metadata_box.config(state=tk.DISABLED)
            self.metadata_label.pack(pady=5)
            self.metadata_box.pack(pady=5)
            self.update_status("Metadata fetched. You can now open the link in your browser.")
        except Exception as e:
            # Display error in the metadata box
            self.metadata_box.config(state=tk.NORMAL)
            self.metadata_box.delete(1.0, tk.END)
            self.metadata_box.insert(tk.END, f"Error fetching metadata: {e}\n")
            self.metadata_box.config(state=tk.DISABLED)

    def open_in_browser(self):
        """Open the selected link in the browser and show the pinned location on Google Maps."""
        try:
            # Ensure a link is selected
            if not self.selected_link:
                messagebox.showwarning("Warning", "No link selected to open.")
                return

            # Open the selected link in the default web browser
            webbrowser.open(self.selected_link)

            # Extract latitude and longitude from the metadata box
            metadata_text = self.metadata_box.get("1.0", tk.END)
            latitude = None
            longitude = None

            # Search for latitude and longitude in the metadata text
            for line in metadata_text.split("\n"):
                if "Latitude:" in line:
                    latitude = line.split(":")[1].strip()
                if "Longitude:" in line:
                    longitude = line.split(":")[1].strip()

            # If latitude and longitude are found, open Google Maps
            if latitude and longitude:
                google_maps_url = f"https://www.google.com/maps?q={latitude},{longitude}"
                webbrowser.open(google_maps_url)
                messagebox.showinfo("Info", f"Opened {self.selected_link} and Google Maps location in your browser.")
            else:
                messagebox.showwarning("Warning", "Latitude and Longitude not found in metadata.")

            # Disable Open in Browser button after opening
            self.open_button.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open link or Google Maps: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = CameraDorkingApp(root)
    root.mainloop()