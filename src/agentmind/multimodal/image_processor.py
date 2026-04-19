"""Image processing utilities for AgentMind."""

import base64
import io
from enum import Enum
from pathlib import Path
from typing import Optional, Union, Tuple

try:
    from PIL import Image as PILImage

    PIL_AVAILABLE = True
    Image = PILImage
except ImportError:
    PIL_AVAILABLE = False
    Image = None  # type: ignore


class ImageFormat(str, Enum):
    """Supported image formats."""

    PNG = "png"
    JPEG = "jpeg"
    JPG = "jpg"
    WEBP = "webp"
    GIF = "gif"


class ImageProcessor:
    """Process images for multi-modal agent interactions."""

    def __init__(self, max_size: Tuple[int, int] = (1024, 1024)):
        """Initialize image processor.

        Args:
            max_size: Maximum image dimensions (width, height)
        """
        if not PIL_AVAILABLE:
            raise ImportError(
                "PIL/Pillow is required for image processing. " "Install with: pip install Pillow"
            )
        self.max_size = max_size

    def load_image(self, path: Union[str, Path]) -> "PILImage.Image":
        """Load an image from file.

        Args:
            path: Path to image file

        Returns:
            PIL Image object
        """
        return Image.open(path)

    def resize_image(
        self, image: "PILImage.Image", max_size: Optional[Tuple[int, int]] = None
    ) -> "PILImage.Image":
        """Resize image while maintaining aspect ratio.

        Args:
            image: PIL Image object
            max_size: Maximum dimensions, defaults to self.max_size

        Returns:
            Resized PIL Image object
        """
        max_size = max_size or self.max_size
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        return image

    def image_to_base64(
        self, image: Union["PILImage.Image", str, Path], format: ImageFormat = ImageFormat.PNG
    ) -> str:
        """Convert image to base64 string.

        Args:
            image: PIL Image object or path to image
            format: Output format

        Returns:
            Base64 encoded string
        """
        if isinstance(image, (str, Path)):
            image = self.load_image(image)

        buffered = io.BytesIO()
        image.save(buffered, format=format.value.upper())
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str

    def base64_to_image(self, base64_str: str) -> "PILImage.Image":
        """Convert base64 string to PIL Image.

        Args:
            base64_str: Base64 encoded image string

        Returns:
            PIL Image object
        """
        img_data = base64.b64decode(base64_str)
        return Image.open(io.BytesIO(img_data))

    def prepare_for_llm(
        self, image: Union["PILImage.Image", str, Path], format: ImageFormat = ImageFormat.PNG
    ) -> dict:
        """Prepare image for LLM input.

        Args:
            image: PIL Image object or path to image
            format: Output format

        Returns:
            Dictionary with image data for LLM
        """
        if isinstance(image, (str, Path)):
            image = self.load_image(image)

        # Resize if needed
        if image.size[0] > self.max_size[0] or image.size[1] > self.max_size[1]:
            image = self.resize_image(image)

        # Convert to base64
        base64_str = self.image_to_base64(image, format)

        return {
            "type": "image",
            "source": {"type": "base64", "media_type": f"image/{format.value}", "data": base64_str},
        }

    def save_image(
        self, image: "PILImage.Image", path: Union[str, Path], format: Optional[ImageFormat] = None
    ) -> None:
        """Save image to file.

        Args:
            image: PIL Image object
            path: Output path
            format: Image format, inferred from path if not provided
        """
        if format is None:
            # Infer from path extension
            ext = Path(path).suffix.lower().lstrip(".")
            format = (
                ImageFormat(ext) if ext in ImageFormat.__members__.values() else ImageFormat.PNG
            )

        image.save(path, format=format.value.upper())

    def create_thumbnail(
        self, image: Union["PILImage.Image", str, Path], size: Tuple[int, int] = (128, 128)
    ) -> "PILImage.Image":
        """Create a thumbnail of the image.

        Args:
            image: PIL Image object or path to image
            size: Thumbnail size

        Returns:
            Thumbnail PIL Image object
        """
        if isinstance(image, (str, Path)):
            image = self.load_image(image)

        thumb = image.copy()
        thumb.thumbnail(size, Image.Resampling.LANCZOS)
        return thumb

    def get_image_info(self, image: Union["PILImage.Image", str, Path]) -> dict:
        """Get information about an image.

        Args:
            image: PIL Image object or path to image

        Returns:
            Dictionary with image metadata
        """
        if isinstance(image, (str, Path)):
            image = self.load_image(image)

        return {
            "format": image.format,
            "mode": image.mode,
            "size": image.size,
            "width": image.width,
            "height": image.height,
        }
