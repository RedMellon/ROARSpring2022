import logging
from websocket import create_connection
from typing import List, Optional, Tuple, List
import cv2
import numpy as np
from pathlib import Path
from ROAR.utilities_module.module import Module

import datetime


class RGBCamStreamer(Module):
    def save(self, **kwargs):
        if self.curr_image is not None:
            cv2.imwrite((self.dir_path / f"{self.name}_{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f')}.jpg").as_posix(),
                        self.curr_image)

    def __init__(self, host, port, show=False, resize: Optional[Tuple] = None,
                 name: str = "world_cam", threaded: bool = True,
                 should_record: bool = False, dir_path: Path = Path("./data/images")):
        super().__init__(threaded=threaded, name=name)
        self.logger = logging.getLogger(f"{self.name} server on [{host}:{port}]")
        self.host = host
        self.port = port
        self.ws = None

        self.resize = resize
        self.show = show

        self.curr_image: Optional[np.ndarray] = None
        self.should_record = should_record
        self.dir_path = dir_path / f"{self.name}"
        if self.dir_path.exists() is False:
            self.dir_path.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"{name} initialized")

    def receive(self):
        try:
            self.ws = create_connection(f"ws://{self.host}:{self.port}/{self.name}")
            result = self.ws.recv()
            try:
                img = np.frombuffer(result, dtype=np.uint8)
                self.curr_image = cv2.imdecode(img, cv2.IMREAD_UNCHANGED)[:, :, :3]
                self.curr_image = cv2.rotate(self.curr_image, cv2.ROTATE_90_CLOCKWISE)
                if self.resize:
                    self.curr_image = cv2.resize(self.curr_image, self.resize)

            except Exception as e:
                self.logger.error(f"Failed to decode image: {e}")

            if self.show:
                cv2.imshow("img", self.curr_image)
                cv2.waitKey(1)
        except Exception as e:
            self.logger.error(f"Failed to get image: {e}")

    def run_in_threaded(self, **kwargs):
        self.run_in_series()

    def run_in_series(self, **kwargs):
        while True:
            self.receive()


if __name__ == '__main__':
    ir_image_server = RGBCamStreamer(host="10.142.143.48", port=8005, name="world_cam", show=True)
    ir_image_server.run_in_series()