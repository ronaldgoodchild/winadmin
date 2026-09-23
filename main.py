"""
REGWinadmin - Main Application
Modern Windows 11 & Server 2022+ Administration Tool
By Ronald Goodchild
"""

import customtkinter as ctk
from tkinter import messagebox, scrolledtext, filedialog
import threading
import json
import platform
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from win_admin_tools import WindowsAdminTools, format_bytes, format_json, export_to_csv
from config import *

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class CredentialDialog(ctk.CTkToplevel):
    """Dialog for entering remote computer credentials"""
    
    def __init__(self, parent, computer_name: str):
        super().__init__(parent)
        
        self.title(f"Remote Connection - {computer_name}")
        self.geometry("450x280")
        self.resizable(False, False)
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Center the dialog
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.winfo_screenheight() // 2) - (280 // 2)
        self.geometry(f"+{x}+{y}")
        
        self.username = None
        self.password = None
        self.result = False
        
        self.setup_ui(computer_name)
        
    def setup_ui(self, computer_name: str):
        """Setup credential dialog UI"""
        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        header_label = ctk.CTkLabel(
            main_frame,
            text=f"🔐 Remote Connection Credentials",
            font=("Arial", 16, "bold")
        )
        header_label.pack(pady=(0, 5))
        
        computer_label = ctk.CTkLabel(
            main_frame,
            text=f"Computer: {computer_name}",
            font=("Arial", 12),
            text_color="gray"
        )
        computer_label.pack(pady=(0, 20))
        
        # Username field
        username_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        username_frame.pack(fill='x', pady=5)
        
        ctk.CTkLabel(
            username_frame,
            text="Username:",
            font=("Arial", 12),
            width=100,
            anchor='w'
        ).pack(side='left', padx=(0, 10))
        
        self.username_entry = ctk.CTkEntry(
            username_frame,
            width=250,
            placeholder_text="DOMAIN\\username or user@domain.com"
        )
        self.username_entry.pack(side='left', fill='x', expand=True)
        self.username_entry.focus()
        
        # Password field
        password_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        password_frame.pack(fill='x', pady=5)
        
        ctk.CTkLabel(
            password_frame,
            text="Password:",
            font=("Arial", 12),
            width=100,
            anchor='w'
        ).pack(side='left', padx=(0, 10))
        
        self.password_entry = ctk.CTkEntry(
            password_frame,
            width=250,
            show="●",
            placeholder_text="Enter password"
        )
        self.password_entry.pack(side='left', fill='x', expand=True)
        
        # Bind Enter key to connect
        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus())
        self.password_entry.bind('<Return>', lambda e: self.on_connect())
        
        # Info label
        info_label = ctk.CTkLabel(
            main_frame,
            text="Note: Credentials are used for this session only",
            font=("Arial", 9),
            text_color="gray60"
        )
        info_label.pack(pady=(15, 10))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=(10, 0))
        
        connect_btn = ctk.CTkButton(
            button_frame,
            text="Connect",
            command=self.on_connect,
            width=120,
            height=35,
            fg_color="green"
        )
        connect_btn.pack(side='left', padx=5)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.on_cancel,
            width=120,
            height=35,
            fg_color="gray"
        )
        cancel_btn.pack(side='left', padx=5)
        
    def on_connect(self):
        """Handle connect button click"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showwarning(
                "Missing Credentials",
                "Please enter both username and password",
                parent=self
            )
            return
        
        self.username = username
        self.password = password
        self.result = True
        self.destroy()
        
    def on_cancel(self):
        """Handle cancel button click"""
        self.result = False
        self.destroy()
        
    def get_credentials(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Wait for dialog to close and return credentials
        
        Returns:
            Tuple of (success, username, password)
        """
        self.wait_window()
        return (self.result, self.username, self.password)


class REGWinadminGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        
        self.admin_tools: Optional[WindowsAdminTools] = None
        self.current_computer = "localhost"
        self.favorites = ["localhost"]
        self.remote_command_history = []
        self.saved_rdp_profiles = {}
        self._last_export_data = {}

        self.setup_ui()
        
    def setup_ui(self):
        """Setup the main user interface"""
        main_container = ctk.CTkFrame(self.root)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)

        self.setup_top_frame(main_container)
        self.setup_tab_view(main_container)
        self.setup_bottom_frame(main_container)
        self.setup_status_bar(main_container)
        
    def setup_top_frame(self, parent):
        """Setup top frame with computer name input"""
        top_frame = ctk.CTkFrame(parent)
        top_frame.pack(fill='x', pady=(0, 10))
        
        # Computer name label and entry
        ctk.CTkLabel(top_frame, text="Computer Name:", font=("Arial", 14, "bold")).pack(side='left', padx=5)
        
        self.computer_entry = ctk.CTkEntry(top_frame, width=300, placeholder_text="localhost or remote computer")
        self.computer_entry.pack(side='left', padx=5)
        self.computer_entry.insert(0, "localhost")
        
        # Connect button
        self.connect_btn = ctk.CTkButton(
            top_frame,
            text="Connect",
            command=self.connect_to_computer,
            width=100
        )
        self.connect_btn.pack(side='left', padx=5)
        
        # Test connection button
        self.test_btn = ctk.CTkButton(
            top_frame,
            text="Test Connection",
            command=self.test_connection,
            width=120,
            fg_color="gray"
        )
        self.test_btn.pack(side='left', padx=5)

        # Favorites dropdown
        self.favorites_menu = ctk.CTkOptionMenu(top_frame, values=self.favorites,
                                                 command=self.select_favorite, width=150)
        self.favorites_menu.pack(side='left', padx=5)
        ctk.CTkButton(top_frame, text="+ Save", command=self.save_favorite, width=70).pack(side='left', padx=2)

        # Status indicator
        self.status_label = ctk.CTkLabel(top_frame, text="● Not Connected", text_color="orange")
        self.status_label.pack(side='right', padx=10)
        
    def setup_tab_view(self, parent):
        """Setup tabbed interface using category sidebar + sub-tabs"""
        # Main horizontal layout: sidebar on left, content on right
        main_frame = ctk.CTkFrame(parent)
        main_frame.pack(fill='both', expand=True, pady=(0, 10))

        # Left sidebar for categories
        sidebar = ctk.CTkFrame(main_frame, width=160)
        sidebar.pack(side='left', fill='y', padx=(0, 5))
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text="Categories", font=("Arial", 13, "bold")).pack(pady=(8, 5))

        # Right content area holds stacked category frames
        self.content_area = ctk.CTkFrame(main_frame)
        self.content_area.pack(side='left', fill='both', expand=True)

        # Define categories and their tabs
        self.categories = {}
        self.category_buttons = {}
        category_defs = [
            ("System", ["System Info", "Services", "Processes", "Disks", "Scheduled Tasks"]),
            ("Network", ["Network", "DNS/DHCP", "Firewall"]),
            ("Remote", ["Remote Desktop", "Remote Cmd", "RDP Connect"]),
            ("Users", ["Active Directory", "Local Users"]),
            ("Software", ["Installed Software", "Winget Install", "Windows Update", "Env Vars"]),
            ("Security", ["Certificates", "Event Viewer"]),
            ("Resources", ["Printers", "Shares", "Tools"]),
        ]

        for cat_name, tab_names in category_defs:
            # Create a frame for this category (stacked in content_area)
            cat_frame = ctk.CTkFrame(self.content_area)
            # Create a CTkTabview inside each category frame
            cat_tabview = ctk.CTkTabview(cat_frame)
            cat_tabview.pack(fill='both', expand=True)

            tab_refs = {}
            for tab_name in tab_names:
                tab_refs[tab_name] = cat_tabview.add(tab_name)

            self.categories[cat_name] = {'frame': cat_frame, 'tabs': tab_refs, 'tabview': cat_tabview}

            # Category button in sidebar
            btn = ctk.CTkButton(sidebar, text=cat_name, width=140, height=32,
                                command=lambda cn=cat_name: self.show_category(cn))
            btn.pack(pady=2, padx=5)
            self.category_buttons[cat_name] = btn

        # Assign tab references for all setup methods
        sys_tabs = self.categories["System"]["tabs"]
        self.tab_system = sys_tabs["System Info"]
        self.tab_services = sys_tabs["Services"]
        self.tab_processes = sys_tabs["Processes"]
        self.tab_disks = sys_tabs["Disks"]
        self.tab_tasks = sys_tabs["Scheduled Tasks"]

        net_tabs = self.categories["Network"]["tabs"]
        self.tab_network = net_tabs["Network"]
        self.tab_dns = net_tabs["DNS/DHCP"]
        self.tab_firewall = net_tabs["Firewall"]

        rem_tabs = self.categories["Remote"]["tabs"]
        self.tab_rdp = rem_tabs["Remote Desktop"]
        self.tab_remcmd = rem_tabs["Remote Cmd"]
        self.tab_rdpconnect = rem_tabs["RDP Connect"]

        usr_tabs = self.categories["Users"]["tabs"]
        self.tab_ad = usr_tabs["Active Directory"]
        self.tab_localusers = usr_tabs["Local Users"]

        sw_tabs = self.categories["Software"]["tabs"]
        self.tab_software = sw_tabs["Installed Software"]
        self.tab_winget = sw_tabs["Winget Install"]
        self.tab_updates = sw_tabs["Windows Update"]
        self.tab_envvars = sw_tabs["Env Vars"]

        sec_tabs = self.categories["Security"]["tabs"]
        self.tab_certs = sec_tabs["Certificates"]
        self.tab_eventlog = sec_tabs["Event Viewer"]

        res_tabs = self.categories["Resources"]["tabs"]
        self.tab_printers = res_tabs["Printers"]
        self.tab_shares = res_tabs["Shares"]
        self.tab_tools = res_tabs["Tools"]

        # Setup all tabs
        self.setup_system_tab()
        self.setup_rdp_tab()
        self.setup_services_tab()
        self.setup_processes_tab()
        self.setup_network_tab()
        self.setup_disks_tab()
        self.setup_ad_tab()
        self.setup_eventlog_tab()
        self.setup_updates_tab()
        self.setup_firewall_tab()
        self.setup_software_tab()
        self.setup_winget_tab()
        self.setup_tasks_tab()
        self.setup_printers_tab()
        self.setup_shares_tab()
        self.setup_dns_tab()
        self.setup_localusers_tab()
        self.setup_envvars_tab()
        self.setup_certs_tab()
        self.setup_remcmd_tab()
        self.setup_rdpconnect_tab()
        self.setup_tools_tab()

        # Show first category by default
        self.show_category("System")

    def show_category(self, category_name: str):
        """Show a category's tab frame, hide all others"""
        for cat_name, cat_data in self.categories.items():
            if cat_name == category_name:
                cat_data['frame'].pack(fill='both', expand=True)
                self.category_buttons[cat_name].configure(fg_color=("gray75", "gray25"))
            else:
                cat_data['frame'].pack_forget()
                self.category_buttons[cat_name].configure(fg_color=("gray70", "gray30") if ctk.get_appearance_mode() == "Light" else ("transparent"))
        
    def setup_system_tab(self):
        """Setup System Information tab"""
        frame = ctk.CTkFrame(self.tab_system)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Buttons frame
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(fill='x', pady=(0, 10))
        
        ctk.CTkButton(btn_frame, text="Get System Info", command=self.get_system_info).pack(side='left', padx=5)
        ctk.CTkButton(btn_frame, text="Get Uptime", command=self.get_uptime).pack(side='left', padx=5)
        ctk.CTkButton(btn_frame, text="Run GPUpdate", command=self.run_gpupdate).pack(side='left', padx=5)
        ctk.CTkButton(btn_frame, text="Clear", command=lambda: self.system_output.delete('1.0', 'end')).pack(side='right', padx=5)
        
        # Output text area
        self.system_output = ctk.CTkTextbox(frame, height=400, font=("Consolas", 10))
        self.system_output.pack(fill='both', expand=True)
        
    def setup_rdp_tab(self):
        """Setup Remote Desktop tab"""
        frame = ctk.CTkFrame(self.tab_rdp)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Control buttons
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(fill='x', pady=(0, 10))
        
        ctk.CTkButton(
            btn_frame,
            text="Enable RDP",
            command=lambda: self.set_rdp(True),
            fg_color="green"
        ).pack(side='left', padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Disable RDP",
            command=lambda: self.set_rdp(False),
            fg_color="red"
        ).pack(side='left', padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Check Status",
            command=self.get_rdp_status
        ).pack(side='left', padx=5)
        
        # Output area
        self.rdp_output = ctk.CTkTextbox(frame, height=400, font=("Consolas", 10))
        self.rdp_output.pack(fill='both', expand=True)
        
        # Add info label
        info_text = """Remote Desktop (RDP) Management for Windows 11 & Server 2022+

This tool uses modern PowerShell cmdlets to:
• Configure Terminal Services registry settings
• Manage Windows Firewall rules for RDP
• Enable/Disable Network Level Authentication (NLA)
• Check current RDP configuration

Note: Requires administrator privileges."""
        
        self.rdp_output.insert('1.0', info_text)
        self.rdp_output.configure(state='disabled')
        
    def setup_services_tab(self):
        """Setup Services tab - Enhanced with Start/Stop/Restart and startup type"""
        frame = ctk.CTkFrame(self.tab_services)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        control_frame = ctk.CTkFrame(frame)
        control_frame.pack(fill='x', pady=(0, 5))

        ctk.CTkButton(control_frame, text="Get All Services", command=self.get_services).pack(side='left', padx=5)
        ctk.CTkButton(control_frame, text="Get Running Only", command=lambda: self.get_services(True)).pack(side='left', padx=5)

        search_frame = ctk.CTkFrame(control_frame)
        search_frame.pack(side='left', padx=20)
        ctk.CTkLabel(search_frame, text="Search:").pack(side='left')
        self.service_search = ctk.CTkEntry(search_frame, width=200)
        self.service_search.pack(side='left', padx=5)

        # Service control row
        svc_control = ctk.CTkFrame(frame)
        svc_control.pack(fill='x', pady=(0, 5))

        ctk.CTkLabel(svc_control, text="Service Name:").pack(side='left', padx=5)
        self.service_name_entry = ctk.CTkEntry(svc_control, width=200, placeholder_text="e.g. Spooler")
        self.service_name_entry.pack(side='left', padx=5)

        ctk.CTkButton(svc_control, text="Start", command=lambda: self.control_service_action('start'), fg_color="green", width=70).pack(side='left', padx=2)
        ctk.CTkButton(svc_control, text="Stop", command=lambda: self.control_service_action('stop'), fg_color="red", width=70).pack(side='left', padx=2)
        ctk.CTkButton(svc_control, text="Restart", command=lambda: self.control_service_action('restart'), fg_color="orange", width=70).pack(side='left', padx=2)

        self.service_startup_type = ctk.CTkOptionMenu(svc_control, values=SERVICE_STARTUP_TYPES, width=150)
        self.service_startup_type.pack(side='left', padx=5)
        ctk.CTkButton(svc_control, text="Set Startup", command=self.set_service_startup, width=90).pack(side='left', padx=2)

        self.services_output = ctk.CTkTextbox(frame, height=400, font=("Consolas", 9))
        self.services_output.pack(fill='both', expand=True)
        
    def setup_processes_tab(self):
        """Setup Processes tab - Enhanced with kill and sort"""
        frame = ctk.CTkFrame(self.tab_processes)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        control_frame = ctk.CTkFrame(frame)
        control_frame.pack(fill='x', pady=(0, 10))

        ctk.CTkButton(control_frame, text="Get Top Processes", command=self.get_processes).pack(side='left', padx=5)

        ctk.CTkLabel(control_frame, text="Top N:").pack(side='left', padx=5)
        self.process_count = ctk.CTkEntry(control_frame, width=60)
        self.process_count.insert(0, "20")
        self.process_count.pack(side='left')

        ctk.CTkLabel(control_frame, text="Sort:").pack(side='left', padx=5)
        self.process_sort = ctk.CTkOptionMenu(control_frame, values=["CPU", "Memory"], width=100)
        self.process_sort.set("CPU")
        self.process_sort.pack(side='left', padx=2)

        ctk.CTkButton(control_frame, text="Refresh", command=self.get_processes, fg_color="gray").pack(side='left', padx=5)

        ctk.CTkLabel(control_frame, text="PID:").pack(side='left', padx=5)
        self.kill_pid_entry = ctk.CTkEntry(control_frame, width=80)
        self.kill_pid_entry.pack(side='left')
        ctk.CTkButton(control_frame, text="Kill Process", command=self.kill_process_action, fg_color="red", width=100).pack(side='left', padx=5)

        self.processes_output = ctk.CTkTextbox(frame, height=400, font=("Consolas", 9))
        self.processes_output.pack(fill='both', expand=True)
        
    def setup_network_tab(self):
        """Setup Network tab - Enhanced with ping/traceroute/nslookup/ipconfig"""
        frame = ctk.CTkFrame(self.tab_network)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        control_frame = ctk.CTkFrame(frame)
        control_frame.pack(fill='x', pady=(0, 5))

        ctk.CTkButton(control_frame, text="Get Adapters", command=self.get_network_adapters).pack(side='left', padx=5)
        ctk.CTkButton(control_frame, text="Test Port", command=self.test_port).pack(side='left', padx=5)
        ctk.CTkLabel(control_frame, text="Port:").pack(side='left', padx=5)
        self.port_entry = ctk.CTkEntry(control_frame, width=80)
        self.port_entry.insert(0, "3389")
        self.port_entry.pack(side='left')
        ctk.CTkButton(control_frame, text="IP Config", command=self.get_ip_config_action).pack(side='left', padx=5)
        ctk.CTkButton(control_frame, text="DNS Servers", command=self.get_dns_servers_action).pack(side='left', padx=5)

        net_control2 = ctk.CTkFrame(frame)
        net_control2.pack(fill='x', pady=(0, 5))

        ctk.CTkLabel(net_control2, text="Host:").pack(side='left', padx=5)
        self.net_host_entry = ctk.CTkEntry(net_control2, width=200, placeholder_text="hostname or IP")
        self.net_host_entry.pack(side='left', padx=5)
        ctk.CTkButton(net_control2, text="Ping", command=self.ping_host_action).pack(side='left', padx=3)
        ctk.CTkButton(net_control2, text="Traceroute", command=self.traceroute_action).pack(side='left', padx=3)
        ctk.CTkButton(net_control2, text="NSLookup", command=self.nslookup_action).pack(side='left', padx=3)

        self.network_output = ctk.CTkTextbox(frame, height=400, font=("Consolas", 10))
        self.network_output.pack(fill='both', expand=True)
        
    def setup_disks_tab(self):
        """Setup Disks tab"""
        frame = ctk.CTkFrame(self.tab_disks)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Control frame
        control_frame = ctk.CTkFrame(frame)
        control_frame.pack(fill='x', pady=(0, 10))
        
        ctk.CTkButton(control_frame, text="Get Disk Info", command=self.get_disk_info).pack(side='left', padx=5)
        ctk.CTkButton(control_frame, text="Refresh", command=self.get_disk_info, fg_color="gray").pack(side='left', padx=5)
        
        # Output
        self.disks_output = ctk.CTkTextbox(frame, height=400, font=("Consolas", 10))
        self.disks_output.pack(fill='both', expand=True)
        
    def setup_tools_tab(self):
        """Setup Tools tab"""
        frame = ctk.CTkFrame(self.tab_tools)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Password Generator
        pw_frame = ctk.CTkFrame(frame)
        pw_frame.pack(fill='x', padx=10, pady=10)
        
        ctk.CTkLabel(pw_frame, text="Password Generator", font=("Arial", 14, "bold")).pack(anchor='w', pady=5)
        
        pw_controls = ctk.CTkFrame(pw_frame)
        pw_controls.pack(fill='x', pady=5)
        
        ctk.CTkLabel(pw_controls, text="Length:").pack(side='left', padx=5)
        self.pw_length = ctk.CTkEntry(pw_controls, width=60)
        self.pw_length.insert(0, "16")
        self.pw_length.pack(side='left')
        
        self.pw_special = ctk.CTkCheckBox(pw_controls, text="Include Special Characters")
        self.pw_special.select()
        self.pw_special.pack(side='left', padx=10)
        
        ctk.CTkButton(pw_controls, text="Generate", command=self.generate_password).pack(side='left', padx=5)
        ctk.CTkButton(pw_controls, text="Copy", command=self.copy_password, width=60).pack(side='left', padx=5)

        self.pw_output = ctk.CTkEntry(pw_frame, width=500)
        self.pw_output.pack(fill='x', pady=5)
        
        # System Control
        sys_frame = ctk.CTkFrame(frame)
        sys_frame.pack(fill='x', padx=10, pady=10)
        
        ctk.CTkLabel(sys_frame, text="System Control", font=("Arial", 14, "bold")).pack(anchor='w', pady=5)
        
        sys_controls = ctk.CTkFrame(sys_frame)
        sys_controls.pack(fill='x', pady=5)
        
        ctk.CTkButton(
            sys_controls,
            text="Restart Computer",
            command=self.restart_computer,
            fg_color="orange",
            width=150
        ).pack(side='left', padx=5)
        
        ctk.CTkButton(
            sys_controls,
            text="Shutdown Computer",
            command=self.shutdown_computer,
            fg_color="red",
            width=150
        ).pack(side='left', padx=5)
        
        # Sessions
        session_frame = ctk.CTkFrame(frame)
        session_frame.pack(fill='x', padx=10, pady=10)
        
        ctk.CTkLabel(session_frame, text="User Sessions", font=("Arial", 14, "bold")).pack(anchor='w', pady=5)
        
        ctk.CTkButton(session_frame, text="Query User Sessions (qwinsta)", command=self.get_sessions).pack(anchor='w', pady=5)
        
        self.session_output = ctk.CTkTextbox(session_frame, height=200, font=("Consolas", 10))
        self.session_output.pack(fill='both', expand=True)
        
    def setup_bottom_frame(self, parent):
        """Setup bottom frame for logs"""
        log_frame = ctk.CTkFrame(parent)
        log_frame.pack(fill='both', pady=(0, 0))
        
        # Log header
        log_header = ctk.CTkFrame(log_frame)
        log_header.pack(fill='x')
        
        ctk.CTkLabel(log_header, text="Activity Log", font=("Arial", 12, "bold")).pack(side='left', padx=5)
        ctk.CTkButton(log_header, text="Clear Log", command=self.clear_log, width=80).pack(side='right', padx=5)
        ctk.CTkButton(log_header, text="Export Log", command=self.export_log, width=80).pack(side='right', padx=5)
        
        # Log text area
        self.log_output = ctk.CTkTextbox(log_frame, height=150, font=("Consolas", 9))
        self.log_output.pack(fill='both', expand=True, padx=5, pady=5)
        
    # ===================== NEW TAB SETUP METHODS =====================

    def setup_ad_tab(self):
        """Setup Active Directory tab"""
        frame = ctk.CTkFrame(self.tab_ad)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        ad_subtabs = ctk.CTkTabview(frame, height=50)
        ad_subtabs.pack(fill='both', expand=True)

        # Users sub-tab
        users_tab = ad_subtabs.add("Users")
        uf = ctk.CTkFrame(users_tab)
        uf.pack(fill='both', expand=True)
        uc = ctk.CTkFrame(uf)
        uc.pack(fill='x', pady=(0, 5))
        ctk.CTkLabel(uc, text="Search:").pack(side='left', padx=5)
        self.ad_user_search = ctk.CTkEntry(uc, width=250, placeholder_text="Username or display name")
        self.ad_user_search.pack(side='left', padx=5)
        ctk.CTkButton(uc, text="Search Users", command=self.search_ad_users_action).pack(side='left', padx=5)
        ctk.CTkButton(uc, text="Unlock Account", command=self.unlock_ad_account_action, fg_color="orange").pack(side='left', padx=5)
        ctk.CTkButton(uc, text="Reset Password", command=self.reset_ad_password_action, fg_color="red").pack(side='left', padx=5)
        self.ad_user_output = ctk.CTkTextbox(uf, font=("Consolas", 9))
        self.ad_user_output.pack(fill='both', expand=True)

        # Groups sub-tab
        groups_tab = ad_subtabs.add("Groups")
        gf = ctk.CTkFrame(groups_tab)
        gf.pack(fill='both', expand=True)
        gc = ctk.CTkFrame(gf)
        gc.pack(fill='x', pady=(0, 5))
        ctk.CTkLabel(gc, text="Search:").pack(side='left', padx=5)
        self.ad_group_search = ctk.CTkEntry(gc, width=250, placeholder_text="Group name")
        self.ad_group_search.pack(side='left', padx=5)
        ctk.CTkButton(gc, text="Search Groups", command=self.search_ad_groups_action).pack(side='left', padx=5)
        ctk.CTkButton(gc, text="Get Members", command=self.get_ad_group_members_action).pack(side='left', padx=5)
        self.ad_group_output = ctk.CTkTextbox(gf, font=("Consolas", 9))
        self.ad_group_output.pack(fill='both', expand=True)

        # Computers sub-tab
        comp_tab = ad_subtabs.add("Computers")
        cf = ctk.CTkFrame(comp_tab)
        cf.pack(fill='both', expand=True)
        cc = ctk.CTkFrame(cf)
        cc.pack(fill='x', pady=(0, 5))
        ctk.CTkLabel(cc, text="Search:").pack(side='left', padx=5)
        self.ad_computer_search = ctk.CTkEntry(cc, width=250, placeholder_text="Computer name")
        self.ad_computer_search.pack(side='left', padx=5)
        ctk.CTkButton(cc, text="Search Computers", command=self.search_ad_computers_action).pack(side='left', padx=5)
        ctk.CTkButton(cc, text="Get OUs", command=self.get_ad_ous_action).pack(side='left', padx=5)
        self.ad_computer_output = ctk.CTkTextbox(cf, font=("Consolas", 9))
        self.ad_computer_output.pack(fill='both', expand=True)

    def setup_eventlog_tab(self):
        """Setup Event Viewer tab"""
        frame = ctk.CTkFrame(self.tab_eventlog)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        c1 = ctk.CTkFrame(frame)
        c1.pack(fill='x', pady=(0, 5))
        ctk.CTkLabel(c1, text="Log:").pack(side='left', padx=5)
        self.eventlog_logname = ctk.CTkOptionMenu(c1, values=EVENT_LOG_NAMES, width=120)
        self.eventlog_logname.pack(side='left', padx=5)
        ctk.CTkLabel(c1, text="Level:").pack(side='left', padx=5)
        self.eventlog_level = ctk.CTkOptionMenu(c1, values=["All", "Critical", "Error", "Warning", "Information"], width=120)
        self.eventlog_level.set("Error")
        self.eventlog_level.pack(side='left', padx=5)
        ctk.CTkLabel(c1, text="Max:").pack(side='left', padx=5)
        self.eventlog_max = ctk.CTkEntry(c1, width=60)
        self.eventlog_max.insert(0, "100")
        self.eventlog_max.pack(side='left')

        c2 = ctk.CTkFrame(frame)
        c2.pack(fill='x', pady=(0, 5))
        ctk.CTkLabel(c2, text="Source:").pack(side='left', padx=5)
        self.eventlog_source = ctk.CTkEntry(c2, width=150, placeholder_text="e.g. NTFS")
        self.eventlog_source.pack(side='left', padx=5)
        ctk.CTkLabel(c2, text="Search:").pack(side='left', padx=5)
        self.eventlog_search = ctk.CTkEntry(c2, width=200, placeholder_text="Text to search in messages")
        self.eventlog_search.pack(side='left', padx=5)
        ctk.CTkButton(c2, text="Get Events", command=self.get_event_logs_action).pack(side='left', padx=5)

        self.eventlog_output = ctk.CTkTextbox(frame, font=("Consolas", 9))
        self.eventlog_output.pack(fill='both', expand=True)

    def setup_updates_tab(self):
        """Setup Windows Update tab"""
        frame = ctk.CTkFrame(self.tab_updates)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        ctrl = ctk.CTkFrame(frame)
        ctrl.pack(fill='x', pady=(0, 10))
        ctk.CTkButton(ctrl, text="Get Installed Updates", command=self.get_installed_updates_action).pack(side='left', padx=5)
        ctk.CTkButton(ctrl, text="Check for Updates", command=self.check_for_updates_action).pack(side='left', padx=5)
        ctk.CTkButton(ctrl, text="View Update History", command=self.get_update_history_action).pack(side='left', padx=5)

        self.updates_output = ctk.CTkTextbox(frame, font=("Consolas", 9))
        self.updates_output.pack(fill='both', expand=True)

    def setup_firewall_tab(self):
        """Setup Firewall tab"""
        frame = ctk.CTkFrame(self.tab_firewall)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        ctrl = ctk.CTkFrame(frame)
        ctrl.pack(fill='x', pady=(0, 5))
        ctk.CTkButton(ctrl, text="Get Rules", command=self.get_firewall_rules_action).pack(side='left', padx=5)
        ctk.CTkLabel(ctrl, text="Direction:").pack(side='left', padx=5)
        self.fw_direction = ctk.CTkOptionMenu(ctrl, values=["All", "Inbound", "Outbound"], width=110)
        self.fw_direction.pack(side='left', padx=2)
        self.fw_enabled_only = ctk.CTkCheckBox(ctrl, text="Enabled Only")
        self.fw_enabled_only.select()
        self.fw_enabled_only.pack(side='left', padx=5)

        ctrl2 = ctk.CTkFrame(frame)
        ctrl2.pack(fill='x', pady=(0, 5))
        ctk.CTkLabel(ctrl2, text="Rule Name:").pack(side='left', padx=5)
        self.fw_rule_name = ctk.CTkEntry(ctrl2, width=300, placeholder_text="Exact display name of rule")
        self.fw_rule_name.pack(side='left', padx=5)
        ctk.CTkButton(ctrl2, text="Enable Rule", command=self.enable_firewall_rule_action, fg_color="green", width=100).pack(side='left', padx=2)
        ctk.CTkButton(ctrl2, text="Disable Rule", command=self.disable_firewall_rule_action, fg_color="red", width=100).pack(side='left', padx=2)
        ctk.CTkButton(ctrl2, text="Create Rule...", command=self.create_firewall_rule_dialog, width=100).pack(side='left', padx=5)

        self.firewall_output = ctk.CTkTextbox(frame, font=("Consolas", 9))
        self.firewall_output.pack(fill='both', expand=True)

    def setup_software_tab(self):
        """Setup Installed Software tab"""
        frame = ctk.CTkFrame(self.tab_software)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        ctrl = ctk.CTkFrame(frame)
        ctrl.pack(fill='x', pady=(0, 10))
        ctk.CTkButton(ctrl, text="Get Installed Software", command=self.get_installed_software_action).pack(side='left', padx=5)
        ctk.CTkButton(ctrl, text="Refresh", command=self.get_installed_software_action, fg_color="gray").pack(side='left', padx=5)

        self.software_output = ctk.CTkTextbox(frame, font=("Consolas", 9))
        self.software_output.pack(fill='both', expand=True)

    def setup_winget_tab(self):
        """Setup Winget Software Installation tab"""
        main_frame = ctk.CTkFrame(self.tab_winget)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Top control frame
        top_frame = ctk.CTkFrame(main_frame)
        top_frame.pack(fill='x', pady=(0, 10))
        
        ctk.CTkLabel(top_frame, text="Category:", font=("Arial", 12, "bold")).pack(side='left', padx=5)
        
        # Category selector
        self.winget_category_var = ctk.StringVar(value="Browsers")
        categories = list(WINGET_SOFTWARE_CATALOG.keys())
        self.winget_category_menu = ctk.CTkOptionMenu(
            top_frame, 
            values=categories,
            variable=self.winget_category_var,
            command=self.update_winget_software_list,
            width=200
        )
        self.winget_category_menu.pack(side='left', padx=5)
        
        # Search box
        ctk.CTkLabel(top_frame, text="Search:", font=("Arial", 12)).pack(side='left', padx=(20, 5))
        self.winget_search_entry = ctk.CTkEntry(top_frame, width=250, placeholder_text="Search software...")
        self.winget_search_entry.pack(side='left', padx=5)
        self.winget_search_entry.bind('<KeyRelease>', lambda e: self.update_winget_software_list())
        
        ctk.CTkButton(top_frame, text="Refresh List", command=self.update_winget_software_list, 
                     fg_color="gray", width=100).pack(side='left', padx=5)
        
        # Content area with scrollable frame
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill='both', expand=True)
        
        # Scrollable frame for software items
        self.winget_scroll = ctk.CTkScrollableFrame(content_frame, label_text="Available Software")
        self.winget_scroll.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Output/Status area
        output_frame = ctk.CTkFrame(main_frame)
        output_frame.pack(fill='x', pady=(10, 0))
        
        ctk.CTkLabel(output_frame, text="Installation Output:", font=("Arial", 11, "bold")).pack(anchor='w', padx=5, pady=(5, 0))
        self.winget_output = ctk.CTkTextbox(output_frame, height=120, font=("Consolas", 9))
        self.winget_output.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Bulk actions frame
        bulk_frame = ctk.CTkFrame(main_frame)
        bulk_frame.pack(fill='x', pady=(5, 0))
        
        ctk.CTkButton(bulk_frame, text="Upgrade All Installed", command=self.winget_upgrade_all,
                     fg_color="orange", width=150).pack(side='left', padx=5, pady=5)
        ctk.CTkButton(bulk_frame, text="List Installed", command=self.winget_list_installed,
                     width=120).pack(side='left', padx=5, pady=5)
        ctk.CTkButton(bulk_frame, text="Clear Output", 
                     command=lambda: self.winget_output.delete('1.0', 'end'),
                     fg_color="gray", width=100).pack(side='right', padx=5, pady=5)
        
        # Initialize with first category
        self.update_winget_software_list()

    def update_winget_software_list(self, *args):
        """Update the software list based on selected category and search"""
        # Clear existing items
        for widget in self.winget_scroll.winfo_children():
            widget.destroy()
        
        category = self.winget_category_var.get()
        search_term = self.winget_search_entry.get().lower()
        
        if category not in WINGET_SOFTWARE_CATALOG:
            return
        
        software_dict = WINGET_SOFTWARE_CATALOG[category]
        
        # Filter by search term
        filtered_software = {
            name: info for name, info in software_dict.items()
            if search_term in name.lower() or search_term in info['description'].lower()
        } if search_term else software_dict
        
        if not filtered_software:
            ctk.CTkLabel(self.winget_scroll, text="No software found", 
                        font=("Arial", 12)).pack(pady=20)
            return
        
        # Create software item cards
        for software_name, info in filtered_software.items():
            self.create_winget_item_card(software_name, info)
    
    def create_winget_item_card(self, name: str, info: dict):
        """Create a card for each software item"""
        card = ctk.CTkFrame(self.winget_scroll, corner_radius=8)
        card.pack(fill='x', padx=5, pady=5)
        
        # Left side - Info
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        
        name_label = ctk.CTkLabel(info_frame, text=name, font=("Arial", 13, "bold"), 
                                  anchor='w')
        name_label.pack(anchor='w')
        
        desc_label = ctk.CTkLabel(info_frame, text=info['description'], 
                                 font=("Arial", 10), anchor='w', text_color="gray")
        desc_label.pack(anchor='w', pady=(2, 0))
        
        id_label = ctk.CTkLabel(info_frame, text=f"ID: {info['id']}", 
                               font=("Consolas", 9), anchor='w', text_color="gray60")
        id_label.pack(anchor='w', pady=(2, 0))
        
        # Right side - Actions
        action_frame = ctk.CTkFrame(card, fg_color="transparent")
        action_frame.pack(side='right', padx=10, pady=10)
        
        install_btn = ctk.CTkButton(
            action_frame, 
            text="Install",
            command=lambda n=name, i=info: self.winget_install_software(n, i),
            fg_color="green",
            width=100,
            height=32
        )
        install_btn.pack(side='left', padx=2)
        
        info_btn = ctk.CTkButton(
            action_frame,
            text="Info",
            command=lambda i=info: self.winget_show_info(i),
            fg_color="gray",
            width=70,
            height=32
        )
        info_btn.pack(side='left', padx=2)

    def winget_install_software(self, name: str, info: dict):
        """Install software using winget"""
        if not self.admin_tools:
            messagebox.showerror("Error", "Not connected to a computer")
            return
        
        self.winget_output.insert('end', f"\n{'='*60}\n")
        self.winget_output.insert('end', f"Installing {name}...\n")
        self.winget_output.insert('end', f"Package ID: {info['id']}\n")
        self.winget_output.insert('end', f"{'='*60}\n")
        self.winget_output.see('end')
        
        def install_thread():
            try:
                command = WINGET_COMMANDS['install'].format(package_id=info['id'])
                result = self.admin_tools.run_powershell_command(command)
                
                self.root.after(0, lambda: self.winget_output.insert('end', f"\n{result}\n"))
                self.root.after(0, lambda: self.winget_output.insert('end', 
                    f"\n✓ Installation command completed for {name}\n"))
                self.root.after(0, lambda: self.winget_output.see('end'))
                
            except Exception as e:
                self.root.after(0, lambda: self.winget_output.insert('end', 
                    f"\n✗ Error installing {name}: {str(e)}\n"))
                self.root.after(0, lambda: self.winget_output.see('end'))
        
        threading.Thread(target=install_thread, daemon=True).start()

    def winget_show_info(self, info: dict):
        """Show detailed information about a package"""
        if not self.admin_tools:
            messagebox.showerror("Error", "Not connected to a computer")
            return
        
        self.winget_output.insert('end', f"\n{'='*60}\n")
        self.winget_output.insert('end', f"Package Information\n")
        self.winget_output.insert('end', f"{'='*60}\n")
        self.winget_output.see('end')
        
        def info_thread():
            try:
                command = WINGET_COMMANDS['show'].format(package_id=info['id'])
                result = self.admin_tools.run_powershell_command(command)
                
                self.root.after(0, lambda: self.winget_output.insert('end', f"\n{result}\n"))
                self.root.after(0, lambda: self.winget_output.see('end'))
                
            except Exception as e:
                self.root.after(0, lambda: self.winget_output.insert('end', 
                    f"\n✗ Error getting info: {str(e)}\n"))
                self.root.after(0, lambda: self.winget_output.see('end'))
        
        threading.Thread(target=info_thread, daemon=True).start()

    def winget_upgrade_all(self):
        """Upgrade all installed packages"""
        if not self.admin_tools:
            messagebox.showerror("Error", "Not connected to a computer")
            return
        
        if not messagebox.askyesno("Confirm", "Upgrade all installed packages? This may take a while."):
            return
        
        self.winget_output.insert('end', f"\n{'='*60}\n")
        self.winget_output.insert('end', f"Upgrading all packages...\n")
        self.winget_output.insert('end', f"{'='*60}\n")
        self.winget_output.see('end')
        
        def upgrade_thread():
            try:
                command = WINGET_COMMANDS['upgrade_all']
                result = self.admin_tools.run_powershell_command(command)
                
                self.root.after(0, lambda: self.winget_output.insert('end', f"\n{result}\n"))
                self.root.after(0, lambda: self.winget_output.insert('end', 
                    f"\n✓ Upgrade all completed\n"))
                self.root.after(0, lambda: self.winget_output.see('end'))
                
            except Exception as e:
                self.root.after(0, lambda: self.winget_output.insert('end', 
                    f"\n✗ Error upgrading: {str(e)}\n"))
                self.root.after(0, lambda: self.winget_output.see('end'))
        
        threading.Thread(target=upgrade_thread, daemon=True).start()

    def winget_list_installed(self):
        """List all installed packages"""
        if not self.admin_tools:
            messagebox.showerror("Error", "Not connected to a computer")
            return
        
        self.winget_output.insert('end', f"\n{'='*60}\n")
        self.winget_output.insert('end', f"Listing installed packages...\n")
        self.winget_output.insert('end', f"{'='*60}\n")
        self.winget_output.see('end')
        
        def list_thread():
            try:
                command = WINGET_COMMANDS['list']
                result = self.admin_tools.run_powershell_command(command)
                
                self.root.after(0, lambda: self.winget_output.insert('end', f"\n{result}\n"))
                self.root.after(0, lambda: self.winget_output.see('end'))
                
            except Exception as e:
                self.root.after(0, lambda: self.winget_output.insert('end', 
                    f"\n✗ Error listing packages: {str(e)}\n"))
                self.root.after(0, lambda: self.winget_output.see('end'))
        
        threading.Thread(target=list_thread, daemon=True).start()

    def setup_tasks_tab(self):
        """Setup Scheduled Tasks tab"""
        frame = ctk.CTkFrame(self.tab_tasks)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        ctrl = ctk.CTkFrame(frame)
        ctrl.pack(fill='x', pady=(0, 5))
        ctk.CTkButton(ctrl, text="Get Tasks", command=self.get_scheduled_tasks_action).pack(side='left', padx=5)
        self.task_show_all = ctk.CTkCheckBox(ctrl, text="Include Microsoft Tasks")
        self.task_show_all.pack(side='left', padx=5)

        ctrl2 = ctk.CTkFrame(frame)
        ctrl2.pack(fill='x', pady=(0, 5))
        ctk.CTkLabel(ctrl2, text="Task Name:").pack(side='left', padx=5)
        self.task_name_entry = ctk.CTkEntry(ctrl2, width=250, placeholder_text="Task name")
        self.task_name_entry.pack(side='left', padx=5)
        ctk.CTkLabel(ctrl2, text="Path:").pack(side='left', padx=5)
        self.task_path_entry = ctk.CTkEntry(ctrl2, width=200, placeholder_text="e.g. \\")
        self.task_path_entry.insert(0, "\\")
        self.task_path_entry.pack(side='left', padx=5)
        ctk.CTkButton(ctrl2, text="Enable", command=lambda: self.set_task_state_action(True), fg_color="green", width=70).pack(side='left', padx=2)
        ctk.CTkButton(ctrl2, text="Disable", command=lambda: self.set_task_state_action(False), fg_color="red", width=70).pack(side='left', padx=2)
        ctk.CTkButton(ctrl2, text="Run Now", command=self.run_task_action, fg_color="orange", width=80).pack(side='left', padx=2)
        ctk.CTkButton(ctrl2, text="History", command=self.get_task_history_action, width=70).pack(side='left', padx=2)

        self.tasks_output = ctk.CTkTextbox(frame, font=("Consolas", 9))
        self.tasks_output.pack(fill='both', expand=True)

    def setup_printers_tab(self):
        """Setup Printers tab"""
        frame = ctk.CTkFrame(self.tab_printers)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        ctrl = ctk.CTkFrame(frame)
        ctrl.pack(fill='x', pady=(0, 5))
        ctk.CTkButton(ctrl, text="Get Printers", command=self.get_printers_action).pack(side='left', padx=5)
        ctk.CTkLabel(ctrl, text="Printer:").pack(side='left', padx=5)
        self.printer_name_entry = ctk.CTkEntry(ctrl, width=250, placeholder_text="Printer name")
        self.printer_name_entry.pack(side='left', padx=5)
        ctk.CTkButton(ctrl, text="Get Queue", command=self.get_print_queue_action).pack(side='left', padx=5)
        ctk.CTkButton(ctrl, text="Clear Queue", command=self.clear_print_queue_action, fg_color="red").pack(side='left', padx=5)

        ctrl2 = ctk.CTkFrame(frame)
        ctrl2.pack(fill='x', pady=(0, 5))
        ctk.CTkLabel(ctrl2, text="Job ID:").pack(side='left', padx=5)
        self.print_job_id_entry = ctk.CTkEntry(ctrl2, width=80)
        self.print_job_id_entry.pack(side='left', padx=5)
        ctk.CTkButton(ctrl2, text="Remove Job", command=self.remove_print_job_action, fg_color="orange").pack(side='left', padx=5)

        self.printers_output = ctk.CTkTextbox(frame, font=("Consolas", 9))
        self.printers_output.pack(fill='both', expand=True)

    def setup_shares_tab(self):
        """Setup Shares tab"""
        frame = ctk.CTkFrame(self.tab_shares)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        ctrl = ctk.CTkFrame(frame)
        ctrl.pack(fill='x', pady=(0, 5))
        ctk.CTkButton(ctrl, text="Get Shares", command=self.get_smb_shares_action).pack(side='left', padx=5)
        ctk.CTkLabel(ctrl, text="Share Name:").pack(side='left', padx=5)
        self.share_name_entry = ctk.CTkEntry(ctrl, width=200, placeholder_text="Share name")
        self.share_name_entry.pack(side='left', padx=5)
        ctk.CTkButton(ctrl, text="Get Permissions", command=self.get_share_permissions_action).pack(side='left', padx=5)
        ctk.CTkButton(ctrl, text="Create Share...", command=self.create_share_dialog).pack(side='left', padx=5)
        ctk.CTkButton(ctrl, text="Remove Share", command=self.remove_share_action, fg_color="red").pack(side='left', padx=5)

        self.shares_output = ctk.CTkTextbox(frame, font=("Consolas", 9))
        self.shares_output.pack(fill='both', expand=True)

    def setup_dns_tab(self):
        """Setup DNS/DHCP tab"""
        frame = ctk.CTkFrame(self.tab_dns)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        ctrl = ctk.CTkFrame(frame)
        ctrl.pack(fill='x', pady=(0, 10))
        ctk.CTkLabel(ctrl, text="Hostname:").pack(side='left', padx=5)
        self.dns_hostname_entry = ctk.CTkEntry(ctrl, width=250, placeholder_text="hostname or IP")
        self.dns_hostname_entry.pack(side='left', padx=5)
        ctk.CTkButton(ctrl, text="DNS Lookup", command=self.dns_lookup_action).pack(side='left', padx=5)
        ctk.CTkButton(ctrl, text="Flush DNS", command=self.flush_dns_action).pack(side='left', padx=5)
        ctk.CTkButton(ctrl, text="DNS Cache", command=self.get_dns_cache_action).pack(side='left', padx=5)
        ctk.CTkButton(ctrl, text="DHCP Info", command=self.get_dhcp_info_action).pack(side='left', padx=5)
        ctk.CTkButton(ctrl, text="DNS Servers", command=self.get_dns_servers_tab_action).pack(side='left', padx=5)

        self.dns_output = ctk.CTkTextbox(frame, font=("Consolas", 9))
        self.dns_output.pack(fill='both', expand=True)

    def setup_localusers_tab(self):
        """Setup Local Users & Groups tab"""
        frame = ctk.CTkFrame(self.tab_localusers)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        lu_subtabs = ctk.CTkTabview(frame, height=50)
        lu_subtabs.pack(fill='both', expand=True)

        # Users sub-tab
        users_tab = lu_subtabs.add("Users")
        uf = ctk.CTkFrame(users_tab)
        uf.pack(fill='both', expand=True)
        uc = ctk.CTkFrame(uf)
        uc.pack(fill='x', pady=(0, 5))
        ctk.CTkButton(uc, text="Get Local Users", command=self.get_local_users_action).pack(side='left', padx=5)
        ctk.CTkLabel(uc, text="Username:").pack(side='left', padx=5)
        self.local_username_entry = ctk.CTkEntry(uc, width=200)
        self.local_username_entry.pack(side='left', padx=5)
        ctk.CTkButton(uc, text="Enable", command=lambda: self.set_local_user_state_action(True), fg_color="green", width=70).pack(side='left', padx=2)
        ctk.CTkButton(uc, text="Disable", command=lambda: self.set_local_user_state_action(False), fg_color="red", width=70).pack(side='left', padx=2)
        self.localusers_output = ctk.CTkTextbox(uf, font=("Consolas", 9))
        self.localusers_output.pack(fill='both', expand=True)

        # Groups sub-tab
        groups_tab = lu_subtabs.add("Groups")
        gf = ctk.CTkFrame(groups_tab)
        gf.pack(fill='both', expand=True)
        gc = ctk.CTkFrame(gf)
        gc.pack(fill='x', pady=(0, 5))
        ctk.CTkButton(gc, text="Get Local Groups", command=self.get_local_groups_action).pack(side='left', padx=5)
        ctk.CTkLabel(gc, text="Group:").pack(side='left', padx=5)
        self.local_group_entry = ctk.CTkEntry(gc, width=200)
        self.local_group_entry.pack(side='left', padx=5)
        ctk.CTkButton(gc, text="Get Members", command=self.get_local_group_members_action).pack(side='left', padx=5)
        ctk.CTkLabel(gc, text="Member:").pack(side='left', padx=5)
        self.local_member_entry = ctk.CTkEntry(gc, width=200)
        self.local_member_entry.pack(side='left', padx=5)
        ctk.CTkButton(gc, text="Add", command=lambda: self.modify_local_group_action(True), fg_color="green", width=60).pack(side='left', padx=2)
        ctk.CTkButton(gc, text="Remove", command=lambda: self.modify_local_group_action(False), fg_color="red", width=70).pack(side='left', padx=2)
        self.localgroups_output = ctk.CTkTextbox(gf, font=("Consolas", 9))
        self.localgroups_output.pack(fill='both', expand=True)

    def setup_envvars_tab(self):
        """Setup Environment Variables tab"""
        frame = ctk.CTkFrame(self.tab_envvars)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        ctrl = ctk.CTkFrame(frame)
        ctrl.pack(fill='x', pady=(0, 5))
        ctk.CTkLabel(ctrl, text="Scope:").pack(side='left', padx=5)
        self.env_scope = ctk.CTkOptionMenu(ctrl, values=["Machine", "User"], width=100)
        self.env_scope.pack(side='left', padx=5)
        ctk.CTkButton(ctrl, text="Get Variables", command=self.get_env_vars_action).pack(side='left', padx=5)

        ctrl2 = ctk.CTkFrame(frame)
        ctrl2.pack(fill='x', pady=(0, 5))
        ctk.CTkLabel(ctrl2, text="Name:").pack(side='left', padx=5)
        self.env_name_entry = ctk.CTkEntry(ctrl2, width=200)
        self.env_name_entry.pack(side='left', padx=5)
        ctk.CTkLabel(ctrl2, text="Value:").pack(side='left', padx=5)
        self.env_value_entry = ctk.CTkEntry(ctrl2, width=300)
        self.env_value_entry.pack(side='left', padx=5)
        ctk.CTkButton(ctrl2, text="Set", command=self.set_env_var_action, fg_color="green", width=60).pack(side='left', padx=2)
        ctk.CTkButton(ctrl2, text="Remove", command=self.remove_env_var_action, fg_color="red", width=70).pack(side='left', padx=2)

        self.envvars_output = ctk.CTkTextbox(frame, font=("Consolas", 9))
        self.envvars_output.pack(fill='both', expand=True)

    def setup_certs_tab(self):
        """Setup Certificates tab"""
        frame = ctk.CTkFrame(self.tab_certs)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        ctrl = ctk.CTkFrame(frame)
        ctrl.pack(fill='x', pady=(0, 10))
        ctk.CTkLabel(ctrl, text="Store:").pack(side='left', padx=5)
        self.cert_store = ctk.CTkOptionMenu(ctrl, values=list(CERT_STORES.keys()), width=220)
        self.cert_store.pack(side='left', padx=5)
        ctk.CTkButton(ctrl, text="Get Certificates", command=self.get_certificates_action).pack(side='left', padx=5)
        ctk.CTkButton(ctrl, text="Show Expiring (30 days)", command=self.get_expiring_certs_action, fg_color="orange").pack(side='left', padx=5)

        self.certs_output = ctk.CTkTextbox(frame, font=("Consolas", 9))
        self.certs_output.pack(fill='both', expand=True)

    def setup_remcmd_tab(self):
        """Setup Remote Commands tab"""
        frame = ctk.CTkFrame(self.tab_remcmd)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        ctrl = ctk.CTkFrame(frame)
        ctrl.pack(fill='x', pady=(0, 5))
        ctk.CTkLabel(ctrl, text="History:").pack(side='left', padx=5)
        self.remcmd_history_menu = ctk.CTkOptionMenu(ctrl, values=["(no history)"], command=self.load_history_command, width=400)
        self.remcmd_history_menu.pack(side='left', padx=5)
        ctk.CTkLabel(ctrl, text="Timeout:").pack(side='left', padx=5)
        self.remcmd_timeout = ctk.CTkEntry(ctrl, width=60)
        self.remcmd_timeout.insert(0, "60")
        self.remcmd_timeout.pack(side='left')

        ctk.CTkLabel(frame, text="PowerShell Command:", font=("Arial", 11)).pack(anchor='w', padx=5)
        self.remcmd_input = ctk.CTkTextbox(frame, height=100, font=("Consolas", 10))
        self.remcmd_input.pack(fill='x', padx=5, pady=(0, 5))

        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(fill='x', pady=(0, 5))
        ctk.CTkButton(btn_frame, text="Execute", command=self.execute_remote_command_action, fg_color="green", width=120).pack(side='left', padx=5)
        ctk.CTkButton(btn_frame, text="Clear Output", command=lambda: self.remcmd_output.delete('1.0', 'end'), width=100).pack(side='left', padx=5)

        ctk.CTkLabel(frame, text="Output:", font=("Arial", 11)).pack(anchor='w', padx=5)
        self.remcmd_output = ctk.CTkTextbox(frame, font=("Consolas", 9))
        self.remcmd_output.pack(fill='both', expand=True, padx=5)

    def setup_rdpconnect_tab(self):
        """Setup RDP Connect tab"""
        frame = ctk.CTkFrame(self.tab_rdpconnect)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="Remote Desktop Connection", font=("Arial", 16, "bold")).pack(anchor='w', pady=10)

        conn_frame = ctk.CTkFrame(frame)
        conn_frame.pack(fill='x', pady=10)
        ctk.CTkLabel(conn_frame, text="Computer:").pack(side='left', padx=5)
        self.rdp_computer = ctk.CTkEntry(conn_frame, width=300, placeholder_text="Computer name or IP")
        self.rdp_computer.pack(side='left', padx=5)

        ctk.CTkLabel(conn_frame, text="Resolution:").pack(side='left', padx=5)
        self.rdp_resolution = ctk.CTkOptionMenu(conn_frame, values=RDP_RESOLUTIONS, width=140)
        self.rdp_resolution.set("1920x1080")
        self.rdp_resolution.pack(side='left', padx=5)

        self.rdp_admin = ctk.CTkCheckBox(conn_frame, text="Admin Mode")
        self.rdp_admin.pack(side='left', padx=10)

        ctk.CTkButton(conn_frame, text="Connect", command=self.launch_rdp_action, fg_color="green", width=120).pack(side='left', padx=10)

        # Saved profiles
        prof_frame = ctk.CTkFrame(frame)
        prof_frame.pack(fill='x', pady=10)
        ctk.CTkLabel(prof_frame, text="Saved Profiles:").pack(side='left', padx=5)
        self.rdp_profiles_menu = ctk.CTkOptionMenu(prof_frame, values=["(none)"], command=self.load_rdp_profile, width=250)
        self.rdp_profiles_menu.pack(side='left', padx=5)
        ctk.CTkButton(prof_frame, text="Save Current", command=self.save_rdp_profile, width=100).pack(side='left', padx=5)
        ctk.CTkButton(prof_frame, text="Delete", command=self.delete_rdp_profile, fg_color="red", width=70).pack(side='left', padx=5)

        self.rdpconnect_output = ctk.CTkTextbox(frame, font=("Consolas", 10))
        self.rdpconnect_output.pack(fill='both', expand=True, pady=10)

        info = "Launch Remote Desktop sessions to desktops and servers.\n\nFeatures:\n- Custom resolution or fullscreen\n- Admin/console mode for server management\n- Save connection profiles for quick access\n\nNote: Uses mstsc.exe (built into Windows)"
        self.rdpconnect_output.insert('1.0', info)

    def setup_status_bar(self, parent):
        """Setup status bar at the bottom"""
        status_bar = ctk.CTkFrame(parent, height=25)
        status_bar.pack(fill='x', side='bottom')

        self.statusbar_computer = ctk.CTkLabel(status_bar, text="Computer: Not connected", font=("Arial", 10))
        self.statusbar_computer.pack(side='left', padx=10)
        self.statusbar_ip = ctk.CTkLabel(status_bar, text="IP: N/A", font=("Arial", 10))
        self.statusbar_ip.pack(side='left', padx=10)
        self.statusbar_os = ctk.CTkLabel(status_bar, text="OS: N/A", font=("Arial", 10))
        self.statusbar_os.pack(side='left', padx=10)

        self.theme_toggle = ctk.CTkSwitch(status_bar, text="Dark Mode", command=self.toggle_theme)
        self.theme_toggle.select()
        self.theme_toggle.pack(side='right', padx=10)

    # Action methods
    
    def connect_to_computer(self):
        """Connect to specified computer"""
        computer_name = self.computer_entry.get().strip()
        if not computer_name:
            messagebox.showerror("Error", "Please enter a computer name")
            return
        
        # Check if connecting to remote computer
        is_remote = computer_name.lower() not in ["localhost", ".", "127.0.0.1", platform.node().lower()]
        
        username = None
        password = None
        
        if is_remote:
            # Show credential dialog for remote connections
            self.log(f"Remote connection detected. Requesting credentials...")
            cred_dialog = CredentialDialog(self.root, computer_name)
            success, username, password = cred_dialog.get_credentials()
            
            if not success:
                self.log("Connection cancelled by user")
                messagebox.showinfo("Cancelled", "Connection cancelled")
                return
            
            self.log(f"Credentials received for user: {username}")
        
        self.current_computer = computer_name
        
        # Create WindowsAdminTools with credentials if remote
        if is_remote and username and password:
            self.admin_tools = WindowsAdminTools(computer_name, username=username, password=password)
            self.log(f"Connecting to {computer_name} with credentials...")
        else:
            self.admin_tools = WindowsAdminTools(computer_name)
            self.log(f"Connecting to {computer_name}...")

        self.status_label.configure(text=f"● Connected to {computer_name}", text_color="green")
        self.update_status_bar()
        self.log(f"Connected successfully to {computer_name}")
        
    def test_connection(self):
        """Test connection to computer"""
        if not self.admin_tools:
            self.connect_to_computer()
            
        self.log("Testing connection...")
        
        def test():
            result = self.admin_tools.test_connection()
            status = "successful" if result else "failed"
            color = "green" if result else "red"
            
            self.root.after(0, lambda: self.status_label.configure(
                text=f"● Connection {status}",
                text_color=color
            ))
            self.log(f"Connection test {status}")
            
        threading.Thread(target=test, daemon=True).start()
        
    def get_system_info(self):
        """Get system information"""
        if not self.admin_tools:
            self.connect_to_computer()
        
        self.log("Retrieving system information...")
        
        def fetch():
            info = self.admin_tools.get_system_info()
            output = format_json(info)
            
            self.root.after(0, lambda: self.system_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.system_output.insert('1.0', output))
            self.log("System information retrieved")
            
        threading.Thread(target=fetch, daemon=True).start()
        
    def get_uptime(self):
        """Get system uptime"""
        if not self.admin_tools:
            self.connect_to_computer()
        
        self.log("Getting system uptime...")
        
        def fetch():
            uptime = self.admin_tools.get_uptime()
            if uptime:
                output = f"System Uptime:\n{self.admin_tools.format_uptime(uptime)}"
            else:
                output = "Failed to get uptime"
            
            self.root.after(0, lambda: self.system_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.system_output.insert('1.0', output))
            self.log("Uptime retrieved")
            
        threading.Thread(target=fetch, daemon=True).start()
        
    def run_gpupdate(self):
        """Run Group Policy update"""
        if not self.admin_tools:
            self.connect_to_computer()
        
        self.log("Running GPUpdate...")
        
        def run():
            success, output = self.admin_tools.run_gpupdate()
            
            result = f"GPUpdate {'completed successfully' if success else 'failed'}:\n\n{output}"
            self.root.after(0, lambda: self.system_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.system_output.insert('1.0', result))
            self.log(f"GPUpdate {'completed' if success else 'failed'}")
            
        threading.Thread(target=run, daemon=True).start()
        
    def set_rdp(self, enable: bool):
        """Enable or disable RDP"""
        if not self.admin_tools:
            self.connect_to_computer()
        
        action = "Enabling" if enable else "Disabling"
        self.log(f"{action} Remote Desktop...")
        
        def set_state():
            self.rdp_output.configure(state='normal')
            self.rdp_output.delete('1.0', 'end')
            
            success, message = self.admin_tools.set_rdp_state(enable)
            
            output = f"{action} RDP:\n{'Success' if success else 'Failed'}\n\n{message}"
            self.root.after(0, lambda: self.rdp_output.insert('1.0', output))
            self.root.after(0, lambda: self.rdp_output.configure(state='disabled'))
            
            self.log(f"RDP {'enabled' if enable else 'disabled'}: {message}")
            
        threading.Thread(target=set_state, daemon=True).start()
        
    def get_rdp_status(self):
        """Get RDP status"""
        if not self.admin_tools:
            self.connect_to_computer()
        
        self.log("Checking RDP status...")
        
        def fetch():
            self.rdp_output.configure(state='normal')
            self.rdp_output.delete('1.0', 'end')
            
            status = self.admin_tools.get_rdp_status()
            output = f"RDP Configuration:\n\n{format_json(status)}"
            
            self.root.after(0, lambda: self.rdp_output.insert('1.0', output))
            self.root.after(0, lambda: self.rdp_output.configure(state='disabled'))
            self.log("RDP status retrieved")
            
        threading.Thread(target=fetch, daemon=True).start()
        
    def get_services(self, running_only: bool = False):
        """Get Windows services"""
        if not self.admin_tools:
            self.connect_to_computer()
        
        self.log("Retrieving services...")
        
        def fetch():
            services = self.admin_tools.get_services(running_only)

            # Map numeric Status values to strings
            status_map = {1: "Stopped", 2: "StartPending", 3: "StopPending", 4: "Running", 5: "ContinuePending", 6: "PausePending", 7: "Paused"}
            startup_map = {0: "Boot", 1: "System", 2: "Automatic", 3: "Manual", 4: "Disabled"}

            output = f"{'Running Services' if running_only else 'All Services'} ({len(services)}):\n\n"
            output += f"{'Name':<30} {'Display Name':<40} {'Status':<12} {'Start Type':<15}\n"
            output += "=" * 100 + "\n"

            for svc in services:
                name = str(svc.get('Name', 'N/A'))[:28]
                display = str(svc.get('DisplayName', 'N/A'))[:38]
                status = svc.get('Status', 'N/A')
                if isinstance(status, int):
                    status = status_map.get(status, str(status))
                start = svc.get('StartType', 'N/A')
                if isinstance(start, int):
                    start = startup_map.get(start, str(start))
                output += f"{name:<30} {display:<40} {str(status):<12} {str(start):<15}\n"

            self.root.after(0, lambda: self.services_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.services_output.insert('1.0', output))
            self.log(f"Retrieved {len(services)} services")
            
        threading.Thread(target=fetch, daemon=True).start()
        
    def get_processes(self):
        """Get running processes"""
        if not self.admin_tools:
            self.connect_to_computer()
        
        try:
            top_n = int(self.process_count.get())
        except ValueError:
            top_n = 20
        
        self.log(f"Retrieving top {top_n} processes...")
        
        def fetch():
            processes = self.admin_tools.get_processes(top_n)
            
            self.processes_output.delete('1.0', 'end')
            
            output = f"Top {len(processes)} Processes (by CPU):\n\n"
            output += f"{'PID':<8} {'Name':<30} {'CPU %':<10} {'Memory %':<12} {'Memory (MB)':<12}\n"
            output += "-" * 80 + "\n"
            
            for proc in processes:
                output += f"{proc.get('pid', 0):<8} "
                output += f"{proc.get('name', 'N/A'):<30} "
                output += f"{proc.get('cpu_percent', 0):<10.2f} "
                output += f"{proc.get('memory_percent', 0):<12.2f} "
                output += f"{proc.get('memory_mb', 0):<12.2f}\n"
            
            self.root.after(0, lambda: self.processes_output.insert('1.0', output))
            self.log(f"Retrieved {len(processes)} processes")
            
        threading.Thread(target=fetch, daemon=True).start()
        
    def get_network_adapters(self):
        """Get network adapter information"""
        if not self.admin_tools:
            self.connect_to_computer()
        
        self.log("Retrieving network adapters...")
        
        def fetch():
            adapters = self.admin_tools.get_network_adapters()
            
            self.network_output.delete('1.0', 'end')
            
            output = f"Network Adapters ({len(adapters)}):\n\n"
            
            for adapter in adapters:
                output += f"Name: {adapter.get('Name', 'N/A')}\n"
                output += f"  Status: {adapter.get('Status', 'N/A')}\n"
                output += f"  Link Speed: {adapter.get('LinkSpeed', 'N/A')}\n"
                output += f"  MAC Address: {adapter.get('MacAddress', 'N/A')}\n"
                output += f"  Description: {adapter.get('InterfaceDescription', 'N/A')}\n"
                output += "-" * 70 + "\n"
            
            self.root.after(0, lambda: self.network_output.insert('1.0', output))
            self.log(f"Retrieved {len(adapters)} network adapters")
            
        threading.Thread(target=fetch, daemon=True).start()
        
    def test_port(self):
        """Test TCP port"""
        if not self.admin_tools:
            self.connect_to_computer()
        
        try:
            port = int(self.port_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
            return
        
        self.log(f"Testing port {port}...")
        
        def test():
            result = self.admin_tools.test_tcp_port(port)
            
            output = f"Port Test Results:\n\n{format_json(result)}"
            
            self.root.after(0, lambda: self.network_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.network_output.insert('1.0', output))
            self.log(f"Port {port} is {result['status']}")
            
        threading.Thread(target=test, daemon=True).start()
        
    def get_disk_info(self):
        """Get disk information"""
        if not self.admin_tools:
            self.connect_to_computer()
        
        self.log("Retrieving disk information...")
        
        def fetch():
            disks = self.admin_tools.get_disk_info()
            
            self.disks_output.delete('1.0', 'end')
            
            output = f"Disk/Volume Information ({len(disks)}):\n\n"
            
            for disk in disks:
                output += f"Drive: {disk.get('DriveLetter', 'N/A')}:\\\n"
                output += f"  Label: {disk.get('FileSystemLabel', 'N/A')}\n"
                output += f"  File System: {disk.get('FileSystem', 'N/A')}\n"
                output += f"  Total Size: {format_bytes(disk.get('Size', 0))}\n"
                output += f"  Free Space: {format_bytes(disk.get('SizeRemaining', 0))}\n"
                output += f"  Used: {disk.get('PercentUsed', 0):.1f}%\n"
                output += "-" * 70 + "\n"
            
            self.root.after(0, lambda: self.disks_output.insert('1.0', output))
            self.log(f"Retrieved {len(disks)} disk volumes")
            
        threading.Thread(target=fetch, daemon=True).start()
        
    def generate_password(self):
        """Generate a secure password"""
        if not self.admin_tools:
            self.admin_tools = WindowsAdminTools()
        
        try:
            length = int(self.pw_length.get())
        except ValueError:
            length = 16
        
        include_special = self.pw_special.get() == 1
        
        password = self.admin_tools.generate_password(length, include_special)
        
        self.pw_output.delete(0, 'end')
        self.pw_output.insert(0, password)
        
        self.log(f"Generated {length}-character password")
        
    def restart_computer(self):
        """Restart the computer"""
        if not self.admin_tools:
            self.connect_to_computer()
        
        result = messagebox.askyesno(
            "Confirm Restart",
            f"Are you sure you want to restart {self.current_computer}?"
        )
        
        if not result:
            return
        
        self.log("Initiating computer restart...")
        
        def restart():
            success, message = self.admin_tools.restart_computer()
            self.log(f"Restart {'initiated' if success else 'failed'}: {message}")
            
        threading.Thread(target=restart, daemon=True).start()
        
    def shutdown_computer(self):
        """Shutdown the computer"""
        if not self.admin_tools:
            self.connect_to_computer()
        
        result = messagebox.askyesno(
            "Confirm Shutdown",
            f"Are you sure you want to shutdown {self.current_computer}?"
        )
        
        if not result:
            return
        
        self.log("Initiating computer shutdown...")
        
        def shutdown():
            success, message = self.admin_tools.shutdown_computer()
            self.log(f"Shutdown {'initiated' if success else 'failed'}: {message}")
            
        threading.Thread(target=shutdown, daemon=True).start()
        
    def get_sessions(self):
        """Get user sessions"""
        if not self.admin_tools:
            self.connect_to_computer()
        
        self.log("Querying user sessions...")
        
        def fetch():
            sessions = self.admin_tools.get_qwinsta()
            
            self.session_output.delete('1.0', 'end')
            
            if sessions:
                output = f"User Sessions ({len(sessions)}):\n\n"
                output += f"{'Username':<20} {'Session':<15} {'ID':<10} {'State':<15}\n"
                output += "-" * 70 + "\n"
                
                for session in sessions:
                    output += f"{session.get('username', 'N/A'):<20} "
                    output += f"{session.get('session_name', 'N/A'):<15} "
                    output += f"{session.get('id', 'N/A'):<10} "
                    output += f"{session.get('state', 'N/A'):<15}\n"
            else:
                output = "No active sessions found or unable to query sessions."
            
            self.root.after(0, lambda: self.session_output.insert('1.0', output))
            self.log(f"Retrieved {len(sessions)} sessions")
            
        threading.Thread(target=fetch, daemon=True).start()
        
    def log(self, message: str):
        """Add message to log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_output.insert('end', log_message)
        self.log_output.see('end')
        
    def clear_log(self):
        """Clear the log"""
        self.log_output.delete('1.0', 'end')

    # ===================== NEW HELPER & INFRASTRUCTURE ACTIONS =====================

    def select_favorite(self, computer_name: str):
        self.computer_entry.delete(0, 'end')
        self.computer_entry.insert(0, computer_name)
        self.connect_to_computer()

    def save_favorite(self):
        name = self.computer_entry.get().strip()
        if name and name not in self.favorites:
            self.favorites.append(name)
            self.favorites_menu.configure(values=self.favorites)
            self.log(f"Saved {name} to favorites")

    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_mode = "light" if current == "Dark" else "dark"
        ctk.set_appearance_mode(new_mode)
        self.log(f"Theme changed to {new_mode}")

    def update_status_bar(self):
        self.statusbar_computer.configure(text=f"Computer: {self.current_computer}")
        try:
            import socket
            ip = socket.gethostbyname(self.current_computer)
            self.statusbar_ip.configure(text=f"IP: {ip}")
        except Exception:
            self.statusbar_ip.configure(text="IP: N/A")
        self.statusbar_os.configure(text=f"OS: {platform.system()} {platform.release()}")

    def copy_password(self):
        password = self.pw_output.get()
        if password:
            self.root.clipboard_clear()
            self.root.clipboard_append(password)
            self.log("Password copied to clipboard")

    def export_log(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Text files", "*.txt")],
                                                 initialdir=str(EXPORT_DIRECTORY))
        if filepath:
            content = self.log_output.get('1.0', 'end')
            with open(filepath, 'w') as f:
                f.write(content)
            self.log(f"Log exported to {filepath}")

    def _export_tab_csv(self, data: list, default_name: str = "export"):
        filepath = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV files", "*.csv")],
                                                 initialfile=default_name,
                                                 initialdir=str(EXPORT_DIRECTORY))
        if filepath and data:
            success, result = export_to_csv(data, filepath)
            if success:
                self.log(f"Exported to {result}")
            else:
                self.log(f"Export failed: {result}")

    # ===================== ENHANCED EXISTING TAB ACTIONS =====================

    def control_service_action(self, action: str):
        if not self.admin_tools:
            self.connect_to_computer()
        service_name = self.service_name_entry.get().strip()
        if not service_name:
            messagebox.showerror("Error", "Enter a service name")
            return
        self.log(f"{action.title()}ing service {service_name}...")

        def do():
            success, msg = self.admin_tools.control_service(service_name, action)
            self.root.after(0, lambda: self.services_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.services_output.insert('1.0', f"Service {action}: {'Success' if success else 'Failed'}\n\n{msg}"))
            self.log(f"Service {action} {'succeeded' if success else 'failed'}")
        threading.Thread(target=do, daemon=True).start()

    def set_service_startup(self):
        if not self.admin_tools:
            self.connect_to_computer()
        service_name = self.service_name_entry.get().strip()
        startup_type = self.service_startup_type.get()
        if not service_name:
            messagebox.showerror("Error", "Enter a service name")
            return
        self.log(f"Setting {service_name} startup to {startup_type}...")

        def do():
            success, msg = self.admin_tools.set_service_startup_type(service_name, startup_type)
            self.root.after(0, lambda: self.services_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.services_output.insert('1.0', f"Set startup type: {'Success' if success else 'Failed'}\n\n{msg}"))
            self.log(f"Startup type change {'succeeded' if success else 'failed'}")
        threading.Thread(target=do, daemon=True).start()

    def kill_process_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        pid = self.kill_pid_entry.get().strip()
        if not pid:
            messagebox.showerror("Error", "Enter a PID")
            return
        if not messagebox.askyesno("Confirm", f"Kill process {pid}?"):
            return
        self.log(f"Killing process {pid}...")

        def do():
            success, msg = self.admin_tools.kill_process(pid=int(pid))
            self.log(f"Kill process: {msg}")
        threading.Thread(target=do, daemon=True).start()

    def ping_host_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        target = self.net_host_entry.get().strip() or self.current_computer
        self.log(f"Pinging {target}...")

        def do():
            results = self.admin_tools.ping_host(target)
            output = f"Ping Results for {target}:\n\n{format_json(results)}"
            self.root.after(0, lambda: self.network_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.network_output.insert('1.0', output))
            self.log(f"Ping complete")
        threading.Thread(target=do, daemon=True).start()

    def traceroute_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        target = self.net_host_entry.get().strip() or self.current_computer
        self.log(f"Traceroute to {target}...")

        def do():
            result = self.admin_tools.traceroute(target)
            output = f"Traceroute to {target}:\n\n{format_json(result)}"
            self.root.after(0, lambda: self.network_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.network_output.insert('1.0', output))
            self.log("Traceroute complete")
        threading.Thread(target=do, daemon=True).start()

    def nslookup_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        target = self.net_host_entry.get().strip()
        if not target:
            messagebox.showerror("Error", "Enter a hostname")
            return
        self.log(f"NSLookup {target}...")

        def do():
            results = self.admin_tools.nslookup(target)
            output = f"NSLookup {target}:\n\n{format_json(results)}"
            self.root.after(0, lambda: self.network_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.network_output.insert('1.0', output))
            self.log("NSLookup complete")
        threading.Thread(target=do, daemon=True).start()

    def get_ip_config_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        self.log("Getting IP configuration...")

        def do():
            configs = self.admin_tools.get_ip_configuration()
            output = f"IP Configuration:\n\n{format_json(configs)}"
            self.root.after(0, lambda: self.network_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.network_output.insert('1.0', output))
            self.log("IP config retrieved")
        threading.Thread(target=do, daemon=True).start()

    def get_dns_servers_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        self.log("Getting DNS servers...")

        def do():
            servers = self.admin_tools.get_dns_servers()
            output = f"DNS Servers:\n\n{format_json(servers)}"
            self.root.after(0, lambda: self.network_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.network_output.insert('1.0', output))
            self.log("DNS servers retrieved")
        threading.Thread(target=do, daemon=True).start()

    # ===================== NEW TAB ACTION METHODS =====================

    # --- Active Directory ---
    def search_ad_users_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        query = self.ad_user_search.get().strip()
        if not query:
            return
        self.log(f"Searching AD users: {query}...")

        def do():
            users = self.admin_tools.search_ad_users(query)
            output = f"AD Users matching '{query}' ({len(users)}):\n\n{format_json(users)}"
            self.root.after(0, lambda: self.ad_user_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.ad_user_output.insert('1.0', output))
            self.log(f"Found {len(users)} AD users")
        threading.Thread(target=do, daemon=True).start()

    def unlock_ad_account_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        username = self.ad_user_search.get().strip()
        if not username:
            messagebox.showerror("Error", "Enter a username to unlock")
            return
        if not messagebox.askyesno("Confirm", f"Unlock AD account: {username}?"):
            return
        self.log(f"Unlocking AD account: {username}...")

        def do():
            success, msg = self.admin_tools.unlock_ad_account(username)
            self.root.after(0, lambda: self.ad_user_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.ad_user_output.insert('1.0', f"Unlock: {'Success' if success else 'Failed'}\n\n{msg}"))
            self.log(f"Account unlock {'succeeded' if success else 'failed'}")
        threading.Thread(target=do, daemon=True).start()

    def reset_ad_password_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        username = self.ad_user_search.get().strip()
        if not username:
            messagebox.showerror("Error", "Enter a username")
            return
        if not self.admin_tools:
            self.admin_tools = WindowsAdminTools()
        new_pw = self.admin_tools.generate_password(16, True)
        if not messagebox.askyesno("Confirm", f"Reset password for {username}?\nNew password will be: {new_pw}"):
            return
        self.log(f"Resetting password for {username}...")

        def do():
            success, msg = self.admin_tools.reset_ad_password(username, new_pw)
            result = f"Password Reset: {'Success' if success else 'Failed'}\n\nNew Password: {new_pw}\n\n{msg}" if success else f"Failed: {msg}"
            self.root.after(0, lambda: self.ad_user_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.ad_user_output.insert('1.0', result))
            self.log(f"Password reset {'succeeded' if success else 'failed'}")
        threading.Thread(target=do, daemon=True).start()

    def search_ad_groups_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        query = self.ad_group_search.get().strip() or "*"
        self.log(f"Searching AD groups: {query}...")

        def do():
            groups = self.admin_tools.get_ad_groups(query)
            output = f"AD Groups ({len(groups)}):\n\n{format_json(groups)}"
            self.root.after(0, lambda: self.ad_group_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.ad_group_output.insert('1.0', output))
            self.log(f"Found {len(groups)} groups")
        threading.Thread(target=do, daemon=True).start()

    def get_ad_group_members_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        group = self.ad_group_search.get().strip()
        if not group:
            return
        self.log(f"Getting members of {group}...")

        def do():
            members = self.admin_tools.get_ad_group_members(group)
            output = f"Members of '{group}' ({len(members)}):\n\n{format_json(members)}"
            self.root.after(0, lambda: self.ad_group_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.ad_group_output.insert('1.0', output))
            self.log(f"Found {len(members)} members")
        threading.Thread(target=do, daemon=True).start()

    def search_ad_computers_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        query = self.ad_computer_search.get().strip() or "*"
        self.log(f"Searching AD computers: {query}...")

        def do():
            computers = self.admin_tools.get_ad_computers(query)
            output = f"AD Computers ({len(computers)}):\n\n{format_json(computers)}"
            self.root.after(0, lambda: self.ad_computer_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.ad_computer_output.insert('1.0', output))
            self.log(f"Found {len(computers)} computers")
        threading.Thread(target=do, daemon=True).start()

    def get_ad_ous_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        self.log("Getting AD OUs...")

        def do():
            ous = self.admin_tools.get_ad_ous()
            output = f"Organizational Units ({len(ous)}):\n\n{format_json(ous)}"
            self.root.after(0, lambda: self.ad_computer_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.ad_computer_output.insert('1.0', output))
            self.log(f"Found {len(ous)} OUs")
        threading.Thread(target=do, daemon=True).start()

    # --- Event Viewer ---
    def get_event_logs_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        log_name = self.eventlog_logname.get()
        level = self.eventlog_level.get()
        if level == "All":
            level = None
        try:
            max_events = int(self.eventlog_max.get())
        except ValueError:
            max_events = 100
        source = self.eventlog_source.get().strip() or None
        search_text = self.eventlog_search.get().strip() or None
        self.log(f"Getting {log_name} events...")

        def do():
            events = self.admin_tools.get_event_logs_filtered(log_name, max_events, level, source, search_text)
            output = f"{log_name} Events ({len(events)}):\n\n"
            for evt in events:
                output += f"[{evt.get('TimeCreated', 'N/A')}] {evt.get('LevelDisplayName', 'N/A')} (ID: {evt.get('Id', 'N/A')})\n"
                output += f"  Source: {evt.get('ProviderName', 'N/A')}\n"
                msg = str(evt.get('Message', 'N/A'))[:200]
                output += f"  {msg}\n"
                output += "-" * 80 + "\n"
            self.root.after(0, lambda: self.eventlog_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.eventlog_output.insert('1.0', output))
            self.log(f"Retrieved {len(events)} events")
        threading.Thread(target=do, daemon=True).start()

    # --- Windows Update ---
    def get_installed_updates_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        self.log("Getting installed updates...")

        def do():
            updates = self.admin_tools.get_installed_updates()
            output = f"Installed Updates ({len(updates)}):\n\n"
            for u in updates:
                output += f"{u.get('HotFixID', 'N/A')} - {u.get('Description', 'N/A')}\n"
                output += f"  Installed: {u.get('InstalledOn', 'N/A')} by {u.get('InstalledBy', 'N/A')}\n"
                output += "-" * 60 + "\n"
            self.root.after(0, lambda: self.updates_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.updates_output.insert('1.0', output))
            self.log(f"Retrieved {len(updates)} updates")
        threading.Thread(target=do, daemon=True).start()

    def check_for_updates_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        self.log("Checking for pending updates (this may take a while)...")

        def do():
            status = self.admin_tools.get_windows_update_status()
            output = f"Windows Update Status:\n\n{format_json(status)}"
            self.root.after(0, lambda: self.updates_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.updates_output.insert('1.0', output))
            self.log("Update check complete")
        threading.Thread(target=do, daemon=True).start()

    def get_update_history_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        self.log("Getting update history...")

        def do():
            history = self.admin_tools.get_update_history()
            output = f"Update History ({len(history)}):\n\n{format_json(history)}"
            self.root.after(0, lambda: self.updates_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.updates_output.insert('1.0', output))
            self.log(f"Retrieved {len(history)} history entries")
        threading.Thread(target=do, daemon=True).start()

    # --- Firewall ---
    def get_firewall_rules_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        direction = self.fw_direction.get()
        if direction == "All":
            direction = None
        enabled_only = self.fw_enabled_only.get() == 1
        self.log("Getting firewall rules...")

        def do():
            rules = self.admin_tools.get_firewall_rules_filtered(direction, enabled_only)
            output = f"Firewall Rules ({len(rules)}):\n\n"
            for r in rules:
                dir_str = "Inbound" if r.get('Direction', 0) == 1 else "Outbound"
                act_str = "Allow" if r.get('Action', 0) == 2 else "Block"
                output += f"{r.get('DisplayName', 'N/A')}\n"
                output += f"  Direction: {dir_str}  Action: {act_str}  Enabled: {r.get('Enabled', 'N/A')}\n"
                output += "-" * 70 + "\n"
            self.root.after(0, lambda: self.firewall_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.firewall_output.insert('1.0', output))
            self.log(f"Retrieved {len(rules)} firewall rules")
        threading.Thread(target=do, daemon=True).start()

    def enable_firewall_rule_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        rule_name = self.fw_rule_name.get().strip()
        if not rule_name:
            return
        self.log(f"Enabling firewall rule: {rule_name}...")

        def do():
            success, msg = self.admin_tools.set_firewall_rule_state(rule_name, True)
            self.log(f"Enable rule: {'Success' if success else 'Failed'} - {msg}")
        threading.Thread(target=do, daemon=True).start()

    def disable_firewall_rule_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        rule_name = self.fw_rule_name.get().strip()
        if not rule_name:
            return
        self.log(f"Disabling firewall rule: {rule_name}...")

        def do():
            success, msg = self.admin_tools.set_firewall_rule_state(rule_name, False)
            self.log(f"Disable rule: {'Success' if success else 'Failed'} - {msg}")
        threading.Thread(target=do, daemon=True).start()

    def create_firewall_rule_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Create Firewall Rule")
        dialog.geometry("400x350")
        dialog.transient(self.root)

        entries = {}
        for label, key, values in [
            ("Name:", "name", None),
            ("Direction:", "direction", FIREWALL_DIRECTIONS),
            ("Action:", "action", FIREWALL_ACTIONS),
            ("Protocol:", "protocol", FIREWALL_PROTOCOLS),
            ("Port:", "port", None),
            ("Profile:", "profile", FIREWALL_PROFILES),
        ]:
            f = ctk.CTkFrame(dialog)
            f.pack(fill='x', padx=10, pady=3)
            ctk.CTkLabel(f, text=label, width=80).pack(side='left')
            if values:
                w = ctk.CTkOptionMenu(f, values=values, width=200)
                w.pack(side='left', padx=5)
            else:
                w = ctk.CTkEntry(f, width=200)
                w.pack(side='left', padx=5)
            entries[key] = w

        def create():
            if not self.admin_tools:
                self.connect_to_computer()
            vals = {k: (v.get() if hasattr(v, 'get') else v.get()) for k, v in entries.items()}
            self.log(f"Creating firewall rule: {vals['name']}...")

            def do():
                success, msg = self.admin_tools.create_firewall_rule(
                    vals['name'], vals['direction'], vals['action'],
                    vals['protocol'], vals['port'], vals['profile']
                )
                self.log(f"Create rule: {'Success' if success else 'Failed'}")
                self.root.after(0, dialog.destroy)
            threading.Thread(target=do, daemon=True).start()

        ctk.CTkButton(dialog, text="Create Rule", command=create, fg_color="green").pack(pady=15)

    # --- Installed Software ---
    def get_installed_software_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        self.log("Getting installed software...")

        def do():
            software = self.admin_tools.get_installed_software()
            output = f"Installed Software ({len(software)}):\n\n"
            output += f"{'Name':<45} {'Version':<18} {'Publisher':<30}\n"
            output += "=" * 95 + "\n"
            for s in software:
                name = str(s.get('DisplayName', 'N/A'))[:43]
                ver = str(s.get('DisplayVersion', 'N/A'))[:16]
                pub = str(s.get('Publisher', 'N/A'))[:28]
                output += f"{name:<45} {ver:<18} {pub:<30}\n"
            self.root.after(0, lambda: self.software_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.software_output.insert('1.0', output))
            self.log(f"Retrieved {len(software)} programs")
        threading.Thread(target=do, daemon=True).start()

    # --- Scheduled Tasks ---
    def get_scheduled_tasks_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        include_ms = self.task_show_all.get() == 1
        self.log("Getting scheduled tasks...")

        def do():
            tasks = self.admin_tools.get_scheduled_tasks(include_ms)
            # Map State numbers: 0=Unknown, 1=Disabled, 2=Queued, 3=Ready, 4=Running
            state_map = {0: "Unknown", 1: "Disabled", 2: "Queued", 3: "Ready", 4: "Running"}

            output = f"Scheduled Tasks ({len(tasks)}):\n\n"
            output += f"{'Task Name':<40} {'State':<12} {'Path':<30}\n"
            output += "=" * 85 + "\n"
            for t in tasks:
                name = str(t.get('TaskName', 'N/A'))[:38]
                state = t.get('State', 'N/A')
                if isinstance(state, int):
                    state = state_map.get(state, str(state))
                path = str(t.get('TaskPath', ''))[:28]
                desc = str(t.get('Description', '') or '')[:80]
                output += f"{name:<40} {str(state):<12} {path:<30}\n"
                if desc:
                    output += f"  {desc}\n"
                output += "-" * 85 + "\n"
            self.root.after(0, lambda: self.tasks_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.tasks_output.insert('1.0', output))
            self.log(f"Retrieved {len(tasks)} tasks")
        threading.Thread(target=do, daemon=True).start()

    def set_task_state_action(self, enabled: bool):
        if not self.admin_tools:
            self.connect_to_computer()
        name = self.task_name_entry.get().strip()
        path = self.task_path_entry.get().strip() or "\\"
        if not name:
            return
        action = "Enabling" if enabled else "Disabling"
        self.log(f"{action} task {name}...")

        def do():
            success, msg = self.admin_tools.set_scheduled_task_state(name, path, enabled)
            self.log(f"{action} task: {'Success' if success else 'Failed'}")
        threading.Thread(target=do, daemon=True).start()

    def run_task_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        name = self.task_name_entry.get().strip()
        path = self.task_path_entry.get().strip() or "\\"
        if not name:
            return
        self.log(f"Running task {name}...")

        def do():
            success, msg = self.admin_tools.run_scheduled_task(name, path)
            self.log(f"Run task: {'Success' if success else 'Failed'}")
        threading.Thread(target=do, daemon=True).start()

    def get_task_history_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        name = self.task_name_entry.get().strip()
        if not name:
            return
        self.log(f"Getting history for {name}...")

        def do():
            history = self.admin_tools.get_scheduled_task_history(name)
            output = f"Task History for '{name}' ({len(history)}):\n\n{format_json(history)}"
            self.root.after(0, lambda: self.tasks_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.tasks_output.insert('1.0', output))
            self.log(f"Retrieved {len(history)} history entries")
        threading.Thread(target=do, daemon=True).start()

    # --- Printers ---
    def get_printers_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        self.log("Getting printers...")

        def do():
            printers = self.admin_tools.get_printers()
            output = f"Printers ({len(printers)}):\n\n"
            for p in printers:
                output += f"{p.get('Name', 'N/A')}\n"
                output += f"  Driver: {p.get('DriverName', 'N/A')}  Port: {p.get('PortName', 'N/A')}  Status: {p.get('PrinterStatus', 'N/A')}\n"
                output += "-" * 60 + "\n"
            self.root.after(0, lambda: self.printers_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.printers_output.insert('1.0', output))
            self.log(f"Found {len(printers)} printers")
        threading.Thread(target=do, daemon=True).start()

    def get_print_queue_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        printer = self.printer_name_entry.get().strip()
        if not printer:
            return
        self.log(f"Getting print queue for {printer}...")

        def do():
            jobs = self.admin_tools.get_print_jobs(printer)
            output = f"Print Queue for '{printer}' ({len(jobs)}):\n\n{format_json(jobs)}"
            self.root.after(0, lambda: self.printers_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.printers_output.insert('1.0', output))
            self.log(f"Found {len(jobs)} print jobs")
        threading.Thread(target=do, daemon=True).start()

    def clear_print_queue_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        printer = self.printer_name_entry.get().strip()
        if not printer:
            return
        if not messagebox.askyesno("Confirm", f"Clear all jobs for {printer}?"):
            return
        self.log(f"Clearing print queue for {printer}...")

        def do():
            success, msg = self.admin_tools.clear_print_queue(printer)
            self.log(f"Clear queue: {'Success' if success else 'Failed'}")
        threading.Thread(target=do, daemon=True).start()

    def remove_print_job_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        printer = self.printer_name_entry.get().strip()
        job_id = self.print_job_id_entry.get().strip()
        if not printer or not job_id:
            return
        self.log(f"Removing print job {job_id}...")

        def do():
            success, msg = self.admin_tools.remove_print_job(printer, int(job_id))
            self.log(f"Remove job: {'Success' if success else 'Failed'}")
        threading.Thread(target=do, daemon=True).start()

    # --- Shares ---
    def get_smb_shares_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        self.log("Getting SMB shares...")

        def do():
            shares = self.admin_tools.get_smb_shares()
            output = f"SMB Shares ({len(shares)}):\n\n"
            for s in shares:
                output += f"{s.get('Name', 'N/A')}  ->  {s.get('Path', 'N/A')}\n"
                output += f"  Description: {s.get('Description', 'N/A')}  Users: {s.get('CurrentUsers', 0)}\n"
                output += "-" * 60 + "\n"
            self.root.after(0, lambda: self.shares_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.shares_output.insert('1.0', output))
            self.log(f"Found {len(shares)} shares")
        threading.Thread(target=do, daemon=True).start()

    def get_share_permissions_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        name = self.share_name_entry.get().strip()
        if not name:
            return
        self.log(f"Getting permissions for {name}...")

        def do():
            perms = self.admin_tools.get_share_permissions(name)
            output = f"Permissions for '{name}':\n\n{format_json(perms)}"
            self.root.after(0, lambda: self.shares_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.shares_output.insert('1.0', output))
            self.log("Permissions retrieved")
        threading.Thread(target=do, daemon=True).start()

    def create_share_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Create SMB Share")
        dialog.geometry("400x250")
        dialog.transient(self.root)

        entries = {}
        for label, key in [("Name:", "name"), ("Path:", "path"), ("Description:", "desc")]:
            f = ctk.CTkFrame(dialog)
            f.pack(fill='x', padx=10, pady=5)
            ctk.CTkLabel(f, text=label, width=100).pack(side='left')
            e = ctk.CTkEntry(f, width=250)
            e.pack(side='left', padx=5)
            entries[key] = e

        def create():
            if not self.admin_tools:
                self.connect_to_computer()
            self.log(f"Creating share {entries['name'].get()}...")

            def do():
                success, msg = self.admin_tools.create_smb_share(entries['name'].get(), entries['path'].get(), entries['desc'].get())
                self.log(f"Create share: {'Success' if success else 'Failed'}")
                self.root.after(0, dialog.destroy)
            threading.Thread(target=do, daemon=True).start()

        ctk.CTkButton(dialog, text="Create", command=create, fg_color="green").pack(pady=15)

    def remove_share_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        name = self.share_name_entry.get().strip()
        if not name:
            return
        if not messagebox.askyesno("Confirm", f"Remove share '{name}'?"):
            return
        self.log(f"Removing share {name}...")

        def do():
            success, msg = self.admin_tools.remove_smb_share(name)
            self.log(f"Remove share: {'Success' if success else 'Failed'}")
        threading.Thread(target=do, daemon=True).start()

    # --- DNS/DHCP ---
    def dns_lookup_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        hostname = self.dns_hostname_entry.get().strip()
        if not hostname:
            return
        self.log(f"DNS lookup: {hostname}...")

        def do():
            results = self.admin_tools.resolve_dns(hostname)
            output = f"DNS Lookup for '{hostname}':\n\n{format_json(results)}"
            self.root.after(0, lambda: self.dns_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.dns_output.insert('1.0', output))
            self.log("DNS lookup complete")
        threading.Thread(target=do, daemon=True).start()

    def flush_dns_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        self.log("Flushing DNS cache...")

        def do():
            success, msg = self.admin_tools.flush_dns_cache()
            self.root.after(0, lambda: self.dns_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.dns_output.insert('1.0', f"Flush DNS: {'Success' if success else 'Failed'}\n\n{msg}"))
            self.log(f"DNS flush {'succeeded' if success else 'failed'}")
        threading.Thread(target=do, daemon=True).start()

    def get_dns_cache_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        self.log("Getting DNS cache...")

        def do():
            entries = self.admin_tools.get_dns_cache()
            output = f"DNS Cache ({len(entries)}):\n\n{format_json(entries)}"
            self.root.after(0, lambda: self.dns_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.dns_output.insert('1.0', output))
            self.log(f"Retrieved {len(entries)} cache entries")
        threading.Thread(target=do, daemon=True).start()

    def get_dhcp_info_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        self.log("Getting DHCP info...")

        def do():
            info = self.admin_tools.get_dhcp_info()
            output = f"DHCP Leases:\n\n{format_json(info)}"
            self.root.after(0, lambda: self.dns_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.dns_output.insert('1.0', output))
            self.log("DHCP info retrieved")
        threading.Thread(target=do, daemon=True).start()

    def get_dns_servers_tab_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        self.log("Getting DNS servers...")

        def do():
            servers = self.admin_tools.get_dns_servers()
            output = f"DNS Servers:\n\n{format_json(servers)}"
            self.root.after(0, lambda: self.dns_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.dns_output.insert('1.0', output))
            self.log("DNS servers retrieved")
        threading.Thread(target=do, daemon=True).start()

    # --- Local Users & Groups ---
    def get_local_users_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        self.log("Getting local users...")

        def do():
            users = self.admin_tools.get_local_users()
            output = f"Local Users ({len(users)}):\n\n"
            for u in users:
                output += f"{u.get('Name', 'N/A')}  [{'Enabled' if u.get('Enabled') else 'Disabled'}]\n"
                output += f"  Description: {u.get('Description', 'N/A')}\n"
                output += f"  Last Logon: {u.get('LastLogon', 'N/A')}\n"
                output += "-" * 50 + "\n"
            self.root.after(0, lambda: self.localusers_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.localusers_output.insert('1.0', output))
            self.log(f"Found {len(users)} local users")
        threading.Thread(target=do, daemon=True).start()

    def set_local_user_state_action(self, enabled: bool):
        if not self.admin_tools:
            self.connect_to_computer()
        username = self.local_username_entry.get().strip()
        if not username:
            return
        action = "Enabling" if enabled else "Disabling"
        self.log(f"{action} user {username}...")

        def do():
            success, msg = self.admin_tools.set_local_user_state(username, enabled)
            self.log(f"{action} user: {'Success' if success else 'Failed'}")
        threading.Thread(target=do, daemon=True).start()

    def get_local_groups_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        self.log("Getting local groups...")

        def do():
            groups = self.admin_tools.get_local_groups()
            output = f"Local Groups ({len(groups)}):\n\n"
            for g in groups:
                output += f"{g.get('Name', 'N/A')}\n"
                output += f"  Description: {g.get('Description', 'N/A')}\n"
                output += "-" * 50 + "\n"
            self.root.after(0, lambda: self.localgroups_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.localgroups_output.insert('1.0', output))
            self.log(f"Found {len(groups)} groups")
        threading.Thread(target=do, daemon=True).start()

    def get_local_group_members_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        group = self.local_group_entry.get().strip()
        if not group:
            return
        self.log(f"Getting members of {group}...")

        def do():
            members = self.admin_tools.get_local_group_members(group)
            output = f"Members of '{group}' ({len(members)}):\n\n{format_json(members)}"
            self.root.after(0, lambda: self.localgroups_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.localgroups_output.insert('1.0', output))
            self.log(f"Found {len(members)} members")
        threading.Thread(target=do, daemon=True).start()

    def modify_local_group_action(self, add: bool):
        if not self.admin_tools:
            self.connect_to_computer()
        group = self.local_group_entry.get().strip()
        member = self.local_member_entry.get().strip()
        if not group or not member:
            return
        action = "Adding" if add else "Removing"
        self.log(f"{action} {member} {'to' if add else 'from'} {group}...")

        def do():
            success, msg = self.admin_tools.modify_local_group_membership(group, member, add)
            self.log(f"{action}: {'Success' if success else 'Failed'}")
        threading.Thread(target=do, daemon=True).start()

    # --- Environment Variables ---
    def get_env_vars_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        scope = self.env_scope.get()
        self.log(f"Getting {scope} environment variables...")

        def do():
            env_vars = self.admin_tools.get_environment_variables(scope)
            output = f"{scope} Environment Variables ({len(env_vars)}):\n\n"
            for name, value in sorted(env_vars.items()):
                output += f"{name} = {value}\n"
            self.root.after(0, lambda: self.envvars_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.envvars_output.insert('1.0', output))
            self.log(f"Retrieved {len(env_vars)} variables")
        threading.Thread(target=do, daemon=True).start()

    def set_env_var_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        name = self.env_name_entry.get().strip()
        value = self.env_value_entry.get().strip()
        scope = self.env_scope.get()
        if not name or not value:
            return
        self.log(f"Setting {name}={value} ({scope})...")

        def do():
            success, msg = self.admin_tools.set_environment_variable(name, value, scope)
            self.log(f"Set env var: {'Success' if success else 'Failed'}")
        threading.Thread(target=do, daemon=True).start()

    def remove_env_var_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        name = self.env_name_entry.get().strip()
        scope = self.env_scope.get()
        if not name:
            return
        if not messagebox.askyesno("Confirm", f"Remove {scope} variable '{name}'?"):
            return
        self.log(f"Removing {name} ({scope})...")

        def do():
            success, msg = self.admin_tools.remove_environment_variable(name, scope)
            self.log(f"Remove env var: {'Success' if success else 'Failed'}")
        threading.Thread(target=do, daemon=True).start()

    # --- Certificates ---
    def get_certificates_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        store_name = self.cert_store.get()
        store_path = CERT_STORES.get(store_name, r"Cert:\LocalMachine\My")
        self.log(f"Getting certificates from {store_name}...")

        def do():
            certs = self.admin_tools.get_certificates(store_path)
            output = f"Certificates in {store_name} ({len(certs)}):\n\n"
            for c in certs:
                output += f"Subject: {c.get('Subject', 'N/A')}\n"
                output += f"  Thumbprint: {c.get('Thumbprint', 'N/A')}\n"
                output += f"  Issuer: {c.get('Issuer', 'N/A')}\n"
                output += f"  Valid: {c.get('NotBefore', 'N/A')} to {c.get('NotAfter', 'N/A')}\n"
                output += "-" * 70 + "\n"
            self.root.after(0, lambda: self.certs_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.certs_output.insert('1.0', output))
            self.log(f"Found {len(certs)} certificates")
        threading.Thread(target=do, daemon=True).start()

    def get_expiring_certs_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        store_name = self.cert_store.get()
        store_path = CERT_STORES.get(store_name, r"Cert:\LocalMachine\My")
        self.log("Checking for expiring certificates...")

        def do():
            certs = self.admin_tools.get_expiring_certificates(30, store_path)
            output = f"Certificates Expiring Within 30 Days ({len(certs)}):\n\n"
            for c in certs:
                output += f"Subject: {c.get('Subject', 'N/A')}\n"
                output += f"  Expires: {c.get('NotAfter', 'N/A')}\n"
                output += "-" * 70 + "\n"
            if not certs:
                output += "No certificates expiring within 30 days."
            self.root.after(0, lambda: self.certs_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.certs_output.insert('1.0', output))
            self.log(f"Found {len(certs)} expiring certificates")
        threading.Thread(target=do, daemon=True).start()

    # --- Remote Commands ---
    def execute_remote_command_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        command = self.remcmd_input.get("1.0", "end").strip()
        if not command:
            return
        try:
            timeout = int(self.remcmd_timeout.get())
        except ValueError:
            timeout = 60

        # Add to history
        if command not in self.remote_command_history:
            self.remote_command_history.insert(0, command)
            self.remote_command_history = self.remote_command_history[:REMOTE_COMMAND_HISTORY_MAX]
            self.remcmd_history_menu.configure(values=self.remote_command_history if self.remote_command_history else ["(no history)"])

        self.log(f"Executing command (timeout={timeout}s)...")

        def do():
            success, output = self.admin_tools.run_remote_command(command, timeout)
            result = f"{'SUCCESS' if success else 'FAILED'}:\n\n{output}"
            self.root.after(0, lambda: self.remcmd_output.delete('1.0', 'end'))
            self.root.after(0, lambda: self.remcmd_output.insert('1.0', result))
            self.log(f"Command {'completed' if success else 'failed'}")
        threading.Thread(target=do, daemon=True).start()

    def load_history_command(self, choice: str):
        if choice != "(no history)":
            self.remcmd_input.delete("1.0", "end")
            self.remcmd_input.insert("1.0", choice)

    # --- RDP Connect ---
    def launch_rdp_action(self):
        if not self.admin_tools:
            self.connect_to_computer()
        computer = self.rdp_computer.get().strip() or self.current_computer
        resolution = self.rdp_resolution.get()
        admin_mode = self.rdp_admin.get() == 1
        fullscreen = resolution == "Fullscreen"
        width, height = (0, 0) if fullscreen else tuple(map(int, resolution.split('x')))

        self.log(f"Launching RDP to {computer}...")
        success, msg = self.admin_tools.launch_rdp_connection(computer, width, height, admin_mode, fullscreen)
        self.rdpconnect_output.delete('1.0', 'end')
        self.rdpconnect_output.insert('1.0', msg)
        self.log(msg)

    def save_rdp_profile(self):
        computer = self.rdp_computer.get().strip()
        if not computer:
            return
        self.saved_rdp_profiles[computer] = {
            'computer': computer,
            'resolution': self.rdp_resolution.get(),
            'admin': self.rdp_admin.get() == 1,
        }
        self.rdp_profiles_menu.configure(values=list(self.saved_rdp_profiles.keys()) or ["(none)"])
        self.log(f"Saved RDP profile for {computer}")

    def load_rdp_profile(self, profile_name: str):
        if profile_name in self.saved_rdp_profiles:
            p = self.saved_rdp_profiles[profile_name]
            self.rdp_computer.delete(0, 'end')
            self.rdp_computer.insert(0, p['computer'])
            self.rdp_resolution.set(p['resolution'])
            if p['admin']:
                self.rdp_admin.select()
            else:
                self.rdp_admin.deselect()

    def delete_rdp_profile(self):
        current = self.rdp_profiles_menu.get()
        if current in self.saved_rdp_profiles:
            del self.saved_rdp_profiles[current]
            self.rdp_profiles_menu.configure(values=list(self.saved_rdp_profiles.keys()) or ["(none)"])
            self.log(f"Deleted RDP profile: {current}")

    def run(self):
        """Run the application"""
        self.root.mainloop()


def main():
    """Main entry point"""
    app = REGWinadminGUI()
    app.run()


if __name__ == "__main__":
    main()
