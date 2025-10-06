from simplegif.simplegif import SimpleGIF

if __name__ == "__main__":
    gif_maker = SimpleGIF()
    gif_maker.process(
        file_path='inputs/robot.mp4',
        output_path='outputs',
        scale=0.6,
        less_colors=True,
        max_frames=2000,
        frame_skip=5
    )