# Gemini Image Labeler

A modern, sleek, and efficient Python GUI tool for manually labeling images. Built with `customtkinter` for a polished look and optimized for speed and usability.

![GUI Screenshot](https://via.placeholder.com/1000x700?text=Insert+Screenshot+Here)
*(Place your screenshot here)*

## Features

*   **Modern UI:** Clean, dark-mode compatible interface built with CustomTkinter.
*   **Broad Format Support:** Supports standard image formats (JPG, PNG, GIF, BMP, WEBP, TIFF) and **HEIC/HEIF** (common on iPhones).
*   **Efficient Workflow:**
    *   **Keyboard Navigation:** Use Left/Right arrow keys to navigate.
    *   **Auto-Advance:** Automatically moves to the next image after selecting a label.
    *   **Hide Labeled:** Option to filter out already labeled images to focus only on new work.
*   **Flexible Labeling:**
    *   Pre-defined categories (configurable).
    *   Add custom categories on the fly.
    *   Edit category lists dynamically.
*   **Organization:**
    *   **Organize Files:** Automatically copy or move labeled images into subfolders based on their category (e.g., `labelled_images/cat`, `labelled_images/dog`).
    *   **Robust Handling:** Skips files that already exist in the destination to prevent duplicates.
*   **Data Persistence:** Labels are saved to a CSV file (default: `image_labels.csv`). You can switch between different label files.
*   **Progress Tracking:** Visual progress bar and counters show your completion status.

## Installation & Usage

This project is designed to be run with [uv](https://github.com/astral-sh/uv), a fast Python package installer and runner.

### Prerequisites

*   **uv:** [Install uv](https://github.com/astral-sh/uv#installation)

### Running the Application

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/shubhamgoel27/gemini-image-labeler.git
    cd gemini-image-labeler
    ```

2.  **Run with uv:**
    `uv` will automatically handle Python version management (requires Python >= 3.13) and dependency installation (`customtkinter`, `Pillow`, `pillow-heif`).

    ```bash
    uv run label_images_gui.py
    ```

### Manual Installation (Alternative)

If you prefer standard pip:

1.  Ensure you have Python 3.13 or newer installed.
2.  Install dependencies:
    ```bash
    pip install customtkinter Pillow packaging pillow-heif
    ```
3.  Run the script:
    ```bash
    python label_images_gui.py
    ```

## Usage Guide

1.  **Open Folder:** Click "Open Folder" to select the directory containing your images.
2.  **Labeling:** Click a category button on the right, or type a custom category and click "Add". The image will be labeled and the app will advance to the next one.
3.  **Hide Labeled:** Check the "Hide Labeled" box to remove finished images from view.
4.  **Organize:** When finished, click "Organize Files" to move or copy your images into folder structures based on their labels.

## Configuration

The application automatically saves your preferences (last folder, categories, etc.) to a `config.json` file in the same directory.
