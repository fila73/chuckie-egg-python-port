
import os
import re
from PIL import Image

def parse_skool(file_path):

    graphics = {}
    current_label = None
    current_data = []
    
    # dimensions determined from comments BEFORE the label
    pending_dims = (8, 0) 
    active_dims = (8, 0)
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        line = line.strip()
        
        if line.startswith(';'):
            # Try to extract dims
            dim_match = re.search(r'\((\d+)x(\d+)\)', line)
            if dim_match:
                pending_dims = (int(dim_match.group(1)), int(dim_match.group(2)))
            
            array_match = re.search(r'#UDGARRAY(\d+)', line)
            if array_match:
                width_bytes = int(array_match.group(1))
                pending_dims = (width_bytes * 8, 0) 
                
        elif line.startswith('@label='):
            label = line.split('=')[1]
            
            # Manual overrides
            if 'sprites_farmer' in label or 'sprites_duck' in label or 'sprites_ostrich' in label:
                 pending_dims = (16, 0)
                 
            if label == 'sprites_ostrich_eating_right':
                 pending_dims = (16, 16)
                 
            if label.startswith('gfx_') or label.startswith('font_') or label.startswith('sprites_'):
                if current_label:
                    graphics[current_label] = {'data': current_data, 'dims': active_dims}
                
                current_label = label
                current_data = []
                active_dims = pending_dims
            
            # Reset for next label regardless of whether we used it
            pending_dims = (8, 0)
                
        elif line.startswith('b$') or line.startswith('$'):
            # Data line: b$84f8 defb $30,$30...
            # or: $8500 defb $0c...
            if current_label and 'defb' in line:
                parts = line.split('defb')[1]
                # Split by comma, strip $
                bytes_str = parts.split(',')
                for b_str in bytes_str:
                    clean_b = b_str.strip().replace('$', '')
                    if clean_b:
                        try:
                           current_data.append(int(clean_b, 16))
                        except ValueError:
                           pass

    # Add last
    if current_label:
         graphics[current_label] = {'data': current_data, 'dims': active_dims}
         
    return graphics

def save_image(label, data, dims, output_dir):
    width, height = dims
    
    # If height is 0, calculate from data
    if height == 0 and width > 0:
        if len(data) > 0:
            height = (len(data) * 8) // width 
        else:
             return

    # If data is insufficient, pad? or truncate?
    # Ensure divisible by 8
    
    if len(data) == 0:
        print(f"Skipping empty {label}")
        return

    # Basic check
    expected_bytes = (width * height) // 8
    
    # Spectrum UDG format: usually scanlines.
    # If standard 8x8: 8 bytes, one per row.
    # If 16x8 (ARRAY2): 2 columns or 16px wide rows?
    # Comments say "Ladder (16x8)"
    # Data: 
    # b$84f8 defb $30,$30,$30,$3f,$3f,$30,$30,$30  (8 bytes)
    #  $8500 defb $0c,$0c,$0c,$fc,$fc,$0c,$0c,$0c  (8 bytes)
    # $30 = 00110000. $0c = 00001100.
    # If it's a ladder, it should look symmetric.
    # Left half, right half?
    # Usually Spectrum UDG arrays are stored column by column (left 8x8, then right 8x8).
    # Let's assume column-major for blocks > 8px width, OR check if it's row-major 16px.
    # Spectrum standard is character blocks. So 16x8 is likely two 8x8 chars.
    # So we should render as blocks of 8x8.
    
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    pixels = img.load()
    
    is_sprite = 'sprites_' in label
    
    if is_sprite:
        # Linear Scanline Order
        # Data is stored Row by Row.
        # Row 0: Byte 0, Byte 1...
        bytes_per_row = width // 8
        
        for y in range(height):
            for b_idx in range(bytes_per_row):
                idx = y * bytes_per_row + b_idx
                if idx >= len(data): break
                
                byte = data[idx]
                base_x = b_idx * 8
                
                for x in range(8):
                    if (byte >> (7-x)) & 1:
                        pixels[base_x + x, y] = (255, 255, 255, 255)
    else:
        # UDG Block Order (8x8 chunks)
        data_idx = 0
        chars_w = width // 8
        chars_h = height // 8
        
        for cy in range(chars_h):
            for cx in range(chars_w):
                # Render one 8x8 char
                if data_idx + 8 > len(data):
                    break
                    
                char_bytes = data[data_idx:data_idx+8]
                data_idx += 8
                
                for y in range(8):
                    byte = char_bytes[y]
                    for x in range(8):
                        # Bit 7 is leftmost
                        if (byte >> (7-x)) & 1:
                            # White pixel
                            pixels[cx*8 + x, cy*8 + y] = (255, 255, 255, 255)
                        
    img.save(os.path.join(output_dir, f"{label}.png"))
    print(f"Saved {label}.png ({width}x{height})")

def main():
    skool_file = os.path.join(os.path.dirname(__file__), '../../chuckie-egg.skool')
    output_dir = os.path.join(os.path.dirname(__file__), '../assets/sprites')
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Parsing {skool_file}...")
    graphics = parse_skool(skool_file)
    
    print(f"Found {len(graphics)} graphic items.")
    
    for label, info in graphics.items():
        save_image(label, info['data'], info['dims'], output_dir)

if __name__ == '__main__':
    main()
