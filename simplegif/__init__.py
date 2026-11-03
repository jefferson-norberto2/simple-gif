"""Pacote simplegif para conversão offline e segura de vídeos em GIFs animados."""

from simplegif.config import ConversionOptions, VideoMetadata
from simplegif.processor import FrameProcessor
from simplegif.reader import VideoReader
from simplegif.core import SimpleGIF
from simplegif.writer import GifWriter

__all__ = [
    "SimpleGIF",
    "ConversionOptions",
    "VideoMetadata",
    "VideoReader",
    "FrameProcessor",
    "GifWriter",
]
