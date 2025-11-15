# ============================================================================
# File: web_stream.py (OPTIMIZED VERSION)
# Author: William Loring
#
# Description:
#   This program creates a web server that captures video from a USB camera
#   and streams it live to web browsers. Students can view the camera feed
#   by opening a web browser and going to the server's address.
#
#   OPTIMIZATIONS FOR SPEED AND BANDWIDTH:
#   - Reduced default resolution to 640x480 (from 1280x720) for less bandwidth
#   - Added JPEG quality control (85% quality) to balance size vs quality
#   - Frame rate limiting to max 15 FPS to reduce bandwidth usage
#   - Camera warm-up sequence to reduce initial lag
#   - Optional known camera index to skip detection (faster startup)
#   - Responsive web page design with CSS styling
#   - Overlay label feature: displays "WNCC STEM Club" for 60 seconds every 15 minutes
#
#   This file is heavily commented for beginning Python programmers in a
#   community college setting. It explains programming concepts, real-world
#   hardware issues, and how web streaming works.
#
# Educational Topics Covered:
#   - Object-Oriented Programming (classes and methods)
#   - Threading (running multiple tasks at the same time)
#   - HTTP servers and web protocols
#   - Camera/video capture with OpenCV
#   - Error handling with try/except blocks
#   - Network programming basics
#   - Real-world troubleshooting and hardware limitations
#   - Performance optimization techniques
#   - Real-time image overlay and text rendering
# ============================================================================


# --------------------------- IMPORTS (Libraries) -------------------------- #
# These are modules (libraries) that add extra features to Python

import os  # For file system operations and path handling
import socketserver  # For creating network servers that handle multiple clients
import time  # For adding delays and timing operations
from http import server  # For creating HTTP web servers
from threading import (
    Condition,  # For synchronizing threads (like a traffic signal)
    Thread,  # For running background tasks
)  # For running multiple tasks simultaneously
from typing import Optional  # For type hints

from logging_config import get_logger
from web_stream_page import PAGE
from config import (
    ENABLE_LABEL_OVERLAY,
    LABEL_TEXT,
    LABEL_CYCLE_MINUTES,
    LABEL_DURATION_SECONDS,
    LABEL_FONT_SCALE,
    LABEL_TRANSPARENCY,
    TEXT_TRANSPARENCY,
    TEXT_COLOR,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    PLANT_CAMERA_WIDTH,
    PLANT_CAMERA_HEIGHT,
    CAMERA_FRAME_RATE,
    PLANT_CAMERA_FRAME_RATE,
    FISH_CAMERA_MAX_STREAM_FPS,
    PLANT_CAMERA_MAX_STREAM_FPS,
    JPEG_QUALITY,
    KNOWN_CAMERA_INDEX,
    # Day/Night config (software only)
    ENABLE_DAY_NIGHT,
    NIGHT_LUMA_THRESHOLD,
    DAY_LUMA_THRESHOLD,
    LUMA_SAMPLE_EVERY_SEC,
)

# Import OpenCV library for camera control
# pip install opencv-python
import cv2

# Import libcamera support for CSI cameras
try:
    from libcamera_capture import LibcameraCapture, detect_csi_cameras, is_libcamera_available
    LIBCAMERA_AVAILABLE = True
except ImportError:
    LIBCAMERA_AVAILABLE = False
    LibcameraCapture = None

# No GPIO IR control (removed by user request)

# --------------------------- LOGGING SETUP -------------------------------- #
# Logging is like a diary for your program. It records what happens and any errors.
# This helps you debug problems and see what your code is doing.
#
# We use the centralized logging_config module for consistent logging setup.

# Setup logging for web_stream module
logger = get_logger("web_stream", enable_console=True)


