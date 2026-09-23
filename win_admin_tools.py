"""
LazyWinAdmin - Windows Administration Tools
Modern implementations for Windows 11 & Server 2022+
"""

import subprocess
import socket
import winreg
import json
import psutil
import platform
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WindowsAdminTools:
    """Modern Windows administration tools for Windows 11 and Server 2022+"""
    
    def __init__(self, computer_name: str = "localhost", username: str = None, password: str = None):
        """
        Initialize Windows Admin Tools
        
        Args:
            computer_name: Target computer name (default: localhost)
            username: Username for remote authentication (optional)
            password: Password for remote authentication (optional)
        """
        self.computer_name = computer_name
        self.is_local = computer_name.lower() in ["localhost", ".", "127.0.0.1"]
        self.username = username
        self.password = password
        self.credential = None
        
        # Create PSCredential object if username and password provided
        if username and password and not self.is_local:
            self._setup_credentials()
    
    def _setup_credentials(self):
        """Setup PowerShell credential object"""
        # This creates a secure credential string for PowerShell
        self.credential = f"-Credential (New-Object System.Management.Automation.PSCredential('{self.username}', (ConvertTo-SecureString '{self.password}' -AsPlainText -Force)))"
        
    def run_powershell(self, command: str, remote: bool = False, timeout: int = 30) -> Tuple[bool, str]:
        """
        Execute PowerShell command (modern approach for Windows 11)

        Args:
            command: PowerShell command to execute
            remote: Execute on remote computer
            timeout: Command timeout in seconds

        Returns:
            Tuple of (success, output)
        """
        try:
            if remote and not self.is_local:
                # Use PowerShell remoting (modern method)
                if self.credential:
                    ps_command = f'Invoke-Command -ComputerName {self.computer_name} {self.credential} -ScriptBlock {{{command}}}'
                else:
                    ps_command = f'Invoke-Command -ComputerName {self.computer_name} -ScriptBlock {{{command}}}'
            else:
                ps_command = command

            # Use PowerShell 7+ if available, fallback to Windows PowerShell
            powershell_exe = self._get_powershell_path()

            result = subprocess.run(
                [powershell_exe, '-NoProfile', '-NonInteractive', '-Command', ps_command],
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode == 0:
                return True, result.stdout
            else:
                # PS7 sometimes returns non-zero exit code but valid stdout
                # (e.g., Get-Service with protected services produces warnings but valid output)
                if result.stdout and result.stdout.strip() and not result.stderr.strip():
                    logger.warning(f"PowerShell returned non-zero exit code ({result.returncode}) but produced valid stdout with no stderr - treating as success")
                    return True, result.stdout
                logger.error(f"PowerShell error: {result.stderr}")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            logger.error(f"PowerShell execution error: {str(e)}")
            return False, str(e)
    
    def _get_powershell_path(self) -> str:
        """Get the best available PowerShell executable"""
        # Try PowerShell 7+ first (modern)
        pwsh_paths = [
            r"C:\Program Files\PowerShell\7\pwsh.exe",
            r"C:\Program Files\PowerShell\7-preview\pwsh.exe",
        ]
        
        for path in pwsh_paths:
            if Path(path).exists():
                return path
        
        # Fallback to Windows PowerShell
        return "powershell.exe"
    
    def test_connection(self, port: int = 135, timeout: int = 3) -> bool:
        """
        Test network connection to computer
        
        Args:
            port: Port to test (default: 135 for RPC)
            timeout: Connection timeout in seconds
            
        Returns:
            True if connection successful
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((self.computer_name, port))
            sock.close()
            return result == 0
        except Exception as e:
            logger.error(f"Connection test error: {str(e)}")
            return False
    
    def test_tcp_port(self, port: int, timeout: int = 3) -> Dict[str, Any]:
        """
        Test if TCP port is open
        
        Args:
            port: Port number to test
            timeout: Connection timeout
            
        Returns:
            Dictionary with status information
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((self.computer_name, port))
            sock.close()
            
            status = "Open" if result == 0 else "Closed/Filtered"
            
            return {
                'computer': self.computer_name,
                'port': port,
                'status': status,
                'open': result == 0,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'computer': self.computer_name,
                'port': port,
                'status': 'Error',
                'open': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get comprehensive system information (Windows 11 optimized)
        
        Returns:
            Dictionary with system information
        """
        if self.is_local:
            return self._get_local_system_info()
        else:
            return self._get_remote_system_info()
    
    def _get_local_system_info(self) -> Dict[str, Any]:
        """Get system information for local computer"""
        try:
            info = {
                'hostname': platform.node(),
                'os': platform.system(),
                'os_version': platform.version(),
                'os_release': platform.release(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'cpu_count': psutil.cpu_count(logical=False),
                'cpu_count_logical': psutil.cpu_count(logical=True),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'memory_percent': psutil.virtual_memory().percent,
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                'uptime': str(datetime.now() - datetime.fromtimestamp(psutil.boot_time())),
            }
            
            # Get Windows-specific info via PowerShell
            success, output = self.run_powershell("Get-ComputerInfo | Select-Object WindowsProductName,WindowsVersion,OsBuildNumber,OsArchitecture | ConvertTo-Json")
            if success:
                try:
                    win_info = json.loads(output)
                    info.update(win_info)
                except json.JSONDecodeError:
                    pass
            
            return info
        except Exception as e:
            logger.error(f"Error getting system info: {str(e)}")
            return {'error': str(e)}
    
    def _get_remote_system_info(self) -> Dict[str, Any]:
        """Get system information for remote computer"""
        command = "Get-ComputerInfo | ConvertTo-Json"
        success, output = self.run_powershell(command, remote=True)
        
        if success:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                return {'error': 'Failed to parse system info'}
        return {'error': output}
    
    def get_uptime(self) -> Optional[timedelta]:
        """
        Get system uptime (modern method using CIM)
        
        Returns:
            timedelta object representing uptime
        """
        try:
            if self.is_local:
                boot_time = datetime.fromtimestamp(psutil.boot_time())
                return datetime.now() - boot_time
            else:
                # Use PowerShell for remote
                command = "(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime | ConvertTo-Json"
                success, output = self.run_powershell(command, remote=True)
                
                if success:
                    uptime_data = json.loads(output)
                    return timedelta(
                        days=uptime_data.get('Days', 0),
                        hours=uptime_data.get('Hours', 0),
                        minutes=uptime_data.get('Minutes', 0),
                        seconds=uptime_data.get('Seconds', 0)
                    )
        except Exception as e:
            logger.error(f"Error getting uptime: {str(e)}")
            return None
    
    def format_uptime(self, uptime: timedelta) -> str:
        """Format uptime for display"""
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{days} Days, {hours} Hours, {minutes} Minutes, {seconds} Seconds"
    
    def set_rdp_state(self, enable: bool) -> Tuple[bool, str]:
        """
        Enable or disable Remote Desktop (modern Windows 11 method)
        
        Args:
            enable: True to enable RDP, False to disable
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if enable:
                # Modern method for Windows 11: Use PowerShell with firewall rule
                commands = [
                    'Set-ItemProperty -Path "HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server" -Name "fDenyTSConnections" -Value 0',
                    'Enable-NetFirewallRule -DisplayGroup "Remote Desktop"',
                    'Set-ItemProperty -Path "HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp" -Name "UserAuthentication" -Value 1'
                ]
                message = "Remote Desktop enabled successfully"
            else:
                commands = [
                    'Set-ItemProperty -Path "HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server" -Name "fDenyTSConnections" -Value 1',
                    'Disable-NetFirewallRule -DisplayGroup "Remote Desktop"'
                ]
                message = "Remote Desktop disabled successfully"
            
            for command in commands:
                success, output = self.run_powershell(command, remote=not self.is_local)
                if not success:
                    return False, f"Failed to configure RDP: {output}"
            
            return True, message
            
        except Exception as e:
            logger.error(f"Error setting RDP state: {str(e)}")
            return False, str(e)
    
    def get_rdp_status(self) -> Dict[str, Any]:
        """
        Get current RDP status (modern method)
        
        Returns:
            Dictionary with RDP configuration
        """
        try:
            command = '''
            $rdp = Get-ItemProperty -Path "HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server" -Name "fDenyTSConnections"
            $nla = Get-ItemProperty -Path "HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp" -Name "UserAuthentication"
            $port = Get-ItemProperty -Path "HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp" -Name "PortNumber"
            
            @{
                Enabled = ($rdp.fDenyTSConnections -eq 0)
                NLA_Enabled = ($nla.UserAuthentication -eq 1)
                Port = $port.PortNumber
            } | ConvertTo-Json
            '''
            
            success, output = self.run_powershell(command, remote=not self.is_local)
            
            if success:
                return json.loads(output)
            else:
                return {'error': output}
                
        except Exception as e:
            logger.error(f"Error getting RDP status: {str(e)}")
            return {'error': str(e)}
    
    def run_gpupdate(self, force: bool = True) -> Tuple[bool, str]:
        """
        Run Group Policy update (modern method)
        
        Args:
            force: Force policy update
            
        Returns:
            Tuple of (success, output)
        """
        command = "gpupdate /force" if force else "gpupdate"
        
        try:
            if self.is_local:
                result = subprocess.run(
                    command.split(),
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                return result.returncode == 0, result.stdout
            else:
                return self.run_powershell(f"Invoke-Command -ComputerName {self.computer_name} -ScriptBlock {{gpupdate /force}}")
        except Exception as e:
            return False, str(e)
    
    def get_services(self, filter_running: bool = False) -> List[Dict[str, Any]]:
        """
        Get list of Windows services (modern CIM method)
        
        Args:
            filter_running: Only return running services
            
        Returns:
            List of service dictionaries
        """
        try:
            if filter_running:
                command = 'Get-Service -ErrorAction SilentlyContinue | Where-Object {$_.Status -eq "Running"} | Select-Object Name,DisplayName,Status,StartType | ConvertTo-Json'
            else:
                command = 'Get-Service -ErrorAction SilentlyContinue | Select-Object Name,DisplayName,Status,StartType | ConvertTo-Json'

            success, output = self.run_powershell(command, remote=not self.is_local, timeout=45)

            if success:
                try:
                    services = json.loads(output)
                    return services if isinstance(services, list) else [services]
                except json.JSONDecodeError:
                    return []
            # If command failed but produced stdout, try parsing it anyway
            if output and output.strip().startswith('['):
                try:
                    services = json.loads(output)
                    return services if isinstance(services, list) else [services]
                except json.JSONDecodeError:
                    pass
            return []
        except Exception as e:
            logger.error(f"Error getting services: {str(e)}")
            return []
    
    def control_service(self, service_name: str, action: str) -> Tuple[bool, str]:
        """
        Control a Windows service
        
        Args:
            service_name: Name of the service
            action: Action to perform (start, stop, restart)
            
        Returns:
            Tuple of (success, message)
        """
        action_map = {
            'start': 'Start-Service',
            'stop': 'Stop-Service',
            'restart': 'Restart-Service'
        }
        
        if action not in action_map:
            return False, f"Invalid action: {action}"
        
        command = f'{action_map[action]} -Name "{service_name}"'
        return self.run_powershell(command, remote=not self.is_local)
    
    def get_processes(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Get running processes (sorted by CPU or memory)
        
        Args:
            top_n: Number of top processes to return
            
        Returns:
            List of process dictionaries
        """
        try:
            if self.is_local:
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
                    try:
                        pinfo = proc.info
                        processes.append({
                            'pid': pinfo['pid'],
                            'name': pinfo['name'],
                            'cpu_percent': pinfo['cpu_percent'],
                            'memory_percent': pinfo['memory_percent'],
                            'memory_mb': pinfo['memory_info'].rss / 1024 / 1024 if pinfo['memory_info'] else 0
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Sort by CPU usage
                processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
                return processes[:top_n]
            else:
                command = f'Get-Process | Sort-Object CPU -Descending | Select-Object -First {top_n} Name,Id,CPU,WorkingSet | ConvertTo-Json'
                success, output = self.run_powershell(command, remote=True)
                
                if success:
                    procs = json.loads(output)
                    return procs if isinstance(procs, list) else [procs]
                return []
        except Exception as e:
            logger.error(f"Error getting processes: {str(e)}")
            return []
    
    def get_disk_info(self) -> List[Dict[str, Any]]:
        """
        Get disk/volume information (modern Storage module method)
        
        Returns:
            List of disk dictionaries
        """
        try:
            command = 'Get-Volume | Where-Object {$_.DriveLetter} | Select-Object DriveLetter,FileSystemLabel,FileSystem,Size,SizeRemaining | ConvertTo-Json'
            success, output = self.run_powershell(command, remote=not self.is_local)
            
            if success:
                disks = json.loads(output)
                result = disks if isinstance(disks, list) else [disks]
                
                # Add percentage calculations
                for disk in result:
                    if disk.get('Size') and disk['Size'] > 0:
                        disk['PercentFree'] = (disk.get('SizeRemaining', 0) / disk['Size']) * 100
                        disk['PercentUsed'] = 100 - disk['PercentFree']
                
                return result
            return []
        except Exception as e:
            logger.error(f"Error getting disk info: {str(e)}")
            return []
    
    def get_network_adapters(self) -> List[Dict[str, Any]]:
        """
        Get network adapter information (modern NetAdapter method)
        
        Returns:
            List of network adapter dictionaries
        """
        try:
            command = 'Get-NetAdapter | Select-Object Name,Status,LinkSpeed,MacAddress,InterfaceDescription | ConvertTo-Json'
            success, output = self.run_powershell(command, remote=not self.is_local)
            
            if success:
                adapters = json.loads(output)
                return adapters if isinstance(adapters, list) else [adapters]
            return []
        except Exception as e:
            logger.error(f"Error getting network adapters: {str(e)}")
            return []
    
    def get_firewall_rules(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get Windows Firewall rules (modern NetSecurity method)
        
        Args:
            enabled_only: Only return enabled rules
            
        Returns:
            List of firewall rule dictionaries
        """
        try:
            if enabled_only:
                command = 'Get-NetFirewallRule | Where-Object {$_.Enabled -eq "True"} | Select-Object DisplayName,Direction,Action,Enabled,Profile | ConvertTo-Json'
            else:
                command = 'Get-NetFirewallRule | Select-Object DisplayName,Direction,Action,Enabled,Profile | ConvertTo-Json'
            
            success, output = self.run_powershell(command, remote=not self.is_local)
            
            if success:
                rules = json.loads(output)
                return rules if isinstance(rules, list) else [rules]
            return []
        except Exception as e:
            logger.error(f"Error getting firewall rules: {str(e)}")
            return []
    
    def get_installed_software(self) -> List[Dict[str, Any]]:
        """
        Get list of installed software from registry (comprehensive method)

        Returns:
            List of installed software dictionaries
        """
        try:
            command = '''
            $paths = @(
                'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',
                'HKLM:\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*'
            )
            Get-ItemProperty $paths -ErrorAction SilentlyContinue |
                Where-Object { $_.DisplayName } |
                Select-Object DisplayName, DisplayVersion, Publisher, InstallDate, EstimatedSize |
                Sort-Object DisplayName |
                ConvertTo-Json
            '''
            success, output = self.run_powershell(command, remote=not self.is_local, timeout=45)

            if success and output.strip():
                try:
                    packages = json.loads(output)
                    return packages if isinstance(packages, list) else [packages]
                except json.JSONDecodeError:
                    return []
            return []
        except Exception as e:
            logger.error(f"Error getting installed software: {str(e)}")
            return []
    
    def get_event_logs(self, log_name: str = "System", max_events: int = 100, level: str = "Error") -> List[Dict[str, Any]]:
        """
        Get Windows Event Logs (modern method)
        
        Args:
            log_name: Event log name (System, Application, Security)
            max_events: Maximum number of events to retrieve
            level: Event level filter (Error, Warning, Information)
            
        Returns:
            List of event dictionaries
        """
        try:
            command = f'Get-WinEvent -LogName {log_name} -MaxEvents {max_events} | Where-Object {{$_.LevelDisplayName -eq "{level}"}} | Select-Object TimeCreated,Id,LevelDisplayName,Message | ConvertTo-Json'
            success, output = self.run_powershell(command, remote=not self.is_local)
            
            if success:
                events = json.loads(output)
                return events if isinstance(events, list) else [events]
            return []
        except Exception as e:
            logger.error(f"Error getting event logs: {str(e)}")
            return []
    
    def restart_computer(self, force: bool = False, delay: int = 0) -> Tuple[bool, str]:
        """
        Restart the computer
        
        Args:
            force: Force restart even if users are logged on
            delay: Delay in seconds before restart
            
        Returns:
            Tuple of (success, message)
        """
        force_flag = "-Force" if force else ""
        command = f"Restart-Computer {force_flag} -Delay {delay}"
        
        return self.run_powershell(command, remote=not self.is_local)
    
    def shutdown_computer(self, force: bool = False) -> Tuple[bool, str]:
        """
        Shutdown the computer
        
        Args:
            force: Force shutdown even if users are logged on
            
        Returns:
            Tuple of (success, message)
        """
        force_flag = "-Force" if force else ""
        command = f"Stop-Computer {force_flag}"
        
        return self.run_powershell(command, remote=not self.is_local)
    
    def generate_password(self, length: int = 16, include_special: bool = True) -> str:
        """
        Generate a secure random password
        
        Args:
            length: Password length
            include_special: Include special characters
            
        Returns:
            Generated password
        """
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits
        if include_special:
            alphabet += string.punctuation
        
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    def get_qwinsta(self) -> List[Dict[str, Any]]:
        """
        Get user sessions (modern query user method)

        Returns:
            List of session dictionaries
        """
        try:
            command = f'query user /server:{self.computer_name}' if not self.is_local else 'query user'
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]
                sessions = []

                for line in lines:
                    parts = line.split()
                    if len(parts) >= 3:
                        session = {
                            'username': parts[0],
                            'session_name': parts[1] if parts[1] != 'console' else 'Console',
                            'id': parts[2] if len(parts) > 2 else '',
                            'state': parts[3] if len(parts) > 3 else '',
                        }
                        sessions.append(session)

                return sessions
            return []
        except Exception as e:
            logger.error(f"Error getting user sessions: {str(e)}")
            return []

    # =========================================================================
    # Event Viewer (Enhanced)
    # =========================================================================

    def get_event_logs_filtered(self, log_name: str = "System", max_events: int = 100,
                                 level: Optional[str] = None, source: Optional[str] = None,
                                 search_text: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get filtered Windows Event Logs with advanced filtering"""
        try:
            filter_parts = [f"LogName='{log_name}'"]
            if level:
                level_map = {'Critical': 1, 'Error': 2, 'Warning': 3, 'Information': 4, 'Verbose': 5}
                if level in level_map:
                    filter_parts.append(f"Level={level_map[level]}")
            if source:
                filter_parts.append(f"ProviderName='{source}'")

            filter_str = "; ".join(filter_parts)
            command = f'Get-WinEvent -FilterHashtable @{{{filter_str}}} -MaxEvents {max_events}'

            if search_text:
                command += f' | Where-Object {{$_.Message -like "*{search_text}*"}}'

            command += ' | Select-Object TimeCreated,Id,LevelDisplayName,ProviderName,Message | ConvertTo-Json'

            success, output = self.run_powershell(command, remote=not self.is_local, timeout=60)

            if success:
                try:
                    events = json.loads(output)
                    return events if isinstance(events, list) else [events]
                except json.JSONDecodeError:
                    return []
            return []
        except Exception as e:
            logger.error(f"Error getting filtered event logs: {str(e)}")
            return []

    # =========================================================================
    # Windows Update
    # =========================================================================

    def get_installed_updates(self) -> List[Dict[str, Any]]:
        """Get installed Windows updates (hotfixes)"""
        try:
            command = 'Get-HotFix | Select-Object HotFixID,Description,InstalledBy,InstalledOn | ConvertTo-Json'
            success, output = self.run_powershell(command, remote=not self.is_local)

            if success:
                try:
                    updates = json.loads(output)
                    return updates if isinstance(updates, list) else [updates]
                except json.JSONDecodeError:
                    return []
            return []
        except Exception as e:
            logger.error(f"Error getting installed updates: {str(e)}")
            return []

    def get_windows_update_status(self) -> Dict[str, Any]:
        """Check for pending Windows updates using COM object"""
        try:
            command = '''
            $session = New-Object -ComObject Microsoft.Update.Session
            $searcher = $session.CreateUpdateSearcher()
            $result = $searcher.Search("IsInstalled=0")
            @{
                PendingCount = $result.Updates.Count
                Updates = @($result.Updates | ForEach-Object {
                    @{ Title = $_.Title; Description = $_.Description; IsDownloaded = $_.IsDownloaded; IsMandatory = $_.IsMandatory }
                })
            } | ConvertTo-Json -Depth 3
            '''
            success, output = self.run_powershell(command, remote=not self.is_local, timeout=120)

            if success:
                try:
                    return json.loads(output)
                except json.JSONDecodeError:
                    return {'error': 'Failed to parse update status'}
            return {'error': output}
        except Exception as e:
            logger.error(f"Error checking update status: {str(e)}")
            return {'error': str(e)}

    def get_update_history(self) -> List[Dict[str, Any]]:
        """Get Windows Update history"""
        try:
            command = '''
            $session = New-Object -ComObject Microsoft.Update.Session
            $searcher = $session.CreateUpdateSearcher()
            $count = $searcher.GetTotalHistoryCount()
            $searcher.QueryHistory(0, [math]::Min($count, 100)) | Select-Object Title,Date,ResultCode,Description | ConvertTo-Json
            '''
            success, output = self.run_powershell(command, remote=not self.is_local, timeout=60)

            if success:
                try:
                    history = json.loads(output)
                    return history if isinstance(history, list) else [history]
                except json.JSONDecodeError:
                    return []
            return []
        except Exception as e:
            logger.error(f"Error getting update history: {str(e)}")
            return []

    # =========================================================================
    # Firewall (Enhanced)
    # =========================================================================

    def get_firewall_rules_filtered(self, direction: Optional[str] = None,
                                     enabled_only: bool = True) -> List[Dict[str, Any]]:
        """Get firewall rules with filtering"""
        try:
            conditions = []
            if enabled_only:
                conditions.append('$_.Enabled -eq "True"')
            if direction and direction != "All":
                dir_val = 1 if direction == "Inbound" else 2
                conditions.append(f'$_.Direction -eq {dir_val}')

            if conditions:
                where_clause = ' | Where-Object {' + ' -and '.join(conditions) + '}'
            else:
                where_clause = ''

            command = f'Get-NetFirewallRule{where_clause} | Select-Object Name,DisplayName,Direction,Action,Enabled,Profile | ConvertTo-Json'
            success, output = self.run_powershell(command, remote=not self.is_local, timeout=60)

            if success:
                try:
                    rules = json.loads(output)
                    return rules if isinstance(rules, list) else [rules]
                except json.JSONDecodeError:
                    return []
            return []
        except Exception as e:
            logger.error(f"Error getting filtered firewall rules: {str(e)}")
            return []

    def set_firewall_rule_state(self, rule_name: str, enabled: bool) -> Tuple[bool, str]:
        """Enable or disable a firewall rule"""
        try:
            action = "Enable-NetFirewallRule" if enabled else "Disable-NetFirewallRule"
            command = f'{action} -DisplayName "{rule_name}"'
            return self.run_powershell(command, remote=not self.is_local)
        except Exception as e:
            logger.error(f"Error setting firewall rule state: {str(e)}")
            return False, str(e)

    def create_firewall_rule(self, name: str, direction: str, action: str,
                              protocol: str, port: str, profile: str = "Any") -> Tuple[bool, str]:
        """Create a new firewall rule"""
        try:
            command = f'New-NetFirewallRule -DisplayName "{name}" -Direction {direction} -Action {action} -Protocol {protocol} -LocalPort {port} -Profile {profile}'
            return self.run_powershell(command, remote=not self.is_local)
        except Exception as e:
            logger.error(f"Error creating firewall rule: {str(e)}")
            return False, str(e)

    # =========================================================================
    # Scheduled Tasks
    # =========================================================================

    def get_scheduled_tasks(self, include_microsoft: bool = False) -> List[Dict[str, Any]]:
        """Get scheduled tasks"""
        try:
            if include_microsoft:
                command = 'Get-ScheduledTask | Select-Object TaskName,TaskPath,State,Description | ConvertTo-Json'
            else:
                command = 'Get-ScheduledTask | Where-Object {$_.TaskPath -notlike "\\Microsoft\\*"} | Select-Object TaskName,TaskPath,State,Description | ConvertTo-Json'
            success, output = self.run_powershell(command, remote=not self.is_local, timeout=60)

            if success:
                try:
                    tasks = json.loads(output)
                    return tasks if isinstance(tasks, list) else [tasks]
                except json.JSONDecodeError:
                    return []
            return []
        except Exception as e:
            logger.error(f"Error getting scheduled tasks: {str(e)}")
            return []

    def set_scheduled_task_state(self, task_name: str, task_path: str, enabled: bool) -> Tuple[bool, str]:
        """Enable or disable a scheduled task"""
        try:
            action = "Enable-ScheduledTask" if enabled else "Disable-ScheduledTask"
            command = f'{action} -TaskName "{task_name}" -TaskPath "{task_path}"'
            return self.run_powershell(command, remote=not self.is_local)
        except Exception as e:
            logger.error(f"Error setting task state: {str(e)}")
            return False, str(e)

    def run_scheduled_task(self, task_name: str, task_path: str) -> Tuple[bool, str]:
        """Run a scheduled task immediately"""
        try:
            command = f'Start-ScheduledTask -TaskName "{task_name}" -TaskPath "{task_path}"'
            return self.run_powershell(command, remote=not self.is_local)
        except Exception as e:
            logger.error(f"Error running scheduled task: {str(e)}")
            return False, str(e)

    def get_scheduled_task_history(self, task_name: str, max_events: int = 20) -> List[Dict[str, Any]]:
        """Get run history for a scheduled task"""
        try:
            command = f'Get-WinEvent -LogName "Microsoft-Windows-TaskScheduler/Operational" -MaxEvents {max_events} | Where-Object {{$_.Message -like "*{task_name}*"}} | Select-Object TimeCreated,Id,Message | ConvertTo-Json'
            success, output = self.run_powershell(command, remote=not self.is_local, timeout=30)

            if success:
                try:
                    events = json.loads(output)
                    return events if isinstance(events, list) else [events]
                except json.JSONDecodeError:
                    return []
            return []
        except Exception as e:
            logger.error(f"Error getting task history: {str(e)}")
            return []

    # =========================================================================
    # Printers
    # =========================================================================

    def get_printers(self) -> List[Dict[str, Any]]:
        """Get installed printers"""
        try:
            command = 'Get-Printer | Select-Object Name,DriverName,PortName,PrinterStatus,Shared,Published | ConvertTo-Json'
            success, output = self.run_powershell(command, remote=not self.is_local)

            if success:
                try:
                    printers = json.loads(output)
                    return printers if isinstance(printers, list) else [printers]
                except json.JSONDecodeError:
                    return []
            return []
        except Exception as e:
            logger.error(f"Error getting printers: {str(e)}")
            return []

    def get_print_jobs(self, printer_name: str) -> List[Dict[str, Any]]:
        """Get print queue for a printer"""
        try:
            command = f'Get-PrintJob -PrinterName "{printer_name}" | Select-Object Id,DocumentName,UserName,SubmittedTime,Size,JobStatus | ConvertTo-Json'
            success, output = self.run_powershell(command, remote=not self.is_local)

            if success:
                try:
                    jobs = json.loads(output)
                    return jobs if isinstance(jobs, list) else [jobs]
                except json.JSONDecodeError:
                    return []
            return []
        except Exception as e:
            logger.error(f"Error getting print jobs: {str(e)}")
            return []

    def remove_print_job(self, printer_name: str, job_id: int) -> Tuple[bool, str]:
        """Remove a specific print job"""
        try:
            command = f'Remove-PrintJob -PrinterName "{printer_name}" -ID {job_id}'
            return self.run_powershell(command, remote=not self.is_local)
        except Exception as e:
            logger.error(f"Error removing print job: {str(e)}")
            return False, str(e)

    def clear_print_queue(self, printer_name: str) -> Tuple[bool, str]:
        """Clear all jobs from a printer queue"""
        try:
            command = f'Get-PrintJob -PrinterName "{printer_name}" | Remove-PrintJob'
            return self.run_powershell(command, remote=not self.is_local)
        except Exception as e:
            logger.error(f"Error clearing print queue: {str(e)}")
            return False, str(e)

    # =========================================================================
    # SMB Shares
    # =========================================================================

    def get_smb_shares(self) -> List[Dict[str, Any]]:
        """Get SMB shares"""
        try:
            command = 'Get-SmbShare | Select-Object Name,Path,Description,CurrentUsers,ShareState | ConvertTo-Json'
            success, output = self.run_powershell(command, remote=not self.is_local)

            if success:
                try:
                    shares = json.loads(output)
                    return shares if isinstance(shares, list) else [shares]
                except json.JSONDecodeError:
                    return []
            return []
        except Exception as e:
            logger.error(f"Error getting SMB shares: {str(e)}")
            return []

    def get_share_permissions(self, share_name: str) -> List[Dict[str, Any]]:
        """Get permissions for an SMB share"""
        try:
            command = f'Get-SmbShareAccess -Name "{share_name}" | Select-Object Name,AccountName,AccessControlType,AccessRight | ConvertTo-Json'
            success, output = self.run_powershell(command, remote=not self.is_local)

            if success:
                try:
                    perms = json.loads(output)
                    return perms if isinstance(perms, list) else [perms]
                except json.JSONDecodeError:
                    return []
            return []
        except Exception as e:
            logger.error(f"Error getting share permissions: {str(e)}")
            return []

    def create_smb_share(self, name: str, path: str, description: str = "") -> Tuple[bool, str]:
        """Create a new SMB share"""
        try:
            command = f'New-SmbShare -Name "{name}" -Path "{path}" -Description "{description}"'
            return self.run_powershell(command, remote=not self.is_local)
        except Exception as e:
            logger.error(f"Error creating SMB share: {str(e)}")
            return False, str(e)

    def remove_smb_share(self, name: str) -> Tuple[bool, str]:
        """Remove an SMB share"""
        try:
            command = f'Remove-SmbShare -Name "{name}" -Force'
            return self.run_powershell(command, remote=not self.is_local)
        except Exception as e:
            logger.error(f"Error removing SMB share: {str(e)}")
            return False, str(e)

    # =========================================================================
    # DNS / DHCP
    # =========================================================================

    def resolve_dns(self, hostname: str) -> List[Dict[str, Any]]:
        """Perform DNS lookup"""
        try:
            command = f'Resolve-DnsName -Name "{hostname}" | Select-Object Name,Type,IPAddress,NameHost,TTL | ConvertTo-Json'
            success, output = self.run_powershell(command, remote=not self.is_local)

            if success:
                try:
                    results = json.loads(output)
                    return results if isinstance(results, list) else [results]
                except json.JSONDecodeError:
                    return []
            return []
        except Exception as e:
            logger.error(f"Error resolving DNS: {str(e)}")
            return []

    def flush_dns_cache(self) -> Tuple[bool, str]:
        """Flush DNS client cache"""
        try:
            return self.run_powershell('Clear-DnsClientCache', remote=not self.is_local)
        except Exception as e:
            logger.error(f"Error flushing DNS cache: {str(e)}")
            return False, str(e)

    def get_dns_cache(self) -> List[Dict[str, Any]]:
        """Get DNS client cache entries"""
        try:
            command = 'Get-DnsClientCache | Select-Object Entry,Name,Type,Data,TimeToLive | ConvertTo-Json'
            success, output = self.run_powershell(command, remote=not self.is_local)

            if success:
                try:
                    entries = json.loads(output)
                    return entries if isinstance(entries, list) else [entries]
                except json.JSONDecodeError:
                    return []
            return []
        except Exception as e:
            logger.error(f"Error getting DNS cache: {str(e)}")
            return []

    def get_dhcp_info(self) -> List[Dict[str, Any]]:
        """Get DHCP lease information"""
        try:
            command = 'Get-NetIPAddress | Where-Object {$_.PrefixOrigin -eq "Dhcp"} | Select-Object InterfaceAlias,IPAddress,PrefixLength,ValidLifetime | ConvertTo-Json'
            success, output = self.run_powershell(command, remote=not self.is_local)

            if success:
                try:
                    leases = json.loads(output)
                    return leases if isinstance(leases, list) else [leases]
                except json.JSONDecodeError:
                    return []
            return []
        except Exception as e:
            logger.error(f"Error getting DHCP info: {str(e)}")
            return []

    def get_dns_servers(self) -> List[Dict[str, Any]]:
        """Get configured DNS servers per interface"""
        try:
            command = 'Get-DnsClientServerAddress | Where-Object {$_.ServerAddresses} | Select-Object InterfaceAlias,ServerAddresses | ConvertTo-Json'
            success, output = self.run_powershell(command, remote=not self.is_local)

            if success:
                try:
                    servers = json.loads(output)
                    return servers if isinstance(servers, list) else [servers]
                except json.JSONDecodeError:
                    return []
            return []
        except Exception as e:
            logger.error(f"Error getting DNS servers: {str(e)}")
            return []

    # =========================================================================
    # Local Users & Groups
    # =========================================================================

    def get_local_users(self) -> List[Dict[str, Any]]:
        """Get local user accounts"""
        try:
            command = 'Get-LocalUser | Select-Object Name,Enabled,Description,LastLogon,PasswordLastSet,PasswordExpires | ConvertTo-Json'
            success, output = self.run_powershell(command, remote=not self.is_local)

            if success:
                try:
                    users = json.loads(output)
                    return users if isinstance(users, list) else [users]
                except json.JSONDecodeError:
                    return []
            return []
        except Exception as e:
            logger.error(f"Error getting local users: {str(e)}")
            return []

    def get_local_groups(self) -> List[Dict[str, Any]]:
        """Get local groups"""
        try:
            command = 'Get-LocalGroup | Select-Object Name,Description,SID | ConvertTo-Json'
            success, output = self.run_powershell(command, remote=not self.is_local)

            if success:
                try:
                    groups = json.loads(output)
                    return groups if isinstance(groups, list) else [groups]
                except json.JSONDecodeError:
                    return []
            return []
        except Exception as e:
            logger.error(f"Error getting local groups: {str(e)}")
            return []

    def get_local_group_members(self, group_name: str) -> List[Dict[str, Any]]:
        """Get members of a local group"""
        try:
            command = f'Get-LocalGroupMember -Group "{group_name}" | Select-Object Name,ObjectClass,PrincipalSource | ConvertTo-Json'
            success, output = self.run_powershell(command, remote=not self.is_local)

            if success:
                try:
                    members = json.loads(output)
                    return members if isinstance(members, list) else [members]
                except json.JSONDecodeError:
                    return []
            return []
        except Exception as e:
            logger.error(f"Error getting group members: {str(e)}")
            return []

    def modify_local_group_membership(self, group_name: str, member_name: str, add: bool = True) -> Tuple[bool, str]:
        """Add or remove a member from a local group"""
        try:
            action = "Add-LocalGroupMember" if add else "Remove-LocalGroupMember"
            command = f'{action} -Group "{group_name}" -Member "{member_name}"'
            return self.run_powershell(command, remote=not self.is_local)
        except Exception as e:
            logger.error(f"Error modifying group membership: {str(e)}")
            return False, str(e)

    def set_local_user_state(self, username: str, enabled: bool) -> Tuple[bool, str]:
        """Enable or disable a local user account"""
        try:
            action = "Enable-LocalUser" if enabled else "Disable-LocalUser"
            command = f'{action} -Name "{username}"'
            return self.run_powershell(command, remote=not self.is_local)
        except Exception as e:
            logger.error(f"Error setting user state: {str(e)}")
            return False, str(e)

    # =========================================================================
    # Environment Variables
    # =========================================================================

    def get_environment_variables(self, scope: str = "Machine") -> Dict[str, str]:
        """Get environment variables for the specified scope"""
        try:
            command = f'[System.Environment]::GetEnvironmentVariables("{scope}") | ConvertTo-Json'
            success, output = self.run_powershell(command, remote=not self.is_local)

            if success:
                try:
                    return json.loads(output)
                except json.JSONDecodeError:
                    return {}
            return {}
        except Exception as e:
            logger.error(f"Error getting environment variables: {str(e)}")
            return {}

    def set_environment_variable(self, name: str, value: str, scope: str = "Machine") -> Tuple[bool, str]:
        """Set an environment variable"""
        try:
            command = f'[System.Environment]::SetEnvironmentVariable("{name}", "{value}", "{scope}")'
            return self.run_powershell(command, remote=not self.is_local)
        except Exception as e:
            logger.error(f"Error setting environment variable: {str(e)}")
            return False, str(e)

    def remove_environment_variable(self, name: str, scope: str = "Machine") -> Tuple[bool, str]:
        """Remove an environment variable"""
        try:
            command = f'[System.Environment]::SetEnvironmentVariable("{name}", $null, "{scope}")'
            return self.run_powershell(command, remote=not self.is_local)
        except Exception as e:
            logger.error(f"Error removing environment variable: {str(e)}")
            return False, str(e)

    # =========================================================================
    # Certificates
    # =========================================================================

    def get_certificates(self, store_path: str = r"Cert:\LocalMachine\My") -> List[Dict[str, Any]]:
        """Get certificates from a certificate store"""
        try:
            command = f'Get-ChildItem {store_path} | Select-Object Thumbprint,Subject,Issuer,NotBefore,NotAfter,HasPrivateKey | ConvertTo-Json'
            success, output = self.run_powershell(command, remote=not self.is_local)

            if success:
                try:
                    certs = json.loads(output)
                    return certs if isinstance(certs, list) else [certs]
                except json.JSONDecodeError:
                    return []
            return []
        except Exception as e:
            logger.error(f"Error getting certificates: {str(e)}")
            return []

    def get_expiring_certificates(self, days: int = 30, store_path: str = r"Cert:\LocalMachine\My") -> List[Dict[str, Any]]:
        """Get certificates expiring within N days"""
        try:
            command = f'Get-ChildItem {store_path} | Where-Object {{$_.NotAfter -lt (Get-Date).AddDays({days})}} | Select-Object Thumbprint,Subject,Issuer,NotAfter | ConvertTo-Json'
            success, output = self.run_powershell(command, remote=not self.is_local)

            if success:
                try:
                    certs = json.loads(output)
                    return certs if isinstance(certs, list) else [certs]
                except json.JSONDecodeError:
                    return []
            return []
        except Exception as e:
            logger.error(f"Error getting expiring certificates: {str(e)}")
            return []

    # =========================================================================
    # Active Directory
    # =========================================================================

    def search_ad_users(self, query: str) -> List[Dict[str, Any]]:
        """Search Active Directory users by name"""
        try:
            command = f'Get-ADUser -Filter "Name -like \'*{query}*\'" -Properties DisplayName,EmailAddress,Enabled,LockedOut,LastLogonDate,PasswordLastSet | Select-Object SamAccountName,DisplayName,EmailAddress,Enabled,LockedOut,LastLogonDate,PasswordLastSet | ConvertTo-Json'
            success, output = self.run_powershell(command, timeout=30)

            if success:
                try:
                    users = json.loads(output)
                    return users if isinstance(users, list) else [users]
                except json.JSONDecodeError:
                    return []
            return [{'error': output}]
        except Exception as e:
            logger.error(f"Error searching AD users: {str(e)}")
            return [{'error': str(e)}]

    def unlock_ad_account(self, username: str) -> Tuple[bool, str]:
        """Unlock an Active Directory user account"""
        try:
            command = f'Unlock-ADAccount -Identity "{username}"'
            return self.run_powershell(command)
        except Exception as e:
            logger.error(f"Error unlocking AD account: {str(e)}")
            return False, str(e)

    def reset_ad_password(self, username: str, new_password: str) -> Tuple[bool, str]:
        """Reset an Active Directory user's password"""
        try:
            command = f'Set-ADAccountPassword -Identity "{username}" -Reset -NewPassword (ConvertTo-SecureString -AsPlainText "{new_password}" -Force)'
            return self.run_powershell(command)
        except Exception as e:
            logger.error(f"Error resetting AD password: {str(e)}")
            return False, str(e)

    def get_ad_groups(self, query: str = "*") -> List[Dict[str, Any]]:
        """Search Active Directory groups"""
        try:
            command = f'Get-ADGroup -Filter "Name -like \'*{query}*\'" -Properties Description | Select-Object Name,GroupScope,GroupCategory,Description | ConvertTo-Json'
            success, output = self.run_powershell(command, timeout=30)

            if success:
                try:
                    groups = json.loads(output)
                    return groups if isinstance(groups, list) else [groups]
                except json.JSONDecodeError:
                    return []
            return [{'error': output}]
        except Exception as e:
            logger.error(f"Error searching AD groups: {str(e)}")
            return [{'error': str(e)}]

    def get_ad_group_members(self, group_name: str) -> List[Dict[str, Any]]:
        """Get members of an AD group"""
        try:
            command = f'Get-ADGroupMember -Identity "{group_name}" | Select-Object Name,SamAccountName,ObjectClass | ConvertTo-Json'
            success, output = self.run_powershell(command, timeout=30)

            if success:
                try:
                    members = json.loads(output)
                    return members if isinstance(members, list) else [members]
                except json.JSONDecodeError:
                    return []
            return [{'error': output}]
        except Exception as e:
            logger.error(f"Error getting AD group members: {str(e)}")
            return [{'error': str(e)}]

    def get_ad_computers(self, query: str = "*") -> List[Dict[str, Any]]:
        """Search Active Directory computer objects"""
        try:
            command = f'Get-ADComputer -Filter "Name -like \'*{query}*\'" -Properties OperatingSystem,LastLogonDate,IPv4Address,Enabled | Select-Object Name,DNSHostName,OperatingSystem,LastLogonDate,IPv4Address,Enabled | ConvertTo-Json'
            success, output = self.run_powershell(command, timeout=30)

            if success:
                try:
                    computers = json.loads(output)
                    return computers if isinstance(computers, list) else [computers]
                except json.JSONDecodeError:
                    return []
            return [{'error': output}]
        except Exception as e:
            logger.error(f"Error searching AD computers: {str(e)}")
            return [{'error': str(e)}]

    def get_ad_ous(self) -> List[Dict[str, Any]]:
        """Get all Organizational Units"""
        try:
            command = 'Get-ADOrganizationalUnit -Filter * | Select-Object Name,DistinguishedName | ConvertTo-Json'
            success, output = self.run_powershell(command, timeout=30)

            if success:
                try:
                    ous = json.loads(output)
                    return ous if isinstance(ous, list) else [ous]
                except json.JSONDecodeError:
                    return []
            return [{'error': output}]
        except Exception as e:
            logger.error(f"Error getting AD OUs: {str(e)}")
            return [{'error': str(e)}]

    # =========================================================================
    # Enhanced Network Tools
    # =========================================================================

    def ping_host(self, target: str, count: int = 4) -> List[Dict[str, Any]]:
        """Ping a host"""
        try:
            command = f'Test-Connection -ComputerName "{target}" -Count {count} | Select-Object Address,Latency,Status | ConvertTo-Json'
            success, output = self.run_powershell(command, timeout=30)

            if success:
                try:
                    results = json.loads(output)
                    return results if isinstance(results, list) else [results]
                except json.JSONDecodeError:
                    return []
            return [{'error': output}]
        except Exception as e:
            logger.error(f"Error pinging host: {str(e)}")
            return [{'error': str(e)}]

    def traceroute(self, target: str) -> Dict[str, Any]:
        """Run traceroute to target"""
        try:
            command = f'Test-NetConnection -ComputerName "{target}" -TraceRoute | Select-Object ComputerName,RemotePort,TraceRoute | ConvertTo-Json'
            success, output = self.run_powershell(command, timeout=60)

            if success:
                try:
                    return json.loads(output)
                except json.JSONDecodeError:
                    return {'error': 'Failed to parse traceroute'}
            return {'error': output}
        except Exception as e:
            logger.error(f"Error running traceroute: {str(e)}")
            return {'error': str(e)}

    def nslookup(self, hostname: str) -> List[Dict[str, Any]]:
        """DNS name resolution lookup"""
        try:
            command = f'Resolve-DnsName -Name "{hostname}" | Select-Object Name,Type,IPAddress,NameHost | ConvertTo-Json'
            success, output = self.run_powershell(command, timeout=15)

            if success:
                try:
                    results = json.loads(output)
                    return results if isinstance(results, list) else [results]
                except json.JSONDecodeError:
                    return []
            return [{'error': output}]
        except Exception as e:
            logger.error(f"Error performing nslookup: {str(e)}")
            return [{'error': str(e)}]

    def get_ip_configuration(self) -> List[Dict[str, Any]]:
        """Get IP configuration (ipconfig equivalent)"""
        try:
            command = 'Get-NetIPConfiguration | Select-Object InterfaceAlias,IPv4Address,IPv6Address,IPv4DefaultGateway,DNSServer | ConvertTo-Json'
            success, output = self.run_powershell(command, remote=not self.is_local)

            if success:
                try:
                    configs = json.loads(output)
                    return configs if isinstance(configs, list) else [configs]
                except json.JSONDecodeError:
                    return []
            return []
        except Exception as e:
            logger.error(f"Error getting IP configuration: {str(e)}")
            return []

    # =========================================================================
    # Enhanced Service Control
    # =========================================================================

    def set_service_startup_type(self, service_name: str, startup_type: str) -> Tuple[bool, str]:
        """Change a service's startup type"""
        try:
            command = f'Set-Service -Name "{service_name}" -StartupType {startup_type}'
            return self.run_powershell(command, remote=not self.is_local)
        except Exception as e:
            logger.error(f"Error setting service startup type: {str(e)}")
            return False, str(e)

    # =========================================================================
    # Enhanced Process Control
    # =========================================================================

    def kill_process(self, pid: int = None, name: str = None) -> Tuple[bool, str]:
        """Kill a process by PID or name"""
        try:
            if pid:
                if self.is_local:
                    try:
                        p = psutil.Process(pid)
                        p.kill()
                        return True, f"Process {pid} terminated"
                    except psutil.NoSuchProcess:
                        return False, f"Process {pid} not found"
                    except psutil.AccessDenied:
                        return False, f"Access denied for process {pid}"
                else:
                    command = f'Stop-Process -Id {pid} -Force'
                    return self.run_powershell(command, remote=True)
            elif name:
                command = f'Stop-Process -Name "{name}" -Force'
                return self.run_powershell(command, remote=not self.is_local)
            else:
                return False, "Provide either PID or process name"
        except Exception as e:
            logger.error(f"Error killing process: {str(e)}")
            return False, str(e)

    # =========================================================================
    # Remote Command Execution
    # =========================================================================

    def run_remote_command(self, command: str, timeout: int = 60) -> Tuple[bool, str]:
        """Execute an arbitrary PowerShell command on the target machine"""
        try:
            return self.run_powershell(command, remote=not self.is_local, timeout=timeout)
        except Exception as e:
            logger.error(f"Error running remote command: {str(e)}")
            return False, str(e)

    # =========================================================================
    # RDP Connection Launch
    # =========================================================================

    def launch_rdp_connection(self, computer: str = None, width: int = 1920, height: int = 1080,
                               admin_mode: bool = False, fullscreen: bool = False) -> Tuple[bool, str]:
        """Launch mstsc.exe to connect via RDP"""
        try:
            target = computer or self.computer_name
            args = ['mstsc.exe', f'/v:{target}']

            if fullscreen:
                args.append('/f')
            else:
                args.append(f'/w:{width}')
                args.append(f'/h:{height}')

            if admin_mode:
                args.append('/admin')

            subprocess.Popen(args)
            return True, f"RDP session launched to {target}"
        except Exception as e:
            logger.error(f"Error launching RDP: {str(e)}")
            return False, str(e)


def format_bytes(bytes_value: int) -> str:
    """Format bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def format_json(data: Any, indent: int = 2) -> str:
    """Format data as JSON string"""
    try:
        return json.dumps(data, indent=indent, default=str)
    except Exception:
        return str(data)


def export_to_csv(data: List[Dict[str, Any]], filepath: str) -> Tuple[bool, str]:
    """Export list of dictionaries to CSV file"""
    import csv
    try:
        if not data:
            return False, "No data to export"

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        return True, filepath
    except Exception as e:
        return False, str(e)
