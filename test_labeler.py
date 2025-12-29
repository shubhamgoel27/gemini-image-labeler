# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pytest",
#     "customtkinter",
#     "Pillow",
#     "packaging",
#     "pillow-heif",
# ]
# ///

import os
import shutil
import csv
import json
import pytest
from pathlib import Path
from label_images_gui import LabelSession, CONFIG_FILE

# Fixture for a temporary directory with some dummy images
@pytest.fixture
def temp_workspace(tmp_path):
    # Setup
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    
    # Create dummy images
    (images_dir / "img1.jpg").touch()
    (images_dir / "img2.png").touch()
    (images_dir / "img3.jpg").touch()
    
    # Switch working directory to temp path so config/csv are created there
    cwd = os.getcwd()
    os.chdir(tmp_path)
    
    yield tmp_path, images_dir
    
    # Teardown
    os.chdir(cwd)

def test_initialization(temp_workspace):
    session = LabelSession()
    assert session.current_index == 0
    assert session.hide_labeled is True
    assert session.image_files == []

def test_load_images(temp_workspace):
    _, images_dir = temp_workspace
    session = LabelSession()
    session.load_images_from_folder(str(images_dir))
    
    assert len(session.all_image_files) == 3
    assert len(session.image_files) == 3
    # Check sorting
    assert session.all_image_files[0].name == "img1.jpg"

def test_save_label_and_filter(temp_workspace):
    _, images_dir = temp_workspace
    session = LabelSession()
    session.load_images_from_folder(str(images_dir))
    
    # Label the first image
    success = session.save_label("cat")
    assert success is True
    assert len(session.labels) == 1
    assert str(session.all_image_files[0]) in session.labels
    assert session.labels[str(session.all_image_files[0])] == "cat"
    
    # Since hide_labeled is True by default, image_files should reduce by 1
    session.apply_filter() # save_label calls it internally in logic? No, GUI calls refresh. 
    # Logic class save_label does NOT call apply_filter automatically to allow UI to animate.
    # So we call it manually here to test logic.
    session.apply_filter()
    
    assert len(session.image_files) == 2
    assert session.image_files[0].name == "img2.png"

def test_csv_persistence(temp_workspace):
    tmp_path, images_dir = temp_workspace
    session = LabelSession()
    session.load_images_from_folder(str(images_dir))
    session.save_label("dog")
    
    # Check if CSV was created
    assert os.path.exists("image_labels.csv")
    
    # Read CSV
    with open("image_labels.csv", "r") as f:
        content = f.read()
    assert "img1.jpg" in content
    assert "dog" in content

    # Create a new session and load
    session2 = LabelSession()
    session2.load_labels()
    assert len(session2.labels) == 1
    assert session2.labels[str(session.all_image_files[0])] == "dog"

def test_undo(temp_workspace):
    _, images_dir = temp_workspace
    session = LabelSession()
    session.load_images_from_folder(str(images_dir))
    
    img1_path = str(session.image_files[0])
    session.save_label("car")
    
    assert len(session.labels) == 1
    assert len(session.history) == 1
    
    # Undo
    restored_path = session.undo()
    
    assert len(session.labels) == 0
    assert len(session.history) == 0
    assert restored_path == img1_path
    
    # Verify removed from CSV
    with open("image_labels.csv", "r") as f:
        content = f.read()
    assert "img1.jpg" not in content

def test_trash(temp_workspace):
    tmp_path, images_dir = temp_workspace
    session = LabelSession()
    session.load_images_from_folder(str(images_dir))
    
    img_to_trash = session.image_files[0]
    img_path = str(img_to_trash)
    
    assert img_to_trash.exists()
    
    success = session.move_to_trash()
    assert success is True
    
    # File should not exist in original location
    assert not img_to_trash.exists()
    
    # File should exist in trash
    trash_path = images_dir / "trash" / img_to_trash.name
    assert trash_path.exists()
    
    # Should be removed from lists
    assert img_to_trash not in session.all_image_files
    assert len(session.image_files) == 2

def test_config_save_load(temp_workspace):
    session = LabelSession()
    session.categories.append("new_cat")
    session.image_folder = "some/path"
    session.save_config()
    
    assert os.path.exists(CONFIG_FILE)
    
    session2 = LabelSession()
    session2.load_config()
    assert "new_cat" in session2.categories
    assert session2.image_folder == "some/path"
