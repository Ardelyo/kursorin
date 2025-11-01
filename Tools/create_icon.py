#!/usr/bin/env python3
"""
Create a simple camera icon for the UI system tray
"""

from PIL import Image, ImageDraw
import os

def create_camera_icon(size=64):
    """Create a simple camera icon"""
    # Create a new image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Camera body (rectangle)
    body_width = int(size * 0.8)
    body_height = int(size * 0.6)
    body_x = (size - body_width) // 2
    body_y = (size - body_height) // 2 + int(size * 0.1)

    # Draw camera body
    draw.rectangle([body_x, body_y, body_x + body_width, body_y + body_height],
                  fill=(100, 100, 100, 255), outline=(50, 50, 50, 255), width=2)

    # Lens (circle)
    lens_size = int(size * 0.3)
    lens_x = body_x + body_width // 2 - lens_size // 2
    lens_y = body_y + body_height // 2 - lens_size // 2

    draw.ellipse([lens_x, lens_y, lens_x + lens_size, lens_y + lens_size],
                fill=(30, 30, 30, 255), outline=(200, 200, 200, 255), width=2)

    # Inner lens reflection
    reflection_size = int(lens_size * 0.3)
    reflection_x = lens_x + lens_size // 4
    reflection_y = lens_y + lens_size // 4

    draw.ellipse([reflection_x, reflection_y, reflection_x + reflection_size, reflection_y + reflection_size],
                fill=(255, 255, 255, 200))

    # Flash (small square on top)
    flash_size = int(size * 0.15)
    flash_x = body_x + body_width - flash_size - int(size * 0.05)
    flash_y = body_y - flash_size // 2

    draw.rectangle([flash_x, flash_y, flash_x + flash_size, flash_y + flash_size],
                  fill=(255, 255, 0, 255), outline=(200, 200, 0, 255), width=1)

    # Save the icon
    img.save('camera_icon.png')
    print("✅ Camera icon created: camera_icon.png")

    # Also create .ico format for Windows
    try:
        img.save('camera_icon.ico', format='ICO', sizes=[(32, 32), (64, 64)])
        print("✅ Camera icon created: camera_icon.ico")
    except:
        print("ℹ️  ICO format not supported, PNG will work fine")

if __name__ == "__main__":
    create_camera_icon()
    print("\n🎨 Icon created! Place camera_icon.png in the same directory as camera_control_ui.py")
