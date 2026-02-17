"""Seed script that populates the database with Phase 1 test data.

Generates a test trailer video via Kling AI, extracts frames, uploads to S3,
and creates all the DB records that Phase 2 expects to find.

Usage:
    cd script_to_movie/backend
    python -m scripts.seed_phase1_data          # full run (Kling + S3)
    python -m scripts.seed_phase1_data --mock   # offline, placeholder data
"""

import argparse
import asyncio
import json
import subprocess
import tempfile
import uuid
from pathlib import Path

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.character import Character
from app.models.project import Project
from app.models.scene import Scene
from app.models.setting import Setting
from app.models.storyboard import StoryboardImage
from app.models.user import User

# ---------------------------------------------------------------------------
# Test data definitions
# ---------------------------------------------------------------------------

SCRIPT_CONTENT = """\
TITLE: The Last Signal

FADE IN:

INT. CONTROL ROOM — NIGHT

A dimly lit space station control room. Screens flicker with incoming data.
ELENA VASQUEZ (35, determined, chief communications officer) sits at the main
console, headphones on. She adjusts dials, listening intently.

ELENA
(whispering)
There it is again. Every twelve hours, same frequency.

She types rapidly, pulling up a waveform on the main screen.

ELENA (CONT'D)
This isn't random noise. Someone — or something — is out there.

CUT TO:

EXT. DEEP SPACE — CONTINUOUS

A vast, star-filled void. The space station orbits a pale blue planet. A faint
pulse of light emanates from a distant nebula, rhythmic and deliberate.

CUT TO:

INT. OBSERVATION DECK — LATER

Elena stands at the panoramic window, staring out at the stars. The nebula
pulses in the distance.

ELENA
If this is a signal, it changes everything. We're not alone.

She presses her communicator.

ELENA (CONT'D)
Command, this is Vasquez. I need to speak with the director. Priority one.

FADE OUT.
"""

SCENES = [
    {
        "sceneNumber": 1,
        "title": "The Discovery",
        "description": (
            "Dimly lit space station control room at night. Elena Vasquez sits at the "
            "main console wearing headphones, adjusting dials as screens flicker with "
            "incoming data. She discovers a repeating signal on the same frequency every "
            "twelve hours and realizes it is not random noise."
        ),
        "setting": "Control Room",
        "characters": json.dumps(["Elena Vasquez"]),
        "dialogue": (
            "ELENA: (whispering) There it is again. Every twelve hours, same frequency.\n"
            "ELENA: This isn't random noise. Someone — or something — is out there."
        ),
        "duration": 45,
        "order": 1,
    },
    {
        "sceneNumber": 2,
        "title": "The Signal Source",
        "description": (
            "A vast, star-filled void of deep space. The space station orbits a pale "
            "blue planet. A faint pulse of light emanates from a distant nebula, "
            "rhythmic and deliberate, hinting at an intelligent origin."
        ),
        "setting": "Deep Space",
        "characters": json.dumps([]),
        "dialogue": "",
        "duration": 20,
        "order": 2,
    },
    {
        "sceneNumber": 3,
        "title": "The Decision",
        "description": (
            "Elena stands at the panoramic window of the observation deck, staring out "
            "at the stars. The nebula pulses in the distance. She decides to escalate "
            "the discovery to command, understanding the implications for humanity."
        ),
        "setting": "Observation Deck",
        "characters": json.dumps(["Elena Vasquez"]),
        "dialogue": (
            "ELENA: If this is a signal, it changes everything. We're not alone.\n"
            "ELENA: Command, this is Vasquez. I need to speak with the director. Priority one."
        ),
        "duration": 30,
        "order": 3,
    },
]

CHARACTER = {
    "name": "Elena Vasquez",
    "description": (
        "35-year-old chief communications officer aboard the space station. "
        "Determined, analytical, and courageous. She is the first to detect "
        "the mysterious repeating signal from deep space."
    ),
    "visualDescription": (
        "A 35-year-old woman with dark brown hair pulled back in a practical bun, "
        "sharp brown eyes, olive skin, wearing a fitted dark blue space station "
        "uniform with a communications badge on the left chest. She has a focused, "
        "determined expression."
    ),
}

