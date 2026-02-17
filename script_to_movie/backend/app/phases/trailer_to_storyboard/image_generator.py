from abc import ABC, abstractmethod


class ImageGenerator(ABC):
    """Abstract interface for image generation APIs.

    Subclasses must implement `generate()` to call a real image generation
    service (DALL-E 3, Flux, Stable Diffusion, etc.) and return raw image bytes.
    """

    @abstractmethod
    async def generate(self, prompt: str, width: int = 1024, height: int = 576) -> bytes:
        """Generate an image from a text prompt.

        Args:
            prompt: Text description of the image to generate.
            width: Image width in pixels. Default 1024.
            height: Image height in pixels. Default 576.
                    Defaults are 16:9 aspect ratio for video compatibility.

        Returns:
            Raw image bytes (PNG or JPEG).
        """
        ...


class PlaceholderImageGenerator(ImageGenerator):
    """Placeholder for testing until a real image generation API is connected."""

    async def generate(self, prompt: str, width: int = 1024, height: int = 576) -> bytes:
        raise NotImplementedError("Connect a real image generation API here")
