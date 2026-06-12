import requests
import json

# --- Kodi Connection Details ---
KODI_IP = "10.0.0.164"  # Replace with your Kodi device's IP address
KODI_PORT = "8080"      # Default port is usually 8080
USERNAME = "kodi"       # Replace with your Kodi web interface username
PASSWORD = "kodi"       # Replace with your Kodi web interface password

# The JSON-RPC endpoint URL
URL = f"http://{KODI_IP}:{KODI_PORT}/jsonrpc"

def fetch_coreelec_settings():
    """
    Queries Kodi for all settings, filters for 'coreelec.' settings, 
    and structures them dynamically into a collection.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "Settings.GetSettings",
        "params": {
            "level": "expert"  # Ensures we get all hidden/advanced settings
        },
        "id": 1
    }

    print("Fetching settings from Kodi...")
    try:
        response = requests.post(
            URL, 
            json=payload, 
            auth=(USERNAME, PASSWORD),
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"\n[-] CONNECTION FAILED. Please check your IP, port, and network. Error: {e}")
        return {}

    settings_list = data.get("result", {}).get("settings", [])
    settings_collection = {}

    for setting in settings_list:
        s_id = setting.get("id", "")
        
        # Initially only expose coreelec settings
        if not s_id.startswith("coreelec."):
            continue

        s_type = setting.get("type")
        choices = {}

        # Handle Booleans
        if s_type == "boolean":
            choices = {"Enable": True, "Disable": False}
        
        # Handle Enums/Integers with predefined options
        elif "options" in setting:
            for opt in setting["options"]:
                if isinstance(opt, dict):
                    # Sometimes labels are numeric IDs referencing Kodi's language files, 
                    # fallback to stringified value if needed.
                    label = str(opt.get("label", opt.get("value")))
                    val = opt.get("value")
                    choices[label] = val
                else:
                    # If option is just a plain list of values
                    choices[str(opt)] = opt
        
        # Skip settings that don't have distinct choices (like free-form text inputs)
        if not choices:
            continue

        # Create a readable Display Name from the ID (e.g. 'coreelec.amlogic.prefer.12bit' -> 'Prefer 12Bit')
        #display_name = s_id.split(".")[-1].replace("_", " ").title()
        display_name = setting.get("help", "")
        
        # Append to our dynamic collection
        settings_collection[display_name] = {
            "id": s_id,
            "choices": choices,
            "current_value": setting.get("value")
        }

    return settings_collection

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
    # Load settings once at startup
    settings_collection = fetch_coreelec_settings()
    
    if not settings_collection:
        print("No settings found or failed to connect. Exiting...")
        return

    while True:
        print("\n" + "="*50)
        print("         KODI SETTINGS DRIVER")
        print("="*50)
        
        # 1. Display available settings
        setting_keys = list(settings_collection.keys())
        for idx, setting_name in enumerate(setting_keys, start=1):
            current = settings_collection[setting_name].get("current_value")
            print(f"{idx}. {setting_name} (Current: {current})")
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
        setting_data = settings_collection[selected_setting_name]
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
        
        # Update the local current_value so the UI reflects the change on next loop
        settings_collection[selected_setting_name]["current_value"] = new_value
        
        # Pause briefly before looping back
        input("\nPress Enter to return to the settings menu...")

if __name__ == "__main__":
    main()