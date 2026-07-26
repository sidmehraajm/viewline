from __future__ import absolute_import


from pxr import Usd


class USDStage(object):

    def __init__(self):
        self.stage = None

    def open(self, filename):
        self.stage = Usd.Stage.Open(filename)

        if self.stage is None:
            raise RuntimeError(f"Unable to open USD file: {filename}")

    def set_time(self, time_code):
        if self.stage is None:
            return

        self.stage.SetTimeCode(time_code)

    def traverse(self):
        if self.stage is None:
            return []

        return list(self.stage.Traverse())