# --------------------- MEDIA RELAY (FRAME BROADCASTER) -------------------- #
class MediaRelay:
    """
    MediaRelay pattern for sharing a single webcam source across multiple connections.
    This class captures frames from the camera in a background thread and allows
    multiple clients to subscribe and receive the latest frame.

    Key Concepts:
    - Only one thread talks to the camera (saves resources)
    - All clients (web browsers) get the latest frame from the relay
    - Uses threading.Condition to let clients wait for new frames
    """

    def __init__(
        self,
        enable_overlay=True,
        rotation_angle=0,
        width=1280,
        height=720,
        frame_rate=10.0,
        max_stream_fps=10.0,
    ):
        # This will store the most recent camera frame as JPEG bytes
        self.frame = None

        # Condition is like a traffic light for threads: it lets them wait for new frames
        self.condition = Condition()

        # Control variables for the camera and background thread
        self.running = False
        self.cap = None
        self.capture_thread = None

        # Store camera-specific settings
        self.enable_overlay = enable_overlay and ENABLE_LABEL_OVERLAY
        self.rotation_angle = rotation_angle
        self.width = width
        self.height = height
        self.frame_rate = frame_rate
        self.max_stream_fps = max_stream_fps

        # Label timing control (only initialize if label overlay is enabled for this camera)
        if self.enable_overlay:
            self.label_start_time = (
                time.time()
            )  # When we started the current cycle
            self.label_shown = False  # Track if label is currently being shown

        # Day/Night state
        self.enable_day_night = ENABLE_DAY_NIGHT
        self.current_mode = "day"  # default
        self._last_luma_check = 0.0

    # ------------------------ START CAPTURE ------------------------------- #
    def start_capture(self, camera_index=0, use_libcamera=False):
        # Start capturing video from camera (USB or CSI)
        # camera_index: 0 = first camera, 1 = second, etc.
        # use_libcamera: True for CSI cameras, False for USB cameras
        
        if use_libcamera:
            if not LIBCAMERA_AVAILABLE:
                raise RuntimeError("Libcamera support not available. Install picamera2: pip install picamera2")
            
            logger.info(
                f"[MediaRelay] Opening CSI camera {camera_index} with libcamera..."
            )
            self.cap = LibcameraCapture(camera_index)
            if not self.cap.isOpened():
                raise RuntimeError(
                    f"Could not open CSI camera {camera_index} with libcamera"
                )
            logger.info(
                f"[MediaRelay] ✓ CSI camera {camera_index} opened successfully with libcamera"
            )
        else:
            logger.info(
                f"[MediaRelay] Opening USB camera {camera_index} with V4L2 backend..."
            )
            # Open camera using OpenCV and the V4L2 backend (best for USB cameras)
            self.cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
            if not self.cap.isOpened():
                # If camera failed to open, raise an error and stop the program
                raise RuntimeError(
                    f"Could not open USB camera {camera_index} with V4L2 backend"
                )
            logger.info(
                f"[MediaRelay] ✓ USB camera {camera_index} opened successfully with V4L2"
            )

        # Enhanced camera configuration with multiple attempts
        self._configure_camera_settings(camera_index)
        
        # For libcamera, start the capture
        if use_libcamera and hasattr(self.cap, 'start'):
            self.cap.start()

        # Check final settings
        actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        logger.info(
            f"[MediaRelay] Final camera settings: {int(actual_width)}x{int(actual_height)} @ {actual_fps} FPS"
        )

        # Check if we got the desired settings
        if int(actual_width) != self.width or int(actual_height) != self.height:
            logger.warning(
                f"[MediaRelay] Camera {camera_index} resolution mismatch: requested {self.width}x{self.height}, got {int(actual_width)}x{int(actual_height)}"
            )
        if actual_fps != self.frame_rate:
            logger.warning(
                f"[MediaRelay] Camera {camera_index} FPS mismatch: requested {self.frame_rate}, got {actual_fps}"
            )

        # Warm up the camera by capturing and discarding a few frames
        # This helps reduce initial lag and ensures stable image quality
        logger.info("[MediaRelay] Warming up camera...")
        for i in range(5):
            ret, _ = self.cap.read()
            if not ret:
                logger.warning(
                    f"[MediaRelay] Frame {i+1} failed during warm-up"
                )
            time.sleep(0.1)  # Small delay between warm-up frames
        logger.info("[MediaRelay] Camera warm-up complete")

        # Start the background thread to capture frames
        self.running = True
        self.capture_thread = Thread(target=self._capture_frames)
        self.capture_thread.daemon = True
        self.capture_thread.start()

    def _configure_camera_settings(self, camera_index):
        """Enhanced camera configuration with multiple attempts to force settings."""
        logger.info(
            f"[MediaRelay] Configuring camera {camera_index} settings: {self.width}x{self.height} @ {self.frame_rate} FPS"
        )

        # Method 1: Standard approach
        success = self._try_camera_config("Standard configuration")
        if success:
            return

        # Method 2: Set FPS first, then resolution
        logger.info(f"[MediaRelay] Trying FPS-first configuration...")
        self.cap.set(cv2.CAP_PROP_FPS, self.frame_rate)
        time.sleep(0.1)  # Small delay
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        time.sleep(0.1)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        success = self._check_settings("FPS-first configuration")
        if success:
            return

        # Method 3: Multiple attempts with delays
        for attempt in range(3):
            logger.info(
                f"[MediaRelay] Configuration attempt {attempt + 1}/3..."
            )
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            time.sleep(0.2)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            time.sleep(0.2)
            self.cap.set(cv2.CAP_PROP_FPS, self.frame_rate)
            time.sleep(0.2)

            if self._check_settings(f"Attempt {attempt + 1}"):
                return

        logger.warning(
            f"[MediaRelay] Camera {camera_index} did not accept requested settings after multiple attempts"
        )

    def _try_camera_config(self, method_name):
        """Try standard camera configuration."""
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.frame_rate)
        return self._check_settings(method_name)

    def _check_settings(self, method_name):
        """Check if camera accepted the requested settings."""
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)

        if actual_width == self.width and actual_height == self.height:
            logger.info(
                f"[MediaRelay] ✓ {method_name} successful: {actual_width}x{actual_height} @ {actual_fps} FPS"
            )
            return True
        else:
            logger.info(
                f"[MediaRelay] ✗ {method_name} failed: got {actual_width}x{actual_height} @ {actual_fps} FPS"
            )
            return False

    # ------------------------ CAPTURE FRAMES ------------------------------- #
    def _capture_frames(self):
        """This method runs in a background thread and keeps grabbing frames from the camera
        It stores the latest frame and notifies all waiting clients"""
        frame_time = (
            1.0 / self.max_stream_fps
        )  # Calculate time between frames for rate limiting
        last_frame_time = 0

        while self.running:
            if self.cap is not None:
                current_time = time.time()

                # Rate limiting: only process frames at the specified max FPS
                if current_time - last_frame_time < frame_time:
                    time.sleep(0.001)  # Small sleep to prevent busy waiting
                    continue

                # Try to read one frame from the camera
                ret, frame = self.cap.read()
                if ret:
                    # Optional: day/night switching using luminance from frame
                    if self.enable_day_night and frame is not None:
                        now = current_time
                        if now - self._last_luma_check >= LUMA_SAMPLE_EVERY_SEC:
                            self._last_luma_check = now
                            # Compute normalized luma ~ mean of grayscale / 255.0
                            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                            mean_luma = float(gray.mean()) / 255.0
                            new_mode = self.current_mode
                            if self.current_mode == "day" and mean_luma < NIGHT_LUMA_THRESHOLD:
                                new_mode = "night"
                            elif self.current_mode == "night" and mean_luma > DAY_LUMA_THRESHOLD:
                                new_mode = "day"
                            if new_mode != self.current_mode:
                                self.current_mode = new_mode
                                try:
                                    if hasattr(self.cap, "set_day_mode") and hasattr(self.cap, "set_night_mode"):
                                        if new_mode == "night":
                                            self.cap.set_night_mode()
                                        else:
                                            self.cap.set_day_mode()
                                    logger.info(f"[MediaRelay] Day/Night switched to {new_mode} (mean luma={mean_luma:.3f})")
                                except Exception:
                                    pass
                    # Add WNCC STEM Club label timing logic (only if enabled for this camera)
                    if self.enable_overlay:
                        current_cycle_time = (
                            current_time - self.label_start_time
                        )

                        # Show label for configured duration every configured interval
                        cycle_duration = (
                            LABEL_CYCLE_MINUTES * 60
                        )  # Convert minutes to seconds
                        if current_cycle_time >= cycle_duration:  # Reset cycle
                            self.label_start_time = current_time
                            current_cycle_time = 0
                            self.label_shown = False

                        # Show label for first X seconds of each cycle
                        show_label = current_cycle_time < LABEL_DURATION_SECONDS

                        # Add overlay text if it's time to show it
                        if show_label:
                            # Add semi-transparent background for better text visibility
                            overlay = frame.copy()

                            # Calculate text size and position
                            font = cv2.FONT_HERSHEY_SIMPLEX
                            thickness = 2

                            # Get text size to position it properly
                            (text_width, text_height), baseline = (
                                cv2.getTextSize(
                                    LABEL_TEXT,
                                    font,
                                    LABEL_FONT_SCALE,
                                    thickness,
                                )
                            )

                            # Position in bottom-left corner with some padding
                            x = 20  # 20 pixels from left edge
                            # 20 pixels from bottom edge
                            y = frame.shape[0] - 20

                            # Draw semi-transparent background rectangle
                            cv2.rectangle(
                                overlay,
                                (x - 10, y - text_height - 10),
                                (x + text_width + 10, y + 10),
                                (0, 0, 0),
                                -1,
                            )  # Black background

                            # Blend the overlay with the original frame for transparency
                            cv2.addWeighted(
                                overlay,
                                LABEL_TRANSPARENCY,
                                frame,
                                1 - LABEL_TRANSPARENCY,
                                0,
                                frame,
                            )

                            # Add label text using the configured text color and transparency
                            if TEXT_TRANSPARENCY < 1.0:
                                text_overlay = frame.copy()
                                cv2.putText(
                                    text_overlay,
                                    LABEL_TEXT,
                                    (x, y),
                                    font,
                                    LABEL_FONT_SCALE,
                                    TEXT_COLOR,
                                    thickness,
                                )
                                cv2.addWeighted(
                                    text_overlay,
                                    TEXT_TRANSPARENCY,
                                    frame,
                                    1 - TEXT_TRANSPARENCY,
                                    0,
                                    frame,
                                )
                            else:
                                cv2.putText(
                                    frame,
                                    LABEL_TEXT,
                                    (x, y),
                                    font,
                                    LABEL_FONT_SCALE,
                                    TEXT_COLOR,
                                    thickness,
                                )

                            # Log when label appears (only once per state change)
                            if not self.label_shown:
                                logger.info(
                                    f"[MediaRelay] Label '{LABEL_TEXT}' displayed for {LABEL_DURATION_SECONDS}s"
                                )
                                self.label_shown = True
                        else:
                            # Log when label disappears (only once per state change)
                            if self.label_shown:
                                logger.info(
                                    f"[MediaRelay] Label '{LABEL_TEXT}' hidden - next display in {LABEL_CYCLE_MINUTES} minutes"
                                )
                                self.label_shown = False

                    # Apply rotation if specified for this camera
                    # Debug logging to help diagnose unexpected rotation behavior
                    logger.debug(
                        f"[MediaRelay] rotation_angle={self.rotation_angle}"
                    )
                    if self.rotation_angle == 90:
                        # Rotate 90 degrees counterclockwise
                        logger.debug(
                            "[MediaRelay] Applying rotation: 90° CCW (ROTATE_90_COUNTERCLOCKWISE)"
                        )
                        frame = cv2.rotate(
                            frame, cv2.ROTATE_90_COUNTERCLOCKWISE
                        )
                    elif self.rotation_angle == 180:
                        # Rotate 180 degrees
                        logger.debug(
                            "[MediaRelay] Applying rotation: 180° (ROTATE_180)"
                        )
                        frame = cv2.rotate(frame, cv2.ROTATE_180)
                    elif self.rotation_angle == 270:
                        # Rotate 270 degrees counterclockwise (or 90 degrees clockwise)
                        logger.debug(
                            "[MediaRelay] Applying rotation: 270° CCW / 90° CW (ROTATE_90_CLOCKWISE)"
                        )
                        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

                    # Convert the frame to JPEG format with controlled quality for web streaming
                    encode_params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
                    _, buffer = cv2.imencode(".jpg", frame, encode_params)
                    frame_bytes = buffer.tobytes()

                    # Notify all clients that a new frame is ready
                    with self.condition:
                        self.frame = frame_bytes
                        self.condition.notify_all()

                    last_frame_time = current_time
                else:
                    # If frame capture failed, wait a tiny bit before trying again
                    time.sleep(0.01)
            else:
                # If camera connection is lost, exit the loop
                break

    # ------------------------- GET FRAME ---------------------------------- #
    def get_frame(self):
        """
        Wait for and return the latest frame (for use by each client).
        Each client (browser) calls this to get the newest frame.
        """
        with self.condition:
            self.condition.wait()  # Wait until a new frame is available
            return self.frame

    def stop(self):
        # Cleanly stop the background thread and release the camera
        self.running = False
        if self.capture_thread:
            self.capture_thread.join()
        if self.cap:
            self.cap.release()


