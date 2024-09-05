import sys
sys.path.append("./")

import threading
import cv2
import time
import RTRQ.Node.NodeApp as NodeApp

class Camera_Custom():
    def __init__(self) -> None:
        self.stop  = threading.Event()
        self.pause = threading.Event()
        self.pause.set()
        self.sw = 0

    def camera_loop(self):
        self.cap = cv2.VideoCapture(0) 
        while not self.stop.is_set():
            self.pause.wait()
            ret, frame = self.cap.read()
            NodeApp.data_Camera.value = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            # cv2.imshow("",frame)
            cv2.waitKey(1)
        self.cap.release()
        cv2.destroyAllWindows()
        NodeApp.handle_stateStop.value = None

    def pause_camera(self):
        self.pause.clear()
        

    def resume_camera(self):
        self.pause.set()

    def stop_camera(self):
        self.stop.set()
        self.sw = 0
        self.pause.set()
        print("Camera Stop")

    def start_camera(self):
        if self.sw == 0:
            self.pause.set()
            self.stop.clear()
            self.thread = threading.Thread(target=self.camera_loop,daemon=True)
            self.thread.start()
            self.sw = 1
            print("Camera Start")

hello = Camera_Custom()
NodeApp.handle_startCamera.add_callback(lambda new_value: hello.start_camera())
NodeApp.handle_stopCamera.add_callback(lambda new_value: hello.stop_camera())
NodeApp.handle_pauseCamera.add_callback(lambda new_value: hello.pause_camera())
NodeApp.handle_resumeCamera.add_callback(lambda new_value: hello.resume_camera())

# Test
# while 1:
#     data = input("user : ")
#     if("start" in data):
#         NodeApp.handle_startCamera.value = None
#     elif("stop" in data):
#         NodeApp.handle_stopCamera.value = None
#     elif("pause" in data):
#         NodeApp.handle_pauseCamera.value = None
#     elif("resume" in data):
#         NodeApp.handle_resumeCamera.value = None
#     else:
#         print(data)