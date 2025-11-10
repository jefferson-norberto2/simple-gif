# Simple GIF Maker

A Python tool to convert video files into optimized GIFs with customizable options.

## Features
- Convert video files to GIF format.
- Scale GIF size.
- Reduce color palette for smaller file sizes.
- Process multiple files in a folder.

## Installation methods

### Using Poetry
1. Clone the repository:
   ```bash
   git clone https://github.com/jefferson-norberto2/simple-gif.git
   ```

2. Install the required dependencies using Poetry:
    ```bash
    poetry install
    ```
### Using pip
1. Download the wheel file from the releases section of the repository.

2. Install the wheel file using pip:
    ```bash
    pip install simple_gif-<version>-py3-none-any.whl
    ```

## Usage
1. Import the `SimpleGIF` class from the `simplegif` module.
    ```python
    from simplegif import SimpleGIF
    ```
2. Create an instance of `SimpleGIF`.
    ```python
    gif_maker = SimpleGIF()
    ```

3. Use the `convert_file` method to convert a single video file.
    ```python
    gif_maker.convert_file(
        file_path='inputs/example.mp4',
        output_path='outputs',
        scale=0.6,
        less_colors=True,
        max_frames=2000,
        frame_skip=5
    )
    ```

4. Use the `convert_folder` method to convert all video files in a folder.
    ```python
    gif_maker.convert_folder(
        folder_path='inputs/',
        output_path='outputs',
        scale=0.6,
        less_colors=True,
        max_frames=2000,
        frame_skip=5
    )
    ```

## License
This project is licensed under the MIT License. See the LICENSE file for details.