# -------------------- STREAMING HANDLER (Web Requests) -------------------- #
class StreamingHandler(server.BaseHTTPRequestHandler):
    """
    This class handles HTTP requests from web browsers.

    When someone opens a web browser and goes to our server's address,
    their browser sends an HTTP request. This class processes those requests
    and sends back the appropriate response (web page or video stream).

    Key Concepts:
    - Inheritance (this class extends BaseHTTPRequestHandler)
    - HTTP protocol basics (GET requests, response codes, headers)
    - Method overriding (we override do_GET from the parent class)
    - String manipulation and encoding
    - Binary data handling
    """

    # Class variable to track the number of active streaming connections
    active_stream_connections = 0

    # -------------------------- DO GET ------------------------------------ #
    def do_GET(self):
        # This method handles GET requests from browsers (like when you type a URL)
        # It decides what to send back based on the requested path
        if self.path == "/":
            # Redirect root path to the main page
            self.send_response(301)
            self.send_header("Location", "/index.html")
            self.end_headers()
        elif self.path == "/index.html":
            # Send the main HTML page
            content = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == "/stream0.mjpg":
            # Handle fish tank camera stream (camera 0)
            self._handle_stream_request(relay0, "Fish Tank")
        elif self.path == "/stream1.mjpg":
            # Handle plant bed camera stream (camera 2)
            self._handle_stream_request(relay1, "Plant Bed")
        elif self.path == "/favicon.ico":
            # Handle favicon requests to prevent 404 errors
            self.send_response(204)  # No Content
            self.end_headers()
        else:
            # Any other path: send a 404 Not Found error
            self.send_error(404)
            self.end_headers()

    def _handle_stream_request(self, camera_relay, camera_description):
        """Handle MJPEG stream requests for a specific camera relay."""
        # Check if the requested camera relay is available
        if camera_relay is None:
            logger.error(
                f"{camera_description} camera not available for {self.path}"
            )
            self.send_error(503, f"{camera_description} camera not available")
            return

        # Increment the connection counter and log new connection
        StreamingHandler.active_stream_connections += 1
        logger.info(
            f"New {camera_description} streaming client connected from {self.client_address[0]} requesting {self.path}. "
            f"Active connections: {StreamingHandler.active_stream_connections}"
        )

        self.send_response(200)
        self.send_header("Age", "0")
        self.send_header("Cache-Control", "no-cache, private")
        self.send_header("Pragma", "no-cache")
        self.send_header(
            "Content-Type", "multipart/x-mixed-replace; boundary=FRAME"
        )
        self.end_headers()
        try:
            while True:
                # Get the latest frame from the specific MediaRelay
                frame = camera_relay.get_frame()
                if frame is not None:
                    # Send the frame boundary marker
                    self.wfile.write(b"--FRAME\r\n")
                    # Send headers for this JPEG image
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Content-Length", str(len(frame)))
                    self.end_headers()
                    # Send the actual image data
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")
        except Exception as e:
            # If the browser disconnects or there's a network error, log it
            logger.warning(
                "Removed streaming client %s (%s): %s",
                self.client_address,
                camera_description,
                str(e),
            )
        finally:
            # Decrement the connection counter when client disconnects
            StreamingHandler.active_stream_connections -= 1
            logger.info(
                f"{camera_description} streaming client {self.client_address[0]} disconnected from {self.path}. "
                f"Active connections: {StreamingHandler.active_stream_connections}"
            )


