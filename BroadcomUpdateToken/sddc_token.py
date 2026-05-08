__autor__ = "Joshua Contreras alias 'Josh'"
import re
import subprocess
import os

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def menu():
    print("\n+------------------------------------------------------------+")
    print("|                        Main Menu                           |")
    print("+------------------------------------------------------------+")
    print("| 1 | SDDC Manager Depot (online method only)                |")
    print("| 2 | Async Patch Tool (online method only)                  |")
    print("+------------------------------------------------------------+")


download_token = input(f"{bcolors.OKGREEN}enter your download token: {bcolors.RED}")
token_parameter = f"/{download_token}/PROD"

default_path_sddc = "/opt/vmware/vcf/lcm/lcm-app/conf/application-prod.properties"
default_path_apt = "/home/vcf/asyncPatchTool/conf/application-asyncpatch.properties"

# List of target parameters
BRC_adapter = "lcm.depot.adapter.host="
token = "lcm.depot.adapter.remote.rootDir="
third_property = "lcm.depot.adapter.remote.repoDir="
forth_property = "lcm.depot.adapter.remote.lcmManifestDir="
fifth_property = "lcm.depot.adapter.remote.lcmProductVersionCatalogDir="

# List of target values
BRC_adapter_value = "dl.broadcom.com"
third_property_value = "/COMP/SDDC_MANAGER_VCF"
forth_property_value = "/COMP/SDDC_MANAGER_VCF/lcm/manifest"
fifth_property_value = "/COMP/SDDC_MANAGER_VCF/lcm/productVersionCatalog"

# Read the file content
with open(default_path_sddc, 'r') as file:
    content = file.read()

# Replace or add properties
def set_property_sddc(content, key, value):
    pattern = rf"^{re.escape(key)}.*$"
    replacement = f"{key}{value}"
    if re.search(pattern, content, flags=re.MULTILINE):
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    else:
        content += f"\n{replacement}"
    return content

def set_property_apt(content, key, value):

    if os.path.exists(default_path_apt):
        print("updating application-asyncpatch.properties file with specified parameters...")
        pattern = rf"^{re.escape(key)}.*$"
        replacement = f"{key}{value}"
        if re.search(pattern, content, flags=re.MULTILINE):
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            with open(default_path_apt, 'w') as file:
                file.write(content)
        else:
            content += f"\n{replacement}"
    return content


def main():
    print(f"{bcolors.OKGREEN}Welcome to the SDDC Manager Depot Configuration Tool!{bcolors.ENDC}")
    while True:
        try:
            option = int(input("enter your option: "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue

        if option == 1:
            menu()
            download_token = input(f"{bcolors.OKGREEN}enter your download token: {bcolors.RED}")
            token_parameter = f"/{download_token}/PROD"
            try:
                with open(default_path_sddc, 'r') as file:
                    content = file.read()
            except FileNotFoundError:
                print(f"{bcolors.WARNING}File {default_path_sddc} not found. Creating new one.{bcolors.ENDC}")
                content = ""
            content = set_property_sddc(content, BRC_adapter, BRC_adapter_value)
            content = set_property_sddc(content, token, token_parameter)
            content = set_property_sddc(content, third_property, third_property_value)
            content = set_property_sddc(content, forth_property, forth_property_value)
            content = set_property_sddc(content, fifth_property, fifth_property_value)
            with open(default_path_sddc, 'w') as file:
                file.write(content)
            # Restart lcm service
            command_sddc = ["systemctl", "restart", "lcm"]
            try:
                print(f"{bcolors.OKGREEN}restarting lcm service, please wait...{bcolors.ENDC}")
                subprocess.run(command_sddc, check=True, universal_newlines=True)
                print(f"LCM service restarted successfully.{bcolors.OKGREEN}")
            except subprocess.CalledProcessError as e:
                print(f"Error restarting LCM service: {e}")
        elif option == 2:
            menu()
            download_token = input(f"{bcolors.OKGREEN}enter your download token: {bcolors.RED}")
            token_parameter = f"/{download_token}/PROD"
            try:
                with open(default_path_apt, 'r') as file:
                    content = file.read()
            except FileNotFoundError:
                print(f"{bcolors.WARNING}File {default_path_apt} not found.")
                content = ""
            content = set_property_apt(content, BRC_adapter, BRC_adapter_value)
            content = set_property_apt(content, token, token_parameter)
            content = set_property_apt(content, third_property, third_property_value)
            content = set_property_apt(content, forth_property, forth_property_value)
            content = set_property_apt(content, fifth_property, fifth_property_value)
            with open(default_path_apt, 'w') as file:
                file.write(content)
            # Restart lcm service if needed
            command_apt = ["systemctl", "restart", "lcm"] 
            try:
                print(f"{bcolors.OKGREEN}restarting async patch tool service, please wait...{bcolors.ENDC}")
                subprocess.run(command_apt, check=True, universal_newlines=True)
                print(f"Async Patch Tool service restarted successfully.{bcolors.OKGREEN}")
            except subprocess.CalledProcessError as e:
                print(f"Error restarting Async Patch Tool service: {e}")
        else:
            print("Invalid option. Please select 1 or 2.")


if __name__ == "__main__":
    main()