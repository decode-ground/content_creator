/**
 * Image generation placeholder
 *
 * This module provides a stub implementation that returns placeholder images.
 * Replace with a real image generation service (DALL-E, Stable Diffusion, etc.) in the future.
 */

export type GenerateImageOptions = {
  prompt: string;
  originalImages?: Array<{
    url?: string;
    b64Json?: string;
    mimeType?: string;
  }>;
};

export type GenerateImageResponse = {
  url?: string;
};

const PLACEHOLDER_IMAGE_URL = "https://placehold.co/1024x1024/2a2a2a/white?text=Image+Generation+Not+Configured";

export async function generateImage(
  options: GenerateImageOptions
): Promise<GenerateImageResponse> {
  console.warn(
    "[Image Generation] Image generation is not configured. Returning placeholder image.",
    { promptLength: options.prompt.length }
  );

  return {
    url: PLACEHOLDER_IMAGE_URL,
  };
}
