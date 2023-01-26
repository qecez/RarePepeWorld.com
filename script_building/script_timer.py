import logging
import time


class ScriptTimer:

    def __init__(self):
        pass

    def start(self):
        logging.info("Starting timer.")
        self.start = time.time()

    def timestamp(self):
        logging.info(f"[{time.time() - self.start}]")
