import os
from PySide6.QtMultimedia import QCamera, QMediaCaptureSession, QMediaDevices, QImageCapture
from PySide6.QtCore import QEventLoop, QTimer


def guard():
    # find camera device
    camera_device = QMediaDevices.videoInputs()[0]
    camera = QCamera(camera_device)
    # create capture session
    capture_session = QMediaCaptureSession()
    capture_session.setCamera(camera)
    image_capture = QImageCapture(camera)
    capture_session.setImageCapture(image_capture)
    # start capture
    camera.start()
    loop = QEventLoop()

    def on_saved() -> None:
        loop.quit()

    def do_capture() -> None:
        save_path = os.path.join(os.getcwd(), "captured_image.jpg")
        image_capture.captureToFile(save_path)

    image_capture.imageSaved.connect(on_saved)

    QTimer.singleShot(1000, do_capture)
    loop.exec()