# -------------------- STREAMING SERVER (Multi-Client) --------------------- #
class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    """
    This class creates the web server that handles multiple clients simultaneously.

    Key Concepts:
    - Multiple inheritance (inherits from both ThreadingMixIn and HTTPServer)
    - Mixin classes (ThreadingMixIn adds threading capability)
    - Class attributes (variables that belong to the class, not instances)
    - Server architecture and design patterns

    ThreadingMixIn allows the server to handle multiple browser connections at once.
    Each client gets its own thread and can independently receive the MJPEG stream.
    The MediaRelay object is shared, but frame access is synchronized for thread safety.
    """

    # Class attributes - these apply to all instances of this class

    # Allow reusing the network address immediately after shutdown
    # Without this, you might get "Address already in use" errors
    allow_reuse_address = True

    # Use daemon threads for client connections
    # This means all client threads will close when the main program exits
    daemon_threads = True


# ======================= GLOBAL VARIABLES ================================= #
# Global MediaRelay objects that will be initialized in main()
# relay0 for fish tank (camera 0), relay1 for plants (camera 2)
relay0: Optional["MediaRelay"] = None  # Fish tank camera
relay1: Optional["MediaRelay"] = None  # Plant bed camera


# ====================== MAIN PROGRAM STARTS HERE ========================== #
# This is where the actual program execution begins.
# Everything above this point was just defining classes and functions.
# Now we use those classes to create and run our camera streaming server.


