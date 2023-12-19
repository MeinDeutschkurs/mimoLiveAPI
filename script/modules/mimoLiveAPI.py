# Version 1.4
import requests
import configparser
import hashlib
import re
import numpy as np
import json
import argparse
import asyncio
import aiohttp
import time

# globals
mimo_data_flat = {}
proc_list = []

# Function to load configuration from an INI file
def load_config(filename):
    config = configparser.ConfigParser()
    try:
        config.read(filename)
        return config
    except FileNotFoundError:
        print(f"Config file '{filename}' not found.")
        exit(1)

# Load configuration from the INI file
config = load_config('../config.ini')

if config:
    # Get BASE_URL from the configuration
    BASE_URL = config.get('API', 'BASE_URL', fallback='http://localhost:8989/api/v1')
    PASSWORD = config.get('API', 'PASSWORD', fallback='')
    MARGIN_IN_PERCENT = float(config.get('design', 'MARGIN_IN_PERCENT', fallback='2'))
    BORDER_IN_PERCENT = float(config.get('design', 'BORDER_IN_PERCENT', fallback='0'))
    BORDER_RADIUS = float(config.get('design', 'BORDER_RADIUS', fallback='0'))
    BORDER_COLOR = "#"+config.get('design', 'BORDER_COLOR', fallback='FFFFFF')
    BACKGROUND_COLOR = "#"+config.get('design', 'BACKGROUND_COLOR', fallback='000000FF')
    ANIMATION_TYPE = config.get('set', 'ANIMATION_TYPE', fallback='MOVE')
    ANIMATION_DURATION = float(config.get('set', 'ANIMATION_DURATION', fallback='0.5'))
    STRETCH_HOLES = int(config.get('design', 'STRETCH_HOLES', fallback='1'))
    TOP = float(config.get('design', 'TOP', fallback='0'))
    LEFT = float(config.get('design', 'LEFT', fallback='0'))
    BOTTOM = float(config.get('design', 'BOTTOM', fallback='0'))
    RIGHT = float(config.get('design', 'RIGHT', fallback='0'))

def putValue(dictionary, key_path, value):
    keys = key_path.split('.')
    current_dict = dictionary

    for key in keys[:-1]:
        if key not in current_dict:
            current_dict[key] = {} 
        current_dict = current_dict[key]

    current_dict[keys[-1]] = value

