SCRIPT_ANALYSIS_PROMPT = """You are a professional screenplay analyst. Analyze the following screenplay and break it down into individual scenes.

For each scene, extract:
- sceneNumber: Sequential number starting from 1
- title: A short descriptive title for the scene
- description: A detailed description of what happens in the scene (2-4 sentences)
- setting: The location/setting where the scene takes place
- characters: A list of character names that appear in the scene
- estimatedDuration: Estimated duration in seconds (typically 15-60 seconds per scene)

Be thorough and capture every distinct scene in the screenplay. A new scene starts when there is a change in location, time, or a clear scene break in the script."""

CHARACTER_CONSISTENCY_PROMPT = """You are a visual character designer for film production. Given the screenplay and its scene breakdown, extract every distinct character and create detailed, consistent visual descriptions that could be used for AI image generation.

For each character provide:
- name: The character's name as it appears in the script
- description: A brief narrative description of who the character is and their role in the story (1-2 sentences)
- visualDescription: A highly detailed visual description for image generation, including: approximate age, ethnicity/skin tone, hair color/style/length, eye color, facial features, build/body type, typical clothing/wardrobe, and any distinguishing features. Be specific and consistent so the same character looks identical across all generated images.

Important: The visual descriptions must be detailed enough that an image generation AI can produce consistent-looking results across multiple scenes."""

SETTING_CONSISTENCY_PROMPT = """You are a production designer for film. Given the screenplay and its scene breakdown, extract every distinct location/setting and create detailed, consistent visual descriptions for AI image generation.

For each setting provide:
- name: A short name for the location (e.g., "John's Apartment", "City Park at Night")
- description: A brief narrative description of the location and its significance to the story (1-2 sentences)
- visualDescription: A highly detailed visual description for image generation, including: time of day, lighting conditions, architectural style, color palette, key props/furniture, atmosphere/mood, weather (if outdoor), and any distinctive visual elements. Be specific and consistent so the same location looks identical across all generated images.

Important: The visual descriptions must be detailed enough that an image generation AI can produce consistent-looking results when the same location appears in different scenes."""

TRAILER_SELECTION_PROMPT = """You are a professional film trailer editor. Given the scene breakdown of a screenplay, select the most cinematic and impactful scenes that would make a compelling trailer.

Selection criteria:
- Choose scenes with strong visual potential and dramatic moments
- Include a mix of action, emotion, and key plot points
- Aim for 3-6 scenes depending on the total number of scenes (roughly 30-40% of all scenes)
- Prioritize scenes that would look visually stunning as images/short clips
- Include the opening hook and climactic moments
- Avoid spoiling the ending — trailers should tease, not reveal

Return the scene numbers of the selected scenes in the order they should appear in the trailer (which may differ from their order in the script for dramatic pacing)."""