def find_working_camera():
    """
    Find a working camera efficiently (USB or CSI).
    Returns tuple of (camera_index, use_libcamera) if found, (None, False) otherwise.
    """
    # First, check for CSI cameras if libcamera is available
    if LIBCAMERA_AVAILABLE and is_libcamera_available():
        logger.info("Checking for CSI cameras with libcamera...")
        csi_cameras = detect_csi_cameras()
        if csi_cameras:
            logger.info(f"Found CSI cameras: {csi_cameras}")
            # Try first CSI camera
            try:
                test_cap = LibcameraCapture(0)
                if test_cap.isOpened():
                    logger.info(f"✓ CSI camera 0 is working")
                    test_cap.release()
                    return (0, True)
                test_cap.release()
            except Exception as e:
                logger.warning(f"CSI camera test failed: {e}")
    
    # If user specified a known camera index, try that first (fastest startup)
    if KNOWN_CAMERA_INDEX is not None:
        logger.info(f"Trying known USB camera index {KNOWN_CAMERA_INDEX}...")
        test_cap = cv2.VideoCapture(KNOWN_CAMERA_INDEX, cv2.CAP_V4L2)
        if test_cap.isOpened():
            ret, frame = test_cap.read()
            if ret and frame is not None:
                logger.info(f"✓ Known USB camera {KNOWN_CAMERA_INDEX} is working")
                test_cap.release()
                return (KNOWN_CAMERA_INDEX, False)
            else:
                logger.warning(
                    f"Known USB camera {KNOWN_CAMERA_INDEX} opens but cannot capture frames"
                )
        else:
            logger.warning(f"Known USB camera {KNOWN_CAMERA_INDEX} not available")
        test_cap.release()

    # If known camera failed or not specified, search for USB cameras
    logger.info("Detecting available USB cameras...")
    for cam_idx in range(4):
        logger.info(f"Testing USB camera {cam_idx} with V4L2...")
        test_cap = cv2.VideoCapture(cam_idx, cv2.CAP_V4L2)
        if test_cap.isOpened():
            ret, frame = test_cap.read()
            if ret and frame is not None:
                logger.info(f"✓ Found working USB camera at index {cam_idx}")
                test_cap.release()
                return (cam_idx, False)
            else:
                logger.warning(
                    f"USB camera {cam_idx} opens but cannot capture frames"
                )
        else:
            logger.info(f"USB camera {cam_idx} not available")
        test_cap.release()

    return (None, False)