def build_mimolive_cache():
    cache = {"documents": {}, "matrix": {}}
    documents = get_all_documents()

    for doc in documents:
        doc_id = doc['id']
        doc_name = doc.get('attributes', {}).get('name', doc.get('attributes', {}).get('title', 'Unknown Document'))
        don = f"documents.{doc_name}"
        putValue(cache, f"{don}", doc)
        putValue(cache, f"{don}._thisAPIpath", f"documents/{doc_id}")
        putValue(cache, f"{don}._thisNamePath", f"documents.{doc_name}")
        putValue(cache, f"{don}._thisDocumentNamePath", f"documents.{doc_name}")    

        # Handling layers, sources, variants, layer-sets, and output-destinations
        for field in ["layers", "sources", "layer-sets", "output-destinations"]:
            items = get_all(doc_id, field)
            cache["documents"][doc_name][field] = {}  # Initialize the field in the cache
            for item in items:
                item_name = item.get('attributes', {}).get('name', item.get('attributes', {}).get('title', 'Unnamed Item'))
                item_id = item['id']
                donfil = f"{don}.{field}.{item_name}"
                putValue(cache, f"{donfil}", item)
                putValue(cache, f"{donfil}._thisAPIpath", f"documents/{doc_id}/{field}/{item_id}")
                putValue(cache, f"{donfil}._thisNamePath", f"documents.{doc_name}.{field}.{item_name}")
                putValue(cache, f"{donfil}._thisDocumentNamePath",f"documents.{doc_name}")
                
                def process_matrix_component(pattern, component_type):
                    match = re.match(pattern, item_name, re.IGNORECASE)
                    if match:
                        x, y, *rest = match.groups()
                        x, y = x.lower(), y.lower()

                        key_path = None
                        if component_type == "element":
                            z = rest[0]
                            xandz = f"{x}.{z}"
                            key_path = f"matrix.{y}.elements.{xandz}"
                            if "auto" in x and key_path not in cache:
                                cache[key_path] = {"options": {}}
                        else:
                            key_path = f"matrix.{y}.{component_type}"
                            if key_path not in cache:
                                cache[key_path] = {"options": {}}

                        if key_path:
                            putValue(cache, f"{key_path}._thisAPIpath", f"documents/{doc_id}/{field}/{item_id}")
                            putValue(cache, f"{key_path}._thisNamePath", f"documents.{doc_name}.{field}.{item_name}")
                            putValue(cache, f"{key_path}._thisDocumentNamePath", f"documents.{doc_name}")
                        
                        return x, key_path
                    return None, None
                
                # Add Matrix-Structure:
                x_auto, maxz = process_matrix_component(r"^(video|audio|auto)_(\w+)_(\d+)$", "element")
                x_exclusive, maxe = process_matrix_component(r"^(exclusive)_(\w+)$", "exclusive")
                x_mode, maxm = process_matrix_component(r"^(mode)_(\w+)$", "mode")
                x_offset, maxo = process_matrix_component(r"^(offset)_(\w+)$", "offset")
                x_matrix, maxh = process_matrix_component(r"^(matrix)_(\w+)$", "head")
                    
                # Handling subfields if applicable
                if field in ["layers", "sources"]:
                    subfield = "variants" if field == "layers" else "filters"
                    sub_items = get_all(doc_id, field, item_id, subfield)
                    cache["documents"][doc_name][field][item_name][subfield] = {}

                    for sub_item in sub_items:
                        sub_item_name = sub_item.get('attributes', {}).get('name', sub_item.get('attributes', {}).get('title', 'Unnamed Subitem'))
                        sub_item_id = sub_item['id']
                        donfilsub = f"{donfil}.{subfield}.{sub_item_name}"
                        putValue(cache, f"{donfilsub}", sub_item)

                        # generalized sub_items:
                        def update_cache(var_prefix, sub_item_name):
                            var_full = f"{var_prefix}.options.{sub_item_name}"
                            putValue(cache, f"{var_full}", {})
                            putValue(cache, f"{var_full}._thisAPIpath", f"documents/{doc_id}/{field}/{item_id}/{subfield}/{sub_item_id}")
                            putValue(cache, f"{var_full}._thisNamePath", f"documents.{doc_name}.{field}.{item_name}.{subfield}.{sub_item_name}")
                            putValue(cache, f"{var_full}._thisDocumentNamePath", f"documents.{doc_name}")

                        # Variant and Filter-Elements
                        update_cache(donfilsub, sub_item_name)

                        # special matrix sub-elements, if available
                        if x_auto and "auto" in x_auto:
                            update_cache(maxz, sub_item_name)
                        if x_matrix and "matrix" in x_matrix:
                            update_cache(maxh, sub_item_name)
                        if x_exclusive and "exclusive" in x_exclusive:
                            update_cache(maxe, sub_item_name)
                        if x_mode and "mode" in x_mode:
                            update_cache(maxm, sub_item_name)
                        if x_offset and "offset" in x_offset:
                            update_cache(maxo, sub_item_name)

    return cache

def make_authenticated_request(api_path, action=""):
    password_hash = hashlib.sha256(PASSWORD.encode()).hexdigest()
    headers = {}
    if len(password_hash) >= 10:
        headers = {"X-MimoLive-Password-SHA256": password_hash}
    if len(action) >= 1:
        action = f"/{action}"
    response = requests.get(api_path + action, headers=headers)
    return response

def get_all_documents():
    api_path = f"{BASE_URL}/documents"
    response = make_authenticated_request(api_path) 
    if response and response.status_code == 200:
        return response.json().get('data', [])
    else:
        if response:
            print(f"Error fetching documents. Status Code: {response.status_code}")
        return []

def get_all(doc_id, field, field_id=None, subfield=None):
    # Construct the API path
    api_path = f"{BASE_URL}/documents/{doc_id}/{field}"
    if field_id and subfield:
        api_path = f"{api_path}/{field_id}/{subfield}"
    # Make the authenticated API request
    response = make_authenticated_request(api_path)
    if response and response.status_code == 200:
        return response.json().get('data', [])
    else:
        if response:
            print(f"Error fetching data for {api_path}. Status Code: {response.status_code}")
        return []

