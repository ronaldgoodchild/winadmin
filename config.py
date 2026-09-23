"""
LazyWinAdmin - Configuration
Modern Windows Administration Tool for Windows 11/Server 2022+
"""

import os
from pathlib import Path

# Application Info
APP_NAME = "REGWinadmin"
APP_VERSION = "3.0.0"
APP_AUTHOR = "Ronald Goodchild"
APP_DESCRIPTION = "Windows 11 & Server 2022+ Administration Tool"

# UI Configuration
WINDOW_TITLE = f"{APP_NAME} v{APP_VERSION}"
WINDOW_SIZE = "1600x900"
THEME = "dark-blue"  # CustomTkinter theme

# Default Values
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_RDP_PORT = 3389
DEFAULT_WINRM_PORT = 5985
DEFAULT_WINRM_HTTPS_PORT = 5986

# Registry Paths (Modern Windows 11/Server 2022)
REGISTRY_PATHS = {
    'rdp_enable': r'SYSTEM\CurrentControlSet\Control\Terminal Server',
    'rdp_firewall': r'SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp',
    'windows_update': r'SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate',
}

# Registry Values
REGISTRY_VALUES = {
    'rdp_deny': 'fDenyTSConnections',
    'rdp_nla': 'UserAuthentication',  # Network Level Authentication
    'rdp_port': 'PortNumber',
}

# Modern PowerShell Commands (Windows 11/Server 2022+)
POWERSHELL_COMMANDS = {
    'system_info': 'Get-ComputerInfo | ConvertTo-Json',
    'uptime': '(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime | Select-Object Days,Hours,Minutes,Seconds | ConvertTo-Json',
    'services': 'Get-Service | Select-Object Name,Status,StartType,DisplayName | ConvertTo-Json',
    'processes': 'Get-Process | Select-Object Name,Id,CPU,WorkingSet | ConvertTo-Json',
    'network_adapters': 'Get-NetAdapter | Select-Object Name,Status,LinkSpeed,MacAddress | ConvertTo-Json',
    'firewall_rules': 'Get-NetFirewallRule | Select-Object DisplayName,Enabled,Direction,Action | ConvertTo-Json',
    'rdp_enable': 'Set-ItemProperty -Path "HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server" -Name "fDenyTSConnections" -Value 0; Enable-NetFirewallRule -DisplayGroup "Remote Desktop"',
    'rdp_disable': 'Set-ItemProperty -Path "HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server" -Name "fDenyTSConnections" -Value 1; Disable-NetFirewallRule -DisplayGroup "Remote Desktop"',
    'rdp_status': 'Get-ItemProperty -Path "HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server" -Name "fDenyTSConnections" | ConvertTo-Json',
    'gpupdate': 'gpupdate /force',
    'windows_update_check': 'Get-WindowsUpdate | ConvertTo-Json',
    'windows_update_install': 'Install-WindowsUpdate -AcceptAll -AutoReboot',
    'disk_info': 'Get-Disk | Select-Object Number,FriendlyName,OperationalStatus,TotalSize,PartitionStyle | ConvertTo-Json',
    'volume_info': 'Get-Volume | Select-Object DriveLetter,FileSystemLabel,FileSystem,SizeRemaining,Size | ConvertTo-Json',
}

# WinRM Configuration
WINRM_CONFIG = {
    'transport': 'ntlm',
    'server_cert_validation': 'ignore',
    'message_encryption': 'auto',
}

# Logging
LOG_DIRECTORY = Path.home() / "REGWinadmin" / "logs"
LOG_FILE = LOG_DIRECTORY / "regwinadmin.log"

# Create log directory if it doesn't exist
LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)

# Color Scheme
COLORS = {
    'success': '#4CAF50',
    'error': '#F44336',
    'warning': '#FF9800',
    'info': '#2196F3',
    'primary': '#1976D2',
}

# Event Log Configuration
EVENT_LEVELS = {
    'Critical': 1,
    'Error': 2,
    'Warning': 3,
    'Information': 4,
    'Verbose': 5,
}

EVENT_LOG_NAMES = ["System", "Application", "Security", "Setup"]

# Service Startup Types
SERVICE_STARTUP_TYPES = ["Automatic", "Manual", "Disabled", "AutomaticDelayedStart"]

