from __future__ import annotations

import pathlib

import cv2
import numpy as np

class Img:
    def __init__(self):
        self.img = None

    
    def read(self, path: str | pathlib.Path,
             size: tuple[int, int] | None = None,
             keep_aspect: bool = False,
             interpolation: int = cv2.INTER_AREA) -> "Img":
        """
        Load image using Unicode-safe method.
        """
        path = str(path)
        try:
            # קריאה בטוחה גם אם יש תווים בעברית
            data = np.fromfile(path, dtype=np.uint8)
            img = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
        except Exception as e:
            print(f"❌ Failed to load image {path}: {e}")
            img = None

        if img is None:
            print(f"⚠️ Warning: failed to load image {path}")
        else:
            print(f"📸 Loaded: {path}")

        self.img = img

        # אפשרות לresize
        if self.img is not None and size:
            self.img = cv2.resize(self.img, size, interpolation=interpolation)

        return self
    
    def draw_on(self, other_img, x, y):
        if self.img is None:
            print("self.img is None")
            return
        if other_img.img is None:
            print("other_img.img is None")
            return
        if not hasattr(self.img, "shape"):
            print("self.img has no shape")
            return
        if not hasattr(other_img.img, "shape"):
            print("other_img.img has no shape")
            return
        if self.img.shape[2] == 3:
            self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2BGRA)
        if self.img.shape[2] != other_img.img.shape[2]:
            print("Shape mismatch:", self.img.shape, other_img.img.shape)
            return

        h, w = self.img.shape[:2]
        H, W = other_img.img.shape[:2]

        if y + h > H or x + w > W:
            raise ValueError("Logo does not fit at the specified position.")

        roi = other_img.img[y:y + h, x:x + w]

        if self.img.shape[2] == 4:
            b, g, r, a = cv2.split(self.img)
            mask = a / 255.0
            for c in range(3):
                roi[..., c] = (1 - mask) * roi[..., c] + mask * self.img[..., c]
        else:
            other_img.img[y:y + h, x:x + w] = self.img

    def put_text(self, txt, x, y, font_size, color=(255, 255, 255, 255), thickness=1):
        if self.img is None:
            raise ValueError("Image not loaded.")
        cv2.putText(self.img, txt, (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, font_size,
                    color, thickness, cv2.LINE_AA)

    def show(self):
        if self.img is None:
            raise ValueError("Image not loaded.")
        cv2.imshow("Image", self.img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
