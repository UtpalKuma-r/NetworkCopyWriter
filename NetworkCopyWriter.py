import customtkinter as ctk
import socket
import threading
import pyautogui
from datetime import datetime
from PIL import Image
import os
import sys

class NetworkCopywriter(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Network Copywriter")
        self.geometry("900x300")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        # self.iconbitmap("logo.ico")

        icon_path = self.resource_path("logo.ico")
        self.iconbitmap(icon_path)  # Taskbar & title bar (Windows)

        # For CustomTkinter
        self.logo_image = ctk.CTkImage(light_image=Image.open(icon_path), size=(40, 40))

        self.REMOVE_NEWLINES = ctk.BooleanVar(value=True)
        self.connected_clients = []
        self.server_running = False
        self.server_socket = None
        self.client_socket = None

        self.show_main_page()

    def resource_path(self, relative_path):
        """Get absolute path for PyInstaller compatibility."""
        if getattr(sys, "frozen", False):  # Running as EXE
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def show_main_page(self):
        """Show the main selection page"""
        self.clear_window()

        label = ctk.CTkLabel(self, text="Run as:", font=("Arial", 20))
        label.pack(pady=20)

        server_button = ctk.CTkButton(self, text="Start as Server", command=self.show_server_setup_page)
        server_button.pack(pady=10)

        client_button = ctk.CTkButton(self, text="Start as Client", command=self.start_client)
        client_button.pack(pady=10)

    def show_server_setup_page(self):
        """Show page to set server port before starting the server."""
        for widget in self.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self, text="Set Server Port", font=("Arial", 18)).pack(pady=10)

        ctk.CTkLabel(self, text="Port:").pack()
        self.server_port_entry = ctk.CTkEntry(self, width=200)
        self.server_port_entry.insert(0, "12345")  # Default port
        self.server_port_entry.pack(pady=5)

        start_button = ctk.CTkButton(self, text="Start Server", command=self.start_server)
        start_button.pack(pady=10)

        back_button = ctk.CTkButton(self, text="Back", command=self.show_main_page)
        back_button.pack(pady=10)

    def start_server(self):
        """Start the server using the given/default port."""
        try:
            self.server_port = int(self.server_port_entry.get())  # Get the user-entered port
        except ValueError:
            self.server_port = 12345  # Fallback to default if invalid

        self.show_server_page()  # Now show the actual server page

    def show_server_page(self):
        """Set up the server UI and start the server"""
        self.clear_window()

        # Grid layout: 3 columns (20% - 60% - 20%)
        self.grid_columnconfigure(0, weight=1)  # Left Column
        self.grid_columnconfigure(1, weight=3)  # Center Column
        self.grid_columnconfigure(2, weight=1)  # Right Column

        # === Column 1: Server Info ===
        server_frame = ctk.CTkFrame(self)
        server_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10, rowspan=2)

        ctk.CTkLabel(server_frame, text="Server Settings", font=("Arial", 16, "bold")).pack(pady=10)
        ctk.CTkLabel(server_frame, text=f"IP Address: {self.get_local_ip()}", font=("Arial", 14)).pack(pady=5)
        ctk.CTkLabel(server_frame, text=f"Port: {self.server_port}", font=("Arial", 14)).pack(pady=5)

        remove_newlines_checkbox = ctk.CTkCheckBox(server_frame, text="Remove New Lines", variable=self.REMOVE_NEWLINES)
        remove_newlines_checkbox.pack(pady=10)

        back_button = ctk.CTkButton(server_frame, text="Back", command=self.stop_server)
        back_button.pack(pady=10)

        # === Column 2: Message Broadcast ===
        message_frame = ctk.CTkFrame(self)
        message_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.message_entry = ctk.CTkTextbox(message_frame, height=200, width=400)
        self.message_entry.pack(pady=10)

        broadcast_button = ctk.CTkButton(message_frame, text="Broadcast", command=self.broadcast_message)
        broadcast_button.pack(pady=10)

        # === Column 3: Client List ===
        client_frame = ctk.CTkFrame(self)
        client_frame.grid(row=0, column=2, sticky="nsew", padx=10, pady=10, rowspan=2)

        ctk.CTkLabel(client_frame, text="Connected Clients", font=("Arial", 16, "bold")).pack(pady=10)

        self.client_count_label = ctk.CTkLabel(client_frame, text="Total Clients: 0", font=("Arial", 14))
        self.client_count_label.pack(pady=5)

        self.client_listbox = ctk.CTkTextbox(client_frame, height=150, width=180)
        self.client_listbox.pack(pady=10)

        # Start server in a thread
        self.server_running = True
        threading.Thread(target=self.run_server, daemon=True).start()

    def run_server(self):
        """Runs the server to accept client connections"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("0.0.0.0", self.server_port))
        self.server_socket.listen(5)
        print("Server started, waiting for connections...")

        while self.server_running:
            try:
                client_socket, client_address = self.server_socket.accept()
                print(f"New connection from {client_address[0]}")
                
                # Store the new client
                self.connected_clients.append((client_socket, client_address[0]))
                self.update_client_list()

                # Start listening for messages from this client
                threading.Thread(target=self.handle_client, args=(client_socket, client_address), daemon=True).start()

            except:
                break  # Stop accepting connections when the server shuts down

    def broadcast_message(self):
        """Broadcast message to all clients"""
        message = self.message_entry.get("1.0", "end-1c")
        if self.REMOVE_NEWLINES.get():
            message = message.replace("\n", " ")

        for client_socket, _ in self.connected_clients:
            try:
                client_socket.sendall(message.encode())
            except:
                pass  

    def stop_server(self):
        """Stop server and disconnect clients"""
        self.server_running = False
        for client_socket, _ in self.connected_clients:
            try:
                client_socket.close()
            except:
                pass  

        self.connected_clients.clear()
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

        self.show_main_page()

    def handle_client(self, client_socket, client_address):
        """Handle individual client messages and disconnections"""
        try:
            while True:
                message = client_socket.recv(1024).decode("utf-8")

                if not message:
                    break  # Client disconnected

                if message == "DISCONNECT":
                    print(f"Client {client_address[0]} disconnected")
                    client_socket.close()
                    self.remove_client(client_socket)
                    break  # Stop listening for this client

        except:
            pass

    def update_client_list(self):
        """Updates the client list UI to show only active clients"""
        self.client_count_label.configure(text=f"Total Clients: {len(self.connected_clients)}")

        # Clear and update client list
        self.client_listbox.delete("1.0", "end")
        for idx, (_, client_ip) in enumerate(self.connected_clients, start=1):
            self.client_listbox.insert("end", f"Client {idx}: {client_ip}\n")

    def remove_client(self, client_socket):
        """Remove the client from the list and update the UI"""
        self.connected_clients = [(sock, ip) for sock, ip in self.connected_clients if sock != client_socket]
        self.update_client_list()

    def start_client(self):
        """Show the client connection page"""
        for widget in self.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self, text="Enter Server Details", font=("Arial", 18)).pack(pady=10)

        ctk.CTkLabel(self, text="Server IP:").pack()
        self.server_ip_entry = ctk.CTkEntry(self, width=200)
        self.server_ip_entry.pack(pady=5)
        
        ctk.CTkLabel(self, text="Server Port:").pack()
        self.server_port_entry = ctk.CTkEntry(self, width=200)
        self.server_port_entry.pack(pady=5)
        
        connect_button = ctk.CTkButton(self, text="Connect", command=self.connect_to_server)
        connect_button.pack(pady=10)
        
        back_button = ctk.CTkButton(self, text="Back", command=self.show_main_page)
        back_button.pack(pady=10)

        # 🔹 Added status label for errors/success messages
        self.status_label = ctk.CTkLabel(self, text="", text_color="red")
        self.status_label.pack()

    def connect_to_server(self):
        """Attempt to connect to the server with provided IP and port"""
        server_ip = self.server_ip_entry.get()
        server_port = self.server_port_entry.get()
        
        if not server_ip or not server_port:
            self.status_label.configure(text="Please enter both IP and Port")
            return
        
        try:
            server_port = int(server_port)
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((server_ip, server_port))
            
            # Store server details
            self.server_ip = server_ip
            self.server_port = server_port
            
            self.status_label.configure(text="Connected successfully!", text_color="green")
            self.show_client_page()
        except Exception as e:
            self.status_label.configure(text=f"Connection failed: {e}", text_color="red")

    def show_client_page(self):
        """Show the client message receiving page after connection"""
        for widget in self.winfo_children():
            widget.destroy()
        
        # Create grid layout
        self.grid_columnconfigure(0, weight=1)  # Column 1 (Server Info)
        self.grid_columnconfigure(1, weight=3)  # Column 2 (Messages)

        # === Column 1: Server Info ===
        server_info_frame = ctk.CTkFrame(self)
        server_info_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10, rowspan=2)

        ctk.CTkLabel(server_info_frame, text="Connected to Server", font=("Arial", 16, "bold")).pack(pady=10)
        ctk.CTkLabel(server_info_frame, text=f"Server IP: {self.server_ip}", font=("Arial", 14)).pack(pady=5)
        ctk.CTkLabel(server_info_frame, text=f"Port: {self.server_port}", font=("Arial", 14)).pack(pady=5)

        # Message Count Label
        self.message_count = 0
        self.message_count_label = ctk.CTkLabel(server_info_frame, text=f"Messages Received: {self.message_count}", font=("Arial", 14))
        self.message_count_label.pack(pady=5)

        # Auto-Typing Checkbox
        self.auto_typing = ctk.BooleanVar(value=False)
        auto_typing_checkbox = ctk.CTkCheckBox(server_info_frame, text="Enable Auto-Typing", variable=self.auto_typing)
        auto_typing_checkbox.pack(pady=10)

        # Back Button (Disconnect)
        back_button = ctk.CTkButton(server_info_frame, text="Back", command=self.disconnect_from_server)
        back_button.pack(pady=10)

        # === Column 2: Messages Display ===
        message_frame = ctk.CTkFrame(self)
        message_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.message_display = ctk.CTkTextbox(message_frame, height=250, width=500)
        self.message_display.pack(pady=10)

        # Start listening for messages
        threading.Thread(target=self.receive_messages, daemon=True).start()

    def disconnect_from_server(self):
        """Disconnect from the server cleanly"""
        if self.client_socket:
            try:
                self.client_socket.sendall(b"DISCONNECT")  # Notify server
                self.client_socket.close()
            except:
                pass

        self.client_socket = None
        self.show_main_page()

    def receive_messages(self):
        """Receive and display messages from the server"""
        try:
            while True:
                message = self.client_socket.recv(1024).decode("utf-8")
                if not message:
                    break

                # Get timestamp with date
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                formatted_message = f"[{timestamp}] {message}"

                # Display message
                self.message_display.insert("end", formatted_message + "\n")
                self.message_display.see("end")  # Auto-scroll

                # Update message count
                self.message_count += 1
                self.message_count_label.configure(text=f"Messages Received: {self.message_count}")

                # Auto-typing feature
                if self.auto_typing.get():
                    pyautogui.write(message, interval=0.05)  # Simulate typing

        except:
            pass

    def get_local_ip(self):
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except:
            return "Unknown"

    def clear_window(self):
        """Clear all widgets from the window"""
        for widget in self.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    app = NetworkCopywriter()
    app.mainloop()