# Firewall Configuration
FIREWALL_PROFILES = ["Any", "Domain", "Private", "Public"]
FIREWALL_DIRECTIONS = ["Inbound", "Outbound"]
FIREWALL_ACTIONS = ["Allow", "Block"]
FIREWALL_PROTOCOLS = ["TCP", "UDP", "Any"]

# Certificate Stores
CERT_STORES = {
    'Local Machine - Personal': r'Cert:\LocalMachine\My',
    'Local Machine - Root': r'Cert:\LocalMachine\Root',
    'Current User - Personal': r'Cert:\CurrentUser\My',
    'Current User - Root': r'Cert:\CurrentUser\Root',
}

# RDP Connection Defaults
RDP_RESOLUTIONS = ["1024x768", "1280x1024", "1920x1080", "Fullscreen"]
RDP_DEFAULTS = {
    'width': 1920,
    'height': 1080,
    'color_depth': 32,
    'admin_mode': False,
}

# Export Configuration
EXPORT_DIRECTORY = Path.home() / "REGWinadmin" / "exports"
EXPORT_DIRECTORY.mkdir(parents=True, exist_ok=True)

# Remote Command History
REMOTE_COMMAND_HISTORY_MAX = 50

# Winget Software Catalog for Quick Install
WINGET_SOFTWARE_CATALOG = {
    'Browsers': {
        'Google Chrome': {'id': 'Google.Chrome', 'description': 'Fast, secure web browser by Google'},
        'Mozilla Firefox': {'id': 'Mozilla.Firefox', 'description': 'Fast, private web browser'},
        'Microsoft Edge': {'id': 'Microsoft.Edge', 'description': 'Microsoft\'s modern web browser'},
        'Brave Browser': {'id': 'Brave.Brave', 'description': 'Privacy-focused browser with ad blocking'},
        'Opera': {'id': 'Opera.Opera', 'description': 'Fast browser with built-in VPN'},
        'Vivaldi': {'id': 'VivaldiTechnologies.Vivaldi', 'description': 'Highly customizable browser'},
    },
    
    'Remote Access & Communication': {
        'TeamViewer': {'id': 'TeamViewer.TeamViewer', 'description': 'Remote desktop and support software'},
        'AnyDesk': {'id': 'AnyDeskSoftwareGmbH.AnyDesk', 'description': 'Fast remote desktop application'},
        'Chrome Remote Desktop': {'id': 'Google.ChromeRemoteDesktop', 'description': 'Remote desktop access via Chrome'},
        'TightVNC': {'id': 'GlavSoft.TightVNC', 'description': 'Free remote control software'},
        'RealVNC Viewer': {'id': 'RealVNC.VNCViewer', 'description': 'VNC remote access viewer'},
        'Microsoft Teams': {'id': 'Microsoft.Teams', 'description': 'Business communication platform'},
        'Zoom': {'id': 'Zoom.Zoom', 'description': 'Video conferencing software'},
        'Slack': {'id': 'SlackTechnologies.Slack', 'description': 'Team collaboration platform'},
        'Discord': {'id': 'Discord.Discord', 'description': 'Voice, video and text chat'},
        'Skype': {'id': 'Microsoft.Skype', 'description': 'Video calling and messaging'},
    },
    
    'System Utilities': {
        '7-Zip': {'id': '7zip.7zip', 'description': 'File archiver with high compression'},
        'WinRAR': {'id': 'RARLab.WinRAR', 'description': 'Powerful archive manager'},
        'PowerToys': {'id': 'Microsoft.PowerToys', 'description': 'Windows system utilities'},
        'Everything': {'id': 'voidtools.Everything', 'description': 'Ultra-fast file search'},
        'TreeSize Free': {'id': 'JAMSoftware.TreeSize.Free', 'description': 'Disk space analyzer'},
        'CCleaner': {'id': 'Piriform.CCleaner', 'description': 'System cleaning and optimization'},
        'Revo Uninstaller': {'id': 'RevoUninstaller.RevoUninstaller', 'description': 'Complete software removal'},
        'Process Explorer': {'id': 'Microsoft.Sysinternals.ProcessExplorer', 'description': 'Advanced task manager'},
        'Autoruns': {'id': 'Microsoft.Sysinternals.Autoruns', 'description': 'Startup program manager'},
        'CPU-Z': {'id': 'CPUID.CPU-Z', 'description': 'System information tool'},
        'HWiNFO': {'id': 'REALiX.HWiNFO', 'description': 'Hardware analysis tool'},
        'CrystalDiskInfo': {'id': 'CrystalDewWorld.CrystalDiskInfo', 'description': 'HDD/SSD health monitor'},
        'Speccy': {'id': 'Piriform.Speccy', 'description': 'System information tool'},
    },
    
    'File Management & Transfer': {
        'WinSCP': {'id': 'WinSCP.WinSCP', 'description': 'SFTP and FTP client'},
        'FileZilla': {'id': 'TimKosse.FileZilla.Client', 'description': 'FTP client'},
        'Total Commander': {'id': 'Ghisler.TotalCommander', 'description': 'File manager'},
        'ShareX': {'id': 'ShareX.ShareX', 'description': 'Screenshot and file sharing'},
        'Dropbox': {'id': 'Dropbox.Dropbox', 'description': 'Cloud storage and sync'},
        'Google Drive': {'id': 'Google.GoogleDrive', 'description': 'Cloud storage by Google'},
        'OneDrive': {'id': 'Microsoft.OneDrive', 'description': 'Microsoft cloud storage'},
    },
    
    'Development Tools': {
        'Visual Studio Code': {'id': 'Microsoft.VisualStudioCode', 'description': 'Code editor by Microsoft'},
        'Git': {'id': 'Git.Git', 'description': 'Distributed version control'},
        'GitHub Desktop': {'id': 'GitHub.GitHubDesktop', 'description': 'GitHub desktop client'},
        'Python': {'id': 'Python.Python.3.12', 'description': 'Python programming language'},
        'Node.js': {'id': 'OpenJS.NodeJS', 'description': 'JavaScript runtime'},
        'Docker Desktop': {'id': 'Docker.DockerDesktop', 'description': 'Container platform'},
        'Notepad++': {'id': 'Notepad++.Notepad++', 'description': 'Advanced text editor'},
        'Sublime Text': {'id': 'SublimeHQ.SublimeText.4', 'description': 'Sophisticated text editor'},
        'IntelliJ IDEA Community': {'id': 'JetBrains.IntelliJIDEA.Community', 'description': 'Java IDE'},
        'PyCharm Community': {'id': 'JetBrains.PyCharm.Community', 'description': 'Python IDE'},
        'Postman': {'id': 'Postman.Postman', 'description': 'API development platform'},
        'Windows Terminal': {'id': 'Microsoft.WindowsTerminal', 'description': 'Modern terminal application'},
        'PuTTY': {'id': 'PuTTY.PuTTY', 'description': 'SSH and telnet client'},
        'WinMerge': {'id': 'WinMerge.WinMerge', 'description': 'File comparison tool'},
    },
    
    'Media Players & Editing': {
        'VLC Media Player': {'id': 'VideoLAN.VLC', 'description': 'Multimedia player'},
        'K-Lite Codec Pack': {'id': 'CodecGuide.K-LiteCodecPack.Standard', 'description': 'Media codec collection'},
        'Audacity': {'id': 'Audacity.Audacity', 'description': 'Audio editor'},
        'HandBrake': {'id': 'HandBrake.HandBrake', 'description': 'Video transcoder'},
        'OBS Studio': {'id': 'OBSProject.OBSStudio', 'description': 'Video recording and streaming'},
        'GIMP': {'id': 'GIMP.GIMP', 'description': 'Image editor'},
        'Paint.NET': {'id': 'dotPDN.PaintDotNet', 'description': 'Image and photo editor'},
        'Inkscape': {'id': 'Inkscape.Inkscape', 'description': 'Vector graphics editor'},
        'Blender': {'id': 'BlenderFoundation.Blender', 'description': '3D creation suite'},
        'Spotify': {'id': 'Spotify.Spotify', 'description': 'Music streaming service'},
        'iTunes': {'id': 'Apple.iTunes', 'description': 'Media player by Apple'},
    },
    
    'Office & Productivity': {
        'LibreOffice': {'id': 'TheDocumentFoundation.LibreOffice', 'description': 'Free office suite'},
        'Adobe Acrobat Reader': {'id': 'Adobe.Acrobat.Reader.64-bit', 'description': 'PDF reader'},
        'Foxit PDF Reader': {'id': 'Foxit.FoxitReader', 'description': 'PDF reader and editor'},
        'Sumatra PDF': {'id': 'SumatraPDF.SumatraPDF', 'description': 'Lightweight PDF reader'},
        'Notion': {'id': 'Notion.Notion', 'description': 'All-in-one workspace'},
        'Obsidian': {'id': 'Obsidian.Obsidian', 'description': 'Knowledge base and note-taking'},
        'Evernote': {'id': 'Evernote.Evernote', 'description': 'Note-taking application'},
        'OneNote': {'id': 'Microsoft.Office.OneNote', 'description': 'Digital note-taking'},
    },
    
    'Security & Privacy': {
        'Bitwarden': {'id': 'Bitwarden.Bitwarden', 'description': 'Password manager'},
        'KeePass': {'id': 'KeePassXCTeam.KeePassXC', 'description': 'Password manager'},
        '1Password': {'id': 'AgileBits.1Password', 'description': 'Password manager'},
        'Malwarebytes': {'id': 'Malwarebytes.Malwarebytes', 'description': 'Anti-malware software'},
        'VeraCrypt': {'id': 'IDRIX.VeraCrypt', 'description': 'Disk encryption software'},
    },
    
    'Download Managers & Torrents': {
        'qBittorrent': {'id': 'qBittorrent.qBittorrent', 'description': 'BitTorrent client'},
        'Internet Download Manager': {'id': 'Tonec.InternetDownloadManager', 'description': 'Download accelerator'},
        'Free Download Manager': {'id': 'SoftDeluxe.FreeDownloadManager', 'description': 'Download manager'},
        'Transmission': {'id': 'Transmission.Transmission', 'description': 'BitTorrent client'},
    },
    
    'Gaming & Platforms': {
        'Steam': {'id': 'Valve.Steam', 'description': 'Gaming platform'},
        'Epic Games Launcher': {'id': 'EpicGames.EpicGamesLauncher', 'description': 'Epic Games store'},
        'GOG Galaxy': {'id': 'GOG.Galaxy', 'description': 'GOG game launcher'},
        'EA App': {'id': 'ElectronicArts.EADesktop', 'description': 'EA games launcher'},
        'Discord': {'id': 'Discord.Discord', 'description': 'Gaming communication'},
    },
    
    'Virtualization': {
        'VirtualBox': {'id': 'Oracle.VirtualBox', 'description': 'Virtual machine platform'},
        'VMware Workstation Player': {'id': 'VMware.WorkstationPlayer', 'description': 'Virtual machine software'},
    },
    
    'Network Tools': {
        'Wireshark': {'id': 'WiresharkFoundation.Wireshark', 'description': 'Network protocol analyzer'},
        'Advanced IP Scanner': {'id': 'Famatech.AdvancedIPScanner', 'description': 'Network scanner'},
        'Angry IP Scanner': {'id': 'angryziber.AngryIPScanner', 'description': 'Fast IP scanner'},
        'Nmap': {'id': 'Insecure.Nmap', 'description': 'Network security scanner'},
    },
    
    'System Monitoring': {
        'HWMonitor': {'id': 'CPUID.HWMonitor', 'description': 'Hardware monitoring'},
        'MSI Afterburner': {'id': 'Guru3D.Afterburner', 'description': 'GPU overclocking utility'},
        'Open Hardware Monitor': {'id': 'openhardwaremonitor.openhardwaremonitor', 'description': 'Hardware sensors monitor'},
    },
}

# Winget Commands
WINGET_COMMANDS = {
    'search': 'winget search "{package_id}"',
    'install': 'winget install --id {package_id} --exact --silent --accept-package-agreements --accept-source-agreements',
    'install_interactive': 'winget install --id {package_id} --exact --interactive',
    'uninstall': 'winget uninstall --id {package_id} --exact --silent',
    'upgrade': 'winget upgrade --id {package_id} --exact --silent --accept-package-agreements --accept-source-agreements',
    'upgrade_all': 'winget upgrade --all --silent --accept-package-agreements --accept-source-agreements',
    'list': 'winget list',
    'show': 'winget show --id {package_id}',
}
