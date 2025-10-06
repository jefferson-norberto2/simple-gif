from cv2 import (VideoCapture, 
                 resize, 
                 cvtColor, 
                 COLOR_BGR2RGB, 
                 CAP_PROP_FRAME_WIDTH, 
                 CAP_PROP_FRAME_HEIGHT, 
                 CAP_PROP_FRAME_COUNT)

from numpy import array, uint8
from PIL.Image import fromarray, Image
from typing import List
from tqdm import tqdm

class GifMaker:
    def __init__(self):
        self._scale = None
        self._less_colors_flag = None
        self._name_file = None
        self._input_path = None
        self._output_path = None
        self._save_name = None

        self._frames : List[Image] = []
    
    def process(self, 
                file_path = 'gif_maker/inputs/example.mp4', 
                output_path='gif_maker/outputs', 
                scale=0.6, 
                less_colors=False,
                max_frames=2000, 
                frame_skip=5):
        
        self._name_file = file_path.split('/')[-1]
        self._save_name = self._name_file.rsplit('.', 1)[0]
        self._input_path = file_path.rsplit('/', 1)[0]
        self._output_path = output_path
        self._scale = scale
        self._less_colors_flag = less_colors

        self._process_video(max_frames, frame_skip)
        self._save_gif()
    
    def _process_video(self, max_frames:int, frame_skip:int):
        self._cap = VideoCapture(f'{self._input_path}/{self._name_file}')
        
        self._width = int(self._cap.get(CAP_PROP_FRAME_WIDTH) * self._scale)
        self._height = int(self._cap.get(CAP_PROP_FRAME_HEIGHT) * self._scale)

        image_count = 0
        total_frames = int(self._cap.get(CAP_PROP_FRAME_COUNT))

        _, frame = self._cap.read()

        print('Reading video file...')

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
        if self._frames:
            print("Saving GIF file ...")
            
            first_frame = self._frames[0]
            
            first_frame.save(
                f"{self._output_path}/{self._save_name}.gif",
                save_all=True,
                append_images=self._frames[1:],
                optimize=True,
                duration=100,  
                loop=0
            )
            print("GIF saved successfully.")
        else:
            print("No frames to save.")

    def less_colors(self, image):
        data = array(image)
        r_data = (data // 8) * 8
        return r_data.astype(uint8)