def flatten(data, parent_key='', sep='.'):
    items = {}
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.update(flatten(value, new_key, sep=sep))
        else:
            items[new_key] = value
    return items

def remove_attributes_prefix(data):
    flatten(data)
    modified_data = {}
    for key, value in data.items():
        # Replace ".attributes." and "/attributes/" with "."
        modified_key = key.replace(".attributes.", ".").replace("/attributes/", ".")
        modified_data[modified_key] = value
    return modified_data

def unflatten(data, sep='.'):
    nested_dict = {}
    for key, value in data.items():
        keys = key.split(sep)
        current_level = nested_dict
        for k in keys[:-1]:
            current_level = current_level.setdefault(k, {})
        current_level[keys[-1]] = value
    return nested_dict

def getValue(key_path):
    global mimo_data_flat
    key_path_lower = key_path.lower()
    return {key: value for key, value in mimo_data_flat.items() if key.lower().startswith(key_path_lower)}

def find_closest_api_path(key_path):
    global mimo_data_flat
    key_parts = key_path.split('.')
    # try to find the longest matching key-path
    for i in range(len(key_parts), 0, -1):
        test_path = '.'.join(key_parts[:i]) + '._thisAPIpath'
        if test_path in mimo_data_flat:
            api_path = mimo_data_flat[test_path]
            query_path = '.'.join(key_parts[i:])
            return api_path, query_path
    return None, None

def group_by_api_path(flat_dict):
    grouped = {}
    for key, value in flat_dict.items():
        api_path, query_path = find_closest_api_path(key)
        if api_path not in grouped:
            grouped[api_path] = {}
        grouped[api_path][query_path] = value
    return grouped

def process_read_requests(read_requests):
    read_results = perform_read_operations(read_requests)
    return read_results

def perform_read_operations(requests):
    results = {}
    for key_path in requests:
        results[key_path] = getValue(key_path)
    return results

def pipWindowBlock(block, top, left, bottom, right, path, status_list, isVisible, switcher_MODE, anim_dur):
    global MARGIN_IN_PERCENT, BORDER_IN_PERCENT, BORDER_COLOR, BORDER_RADIUS, BACKGROUND_COLOR
    # initiate
    if path not in block:
        block[path] = {}

    if BORDER_IN_PERCENT <= 0:
        border = 0
    else:
        border = MARGIN_IN_PERCENT*(BORDER_IN_PERCENT/100)

    if BORDER_RADIUS <= 0:
        radius = 0
    else:
        radius = MARGIN_IN_PERCENT*(BORDER_RADIUS/100)
    
    # Full Screen
    if sum(status_list) == 0 or isVisible == False or (top, left, bottom, right) == (0,0,0,0):
        block[path]["input-values.tvGroup_Appearance__Corner_Radius_TypeBoinxY"] = 0
        block[path]["input-values.tvGroup_Appearance__Boarder_Width_TypeBoinxY"] = 0
        block[path]["input-values.tvGroup_Appearance__Background_Color"] = json.loads(preprocess_args(f"hex2color({BACKGROUND_COLOR})"))
        block[path]["input-values.tvGroup_tvGroup_Appearance__Drop_Shadow"] = 0
    else:
        block[path]["input-values.tvGroup_Appearance__Corner_Radius_TypeBoinxY"] = radius
        block[path]["input-values.tvGroup_Appearance__Boarder_Width_TypeBoinxY"] = border
        block[path]["input-values.tvGroup_Appearance__Background_Color"] = json.loads(preprocess_args(f"hex2color({BACKGROUND_COLOR})"))
        block[path]["input-values.tvGroup_tvGroup_Appearance__Drop_Shadow"] = 0
    
    if switcher_MODE == "CUT":
        block[path]["input-values.tvIn_TransitionDuration"] = 0
        block[path]["input-values.tvGroup_Transition__Variant_Animation_TypeDuration"] = 0
        block[path]["input-values.tvIn_TransitionType"] = 1
    elif switcher_MODE == "MOVE":
        block[path]["input-values.tvIn_TransitionType"] = 2
        block[path]["input-values.tvIn_TransitionDuration"] = anim_dur
        block[path]["input-values.tvGroup_Transition__Variant_Animation_TypeDuration"] = anim_dur

    # individual
    block[path]["input-values.tvGroup_Appearance__Shape"] = 2
    block[path]["input-values.tvGroup_Geometry__Window_Top_TypeBoinxY"] = top
    block[path]["input-values.tvGroup_Geometry__Window_Left_TypeBoinxX"] = left
    block[path]["input-values.tvGroup_Geometry__Window_Bottom_TypeBoinxY"] = bottom
    block[path]["input-values.tvGroup_Geometry__Window_Right_TypeBoinxX"] = right
    block[path]["input-values.tvGroup_Appearance__Boarder_Color"] = json.loads(preprocess_args(f"hex2color({BORDER_COLOR})"))
    block[path]["volume"] = 0
    return block

