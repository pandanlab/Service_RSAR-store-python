import cv2
import numpy as np
import requests
import threading
import RTRQ.Node.NodeApp as NodeApp
import time

class CameraRemote:
    def __init__(self) -> None:
        self.url = 'http://192.168.1.19:5000/video_feed'
        self.stop = threading.Event()
        self.pause = threading.Event()
        self.pause.set()
        self.sw = 0

    def enhance_image(self, img):
        try:
            # Convert to YUV color space
            yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
            y, u, v = cv2.split(yuv)

            # Apply CLAHE to the Y channel
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            y_clahe = clahe.apply(y)

            # Merge back the channels
            yuv_clahe = cv2.merge([y_clahe, u, v])
            img_clahe = cv2.cvtColor(yuv_clahe, cv2.COLOR_YUV2BGR)

            # Apply Non-Local Means Denoising
            img_denoised = cv2.fastNlMeansDenoisingColored(img_clahe, None, h=10, hForColor=10, templateWindowSize=7, searchWindowSize=21)

            # Increase brightness and contrast
            alpha = 1.5  # Contrast control
            beta = 40    # Brightness control
            img_contrast = cv2.convertScaleAbs(img_denoised, alpha=alpha, beta=beta)

            # Adaptive Contrast Enhancement
            lab = cv2.cvtColor(img_contrast, cv2.COLOR_BGR2Lab)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            limg = cv2.merge((cl, a, b))
            img_adaptive_contrast = cv2.cvtColor(limg, cv2.COLOR_Lab2BGR)

            # Sharpen the image
            kernel = np.array([[0, -1, 0],
                               [-1, 5, -1],
                               [0, -1, 0]])
            img_sharpened = cv2.filter2D(img_adaptive_contrast, -1, kernel)

            return img_sharpened
        except Exception as e:
            print(f"Error in enhance_image: {e}")
            return img  # Return the original image if enhancement fails

    def camera_loop(self):
        try:
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
        except Exception as e:
            print(f"Error in camera_loop: {e}")
        finally:
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
