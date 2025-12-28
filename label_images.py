# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "Pillow",
# ]
# ///

import os
import csv
import sys
import datetime
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow is required. Please install it (e.g., 'pip install Pillow') or run with 'uv run'.")
    sys.exit(1)

# --- Configuration ---
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
DEFAULT_CATEGORIES = ["cat", "dog", "car", "person", "other"]
OUTPUT_FILE = "labels.csv"
IMAGE_FOLDER = "images"

def get_image_files(folder):
    """Scans the folder for image files with supported extensions."""
    path = Path(folder)
    if not path.exists():
        print(f"Warning: Folder '{folder}' does not exist.")
        return []
    
    files = []
    for f in path.iterdir():
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS:
            files.append(f)
    return sorted(files)

def load_existing_labels(csv_file):
    """Loads already labeled image paths from the CSV file."""
    labeled = set()
    if not os.path.exists(csv_file):
        return labeled
    
    with open(csv_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            header = next(reader) # Skip header
        except StopIteration:
            return labeled # Empty file
            
        for row in reader:
            if row:
                labeled.add(row[0])
    return labeled

def append_label(csv_file, image_path, category):
    """Appends a new label to the CSV file."""
    file_exists = os.path.exists(csv_file)
    
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["image_path", "category", "timestamp"])
        
        writer.writerow([str(image_path), category, datetime.datetime.now().isoformat()])

def main():
    print(f"--- Image Labeler ---")
    print(f"Scanning folder: {IMAGE_FOLDER}")
    print(f"Saving to: {OUTPUT_FILE}")
    print("Press Ctrl+C to exit safely.\n")

    labeled_images = load_existing_labels(OUTPUT_FILE)
    all_images = get_image_files(IMAGE_FOLDER)
    
    images_to_process = [img for img in all_images if str(img) not in labeled_images]
    
    total = len(all_images)
    remaining = len(images_to_process)
    skipped = total - remaining
    
    print(f"Found {total} images. {skipped} already labeled. {remaining} to go.\n")
    
    if remaining == 0:
        print("All images labeled! Exiting.")
        return

    try:
        for i, img_path in enumerate(images_to_process):
            print(f"[{i+1}/{remaining}] processing: {img_path}")
            
            # Show image
            try:
                with Image.open(img_path) as img:
                    # Show image using the default OS viewer
                    img.show()
            except Exception as e:
                print(f"Error opening image {img_path}: {e}")
                continue

            # Prompt user
            while True:
                print("Categories:")
                for idx, cat in enumerate(DEFAULT_CATEGORIES):
                    print(f"  {idx + 1}. {cat}")
                print("  c. Custom category")
                print("  s. Skip")
                
                choice = input("Select category: ").strip().lower()
                
                selected_category = None
                
                if choice == 's':
                    print("Skipping...")
                    break # Break inner loop to go to next image
                
                if choice == 'c':
                    custom = input("Enter custom category: ").strip()
                    if custom:
                        selected_category = custom
                    else:
                        print("Empty category not allowed.")
                        continue
                elif choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(DEFAULT_CATEGORIES):
                        selected_category = DEFAULT_CATEGORIES[idx]
                    else:
                        print("Invalid selection.")
                        continue
                else:
                     # Check if they typed the category name directly
                    if choice in DEFAULT_CATEGORIES:
                        selected_category = choice
                    else:
                        print("Invalid input. Enter a number or 'c'.")
                        continue
                
                if selected_category:
                    append_label(OUTPUT_FILE, img_path, selected_category)
                    print(f"Saved: {selected_category}")
                    break
            
            print("-" * 20)

    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user. Progress saved.")
        sys.exit(0)

    print("Done scanning images.")

if __name__ == "__main__":
    main()