def volumeBlock(block, volume, path):
    if path not in block:
        block[path] = {}
    block[path]["volume"] = volume
    return block

def calculate_element_coordinates(layout, mode=1, frame=(0, 0, 0, 0), original_dimensions=(1920, 1080)):
    global MARGIN_IN_PERCENT
    # Rahmenparameter auspacken
    frame_top, frame_left, frame_bottom, frame_right = frame
    width, height = original_dimensions
    aspect_ratio = width / height

    size = 2.0
    margin_width = size * (MARGIN_IN_PERCENT/100)  # Margin für die Breite
    margin_height = size * (MARGIN_IN_PERCENT/100) * aspect_ratio  # Margin für die Höhe, basierend auf dem Seitenverhältnis

    total_elements = len(layout)
    columns = int(np.ceil(np.sqrt(total_elements)))
    rows = int(np.ceil(total_elements / columns))

    if sum(layout) == 1 and frame == (0,0,0,0):
        margin_width = margin_height = 0

    if mode == 1:  # Auffüllen nach Zeilen
        visible_rows = sum(1 for row in range(rows) if sum(layout[row * columns:(row + 1) * columns]) > 0)
        if visible_rows == 0:
            frame_center_top = (frame_top + size - frame_bottom) / 2
            frame_center_left = (frame_left + size - frame_right) / 2
            return {f'Element {i + 1}': {'m_top': frame_center_top, 'm_left': frame_center_left, 'm_bottom': size - frame_center_top, 'm_right': size - frame_center_left} for i in range(total_elements)}

        # Anpassung für den Rahmen
        height = (size - (visible_rows + 1) * margin_height - frame_top - frame_bottom) / visible_rows
        x, y = margin_width + frame_left, margin_height + frame_top
        coordinates = {}

        for row in range(rows):
            row_elements = layout[row * columns:(row + 1) * columns]
            visible_in_row = sum(row_elements)
            width_per_visible = (size - margin_width * (visible_in_row + 1) - frame_left - frame_right) / visible_in_row if visible_in_row > 0 else 0

            for col in range(len(row_elements)):
                element = row_elements[col]
                element_index = row * columns + col

                m_top = y
                m_left = x
                m_bottom = size - y - height
                m_right = size - x - (width_per_visible if element else 0)

                coordinates[f'Element {element_index + 1}'] = {'m_top': m_top, 'm_left': m_left, 'm_bottom': m_bottom, 'm_right': m_right}
                x += width_per_visible + margin_width if element else 0

            x = margin_width + frame_left
            if visible_in_row > 0:
                y += height + margin_height

    elif mode == 2:  # Fill by Columns
        visible_columns = sum(1 for col in range(columns) if sum(layout[col::columns]) > 0)
        if visible_columns == 0:
            frame_center_top = (frame_top + size - frame_bottom) / 2
            frame_center_left = (frame_left + size - frame_right) / 2
            return {f'Element {i + 1}': {'m_top': frame_center_top, 'm_left': frame_center_left, 'm_bottom': size - frame_center_top, 'm_right': size - frame_center_left} for i in range(total_elements)}

        # Adjustment for the frame
        width = (size - (visible_columns + 1) * margin_width - frame_left - frame_right) / visible_columns
        x, y = margin_width + frame_left, margin_height + frame_top
        coordinates = {}

        for col in range(columns):
            col_elements = layout[col::columns]
            visible_in_col = sum(col_elements)
            height_per_visible = (size - margin_height * (visible_in_col + 1) - frame_top - frame_bottom) / visible_in_col if visible_in_col > 0 else 0

            for row in range(len(col_elements)):
                element = col_elements[row]
                element_index = col + row * columns

                m_top = y
                m_left = x
                m_bottom = size - y - (height_per_visible if element else 0)
                m_right = size - x - (width)

                coordinates[f'Element {element_index + 1}'] = {'m_top': m_top, 'm_left': m_left, 'm_bottom': m_bottom, 'm_right': m_right}
                y += height_per_visible + margin_height if element else 0

            y = margin_height + frame_top
            if visible_in_col > 0:
                x += width + margin_width

    return coordinates

