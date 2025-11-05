# Vision App

This project is a computer vision application designed to detect humans and cats from video streams. It uses the YOLOv8 model for object detection and can analyze images with an LM Studio server.

## Features

*   **Real-time object detection:** Detects objects in video streams using the YOLOv8 model.
*   **Motion detection:** Only processes frames when motion is detected.
*   **LM Studio integration:** Sends image snapshots to an LM Studio server for further analysis.
*   **Extensible architecture:** Easily supports new video stream sources.
*   **Terminal UI:** Includes a terminal-based user interface for monitoring.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/SysDevJT/pidetect
    cd detect
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Download the YOLOv8 model:**
    ```bash
    wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
    ```

It wil most likely download itself.

## Configuration

The application is configured through environment variables. You can set the following variables:

*   `RTSP_URL`: The URL of the RTSP stream to connect to.
*   `USE_PICAM`: Set to `true` to use a PiCamera instead of an RTSP stream.
*   `LMSTUDIO_URL`: The URL of the LM Studio server.
*   `LMSTUDIO_MODEL`: The name of the model to use in LM Studio.
*   `WEBHOOK_URL`: The URL to send webhook notifications to.

## Usage

To run the application, use the following command:

```bash
python3 detect_picam_rtsp.py
```

## Examples

# Using picam

USE_PICAM=1 python detect_picam_rtsp.py

# Using rtsp:

RTSP_URL=rtsp://username:password@127.0.0.1:554 python3 detect_picam_rtsp.py

# Use the credentials of the rtsp cam.

See the config.py if you want to use a default.