def main():
    global relay0, relay1  # Declare relays as global so they can be accessed by StreamingHandler

    # Print status messages to help users understand what's happening
    logger.info("Starting dual camera streaming server...")
    logger.info("Camera 0: Fish Tank | Camera 2: Plant Bed")
    
    # Detect if libcamera is available
    if LIBCAMERA_AVAILABLE:
        logger.info("Libcamera support available for CSI cameras")
    
    # Try to detect camera type for camera 0 (Fish Tank)
    use_libcamera_0 = False
    if LIBCAMERA_AVAILABLE and is_libcamera_available():
        csi_cameras = detect_csi_cameras()
        if 0 in csi_cameras:
            use_libcamera_0 = True
            logger.info("Camera 0 detected as CSI camera")

    # Initialize camera relay for fish tank (camera 0) with overlay enabled
    relay0 = MediaRelay(
        enable_overlay=True,
        rotation_angle=0,
        width=CAMERA_WIDTH,
        height=CAMERA_HEIGHT,
        frame_rate=CAMERA_FRAME_RATE,
        max_stream_fps=FISH_CAMERA_MAX_STREAM_FPS,
    )
    try:
        relay0.start_capture(camera_index=0, use_libcamera=use_libcamera_0)
        cam_type_0 = "CSI" if use_libcamera_0 else "USB"
        logger.info(
            f"✓ Fish Tank camera ({cam_type_0} camera 0) initialized successfully with overlay at {CAMERA_WIDTH}x{CAMERA_HEIGHT} @ {CAMERA_FRAME_RATE} FPS (max stream: {FISH_CAMERA_MAX_STREAM_FPS} FPS)"
        )
    except Exception as e:
        logger.error(
            f"✗ Fish Tank camera (camera 0) failed to initialize: {e}"
        )
        relay0 = None

    # Try to detect camera type for camera 2 (Plant Bed)
    use_libcamera_2 = False
    if LIBCAMERA_AVAILABLE and is_libcamera_available():
        csi_cameras = detect_csi_cameras()
        if 1 in csi_cameras:  # Second CSI camera would be index 1
            use_libcamera_2 = True
            logger.info("Camera 2 (Plant Bed) detected as CSI camera")

    # PlantCam (camera 2) is used for plants in the aquaponics system
    # It is mounted upside down, so we rotate the image 180 degrees
    # Initialize camera relay for plant bed (camera 2) with overlay disabled and 180° rotation
    relay1 = MediaRelay(
        enable_overlay=False,
        rotation_angle=180,
        width=PLANT_CAMERA_WIDTH,
        height=PLANT_CAMERA_HEIGHT,
        frame_rate=PLANT_CAMERA_FRAME_RATE,
        max_stream_fps=PLANT_CAMERA_MAX_STREAM_FPS,
    )
    try:
        # For second CSI camera, use index 1 instead of 2
        plant_cam_index = 1 if use_libcamera_2 else 2
        relay1.start_capture(camera_index=plant_cam_index, use_libcamera=use_libcamera_2)
        cam_type_1 = "CSI" if use_libcamera_2 else "USB"
        logger.info(
            f"✓ Plant Bed camera ({cam_type_1} camera {plant_cam_index}) initialized successfully without overlay, rotated 180° at {PLANT_CAMERA_WIDTH}x{PLANT_CAMERA_HEIGHT} @ {PLANT_CAMERA_FRAME_RATE} FPS (max stream: {PLANT_CAMERA_MAX_STREAM_FPS} FPS)"
        )
    except Exception as e:
        logger.error(
            f"✗ Plant Bed camera (camera 2) failed to initialize: {e}"
        )
        relay1 = None

    # Check if at least one camera is working
    if relay0 is None and relay1 is None:
        logger.error("No cameras could be initialized!")
        logger.error("Please check:")
        logger.error("  - USB cameras are connected properly")
        logger.error("  - Cameras are not being used by another application")
        logger.error("  - Camera permissions: sudo usermod -a -G video $USER")
        logger.error("  - Available devices: ls -la /dev/video*")
        logger.error("  - V4L2 info: v4l2-ctl --list-devices")
        exit(1)

    # Log which cameras are available
    if relay0:
        logger.info("Fish Tank camera available at: /stream0.mjpg")
    if relay1:
        logger.info("Plant Bed camera available at: /stream1.mjpg")

    # Now start the web server
    try:
        # Create the network address for our server
        # ("", 8000) means:
        # - "" = listen on all available network interfaces (localhost, WiFi, Ethernet)
        # - 8000 = port number (like a channel number for network communication)
        address = ("", 8000)

        # Create the HTTP server object
        # This combines our StreamingHandler (processes requests) with
        # the StreamingServer (manages network connections)
        server = StreamingServer(address, StreamingHandler)

        # Get network information to display to the user
        import socket  # Import here since we only need it once

        hostname = socket.gethostname()  # Get the computer's name
        try:
            # Try to get the computer's IP address on the local network
            local_ip = socket.gethostbyname(hostname)

            # Print connection information for users
            logger.info(f"Dual camera streaming server started successfully!")
            logger.info(f"Dual camera view: http://localhost:8000/")
            logger.info(f"Network access: http://{local_ip}:8000/")
            logger.info(f"Raspberry Pi access: http://{hostname}.local:8000/")
            if relay0:
                logger.info(
                    f"Fish Tank stream: http://{local_ip}:8000/stream0.mjpg"
                )
            if relay1:
                logger.info(
                    f"Plant Bed stream: http://{local_ip}:8000/stream1.mjpg"
                )
        except:
            # If we can't get the IP address, just show localhost
            logger.info(
                "Dual camera streaming server started on http://localhost:8000/"
            )

        logger.info("Press Ctrl+C to stop the server")
        logger.info("-" * 50)

        # Start the server and keep it running
        # serve_forever() is a blocking call - the program waits here
        # and processes incoming requests until we stop it
        server.serve_forever()

    except KeyboardInterrupt:
        # This exception occurs when user presses Ctrl+C
        logger.info("Streaming stopped by user")

    finally:
        # This block always runs, even if an error occurred
        # It ensures we clean up resources properly

        # Stop both camera capture threads and close camera connections
        if relay0:
            relay0.stop()
            logger.info("Fish Tank camera stopped")
        if relay1:
            relay1.stop()
            logger.info("Plant Bed camera stopped")

        logger.info("Cleanup completed. Goodbye!")


# If this script is run directly (not imported), call the main function
if __name__ == "__main__":
    # Start the main program
    main()
else:
    # If this script is imported as a module, we don't run the main function
    # This allows other scripts to use the MediaRelay and StreamingServer classes
    logger.info(
        "web_stream.py module imported. Use main() to start the server."
    )