def preprocess_args(args_str):
    # Erstellen Sie eine reguläre Ausdrucksübereinstimmung, um hex2color-Vorkommen in args_str zu finden
    pattern = r'hex2color\((#[0-9A-Fa-f]+)\)'
    
    # Verwenden Sie re.sub, um alle Vorkommen von hex2color(?) durch die entsprechenden Farbwerte zu ersetzen
    def replace_hex(match):
        hex_color = match.group(1)
        thisreturn = parse_all(hex_color)
        return str(thisreturn)
    
    replaced_args_str = re.sub(pattern, replace_hex, args_str)
    
    return replaced_args_str

def parse_all(string):
    string = parse_color(string)
    # add future parsers
    # return
    return string

def parse_color(hex_code):
    hex_code = hex_code.strip('#')  # Entfernen Sie das '#' Zeichen, falls vorhanden

    # Bestimmen Sie die Länge des Hex-Codes
    code_length = len(hex_code)
    
    if code_length == 1:
        # Einzelwert für R, G, B; Alpha = F
        red = int(hex_code, 16) / 15.0
        green = int(hex_code, 16) / 15.0
        blue = int(hex_code, 16) / 15.0
        alpha = 1.0
    elif code_length == 2:
        # Erste Stelle für R, G, B; Letzte Stelle für Alpha
        red = int(hex_code[0], 16) / 15.0
        green = int(hex_code[0], 16) / 15.0
        blue = int(hex_code[0], 16) / 15.0
        alpha = int(hex_code[1], 16) / 15.0
    elif code_length == 3:
        # Erste Stelle für R, Zweite Stelle für G, Dritte Stelle für B; Alpha = F
        red = int(hex_code[0], 16) / 15.0
        green = int(hex_code[1], 16) / 15.0
        blue = int(hex_code[2], 16) / 15.0
        alpha = 1.0
    elif code_length == 4:
        # Erste Stelle für R, Zweite Stelle für G, Dritte Stelle für B, Vierte Stelle für Alpha
        red = int(hex_code[0], 16) / 15.0
        green = int(hex_code[1], 16) / 15.0
        blue = int(hex_code[2], 16) / 15.0
        alpha = int(hex_code[3], 16) / 15.0
    elif code_length == 6:
        # Erste zwei Stellen für R, Nächsten zwei Stellen für G, Letzten zwei Stellen für B; Alpha = FF
        red = int(hex_code[0:2], 16) / 255.0
        green = int(hex_code[2:4], 16) / 255.0
        blue = int(hex_code[4:6], 16) / 255.0
        alpha = 1.0
    elif code_length == 8:
        # Erste zwei Stellen für R, Nächsten zwei Stellen für G, Letzten zwei Stellen für B, Letzten zwei Stellen für Alpha
        red = int(hex_code[0:2], 16) / 255.0
        green = int(hex_code[2:4], 16) / 255.0
        blue = int(hex_code[4:6], 16) / 255.0
        alpha = int(hex_code[6:8], 16) / 255.0
    else:
        # Ungültiger Hex-Code
        red = green = blue = alpha = 1.0

    # Erstellen Sie eine Zeichenkette im gewünschten Format
    color_string = f'{{"red": {red}, "green": {green}, "blue": {blue}, "alpha": {alpha}}}'

    return color_string


