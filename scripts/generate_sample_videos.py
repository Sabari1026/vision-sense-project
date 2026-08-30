import os
import cv2
import numpy as np
import random
import math

def create_cctv_video(filename, camera_title, num_frames=300, fps=25, width=1280, height=720):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))

    # Define moving shoppers with realistic walking trajectories
    num_shoppers = 5
    shoppers = []
    for i in range(num_shoppers):
        shoppers.append({
            'id': i + 1,
            'x': random.randint(100, width - 100),
            'y': random.randint(100, height - 100),
            'vx': random.choice([-2, -1, 1, 2, 3]),
            'vy': random.choice([-2, -1, 1, 2, 3]),
            'color': (random.randint(50, 200), random.randint(50, 200), random.randint(150, 255)),
            'height_person': random.randint(120, 160),
            'width_person': random.randint(50, 70),
            'pause': 0
        })

    print(f"Generating synthetic CCTV video: {filename}...")

    for frame_idx in range(num_frames):
        # Create CCTV background with grid pattern
        frame = np.full((height, width, 3), (35, 38, 45), dtype=np.uint8)

        # Draw tile grid floor pattern
        for x in range(0, width, 80):
            cv2.line(frame, (x, 0), (x, height), (50, 54, 62), 1)
        for y in range(0, height, 80):
            cv2.line(frame, (0, y), (width, y), (50, 54, 62), 1)

        # Draw store layout features (counter, racks, door)
        cv2.rectangle(frame, (80, 80), (350, 220), (70, 75, 90), -1)
        cv2.putText(frame, "RETAIL DISPLAY Z-1", (90, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 210, 225), 2)

        cv2.rectangle(frame, (width - 400, height - 250), (width - 100, height - 80), (80, 70, 60), -1)
        cv2.putText(frame, "CHECKOUT DESK Z-2", (width - 380, height - 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (220, 210, 200), 2)

        # Draw Entry/Exit Line
        cv2.line(frame, (100, height - 100), (width - 100, height - 100), (0, 165, 255), 3)
        cv2.putText(frame, "ENTRY / EXIT COUNTING LINE", (120, height - 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

        # Draw moving human-shaped figures (Head, Body, Arms, Legs)
        for s in shoppers:
            if s['pause'] > 0:
                s['pause'] -= 1
            else:
                s['x'] += s['vx']
                s['y'] += s['vy']

                # Bounce off walls
                if s['x'] < 80 or s['x'] > width - 120:
                    s['vx'] *= -1
                if s['y'] < 80 or s['y'] > height - 180:
                    s['vy'] *= -1

                # Random pause to simulate looking at items
                if random.random() < 0.02:
                    s['pause'] = random.randint(15, 45)

            px, py = int(s['x']), int(s['y'])
            pw, ph = s['width_person'], s['height_person']

            # Draw human shape: Torso rectangle, head circle, legs
            # Torso
            cv2.rectangle(frame, (px - pw//2, py - ph//2), (px + pw//2, py + ph//4), s['color'], -1)
            # Head (skin color/shirt top)
            cv2.circle(frame, (px, py - ph//2 - 15), 18, (210, 180, 140), -1)
            # Legs
            cv2.rectangle(frame, (px - pw//2 + 5, py + ph//4), (px - 5, py + ph//2), (30, 30, 30), -1)
            cv2.rectangle(frame, (px + 5, py + ph//4), (px + pw//2 - 5, py + ph//2), (30, 30, 30), -1)

            # Draw subtle shadow on ground
            cv2.ellipse(frame, (px, py + ph//2 + 5), (pw//2, 10), 0, 0, 360, (20, 20, 20), -1)

        # CCTV OSD (On Screen Display) overlay
        timestamp_str = f"2026-08-30 {12 + (frame_idx // 1500):02d}:{(frame_idx // 25) % 60:02d}:{frame_idx % 25:02d}"
        cv2.rectangle(frame, (0, 0), (width, 45), (15, 15, 20), -1)
        cv2.putText(frame, f"[VISION SENSE CCTV STREAM] - {camera_title}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 200), 2)
        cv2.putText(frame, timestamp_str, (width - 320, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "● LIVE REC", (width - 480, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        out.write(frame)

    out.release()
    print(f"Successfully created: {filename}")

if __name__ == "__main__":
    videos_dir = os.path.join(os.path.dirname(__file__), "..", "videos")
    os.makedirs(videos_dir, exist_ok=True)
    create_cctv_video(os.path.join(videos_dir, "camera1.mp4"), "CAM-01 MAIN ENTRANCE")
    create_cctv_video(os.path.join(videos_dir, "camera2.mp4"), "CAM-02 CLOTHING SECTION")
    create_cctv_video(os.path.join(videos_dir, "camera3.mp4"), "CAM-03 ELECTRONICS HUB")
    create_cctv_video(os.path.join(videos_dir, "camera4.mp4"), "CAM-04 CHECKOUT DESKS")
    print("All 4 synthetic CCTV videos generated successfully!")
