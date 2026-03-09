import subprocess
from langchain.tools import tool

class ArchTools:
    @tool("check_system_logs")
    def check_system_logs(service_name: str):
        """Queries journalctl for errors in a specific service."""
        result = subprocess.run(
            ['journalctl', '-u', service_name, '-n', '20', '--no-pager'],
            capture_output=True, text=True
        )
        return result.stdout

    @tool("check_package_status")
    def check_package_status(package_name: str):
        """Runs pacman -Q to verify if a package is installed and its version."""
        result = subprocess.run(['pacman', '-Q', package_name], capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else "Package not found."

    @tool("manage_service")
    def manage_service(service_name: str, action: str):
        """
        Manages a systemd service. 
        Actions allowed: 'start', 'stop', 'restart'.
        Example: manage_service('bluetooth', 'restart')
        """
        # Note: This might require sudo/polkit permissions on a real system
        result = subprocess.run(['sudo', 'systemctl', action, service_name], capture_output=True, text=True)
        if result.returncode == 0:
            return f"Successfully executed {action} on {service_name}."
        return f"Failed to {action} {service_name}: {result.stderr}"

    @tool("install_package")
    def install_package(package_name: str):
        """Installs a package using pacman."""
        # Note: High stakes! Always used with human_input=True in the task.
        result = subprocess.run(['sudo', 'pacman', '-S', '--noconfirm', package_name], capture_output=True, text=True)
        if result.returncode == 0:
            return f"Successfully installed {package_name}."
        return f"Failed to install {package_name}: {result.stderr}"
