#!/home/pi/FishCam/.venv/bin/python
"""
Video Recorder
Simple menu-based program to capture video from the camera
"""

import cv2
import os
import time
from datetime import datetime
import platform
import math

# Import camera settings
from config import (
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    CAMERA_FRAME_RATE,
    # Software-only day/night auto thresholds
    ENABLE_DAY_NIGHT,
    NIGHT_LUMA_THRESHOLD,
    DAY_LUMA_THRESHOLD,
    LUMA_SAMPLE_EVERY_SEC,
)

# Optional CSI (Picamera2/libcamera) support
try:
    from libcamera_capture import LibcameraCapture, detect_csi_cameras, is_libcamera_available
    _LIBCAMERA_OK = True
except Exception:
    LibcameraCapture = None
    detect_csi_cameras = None
    is_libcamera_available = lambda: False  # type: ignore
    _LIBCAMERA_OK = False


def clear_screen():
    """Clear the terminal screen."""
    os.system('clear' if os.name != 'nt' else 'cls')


def show_menu():
    """Display the main menu."""
    clear_screen()
    print("=" * 50)
    print("    VIDEO RECORDER")
    print("=" * 50)
    print()
    print("1. Record 30 second video")
    print("2. Record 1 minute video")
    print("3. Record 5 minute video")
    print("4. Record custom duration (Day mode)")
    print("5. View recording settings")
    print("6. Exit")
    print("-")
    print("7. Record 30s (Night/IR mode)")
    print("8. Record 1 minute (Night/IR mode)")
    print("9. Record custom duration (choose mode: Day/Night/Auto)")
    print()
    print("=" * 50)


def _open_capture():
    """Open best-available capture: prefer CSI if present, otherwise USB.

    Returns: (cap, use_libcamera: bool)
    """
    # Prefer CSI on Linux when Libcamera available
    if platform.system().lower() == "linux" and _LIBCAMERA_OK and is_libcamera_available():
        try:
            csi = detect_csi_cameras() if detect_csi_cameras else []
            if csi:
                cap = LibcameraCapture(0)
                if cap.isOpened():
                    return cap, True
        except Exception:
            pass
    # Fallback to USB (V4L2 or default on other OS)
    backend = cv2.CAP_V4L2 if platform.system().lower() == "linux" else 0
    cap = cv2.VideoCapture(0, backend)
    return cap, False


def _set_mode_if_supported(cap, mode: str):
    """Set AWB mode on libcamera capture if available.

    mode: 'day' -> auto AWB, 'night' -> greyworld AWB
    """
    if hasattr(cap, "set_day_mode") and hasattr(cap, "set_night_mode"):
        try:
            if mode == "night":
                cap.set_night_mode()
            else:
                cap.set_day_mode()
        except Exception:
            pass