def setValues(set, sleep_duration=0):
    set = remove_attributes_prefix(set)
    updates_by_path = {}
    for path, updates in set.items():
        api_path_result = find_closest_api_path(path)
        if api_path_result:
            full_path, query_path = api_path_result
            if full_path not in updates_by_path:
                updates_by_path[full_path] = {}
            for key, value in updates.items():
                # Fügen Sie den query_path zum Schlüssel hinzu, um eine korrekte Struktur zu gewährleisten
                updates_by_path[full_path][query_path + key] = value

    for full_path, update_data_flat in updates_by_path.items():
        # Entflachen der Update-Daten
        update_data_unflattened = unflatten(update_data_flat)

        proc_list.append({
            "api_path": f"{BASE_URL}/{full_path}",
            "request": "PUT",
            "update": update_data_unflattened
        })

    if sleep_duration > 0:
        sleep(sleep_duration)

def get_key_value_by_prefix(dictionary, prefix):
    key_value_pairs_with_prefix = {}
    prefix_length = len(prefix)
    for key, value in dictionary.items():
        if key.startswith(prefix):
            new_key = key[prefix_length:]  # Entfernen des Präfixes aus dem Schlüssel
            key_value_pairs_with_prefix[new_key] = value
    return key_value_pairs_with_prefix

def get_live_status_from_keys(data):
    live_status_dict = {}
    for key, value in data.items():
        if key.startswith("matrix.") and key.endswith("._thisNamePath"):
            live_status_key = value + ".attributes.live-state"
            live_status = data.get(live_status_key, "Unbekannter Status")
            live_status_dict[key] = live_status
    return live_status_dict

def add_livestate_to_matrix(data):
    # Abrufen des Live-Status für die relevanten Schlüssel
    live_status_results = get_live_status_from_keys(data)

    # Hinzufügen der gefundenen Live-Status-Ergebnisse zur mimo_data_flat-Variable
    for key, live_status in live_status_results.items():
        new_key = key.replace('_thisNamePath', '_thisLiveState')
        data[new_key] = live_status
    return data

