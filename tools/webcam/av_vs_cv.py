import numpy as np
import cv2 as cv
import av
import time

class Converter:
    def cv_bgr2nv12(self, bgr):
        yuv = cv.cvtColor(bgr, cv.COLOR_BGR2YUV_I420)
        uv_row_cnt = yuv.shape[0] // 3
        uv_plane = np.transpose(yuv[uv_row_cnt * 2:].reshape(2, -1), [1, 0])
        yuv[uv_row_cnt * 2:] = uv_plane.reshape(uv_row_cnt, -1)
        return yuv.tobytes()

    def bgr2nv12(self, bgr):
        frame = av.VideoFrame.from_ndarray(bgr, format='bgr24')
        return frame.reformat(format='nv12').to_ndarray()

def benchmark(func, input_data, repeat=100):
    start = time.perf_counter()
    for _ in range(repeat):
        func(input_data)
    end = time.perf_counter()
    return (end - start) / repeat

if __name__ == "__main__":
    converter = Converter()

    height, width = 1080, 1920
    bgr_image = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)

    repeat = 100
    print(f"Running benchmark with {repeat} runs on {width}x{height} image...")

    t_cv = benchmark(converter.cv_bgr2nv12, bgr_image, repeat)
    t_av = benchmark(converter.bgr2nv12, bgr_image, repeat)

    print(f"cv_bgr2nv12 average time: {t_cv * 1000:.3f} ms")
    print(f"bgr2nv12 average time:   {t_av * 1000:.3f} ms")

    if t_cv < t_av:
        print("OpenCV version is faster")
    else:
        print("PyAV version is faster")

