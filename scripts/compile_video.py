import glob
import os
import shutil
import sys
import imageio
from PIL import Image

FRAMES_DIR = os.path.abspath("artifacts/screencast_frames")
OUTPUT_DIR = os.path.abspath("artifacts/video")
ARTIFACT_BRAIN_DIR = os.path.abspath("C:/Users/Jaweria/.gemini/antigravity/brain/5297cf64-eab5-4fe9-af63-8878e967fa15")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ARTIFACT_BRAIN_DIR, exist_ok=True)

frame_files = sorted(glob.glob(os.path.join(FRAMES_DIR, "frame_*.jpg")))
total_frames = len(frame_files)
print(f"Compiling {total_frames} frames into video...")

if total_frames == 0:
    print("Error: No frames found to compile!")
    sys.exit(1)

# Target 15 FPS
FPS = 15
mp4_path = os.path.join(OUTPUT_DIR, "atip_autonomous_walkthrough.mp4")
gif_path = os.path.join(OUTPUT_DIR, "atip_autonomous_walkthrough.gif")

# 1. Compile MP4 with H.264
print(f"Writing MP4: {mp4_path}")
writer = imageio.get_writer(mp4_path, fps=FPS, codec="libx264", quality=8, pixelformat="yuv420p")
for i, fpath in enumerate(frame_files):
    if i % 50 == 0:
        print(f"Encoding MP4 frame {i}/{total_frames}...")
    img = imageio.imread(fpath)
    writer.append_data(img)
writer.close()
print("MP4 compilation complete!")

# 2. Compile an optimized GIF (resampled to 960x600 and every 2nd frame for web playback)
print(f"Writing GIF: {gif_path}")
gif_frames = []
for i, fpath in enumerate(frame_files):
    if i % 2 == 0:  # step to keep gif lightweight (~7.5 fps)
        with Image.open(fpath) as im:
            resized = im.resize((960, 600), Image.Resampling.LANCZOS)
            gif_frames.append(resized.convert("P", palette=Image.Palette.ADAPTIVE))

if gif_frames:
    gif_frames[0].save(
        gif_path,
        save_all=True,
        append_images=gif_frames[1:],
        duration=int(1000 / (FPS / 2)),
        loop=0,
        optimize=True,
    )
    print("GIF compilation complete!")

# 3. Copy to brain artifact directory
target_mp4 = os.path.join(ARTIFACT_BRAIN_DIR, "atip_autonomous_walkthrough.mp4")
target_gif = os.path.join(ARTIFACT_BRAIN_DIR, "atip_autonomous_walkthrough.gif")
shutil.copy2(mp4_path, target_mp4)
shutil.copy2(gif_path, target_gif)

print(f"Successfully copied video artifacts to:\n  {target_mp4}\n  {target_gif}")
