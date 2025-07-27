import pathlib
from It1_interfaces.Graphics import Graphics
from It1_interfaces.Board  import Board


class GraphicsFactory:
    def load(self,
             sprites_dir: pathlib.Path,
             cfg: dict,
             board: Board) -> Graphics:
        """Load graphics from sprites directory with configuration."""
        fps = cfg.get("frames_per_sec", 6)
        loop = cfg.get("is_loop", True)
        return Graphics(
            sprites_folder=sprites_dir,
            board=board,
            loop=loop,
            fps=fps
        )
