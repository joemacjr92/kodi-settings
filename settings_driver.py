import requests
import json

# --- Kodi Connection Details ---
KODI_IP = "10.0.0.164"  # Replace with your Kodi device's IP address
KODI_PORT = "8080"      # Default port is usually 8080
USERNAME = "kodi"       # Replace with your Kodi web interface username
PASSWORD = "kodi"       # Replace with your Kodi web interface password

# The JSON-RPC endpoint URL
URL = f"http://{KODI_IP}:{KODI_PORT}/jsonrpc"

# --- Settings Collection ---
# Define the settings you want to expose to the user here.
# Structure: "Display Name": {"id": "kodi.setting.id", "choices": {"Choice Display Name": actual_value}}
SETTINGS_COLLECTION = {
    "Use Display vsync as playback reference clock": {
        "id": "coreelec.amlogic.usedisplayasclock",
        "choices": {
            "Enable": True,
            "Disable": False
        }
    },
    "12-bit Deep Color pipeline": {
        "id": "coreelec.amlogic.prefer.12bit",
        "choices": {
            "Enable": True,
            "Disable": False
        }
    },
    "DV VS10 for SDR8 video": {
        "id": "coreelec.amlogic.dolbyvision.vs10.sdr8",
        "choices": {
            "Off": 5,
            "SDR": 3,
            "HDR10": 2,
            "DV":0
        }
    }
}

def set_kodi_setting(setting_id, new_value):
    """
    Sets a specific setting in Kodi via JSON-RPC.
    
    :param setting_id: The string ID of the setting (e.g., "audiooutput.guisoundmode")
    :param new_value: The new value for the setting (boolean, integer, string, etc.)
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "Settings.SetSettingValue",
        "params": {
            "setting": setting_id,
            "value": new_value
        },
        "id": 1
    }

    try:
        response = requests.post(
            URL, 
            json=payload, 
            auth=(USERNAME, PASSWORD),
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status() 
        
        data = response.json()
        
        # Check if Kodi returned a successful result
        if "result" in data and data["result"] == True:
            print(f"\n[+] SUCCESS: Setting '{setting_id}' successfully updated to '{new_value}'.")
        elif "error" in data:
            print(f"\n[-] ERROR from Kodi API: {data['error']['message']}")
        else:
            print(f"\n[?] UNEXPECTED response: {data}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n[-] CONNECTION FAILED. Please check your IP, port, and network. Error: {e}")

def main():
    while True:
        print("\n" + "="*40)
        print("         KODI SETTINGS DRIVER")
        print("="*40)
        
        # 1. Display available settings
        setting_keys = list(SETTINGS_COLLECTION.keys())
        for idx, setting_name in enumerate(setting_keys, start=1):
            print(f"{idx}. {setting_name}")
        print("0. Exit")
        
        # Get user input for setting
        try:
            setting_choice = int(input("\nSelect a setting to change (0 to exit): "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue

        if setting_choice == 0:
            print("Exiting...")
            break
            
        if setting_choice < 1 or setting_choice > len(setting_keys):
            print("Invalid selection. Please choose a valid number from the list.")
            continue
            
        # Get the selected setting object
        selected_setting_name = setting_keys[setting_choice - 1]
        setting_data = SETTINGS_COLLECTION[selected_setting_name]
        kodi_setting_id = setting_data["id"]
        
        print(f"\n--- Choices for: {selected_setting_name} ---")
        
        # 2. Display available choices for the selected setting
        choice_keys = list(setting_data["choices"].keys())
        for idx, choice_name in enumerate(choice_keys, start=1):
            print(f"{idx}. {choice_name}")
            
        # Get user input for choice
        try:
            value_choice = int(input(f"Select the new value for '{selected_setting_name}': "))
        except ValueError:
            print("Invalid input. Cancelling and returning to main menu.")
            continue
            
        if value_choice < 1 or value_choice > len(choice_keys):
            print("Invalid selection. Cancelling and returning to main menu.")
            continue
            
        # Extract the actual value to send to Kodi
        selected_choice_name = choice_keys[value_choice - 1]
        new_value = setting_data["choices"][selected_choice_name]
        
        # 3. Send the change to Kodi
        print(f"\nSending change: {selected_setting_name} -> {selected_choice_name}...")
        set_kodi_setting(kodi_setting_id, new_value)
        
        # Pause briefly before looping back (optional, just to let user read the output)
        input("\nPress Enter to return to the settings menu...")

if __name__ == "__main__":
    main()