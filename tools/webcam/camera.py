import subprocess
import os

class Camera:
  def __init__(self, cam_type_state, stream_type, camera_id):
    self.cam_type_state = cam_type_state
    self.stream_type = stream_type
    self.cur_frame_id = 0
    self.W, self.H = 1280, 720
    self.frame_size = self.W * self.H * 3 // 2  # NV12 格式大小
    self.proc = self._start_gst_pipeline()

  def _start_gst_pipeline(self):
    env = os.environ.copy()
    env["GST_PLUGIN_PATH"] = "/usr/lib/gstreamer-1.0:" + env.get("GST_PLUGIN_PATH", "")
    env["LD_LIBRARY_PATH"] = "/usr/lib:" + env.get("LD_LIBRARY_PATH", "")

    # GStreamer pipeline with rotation
    gst_command = f"""
    export GST_PLUGIN_PATH="{env['GST_PLUGIN_PATH']}";
    export LD_LIBRARY_PATH="{env['LD_LIBRARY_PATH']}";
    gst-launch-1.0 -q qtiqmmfsrc camera=0 name=camsrc \
        ! video/x-raw,format=NV12,width={self.W},height={self.H},framerate=25/1 \
        ! videoflip method=rotate-180 \
        ! fdsink fd=1
    """

    # Use sudo with -E to preserve environment
    cmd = ["sudo", "-E", "bash", "-c", gst_command]

    return subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10**8, env=env)

  def read_frames(self):
    try:
      while True:
        raw = self.proc.stdout.read(self.frame_size)
        if len(raw) != self.frame_size:
          break
        yield raw
    except Exception as e:
      print(f"{e}")
    self.proc.terminate()
