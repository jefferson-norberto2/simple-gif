from gif_maker.gif_maker import GifMaker

if __name__ == "__main__":
    gif_maker = GifMaker()
    gif_maker.process(
        file_path='inputs/robot.mp4',
        output_path='outputs',
        scale=0.6,
        less_colors=True,
        max_frames=2000,
        frame_skip=5
    )