SETTINGS_DATA = [
    {
        "name": "Control Room",
        "description": (
            "The main communications hub of the space station, filled with "
            "consoles, screens, and blinking equipment."
        ),
        "visualDescription": (
            "A dimly lit, futuristic space station control room. Banks of monitors "
            "display star charts and waveform data. Blue and amber indicator lights "
            "glow across control panels. The room has a curved ceiling with exposed "
            "conduits and a large central display screen showing signal analysis."
        ),
    },
    {
        "name": "Deep Space",
        "description": (
            "The vast void of outer space surrounding the station, with a distant "
            "nebula emitting a rhythmic pulse of light."
        ),
        "visualDescription": (
            "An infinite star-filled expanse of deep space. A sleek space station "
            "orbits a pale blue planet in the foreground. In the distance, a "
            "colorful nebula in hues of purple and blue emits a faint, rhythmic "
            "pulse of white light."
        ),
    },
    {
        "name": "Observation Deck",
        "description": (
            "A panoramic viewing area on the station with floor-to-ceiling windows "
            "offering a breathtaking view of space and the distant nebula."
        ),
        "visualDescription": (
            "A spacious observation deck with floor-to-ceiling curved glass windows "
            "looking out into star-filled space. The interior is minimally furnished "
            "with sleek metallic surfaces. The distant nebula is visible through the "
            "glass, casting a faint purple glow on the deck's polished floor."
        ),
    },
]

TRAILER_PROMPT = (
    "A cinematic sci-fi trailer: A determined female astronaut in a dark blue uniform "
    "discovers a mysterious repeating signal in a dimly lit space station control room "
    "filled with glowing monitors. Cut to a vast star-filled void where a distant "
    "nebula pulses with rhythmic light. Cut to her standing at a panoramic observation "
    "window staring at the pulsing nebula, dramatic lighting, 4K cinematic quality."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def get_or_create_user(session) -> User:
    """Get or create the test user."""
    result = await session.execute(
        select(User).where(User.email == "testuser@example.com")
    )
    user = result.scalar_one_or_none()
    if user:
        print(f"  Found existing test user (id={user.id})")
        return user

    user = User(
        openId=f"test-{uuid.uuid4().hex[:12]}",
        name="Test User",
        email="testuser@example.com",
        passwordHash=get_password_hash("testpassword123"),
        loginMethod="password",
        role="user",
    )
    session.add(user)
    await session.flush()
    print(f"  Created test user (id={user.id})")
    return user


def extract_frames(video_bytes: bytes, num_frames: int) -> list[bytes]:
    """Extract evenly-spaced frames from video bytes using ffmpeg."""
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = Path(tmpdir) / "trailer.mp4"
        video_path.write_bytes(video_bytes)

        # Probe duration
        probe = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ],
            capture_output=True, text=True,
        )
        duration = float(probe.stdout.strip())
        print(f"  Video duration: {duration:.1f}s")

        frames = []
        for i in range(num_frames):
            # Evenly space frames across the video
            timestamp = duration * (i + 0.5) / num_frames
            frame_path = Path(tmpdir) / f"frame_{i}.png"
            subprocess.run(
                [
                    "ffmpeg", "-y", "-ss", str(timestamp),
                    "-i", str(video_path),
                    "-frames:v", "1",
                    "-q:v", "2",
                    str(frame_path),
                ],
                capture_output=True,
            )
            if frame_path.exists():
                frames.append(frame_path.read_bytes())
                print(f"  Extracted frame {i + 1} at {timestamp:.1f}s ({len(frames[-1])} bytes)")
            else:
                print(f"  WARNING: Failed to extract frame {i + 1}")
                frames.append(b"")

        return frames


# ---------------------------------------------------------------------------
# Main seed function
# ---------------------------------------------------------------------------


