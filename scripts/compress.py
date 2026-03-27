from PIL import Image
import os

def convert_jpg_to_webp(jpg_path, webp_path, quality=80):
    try:
        with Image.open(jpg_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(webp_path, 'webp', quality=quality)
            print(f"Successfully converted {jpg_path} to {webp_path} with quality {quality}")

    except FileNotFoundError:
        print(f"Error: {jpg_path} not found.")
    except Exception as e:
        print(f"Failed to convert {jpg_path}: {e}")

# --- Example Usage ---
input_file = 'input_image.jpg' 
output_file = 'output_image.webp'
compression_quality = 85 # 

# Create a dummy image for testing if one doesn't exist
if not os.path.exists(input_file):
    print(f"Creating a sample image named '{input_file}' for demonstration.")
    sample_img = Image.new('RGB', (500, 500), color = 'red')
    sample_img.save(input_file, 'jpeg')

convert_jpg_to_webp(input_file, output_file, quality=compression_quality)
