import av
import cv2 as cv

class Camera:
  def __init__(self, cam_type_state, stream_type, camera_id):
    try:
      camera_id = int(camera_id)
    except ValueError: # allow strings, ex: /dev/video0
      pass
    self.cam_type_state = cam_type_state
    self.stream_type = stream_type
    self.cur_frame_id = 0

    print(f"Opening {cam_type_state} at {camera_id}")

    #self.cap = cv.VideoCapture(camera_id)
    self.cap = cv.VideoCapture(f"gst-launch-1.0 v4l2src device={camera_id} io-mode=2 ! image/jpeg, width=1280, height=720, framerate=30/1, format=MJPG ! jpegdec ! videoconvert ! appsink", cv.CAP_GSTREAMER)

    #self.cap.set(cv.CAP_PROP_FRAME_WIDTH, 1280.0)
    #self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, 720.0)
    #self.cap.set(cv.CAP_PROP_FPS, 25)

    self.W = self.cap.get(cv.CAP_PROP_FRAME_WIDTH)
    self.H = self.cap.get(cv.CAP_PROP_FRAME_HEIGHT)

  @classmethod
  def bgr2nv12(self, bgr):
    frame = av.VideoFrame.from_ndarray(bgr, format='bgr24')
    return frame.reformat(format='nv12').to_ndarray()

  def cv_rgb2nv12(self, rgb):
    yuv = cv2.cvtColor(rgb, cv2.COLOR_BGR2YUV_I420)
    uv_row_cnt = yuv.shape[0] // 3
    uv_plane = np.transpose(yuv[uv_row_cnt * 2:].reshape(2, -1), [1, 0])
    yuv[uv_row_cnt * 2:] = uv_plane.reshape(uv_row_cnt, -1)
    return yuv.tobytes()

  def read_frames(self):
    while True:
      ret, frame = self.cap.read()
      if not ret:
        break
      #yuv = Camera.bgr2nv12(frame)
      yuv = cv_rgb2nv12(frame)
      yield yuv.data.tobytes()
    self.cap.release()