async def seed(mock: bool = False):
    print("=" * 60)
    print("Seeding Phase 1 test data")
    print(f"Mode: {'MOCK (offline)' if mock else 'LIVE (Kling + S3)'}")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        async with session.begin():
            # 1. User
            print("\n[1/7] User")
            user = await get_or_create_user(session)

            # 2. Project
            print("\n[2/7] Project")
            project = Project(
                userId=user.id,
                title="The Last Signal",
                description="A 3-scene sci-fi short about humanity's first contact with an alien signal.",
                scriptContent=SCRIPT_CONTENT,
                status="draft",
                progress=0,
            )
            session.add(project)
            await session.flush()
            print(f"  Created project (id={project.id})")

            # 3. Scenes
            print("\n[3/7] Scenes")
            scene_records = []
            for scene_data in SCENES:
                scene = Scene(projectId=project.id, **scene_data)
                session.add(scene)
                scene_records.append(scene)
            await session.flush()
            for s in scene_records:
                print(f"  Scene {s.sceneNumber}: {s.title} (id={s.id})")

            # 4. Character
            print("\n[4/7] Character")
            character = Character(projectId=project.id, **CHARACTER)
            session.add(character)
            await session.flush()
            print(f"  {character.name} (id={character.id})")

            # 5. Settings
            print("\n[5/7] Settings")
            for setting_data in SETTINGS_DATA:
                setting = Setting(projectId=project.id, **setting_data)
                session.add(setting)
            await session.flush()
            print(f"  Created {len(SETTINGS_DATA)} settings")

            # 6. Generate trailer + extract frames
            print("\n[6/7] Trailer & Frames")
            if mock:
                trailer_url = f"https://mock-bucket.s3.us-east-1.amazonaws.com/projects/{project.id}/trailer.mp4"
                trailer_key = f"projects/{project.id}/trailer.mp4"
                frame_urls = []
                frame_keys = []
                for i in range(len(scene_records)):
                    key = f"projects/{project.id}/frames/scene_{i + 1}.png"
                    url = f"https://mock-bucket.s3.us-east-1.amazonaws.com/{key}"
                    frame_keys.append(key)
                    frame_urls.append(url)
                print("  MOCK: Using placeholder URLs (no Kling/S3 calls)")
            else:
                from app.core.kling import kling_client
                from app.core.storage import storage_client

                print("  Generating trailer via Kling AI...")
                video_url, video_bytes = await kling_client.generate_video(
                    prompt=TRAILER_PROMPT,
                    model="kling-v2",
                    duration="5",
                    aspect_ratio="16:9",
                )

                # Upload trailer to S3
                trailer_key = f"projects/{project.id}/trailer.mp4"
                trailer_url = await storage_client.upload(
                    key=trailer_key,
                    data=video_bytes,
                    content_type="video/mp4",
                )
                print(f"  Uploaded trailer to S3: {trailer_key}")

                # Extract and upload frames
                print("  Extracting frames with ffmpeg...")
                frames = extract_frames(video_bytes, len(scene_records))
                frame_urls = []
                frame_keys = []
                for i, frame_data in enumerate(frames):
                    key = f"projects/{project.id}/frames/scene_{i + 1}.png"
                    if frame_data:
                        url = await storage_client.upload(
                            key=key,
                            data=frame_data,
                            content_type="image/png",
                        )
                    else:
                        url = f"https://placeholder.s3.amazonaws.com/{key}"
                    frame_keys.append(key)
                    frame_urls.append(url)
                    print(f"  Uploaded frame {i + 1}: {key}")

            # 7. StoryboardImages + update project
            print("\n[7/7] StoryboardImages & Project Update")
            for i, scene in enumerate(scene_records):
                sb = StoryboardImage(
                    sceneId=scene.id,
                    projectId=project.id,
                    imageUrl=frame_urls[i],
                    imageKey=frame_keys[i],
                    prompt=scene.description,
                    status="completed",
                )
                session.add(sb)

            project.status = "parsed"
            project.progress = 33
            project.trailerUrl = trailer_url
            project.trailerKey = trailer_key
            await session.flush()

        # Commit happens automatically when `async with session.begin()` exits

    # Summary
    print("\n" + "=" * 60)
    print("SEED COMPLETE")
    print("=" * 60)
    print(f"  Project ID:       {project.id}")
    print(f"  Project title:    {project.title}")
    print(f"  Project status:   {project.status}")
    print(f"  Project progress: {project.progress}%")
    print(f"  Scenes:           {len(scene_records)}")
    print(f"  Characters:       1 ({CHARACTER['name']})")
    print(f"  Settings:         {len(SETTINGS_DATA)}")
    print(f"  StoryboardImages: {len(scene_records)}")
    print(f"  Trailer URL:      {trailer_url}")
    print("=" * 60)
    print(f"\nPhase 2 can now run against project_id={project.id}")


def main():
    parser = argparse.ArgumentParser(description="Seed Phase 1 test data")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Skip Kling/S3 calls; use placeholder URLs for offline testing",
    )
    args = parser.parse_args()
    asyncio.run(seed(mock=args.mock))


if __name__ == "__main__":
    main()
