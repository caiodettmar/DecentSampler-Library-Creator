#!/usr/bin/env python3
"""
Create a professional app icon for DecentSampler Library Creator.
Generates a modern icon with sound wave and library elements using Pillow.
"""

from PIL import Image, ImageDraw, ImageFont
import math
import os

def create_gradient_background(width, height, color1, color2):
    """Create a gradient background."""
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)
    
    for y in range(height):
        # Calculate gradient ratio
        ratio = y / height
        # Interpolate between colors
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    return image

def draw_sound_wave(draw, center_x, center_y, width, height, color, amplitude=20):
    """Draw a stylized sound wave."""
    # Sound wave parameters
    wave_length = width * 0.8
    wave_height = height * 0.3
    num_points = 50
    
    points = []
    
    for i in range(num_points + 1):
        x = int(center_x - wave_length/2 + (i / num_points) * wave_length)
        # Create a smooth sine wave with some variation
        t = (i / num_points) * 4 * math.pi
        y_offset = math.sin(t) * amplitude + math.sin(t * 2) * amplitude * 0.3
        y = int(center_y + y_offset)
        points.append((x, y))
    
    # Draw the wave as connected lines
    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=color, width=3)
    
    # Add some decorative dots
    for i in range(0, len(points), 8):
        x, y = points[i]
        draw.ellipse([x-3, y-3, x+3, y+3], fill=color)

def draw_library_symbols(draw, center_x, center_y, size, color):
    """Draw library/document symbols."""
    # Draw a stylized document stack
    doc_width = size * 0.4
    doc_height = size * 0.6
    
    # Main document
    doc_x = center_x - doc_width/2
    doc_y = center_y - doc_height/2
    
    # Draw document with rounded corners
    draw.rounded_rectangle(
        [int(doc_x), int(doc_y), int(doc_x + doc_width), int(doc_y + doc_height)],
        radius=int(size * 0.05),
        fill=color,
        outline=None
    )
    
    # Add lines to represent text
    line_spacing = doc_height / 6
    for i in range(4):
        line_y = int(doc_y + line_spacing + i * line_spacing)
        line_width = doc_width * (0.8 - i * 0.1)  # Decreasing line lengths
        draw.line(
            [int(doc_x + doc_width * 0.1), line_y, 
             int(doc_x + doc_width * 0.1 + line_width), line_y],
            fill=(255, 255, 255), width=2
        )
    
    # Draw a second document (stacked effect)
    offset = size * 0.03
    draw.rounded_rectangle(
        [int(doc_x + offset), int(doc_y + offset), 
         int(doc_x + doc_width + offset), int(doc_y + doc_height + offset)],
        radius=int(size * 0.05),
        fill=(int(color[0] * 0.7), int(color[1] * 0.7), int(color[2] * 0.7)),
        outline=None
    )

