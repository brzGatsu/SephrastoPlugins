"""
This is a development utility script used to make updating the maneuvers in maneuver_foundry_extensions.json more convenient.
It extracts maneuver data from Foundry VTT's source files and updates the plugin's configuration.
This script is not required for the plugin to function and is only used during development.
"""

import json
import os
import glob

FOUNDRY_PATH = "{...wo auch immer der Pfad ist}/FoundryVTT/Data/systems/Ilaris/packs/manover/_source"

def extract_maneuvers():
    maneuvers = {}
    
    if not os.path.exists(FOUNDRY_PATH):
        print(f"Foundry maneuvers path not found: {FOUNDRY_PATH}")
        return
    
    for file_path in glob.glob(os.path.join(FOUNDRY_PATH, "*.json")):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                name = data.get('name', '')
                if name:
                    modifications = []
                    
                    # Extract modifications from flags if they exist (array)
                    flags = data.get('flags', {})
                    if 'modifications' in flags:
                        flag_mods = flags['modifications']
                        if isinstance(flag_mods, list):
                            # Ensure each modification has the affectedByInput field
                            for mod in flag_mods:
                                if isinstance(mod, dict):
                                    mod['affectedByInput'] = mod.get('affectedByInput', False)
                                    modifications.append(mod)
                    
                    # Extract modifications from system.modifications if they exist (object)
                    system = data.get('system', {})
                    if 'modifications' in system:
                        system_mods = system['modifications']
                        if isinstance(system_mods, dict):
                            # Add each value from the modifications object
                            for mod in system_mods.values():
                                if isinstance(mod, dict):
                                    mod['affectedByInput'] = mod.get('affectedByInput', False)
                                    modifications.append(mod)
                    
                    # Extract defense flag
                    is_defense = flags.get('isDefense', False)
                    
                    # Extract icon
                    icon = data.get('img', '')
                    
                    # Only save if we have any data
                    if modifications or is_defense or icon:
                        maneuvers[name] = {
                            'modifications': modifications,
                            'isDefense': is_defense,
                            'icon': icon
                        }
                        print(f"Extracted maneuver: {name} with {len(modifications)} modifications")
        except Exception as e:
            print(f"Error loading maneuver file {file_path}: {str(e)}")
    
    print(f"Extracted {len(maneuvers)} maneuvers")
    return maneuvers

def main():
    maneuvers = extract_maneuvers()
    if maneuvers:
        config = {
            "maneuvers": maneuvers
        }
        
        config_path = os.path.join(os.path.dirname(__file__), "maneuver_foundry_extensions.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print(f"Saved maneuver data to {config_path}")

if __name__ == "__main__":
    main() 