def apply_switcher_logic(matrix):
    global mimo_data_flat, ANIMATION_TYPE, ANIMATION_DURATION, STRETCH_HOLES, TOP, LEFT, BOTTOM, RIGHT
    switcher_results = {}

    # Ermitteln aller einzigartigen Präfixe für die Switcher
    switcher_prefixes = set(key.split('.elements.')[0] for key in matrix.keys() if '.elements.' in key)

    for prefix in switcher_prefixes:
        pause_live = matrix.get(f"{prefix}.head.options.PAUSE._thisLiveState", "off") == "live"

        if pause_live:
            return {}
        
        on_live = matrix.get(f"{prefix}.head.options.ON._thisLiveState", "off") == "live"
        
        if on_live != True:
            off_live = True
        else:
            off_live = False

        audio = {}
        video = {}

        switcher_MODE = ANIMATION_TYPE
        for key in matrix.keys():
            if key.startswith(f'{prefix}.mode.options.'):
                live_status = matrix.get(key)
                if live_status == 'live':
                    switcher_MODE = key.split('.mode.options.')[1].replace("._thisLiveState", "")
                    break

        for key in matrix.keys():
            if key.startswith(f'{prefix}.offset.options.'):
                live_status = matrix.get(key)
                if live_status == 'live':
                    input_string = key.split('.offset.options.')[1].replace("._thisLiveState", "")
                    values = input_string.split(",")

                    if len(values) == 4:
                        try:
                            TOP, LEFT, BOTTOM, RIGHT = map(float, values)
                        except ValueError:
                            print("Invalid input for TOP, LEFT, BOTTOM, RIGHT")
                    else:
                        print("Values missing in TOP, LEFT, BOTTOM, RIGHT.")
                    break

        exclusive_live_variant = None
        for key in matrix.keys():
            if key.startswith(f'{prefix}.exclusive.options.'):
                live_status = matrix.get(key)
                if live_status == 'live' and on_live!=False:
                    exclusive_live_variant = key.split('.exclusive.options.')[1].replace("._thisLiveState", "")
                    break

        # find state of auto-layers
        auto_layers = [key.split('.')[3] for key in matrix.keys() if key.startswith(f'{prefix}.elements.auto.')]

        for auto_name in auto_layers:
            video_path_key = f"{prefix}.elements.video.{auto_name}._thisNamePath"
            audio_path_key = f"{prefix}.elements.audio.{auto_name}._thisNamePath"
            video_path = matrix.get(video_path_key, "Unbekannter Pfad")
            audio_path = matrix.get(audio_path_key, "Unbekannter Pfad")

            # default values
            action_video = "setLive"
            action_audio = "setLive"
            video_visible = False
            audio_volume = 0

            # check only, if off_live is NOT live.
            if not off_live:
                for option in ['ON', 'VIDEO', 'AUDIO', 'OFF']:
                    option_state = matrix.get(f'{prefix}.elements.auto.{auto_name}.options.{option}._thisLiveState')
                    if option_state == 'live':
                        action_video = "setLive" if option in ['ON', 'VIDEO'] else "setOff"
                        action_audio = "setLive" if option in ['ON', 'AUDIO'] else "setOff"
                        video_visible = option in ['ON', 'VIDEO']
                        audio_volume = 1 if option in ['ON', 'AUDIO'] else 0
                        break

            # modify exclusive option
            if exclusive_live_variant:
                if auto_name == exclusive_live_variant:
                    video_visible = True  # Setzen auf True, wenn es die exklusive Option ist
                    audio_volume = 1
                else:
                    video_visible = False

            audio[audio_path] = {"action": action_audio, "volume": audio_volume}
            video[video_path] = {"action": action_video, "visible": video_visible}

        # Get Values from Document Path, to have correct ratios
        documentPath = matrix.get(f"{prefix}.head._thisDocumentNamePath")
        width = mimo_data_flat.get(f"{documentPath}.attributes.metadata.width")
        height = mimo_data_flat.get(f"{documentPath}.attributes.metadata.height")

        thisMode=STRETCH_HOLES

        status_list = [1 if layer_visible else 0 for layer_visible in [video_info['visible'] for video_info in video.values()]]
        coordinates = calculate_element_coordinates(status_list, thisMode, (TOP,LEFT,BOTTOM,RIGHT), (width,height))

        for video_index, (video_path, video_info) in enumerate(video.items()):
            coord = coordinates.get(f'Element {video_index + 1}', {})
            isVisible = status_list[video_index] == 1
            video_block = pipWindowBlock({}, coord['m_top'], coord['m_left'], coord['m_bottom'], coord['m_right'], video_path, status_list, isVisible, switcher_MODE, ANIMATION_DURATION)
            setLive(video_path)
            setValues(video_block)

        for audio_path, audio_info in audio.items():
            volume = audio_info["volume"]
            audio_block = volumeBlock({}, volume, audio_path)
            setLive(audio_path)
            setValues(audio_block)
    pass

def sleep(time):
    proc_list.append({"request": "SLEEP", "time": time})
    pass

def setLive(path):
    setLiveOrOff(path, "setLive")
    pass

def setOff(path):
    setLiveOrOff(path, "setOff")
    pass

def recall(path):
    setLiveOrOff(path, "recall")
    pass

def setLiveOrOff(path, mode):
    # this is currently without updating the cache!!!
    global proc_list
    api_path = find_closest_api_path(path)
    status = getValue(path + ".attributes.live-state")
    active = getValue(path + ".attributes.active")

    # avoid unnecessary steps
    if (mode == "setOff" and status == "off") or (mode == "setLive" and status == "live"):
        return None

    if api_path:
        full_path, _ = api_path

        if "layer-sets" in path:
            mode = "recall"
            # avoid unnecessary steps
            if mode == "setLive" and active == True:
                return None

        # Hinzufügen eines neuen Blocks zur Prozessliste
        proc_list.append({
            "api_path": f"{BASE_URL}/{full_path}/{mode}",
            "path": path,
            "mode": mode,
            "request": "GET"
        })
        return full_path
    else:
        print("API-Pfad nicht gefunden.")
        return None

