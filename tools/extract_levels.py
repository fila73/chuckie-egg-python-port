
import os
import json
import re

def parse_levels(file_path):
    levels = {}
    current_level = None
    current_data = []
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
        
    for line in lines:
        line = line.strip()
        
        if line.startswith('@label=level_'):
            label = line.split('=')[1]
            # Match level_1, level_2 ... level_8
            if re.match(r'level_\d+$', label):
                if current_level:
                    levels[current_level] = current_data
                
                current_level = label
                current_data = []
        
        elif line.startswith('@label='):
             # New label that is NOT a level -> end current level
             if current_level:
                 levels[current_level] = current_data
                 current_level = None
                 current_data = []

        elif current_level and (line.startswith('b$') or line.startswith('$')):
             # Data line
             if 'defb' in line:
                parts = line.split('defb')[1]
                bytes_str = parts.split(',')
                for b_str in bytes_str:
                    clean_b = b_str.strip().replace('$', '')
                    if clean_b:
                        try:
                           current_data.append(int(clean_b, 16))
                           # Stop reading if we reached the full level size (32x21 = 672 bytes)
                           if len(current_data) >= 672:
                               levels[current_level] = current_data
                               current_level = None
                               current_data = []
                               break # Stop processing this line
                        except ValueError:
                           pass
                           
    if current_level:
        levels[current_level] = current_data
        
    return levels

def save_levels(levels, output_file):
    # Validate size?
    # Each level should be 672 bytes (32x21)
    
    formatted_levels = {}
    for name, data in levels.items():
        if len(data) != 672:
            print(f"Warning: {name} has {len(data)} bytes (expected 672).")
        
        # Convert to 2D array (rows of 32)
        grid = []
        for i in range(0, len(data), 32):
            row = data[i:i+32]
            grid.append(row)
            
        # Reverse rows (Data stored Bottom-to-Top?)
        # User said "Rows are reversed".
        # If the Skool file stores 0..31 (Top Row), then 32..63 (2nd Row).
        # But if the user sees it upside down, then my Top Row is actually the Bottom Row.
        # But "level is horizontaly flipped" is confusing.
        # Let's try reversing the grid first (Vertical Flip).
        # Actually user said "horizontálně otočen" (Horizontally Flipped? or Flipped OVER Horizontal Axis?)
        # "rows levelu jsou obráceně" = Rows (lines) are reversed.
        
        # Let's assume storage is standard, but the User wants it flipped?
        # Or storage IS reversed.
        # Let's reverse it.
        grid.reverse()
            
        formatted_levels[name] = grid
        
    with open(output_file, 'w') as f:
        json.dump(formatted_levels, f, indent=2)
        
    print(f"Saved {len(levels)} levels to {output_file}")

def main():
    skool_file = os.path.join(os.path.dirname(__file__), '../../chuckie-egg-disassembly/chuckie-egg.skool')
    output_file = os.path.join(os.path.dirname(__file__), '../data/levels.json')
    
    output_dir = os.path.dirname(output_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Parsing {skool_file}...")
    levels = parse_levels(skool_file)
    
    save_levels(levels, output_file)

if __name__ == '__main__':
    main()
