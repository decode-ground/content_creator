import { generateImage } from "./_core/imageGeneration";
import { storagePut } from "./storage";
import { nanoid } from "nanoid";

const PLACEHOLDER_PREFIX = "https://placehold.co/";

/**
 * Generates a storyboard image for a scene and uploads it to S3
 */
export async function generateSceneStoryboard(
  prompt: string,
  projectId: number,
  sceneId: number
): Promise<{ imageUrl: string; imageKey: string }> {
  try {
    const { url: imageUrl } = await generateImage({
      prompt,
    });

    if (!imageUrl) {
      throw new Error("Image generation failed - no URL returned");
    }

    // If it's a placeholder image, return it directly without S3 upload
    if (imageUrl.startsWith(PLACEHOLDER_PREFIX)) {
      return {
        imageUrl,
        imageKey: `placeholder/scene-${sceneId}`,
      };
    }

    // Download the image and upload to S3
    const response = await fetch(imageUrl);
    const buffer = await response.arrayBuffer();

    const fileKey = `projects/${projectId}/storyboards/scene-${sceneId}-${nanoid()}.jpg`;
    const { url: s3Url } = await storagePut(fileKey, Buffer.from(buffer), "image/jpeg");

    return {
      imageUrl: s3Url,
      imageKey: fileKey,
    };
  } catch (error) {
    console.error("Error generating storyboard image:", error);
    throw error;
  }
}

/**
 * Generates a character portrait image and uploads it to S3
 */
export async function generateCharacterPortrait(
  characterName: string,
  visualDescription: string,
  projectId: number,
  characterId: number
): Promise<{ imageUrl: string; imageKey: string }> {
  const prompt = `Create a professional character portrait for a film:

Character: ${characterName}
${visualDescription}

Requirements:
- Headshot or upper body portrait
- Professional lighting and cinematography
- Clear facial features and distinctive characteristics
- Consistent with the visual description
- High production quality
- Suitable for a professional film production

Generate a single, clear portrait image.`;

  try {
    const { url: imageUrl } = await generateImage({
      prompt,
    });

    if (!imageUrl) {
      throw new Error("Image generation failed - no URL returned");
    }

    // If it's a placeholder image, return it directly without S3 upload
    if (imageUrl.startsWith(PLACEHOLDER_PREFIX)) {
      return {
        imageUrl,
        imageKey: `placeholder/character-${characterId}`,
      };
    }

    const response = await fetch(imageUrl);
    const buffer = await response.arrayBuffer();

    const fileKey = `projects/${projectId}/characters/portrait-${characterId}-${nanoid()}.jpg`;
    const { url: s3Url } = await storagePut(fileKey, Buffer.from(buffer), "image/jpeg");

    return {
      imageUrl: s3Url,
      imageKey: fileKey,
    };
  } catch (error) {
    console.error("Error generating character portrait:", error);
    throw error;
  }
}

/**
 * Generates a setting/location reference image and uploads it to S3
 */
export async function generateSettingReference(
  settingName: string,
  visualDescription: string,
  projectId: number,
  settingId: number
): Promise<{ imageUrl: string; imageKey: string }> {
  const prompt = `Create a cinematic establishing shot for a film location:

Location: ${settingName}
${visualDescription}

Requirements:
- Wide establishing shot showing the full environment
- Professional cinematography and lighting
- Atmospheric and immersive
- Consistent with the visual description
- High production quality
- Suitable for a professional film production

Generate a single, cohesive environmental image.`;

  try {
    const { url: imageUrl } = await generateImage({
      prompt,
    });

    if (!imageUrl) {
      throw new Error("Image generation failed - no URL returned");
    }

    // If it's a placeholder image, return it directly without S3 upload
    if (imageUrl.startsWith(PLACEHOLDER_PREFIX)) {
      return {
        imageUrl,
        imageKey: `placeholder/setting-${settingId}`,
      };
    }

    const response = await fetch(imageUrl);
    const buffer = await response.arrayBuffer();

    const fileKey = `projects/${projectId}/settings/reference-${settingId}-${nanoid()}.jpg`;
    const { url: s3Url } = await storagePut(fileKey, Buffer.from(buffer), "image/jpeg");

    return {
      imageUrl: s3Url,
      imageKey: fileKey,
    };
  } catch (error) {
    console.error("Error generating setting reference:", error);
    throw error;
  }
}