async def make_authenticated_request_async(method, api_path, action="", data=None):
    password_hash = hashlib.sha256(PASSWORD.encode()).hexdigest()
    headers = {
        "X-MimoLive-Password-SHA256": password_hash,
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        if method == 'PUT':
            async with session.put(api_path + action, headers=headers, json=data) as response:
                return await response.text()
        elif method == 'GET':
            async with session.get(api_path + action, headers=headers) as response:
                return await response.text()

async def process_item(item):
    if item["request"] == "PUT":
        # item["update"] = unflatten(item.get("update")) 
        data_str = json.dumps(item["update"]) if item.get("update") else '{}'
        return await make_authenticated_request_async('PUT', item["api_path"], data=json.loads(data_str))
    elif item["request"] == "GET":
        return await make_authenticated_request_async('GET', item["api_path"])
    elif item["request"] == "SLEEP":
        await asyncio.sleep(item["time"])
        return "Sleep completed"

async def execute_proc_list_async(proc_list):
    return await asyncio.gather(*[process_item(item) for item in proc_list])

def prepare_proc_list():
    global proc_list
    for item in proc_list:
        if item["request"] == "PUT":
            item["update"] = unflatten(item.get("update"))
            item["data_str"] = json.dumps(item["update"]) if item.get("update") else '{}'

def separate_proc_list(proc_list):
    put_list = [item for item in proc_list if item["request"] == "PUT"]
    get_list = [item for item in proc_list if item["request"] == "GET"]
    sleep_list = [item for item in proc_list if item["request"] == "SLEEP"]
    return put_list, get_list, sleep_list

async def execute_separated_lists(put_list, get_list, sleep_list):
    put_results = await asyncio.gather(*[process_item(item) for item in put_list])
    get_results = await asyncio.gather(*[process_item(item) for item in get_list])
    sleep_results = await asyncio.gather(*[process_item(item) for item in sleep_list])
    return put_results, get_results, sleep_results

# main method
async def main():
    global mimo_data_flat 
    # GET EVERYTHING FROM MIMO-LIVE TO REDUCE REQUESTS
    mimolive_data = build_mimolive_cache()
    # WORK WITH FLAT STRUCTURE
    mimo_data_flat = flatten(mimolive_data)
    
    # COMMAND LINE
    parser = argparse.ArgumentParser(description='Control mimoLive documents.')
    parser.add_argument('--setLive', type=str, help='Set documents, layers, variants, layer-sets or output-destinations live')
    parser.add_argument('--setOff', type=str, help='Set documents, layers, variants or output-destinations off')
    parser.add_argument('--setValue', type=str, help='Set specific values for given key paths')
    parser.add_argument('--matrix', action='store_true', help='updates matrix, used by server.py')

    args = parser.parse_args()

    if args.matrix:
        # ADD LIVESTATES TO MATRIX
        mimo_data_flat = add_livestate_to_matrix(mimo_data_flat)
        # CALCULATE MATRIX
        matrix = get_key_value_by_prefix(mimo_data_flat, "matrix.")
        apply_switcher_logic(matrix)

    if args.setValue:
        args.setValue = preprocess_args(args.setValue)
        value_requests = json.loads(args.setValue)
        for path, updates in value_requests.items():
            api_path, query_path = find_closest_api_path(path)
            if api_path:
                full_path, query = api_path
                update_data = {query_path: updates}
                proc_list.append({
                    "api_path": f"{BASE_URL}/{full_path}",
                    "request": "PUT",
                    "update": update_data
                })

    if args.setOff:
        args.setOff = preprocess_args(args.setOff)
        paths = json.loads(args.setOff)
        for path in paths:
            setLiveOrOff(path, "setOff")

    if args.setLive:
        args.setLive = preprocess_args(args.setLive)
        paths = json.loads(args.setLive)
        for path in paths:
            setLiveOrOff(path, "setLive")

    # EXECUTE THE PROCESS LIST
    prepare_proc_list()
    put_list, get_list, sleep_list = separate_proc_list(proc_list)
    await execute_separated_lists(put_list, get_list, sleep_list)

# run script/main method
if __name__ == "__main__":
    asyncio.run(main())