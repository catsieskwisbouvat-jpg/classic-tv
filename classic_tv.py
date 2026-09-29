import cv2
import numpy as np
import random
import os
import yt_dlp

# CHANNELS: YouTube URL of een pad naar een lokaal MP4-bestand op je pc
CHANNELS = {
    "1": {
        "name": "MTV / TMF (Retro Music)",
        "source": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    },
    "2": {
        "name": "Cartoon Network / Fox Kids",
        "source": "https://www.youtube.com/watch?v=L_LUpnjgPso"
    },
    "3": {
        "name": "Classic TV Testcard",
        "source": None
    },
    "0": {
        "name": "Static Noise / Off-Air",
        "source": None
    }
}

def get_video_stream(source):
    """Haalt direct de geschikte videostream op via yt-dlp of opent een lokaal bestand."""
    if not source:
        return None

    if os.path.exists(source):
        return source

    ydl_opts = {
        'format': 'b*/bestvideo[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(source, download=False)
            return info.get('url')
    except Exception as e:
        print(f"\n[!] Stream loading error: {e}\nFalling back to TV testcard...")
        return None

def generate_testcard(width=640, height=480, channel_name="TEST CHANNEL"):
    """Genereert een klassiek EBU testbeeld."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    colors = [
        (255, 255, 255), (0, 255, 255), (255, 255, 0), (0, 255, 0),
        (255, 0, 255), (0, 0, 255), (255, 0, 0), (0, 0, 0)
    ]
    col_width = width // len(colors)
    for i, color in enumerate(colors):
        img[0:int(height * 0.75), i * col_width:(i + 1) * col_width] = color

    cv2.rectangle(img, (0, int(height * 0.75)), (width, height), (30, 30, 30), -1)
    cv2.putText(img, f"NO SIGNAL - {channel_name}", (30, height - 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
    return img

def apply_crt_effects(frame):
    """Past CRT TV effecten toe: scanlines, ruis, kleurverstoring en VHS glitch."""
    h, w, _ = frame.shape

    # 1. Lage resolutie (downscale & upscale)
    low_res = cv2.resize(frame, (w // 2, h // 2), interpolation=cv2.INTER_NEAREST)
    frame = cv2.resize(low_res, (w, h), interpolation=cv2.INTER_NEAREST)

    # 2. Chromatic Aberration (Rood/Blauw randje)
    b, g, r = cv2.split(frame)
    r = np.roll(r, 2, axis=1)
    b = np.roll(b, -2, axis=1)
    frame = cv2.merge([b, g, r])

    # 3. Analoge sneeuw/ruis
    noise = np.random.randint(0, 35, (h, w, 3), dtype=np.uint8)
    frame = cv2.add(frame, noise)

    # 4. CRT Scanlines
    scanlines = np.ones((h, w, 3), dtype=np.float32)
    scanlines[::2, :, :] = 0.75
    frame = (frame * scanlines).astype(np.uint8)

    # 5. VHS-storing/streep
    if random.random() < 0.10:
        y_stripe = random.randint(0, h - 15)
        stripe_height = random.randint(2, 8)
        frame[y_stripe:y_stripe + stripe_height, :] = np.roll(
            frame[y_stripe:y_stripe + stripe_height, :], random.randint(-15, 15), axis=1
        )
        frame[y_stripe:y_stripe + stripe_height, :] += random.randint(30, 80)

    return frame

def show_loading_screen(window_name, channel_name):
    """Toont een retro sneeuw/laadscherm terwijl de stream wordt opgehaald."""
    for _ in range(12):
        loading_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        cv2.putText(loading_frame, f"TUNING SIGNAL: {channel_name}...", (80, 240),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.imshow(window_name, loading_frame)
        cv2.waitKey(30)

def main():
    window_name = "Classic CRT TV"
    
    print("=" * 60)
    print("        CLASSIC 90s & 2000s TV EMULATOR        ")
    print("=" * 60)
    print("Select a channel using keys 0 to 3:")
    for key, info in CHANNELS.items():
        print(f" [{key}] - {info['name']}")
    print("\nPress 'q' or click the [X] button to turn off the TV.\n")

    current_key = "1"
    
    # Maak het venster aan
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 800, 600)

    # Toon direct laadscherm
    show_loading_screen(window_name, CHANNELS[current_key]['name'])

    stream_url = get_video_stream(CHANNELS[current_key]['source'])
    cap = cv2.VideoCapture(stream_url) if stream_url else None

    zapping_effect = 0

    while True:
        # --- FIX VOOR DE 'X' IN DE HOEK ---
        # Controleer of het venster nog openstaat. Als de gebruiker op [X] klikt, stopt de lus.
        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            print("TV turned off via window close [X].")
            break

        frame = None
        
        if cap and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()

        if frame is None:
            if current_key == "0":
                frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            else:
                frame = generate_testcard(640, 480, CHANNELS[current_key]['name'])
        else:
            frame = cv2.resize(frame, (640, 480))

        if zapping_effect > 0:
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            zapping_effect -= 1
        else:
            frame = apply_crt_effects(frame)

            cv2.putText(frame, f"CH {current_key} - {CHANNELS[current_key]['name']}", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA)

        cv2.imshow(window_name, frame)

        key = cv2.waitKey(30) & 0xFF
        
        # Sluiten met de 'q'-toets
        if key == ord('q'):
            print("Turning off TV...")
            break
        # Overschakelen naar ander kanaal
        elif chr(key) in CHANNELS and chr(key) != current_key:
            current_key = chr(key)
            print(f"Switching to channel {current_key}: {CHANNELS[current_key]['name']}...")
            
            show_loading_screen(window_name, CHANNELS[current_key]['name'])
            
            if cap:
                cap.release()
            
            stream_url = get_video_stream(CHANNELS[current_key]['source'])
            cap = cv2.VideoCapture(stream_url) if stream_url else None

    if cap:
        cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()