from cv2 import (VideoCapture, 
                 resize, 
                 cvtColor, 
                 COLOR_BGR2RGB, 
                 CAP_PROP_FRAME_WIDTH, 
                 CAP_PROP_FRAME_HEIGHT, 
                 CAP_PROP_FRAME_COUNT)

from tqdm import tqdm
from os import listdir
from typing import List
from numpy import array, uint8
from PIL.Image import fromarray, Image
from os.path import isfile, isdir, exists, join

class SimpleGIF:
    '''A class to convert video files to GIF format.

    Methods:
        - convert_file: Convert a single video file to GIF.
        - convert_folder: Convert all video files in a folder to GIF.
    '''
    def __init__(self):
        self._scale = None
        self._less_colors_flag = None
        self._last_name_file = None
        self._input_path = None
        self._output_path = None
        self._save_name = None
        self._frames : List[Image] = []
    
    def _adjust_parameters(
            self, path:str, 
            output_path:str, 
            scale:float, 
            less_colors:bool):
        '''Adjust internal parameters based on input.
        
        Args:
            path (str): Path to the input video file.
            output_path (str): Path to save the output GIF.
            scale (float): Scaling factor for the video frames.
            less_colors (bool): Flag to reduce color depth.
        '''
        self._last_name_file = path.split('/')[-1]
        self._save_name = self._last_name_file.rsplit('.', 1)[0]
        self._input_path = path.rsplit('/', 1)[0]
        self._output_path = output_path
        self._scale = scale
        self._less_colors_flag = less_colors
    
    def convert_file(self, 
                path = 'inputs/example.mp4', 
                output_path='outputs', 
                scale=0.6, 
                less_colors=False,
                max_frames=2000, 
                frame_skip=5):
        '''Convert a single video file to GIF format.
        
        Args:
            path (str): Path to the input video file.
            output_path (str): Path to save the output GIF.
            scale (float): Scaling factor for the video frames.
            less_colors (bool): Flag to reduce color depth.
            max_frames (int): Maximum number of frames to process.
            frame_skip (int): Number of frames to skip between processed frames.
        '''
        if not isfile(path):
            print(f"Error: {path} is not a valid file path.", end="\n\n")
        else:
            self._adjust_parameters(path, output_path, scale, less_colors)

            save_path = f"{self._output_path}/{self._save_name}.gif"
            if exists(save_path):
                print(f"Error: {save_path} already exists on {self._output_path}.", end="\n\n")
            else:
                self._process_video(max_frames, frame_skip)
                self._save_gif()
    
    def convert_folder(self, path='inputs/', 
                       output_path='outputs', 
                       scale=0.6, 
                       less_colors=False,
                       max_frames=2000, 
                       frame_skip=5):
        '''Convert all video files in a folder to GIF format.
        
        Args:
            path (str): Path to the input folder containing video files.
            output_path (str): Path to save the output GIFs.
            scale (float): Scaling factor for the video frames.
            less_colors (bool): Flag to reduce color depth.
            max_frames (int): Maximum number of frames to process per video.
            frame_skip (int): Number of frames to skip between processed frames.
        '''
        
        if not isdir(path):
            print(f"Error: {path} is not a valid folder path.", end="\n\n")
            return
        
        for file_name in listdir(path):
            if file_name.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                self.convert_file(
                    path=join(path, file_name),
                    output_path=output_path,
                    scale=scale,
                    less_colors=less_colors,
                    max_frames=max_frames,
                    frame_skip=frame_skip
                )
    
    def _process_video(self, max_frames:int, frame_skip:int):
        '''Process the video file and extract frames.
        
        Args:
            max_frames (int): Maximum number of frames to process.
            frame_skip (int): Number of frames to skip between processed frames.
        '''
        self._cap = VideoCapture(f'{self._input_path}/{self._last_name_file}')
        
        self._width = int(self._cap.get(CAP_PROP_FRAME_WIDTH) * self._scale)
        self._height = int(self._cap.get(CAP_PROP_FRAME_HEIGHT) * self._scale)

        image_count = 0
        total_frames = int(self._cap.get(CAP_PROP_FRAME_COUNT))

        _, frame = self._cap.read()

        print(f'Reading {self._last_name_file} video file')

        for _ in tqdm(range(min(total_frames, max_frames))):
            if image_count % frame_skip == 0:
                frame = resize(frame, (self._width, self._height))
                rgb_frame = cvtColor(frame, COLOR_BGR2RGB)
                
                if self._less_colors_flag:
                    rgb_frame = self.less_colors(rgb_frame) 
                
                pil_img = fromarray(rgb_frame)
                self._frames.append(pil_img)
                
            image_count += 1
            _, frame = self._cap.read()

        self._cap.release()
    
    def _save_gif(self):
        '''Save the processed frames as a GIF file.
        '''
        if self._frames:
            save_path = f"{self._output_path}/{self._save_name}.gif"
            print(f"Saving file in {save_path}")
            
            first_frame = self._frames[0]
            
            first_frame.save(
                f"{self._output_path}/{self._save_name}.gif",
                save_all=True,
                append_images=self._frames[1:],
                optimize=True,
                duration=100,  
                loop=0
            )
            print("GIF saved successfully.", end="\n\n")
        else:
            print("No frames to save.", end="\n\n")

    def less_colors(self, image):
        '''Reduce the color depth of an image.
        Args:
            image (ndarray): Input image array.
        Returns:
            ndarray: Image array with reduced color depth.
        '''
        data = array(image)
        r_data = (data // 8) * 8
        return r_data.astype(uint8)