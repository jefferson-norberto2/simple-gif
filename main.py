"""Script principal para conversão em lote de vídeos para GIF usando simplegif."""

from pathlib import Path

from simplegif import SimpleGIF


def main() -> None:
    """Executa a conversão de todos os vídeos da pasta inputs/ para a pasta outputs/."""
    input_folder = Path("inputs")
    output_folder = Path("outputs")

    input_folder.mkdir(parents=True, exist_ok=True)
    output_folder.mkdir(parents=True, exist_ok=True)

    gif_maker = SimpleGIF()

    print(f"Buscando vídeos em: {input_folder.resolve()}")
    converted_files = gif_maker.convert_folder(
        path=input_folder,
        output_path=output_folder,
        scale=0.6,
        less_colors=True,
        max_frames=2000,
        frame_skip=5,
        overwrite=True,
    )

    if converted_files:
        print(f"{len(converted_files)} GIF(s) gerado(s) com sucesso em: {output_folder.resolve()}")
        for gif in converted_files:
            print(f" - {gif.name}")
    else:
        print(f"Nenhum arquivo de vídeo encontrado para conversão em: {input_folder.resolve()}")


if __name__ == "__main__":
    main()