def draw_music_note(draw, center_x, center_y, size, color):
    """Draw a stylized music note."""
    # Note head
    note_radius = int(size * 0.15)
    draw.ellipse(
        [center_x - note_radius, center_y - note_radius,
         center_x + note_radius, center_y + note_radius],
        fill=color
    )
    
    # Note stem
    stem_width = int(size * 0.08)
    stem_height = int(size * 0.4)
    # Ensure proper coordinate ordering (top-left to bottom-right)
    stem_top = center_y - note_radius - stem_height
    stem_bottom = center_y - note_radius
    stem_left = center_x + note_radius - stem_width//2
    stem_right = center_x + note_radius + stem_width//2
    draw.rectangle(
        [stem_left, stem_top, stem_right, stem_bottom],
        fill=color
    )
    
    # Flag
    flag_points = [
        (center_x + note_radius + stem_width//2, center_y - note_radius - stem_height),
        (center_x + note_radius + stem_width//2 + int(size * 0.2), center_y - note_radius - stem_height + int(size * 0.1)),
        (center_x + note_radius + stem_width//2, center_y - note_radius - stem_height + int(size * 0.2))
    ]
    draw.polygon(flag_points, fill=color)

def create_app_icon(size=512):
    """Create the main app icon."""
    # Create gradient background
    # Modern blue gradient
    color1 = (30, 60, 120)    # Dark blue
    color2 = (70, 130, 180)   # Light blue
    
    image = create_gradient_background(size, size, color1, color2)
    draw = ImageDraw.Draw(image)
    
    # Add subtle overlay for depth (only for larger sizes)
    if size >= 64:
        overlay = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Draw subtle radial gradient overlay
        for i in range(size//4):  # Reduced iterations for smaller sizes
            alpha = int(20 * (1 - i / (size//4)))
            overlay_draw.ellipse(
                [i, i, size-i, size-i],
                fill=(255, 255, 255, alpha),
                outline=None
            )
        
        # Composite overlay
        image = Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(image)
    
    # Main elements
    center_x = size // 2
    center_y = size // 2
    
    # Draw sound wave (primary element) - simplified for small sizes
    wave_color = (255, 255, 255)  # White
    if size >= 32:
        draw_sound_wave(draw, center_x, center_y - size * 0.1, size, size, wave_color, size * 0.08)
    else:
        # Simple wave for very small sizes
        wave_y = center_y - size * 0.1
        for i in range(5):
            x = center_x - size * 0.3 + i * size * 0.15
            y = wave_y + int(math.sin(i) * size * 0.1)
            draw.ellipse([x-2, y-2, x+2, y+2], fill=wave_color)
    
    # Draw library symbols (secondary element) - only for larger sizes
    if size >= 48:
        library_color = (200, 220, 255)  # Light blue
        draw_library_symbols(draw, center_x - size * 0.25, center_y + size * 0.15, size * 0.3, library_color)
    
    # Draw music note (accent element) - only for larger sizes
    if size >= 48:
        note_color = (255, 200, 100)  # Gold/yellow
        draw_music_note(draw, center_x + size * 0.25, center_y + size * 0.15, size * 0.25, note_color)
    
    # Add subtle border (only for larger sizes)
    if size >= 32:
        border_color = (100, 150, 200)
        draw.rectangle([0, 0, size-1, size-1], outline=border_color, width=max(1, size//256))
    
    return image

def create_icon_variants():
    """Create multiple icon sizes for different uses."""
    sizes = [16, 32, 48, 64, 128, 256, 512]
    icons = {}
    
    print("Creating icon variants...")
    for size in sizes:
        print(f"Creating {size}x{size} icon...")
        icon = create_app_icon(size)
        icons[size] = icon
    
    return icons

def save_icons(icons, base_name="app_icon"):
    """Save icons in different formats."""
    # Save individual PNG files
    for size, icon in icons.items():
        filename = f"{base_name}_{size}x{size}.png"
        icon.save(filename, "PNG")
        print(f"Saved: {filename}")
    
    # Create ICO file (Windows icon)
    ico_sizes = [16, 32, 48, 64, 128, 256]
    ico_images = [icons[size] for size in ico_sizes if size in icons]
    
    if ico_images:
        ico_images[0].save("icon.ico", format="ICO", sizes=[(size, size) for size in ico_sizes])
        print("Saved: icon.ico")
    
    # Create high-resolution PNG for documentation
    if 512 in icons:
        icons[512].save(f"{base_name}_high_res.png", "PNG")
        print("Saved: app_icon_high_res.png")

def main():
    """Main function to create the app icon."""
    print("DecentSampler Library Creator - Icon Generator")
    print("=" * 50)
    
    try:
        # Create icon variants
        icons = create_icon_variants()
        
        # Save icons
        save_icons(icons)
        
        print("\n" + "=" * 50)
        print("Icon generation completed successfully!")
        print("\nGenerated files:")
        print("- icon.ico (Windows icon file)")
        print("- app_icon_*.png (Various sizes)")
        print("- app_icon_high_res.png (High resolution)")
        
        print("\nThe icon features:")
        print("- Modern gradient background (blue theme)")
        print("- Sound wave visualization (primary element)")
        print("- Library/document symbols (secondary element)")
        print("- Music note accent (tertiary element)")
        print("- Clean, professional design suitable for audio applications")
        
    except ImportError:
        print("Error: Pillow library not found!")
        print("Please install it using: pip install Pillow")
        return False
    except Exception as e:
        print(f"Error creating icon: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