def record_video(duration_seconds, mode: str = "day"):
    """
    Record video from fish camera for specified duration.
    
    Args:
        duration_seconds: How long to record in seconds
    """
    print(f"\nPreparing to record {duration_seconds} seconds of video (mode={mode})...")

    # Open camera (CSI preferred)
    print("Opening camera...")
    cap, used_libcamera = _open_capture()

    if not cap or not cap.isOpened():
        print("ERROR: Could not open camera!")
        return False
    
    print(f"✓ Camera opened successfully ({'CSI/libcamera' if used_libcamera else 'USB/V4L2'})")
    
    # Configure camera (request values; device may choose closest)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, CAMERA_FRAME_RATE)
    # Apply requested mode for libcamera
    _set_mode_if_supported(cap, "night" if mode == "night" else "day")
    # Start libcamera capture if needed
    if used_libcamera and hasattr(cap, 'start'):
        cap.start()
        time.sleep(0.3)
    
    # Warm-up and verify first frame; determine actual size from real frame
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 1 or math.isnan(fps):
        fps = float(CAMERA_FRAME_RATE) if CAMERA_FRAME_RATE > 0 else 10.0

    print("Warming up and checking first frame...")
    first_frame = None
    warm_start = time.time()
    warm_limit = 6.0
    while time.time() - warm_start < warm_limit:
        ret, frm = cap.read()
        if ret and frm is not None:
            first_frame = frm
            break
        time.sleep(0.02)
    if first_frame is None:
        # If CSI/libcamera failed to warm up, retry with USB/V4L2
        if used_libcamera:
            print("No frames from CSI camera. Falling back to USB/V4L2...")
            try:
                cap.release()
            except Exception:
                pass
            cap = cv2.VideoCapture(0, cv2.CAP_V4L2 if platform.system().lower() == "linux" else 0)
            if not cap.isOpened():
                print("ERROR: Could not open USB/V4L2 camera either.")
                return False
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            cap.set(cv2.CAP_PROP_FPS, CAMERA_FRAME_RATE)
            warm_start = time.time()
            while time.time() - warm_start < warm_limit:
                ret, frm = cap.read()
                if ret and frm is not None:
                    first_frame = frm
                    used_libcamera = False
                    break
                time.sleep(0.02)
            if first_frame is None:
                print("ERROR: No frames received from any camera.")
                try:
                    cap.release()
                except Exception:
                    pass
                return False
        else:
            print("ERROR: No frames received from camera.")
            try:
                cap.release()
            except Exception:
                pass
            return False
    # Align writer size with actual frame
    height, width = first_frame.shape[:2]
    
    print(f"Resolution: {width}x{height} @ {fps} FPS")
    
    # Create output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs('videos', exist_ok=True)
    suffix = "day" if mode == "day" else ("night" if mode == "night" else "auto")
    output_file = f"videos/fish_{suffix}_{timestamp}.mp4"
    
    print(f"Output file: {output_file}")
    
    # Create video writer with fallbacks
    writer_options = [
        ("mp4v", ".mp4"),
        ("avc1", ".mp4"),
        ("H264", ".mp4"),
        ("XVID", ".avi"),
        ("MJPG", ".avi"),
    ]
    out = None
    chosen = None
    for codec, ext in writer_options:
        try:
            trial_file = output_file if output_file.endswith(ext) else (os.path.splitext(output_file)[0] + ext)
            fourcc = cv2.VideoWriter_fourcc(*codec)
            vw = cv2.VideoWriter(trial_file, fourcc, fps, (width, height))
            if vw.isOpened():
                # Try writing the first frame to validate
                vw.write(first_frame)
                out = vw
                output_file = trial_file
                chosen = codec
                break
        except Exception:
            pass
    if out is None:
        print("ERROR: Could not create a working video file with available codecs.")
        try:
            cap.release()
        except Exception:
            pass
        return False
    else:
        print(f"Using codec {chosen}, file: {output_file}")
    
    print("\n🔴 RECORDING...")
    print("Press Ctrl+C to stop early\n")
    
    start_time = time.time()
    frame_count = 0
    last_luma_check = 0.0
    current_mode = mode if mode in ("day", "night") else "day"
    
    try:
        while True:
            elapsed = time.time() - start_time
            
            # Check if done
            if elapsed >= duration_seconds:
                break
            
            # Read frame
            ret, frame = cap.read()
            if not ret:
                print("Warning: Failed to read frame")
                continue

            # Auto-switch mode based on brightness, software-only (no GPIO)
            if mode == "auto" and ENABLE_DAY_NIGHT and frame is not None:
                now = time.time()
                if now - last_luma_check >= LUMA_SAMPLE_EVERY_SEC:
                    last_luma_check = now
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    mean_luma = float(gray.mean()) / 255.0
                    new_mode = current_mode
                    if current_mode == "day" and mean_luma < NIGHT_LUMA_THRESHOLD:
                        new_mode = "night"
                    elif current_mode == "night" and mean_luma > DAY_LUMA_THRESHOLD:
                        new_mode = "day"
                    if new_mode != current_mode:
                        current_mode = new_mode
                        _set_mode_if_supported(cap, current_mode)
                        print(f"\nSwitched to {current_mode} mode (mean luma={mean_luma:.3f})")
            
            # Write frame
            try:
                out.write(frame)
            except Exception:
                print("ERROR: Failed to write frame; stopping.")
                break
            frame_count += 1
            
            # Show progress every second
            if frame_count % int(fps) == 0:
                remaining = duration_seconds - elapsed
                print(f"  Time remaining: {int(remaining)} seconds ({frame_count} frames)", end='\r')
        
        print()  # New line after progress
        
    except KeyboardInterrupt:
        print("\n\nRecording stopped by user")
    
    finally:
        # Cleanup
        elapsed = time.time() - start_time
        out.release()
        try:
            cap.release()
        except Exception:
            pass
        
        print(f"\n✓ Recording complete!")
        print(f"  Duration: {elapsed:.1f} seconds")
        print(f"  Frames: {frame_count}")
        print(f"  File: {output_file}")
        
        # Check file size
        if os.path.exists(output_file):
            size_mb = os.path.getsize(output_file) / (1024 * 1024)
            print(f"  Size: {size_mb:.1f} MB")
    
    return True


def show_settings():
    """Display current recording settings."""
    clear_screen()
    print("=" * 50)
    print("    CURRENT SETTINGS")
    print("=" * 50)
    print()
    print(f"Camera: Fish Tank (Camera 0)")
    print(f"Resolution: {CAMERA_WIDTH}x{CAMERA_HEIGHT}")
    print(f"Frame Rate: {CAMERA_FRAME_RATE} FPS")
    print(f"Output Format: MP4")
    print(f"Output Directory: ./videos/")
    print(f"CSI support: {'Yes' if _LIBCAMERA_OK and is_libcamera_available() else 'No'}")
    print(f"Auto Day/Night available: {'Yes' if ENABLE_DAY_NIGHT else 'No'}")
    print()
    print("=" * 50)
    input("\nPress Enter to continue...")


def main():
    """Main program loop."""
    while True:
        show_menu()
        
        choice = input("Enter your choice (1-6): ").strip()
        
        if choice == '1':
            record_video(30, mode="day")
            input("\nPress Enter to continue...")
            
        elif choice == '2':
            record_video(60, mode="day")
            input("\nPress Enter to continue...")
            
        elif choice == '3':
            record_video(300, mode="day")
            input("\nPress Enter to continue...")
            
        elif choice == '4':
            try:
                duration = int(input("\nEnter duration in seconds: "))
                if duration > 0:
                    record_video(duration, mode="day")
                else:
                    print("Duration must be positive!")
            except ValueError:
                print("Invalid input! Please enter a number.")
            input("\nPress Enter to continue...")
            
        elif choice == '5':
            show_settings()
            
        elif choice == '6':
            clear_screen()
            print("\nGoodbye!\n")
            break
        elif choice == '7':
            record_video(30, mode="night")
            input("\nPress Enter to continue...")
        elif choice == '8':
            record_video(60, mode="night")
            input("\nPress Enter to continue...")
        elif choice == '9':
            try:
                duration = int(input("\nEnter duration in seconds: "))
                mode_in = input("Mode (day/night/auto) [day]: ").strip().lower() or "day"
                if mode_in not in ("day", "night", "auto"):
                    mode_in = "day"
                if duration > 0:
                    record_video(duration, mode=mode_in)
                else:
                    print("Duration must be positive!")
            except ValueError:
                print("Invalid input! Please enter a number.")
            input("\nPress Enter to continue...")
            
        else:
            print("\nInvalid choice! Please enter 1-6.")
            time.sleep(1)


if __name__ == "__main__":
    main()
