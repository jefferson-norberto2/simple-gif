from simplegif import SimpleGIF

if __name__ == "__main__":
    gif_maker = SimpleGIF()

    gif_maker.convert_folder(
        path='inputs/',
        output_path='outputs',
        scale=0.6,
        less_colors=True,
        max_frames=2000,
        frame_skip=5
    )