import sys
sys.path.append("./")

import cv2
import numpy as np
import requests
import threading
import RTRQ.Node.NodeApp as NodeApp
import time

class CameraRemote:
    def __init__(self) -> None:
        self.url = 'http://192.168.1.19:5000/video_feed'
        self.stop  = threading.Event()
        self.pause = threading.Event()
        self.pause.set()
        self.sw = 0

    def enhance_image(self, img):
        # Convert to YUV color space
        yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
        y, u, v = cv2.split(yuv)
        
        # Apply histogram equalization to the Y channel
        y_eq = cv2.equalizeHist(y)
        
        # Merge back the channels
        yuv_eq = cv2.merge([y_eq, u, v])
        img_eq = cv2.cvtColor(yuv_eq, cv2.COLOR_YUV2BGR)
        
        # Increase brightness and contrast
        alpha = 1.3  # Contrast control
        beta = 30    # Brightness control
        img_enhanced = cv2.convertScaleAbs(img_eq, alpha=alpha, beta=beta)
        
        return img_enhanced

    def camera_loop(self):
        self.stream = requests.get(self.url, stream=True)
        self.bytes_data = b''
        for chunk in self.stream.iter_content(chunk_size=1024):
            self.bytes_data += chunk
            a = self.bytes_data.find(b'\xff\xd8')  # Start of JPEG frame
            b = self.bytes_data.find(b'\xff\xd9')  # End of JPEG frame
            
            if a != -1 and b != -1:
                jpg = self.bytes_data[a:b+2]  # Extract JPEG frame
                self.bytes_data = self.bytes_data[b+2:]  # Remove processed bytes
                img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)  # Decode JPEG frame
                
                # Enhance the image for better night-time visibility
                img = self.enhance_image(img)
                
                frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                NodeApp.data_Camera.value = frame
                # Uncomment if you want to display the image
                # cv2.imshow("Camera Feed", img)
                cv2.waitKey(1)

            self.pause.wait()
            if self.stop.is_set():
                break
        print("Camera Stop")
        self.sw = 0
        self.stop.clear()
        self.pause.set()
        NodeApp.handle_stateStop.value = None
        time.sleep(1)

    def pause_camera(self):
        self.pause.clear()
        
    def resume_camera(self):
        self.pause.set()

    def stop_camera(self):
        self.stop.set()

    def start_camera(self):
        if self.sw == 0:
            self.thread = threading.Thread(target=self.camera_loop, daemon=True)
            self.thread.start()
            self.sw = 1
            print("Camera Start")

hello = CameraRemote()
NodeApp.handle_startCamera.add_callback(lambda new_value: hello.start_camera())
NodeApp.handle_stopCamera.add_callback(lambda new_value: hello.stop_camera())
NodeApp.handle_pauseCamera.add_callback(lambda new_value: hello.pause_camera())
NodeApp.handle_resumeCamera.add_callback(lambda new_value: hello.resume_camera())
