#!/usr/bin/env python3
"""
Create a simple application icon for DecentSampler Library Creator.
This creates a basic icon if one doesn't exist.
"""

import os
from pathlib import Path

def create_simple_icon():
    """Create a simple icon file using PIL if available, otherwise create a placeholder."""
    try:
        from PIL import Image, ImageDraw
        
        # Create a 256x256 icon
        size = 256
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw a simple music note icon
        # Background circle
        margin = 20
        draw.ellipse([margin, margin, size-margin, size-margin], 
                    fill=(70, 130, 180, 255), outline=(50, 100, 150, 255), width=4)
        
        # Music note symbol
        note_size = 80
        note_x = size // 2 - note_size // 2
        note_y = size // 2 - note_size // 2
        
        # Draw a simple note shape
        draw.ellipse([note_x + 20, note_y + 10, note_x + 40, note_y + 30], fill=(255, 255, 255, 255))
        draw.rectangle([note_x + 35, note_y + 20, note_x + 45, note_y + 60], fill=(255, 255, 255, 255))
        draw.rectangle([note_x + 40, note_y + 50, note_x + 60, note_y + 70], fill=(255, 255, 255, 255))
        
        # Save as ICO
        img.save('icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
        print("Created icon.ico using PIL")
        return True
        
    except ImportError:
        print("PIL not available, creating placeholder icon file...")
        # Create a minimal ICO file header (placeholder)
        ico_data = b'\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00\x20\x00\x68\x05\x00\x00\x16\x00\x00\x00'
        ico_data += b'\x00' * 1400  # Minimal icon data
        
        with open('icon.ico', 'wb') as f:
            f.write(ico_data)
        print("Created placeholder icon.ico")
        return True

if __name__ == "__main__":
    if not os.path.exists('icon.ico'):
        create_simple_icon()
    else:
        print("icon.ico already exists")
