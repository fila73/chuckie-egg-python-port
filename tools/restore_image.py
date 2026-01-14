"""
ZX Spectrum Loading Screen Restorer for Chuckie Egg
Parses loading-screen.skool and generates a PNG image.
"""

import pygame
import os
import re

def parse_skool_file(filepath):
    """
    Parses a .skool file and returns a bytearray of data.
    Assumes standard format: $ADDR DEFB $XX,$XX...
    """
    screen_data = bytearray(6912) # 6144 (bitmap) + 768 (attributes)
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if 'DEFB' not in line:
                continue
            
            # Match address and hex bytes
            # Example: $4090 DEFB $07,$E0,$00...
            match = re.search(r'\$([0-9A-Fa-f]{4})\s+DEFB\s+(.*)', line)
            if match:
                addr_hex = match.group(1)
                bytes_str = match.group(2)
                
                addr = int(addr_hex, 16)
                if 0x4000 <= addr <= 0x5AFF:
                    # Clean up bytes string and split
                    hex_values = bytes_str.replace('$', '').split(',')
                    for i, h in enumerate(hex_values):
                        if h.strip():
                            val = int(h.strip(), 16)
                            offset = addr + i - 0x4000
                            if offset < len(screen_data):
                                screen_data[offset] = val
                                
    return screen_data

def get_spectrum_color(color_idx, bright=False):
    """Returns (R,G,B) for a Spectrum color index (0-7)."""
    val = 255 if bright else 200
    colors = [
        (0, 0, 0),       # 0: Black
        (0, 0, val),     # 1: Blue
        (val, 0, 0),     # 2: Red
        (val, 0, val),   # 3: Magenta
        (0, val, 0),     # 4: Green
        (0, val, val),   # 5: Cyan
        (val, val, 0),   # 6: Yellow
        (255, 255, 255)  # 7: White
    ]
    if color_idx == 7 and not bright:
        colors[7] = (200, 200, 200) # Dim white (grey)
    return colors[color_idx]

def restore_image(screen_data, output_path):
    """Reconstructs the 256x192 screen and saves as image."""
    pygame.init()
    surface = pygame.Surface((256, 192))
    
    bitmap = screen_data[:6144]
    attribs = screen_data[6144:6912]
    
    # Render pixels
    for y in range(192):
        for x_byte in range(32):
            # Calculate address in Spectrum memory for (x_byte, y)
            # Address = 010 (Section) | Scanline (0-7) | Row (0-7) | Column (0-31)
            # Binary: 010 s2 s1 s0 r2 r1 r0 c4 c3 c2 c1 c0
            # s = y % 8
            # r = (y // 8) % 8
            # section = y // 64
            
            section = y // 64
            row = (y // 8) % 8
            scanline = y % 8
            
            addr = (section << 11) | (scanline << 8) | (row << 5) | x_byte
            byte_val = bitmap[addr]
            
            # Get attribute for this 8x8 block
            attr_addr = (y // 8) * 32 + x_byte
            attr = attribs[attr_addr]
            
            # Flash | Bright | Paper(3) | Ink(3)
            bright = bool(attr & 0x40)
            paper_idx = (attr >> 3) & 0x07
            ink_idx = attr & 0x07
            
            paper_color = get_spectrum_color(paper_idx, bright)
            ink_color = get_spectrum_color(ink_idx, bright)
            
            # Bits (from MSB to LSB)
            for bit in range(8):
                if (byte_val >> (7 - bit)) & 0x01:
                    surface.set_at((x_byte * 8 + bit, y), ink_color)
                else:
                    surface.set_at((x_byte * 8 + bit, y), paper_color)
                    
    pygame.image.save(surface, output_path)
    print(f"Loading screen restored to: {output_path}")
    pygame.quit()

if __name__ == "__main__":
    input_file = "loading-screen.skool"
    output_dir = os.path.join("assets", "graphics")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "loading_screen.png")
    
    if os.path.exists(input_file):
        data = parse_skool_file(input_file)
        restore_image(data, output_file)
    else:
        print(f"Error: {input_file} not found.")
