import sys


from PySide6 import QtWidgets

from viewline.usd_viewer.viewer_widget import USDViewWidget

from viewline import resources


def main():
    """
    Application entry point.
    """

    app = QtWidgets.QApplication(sys.argv)

    viewer = USDViewWidget()
    viewer.resize(1280, 720)
    viewer.setWindowTitle("USD Viewer Test")

    viewer.show()

    filepath = "D:/works/developments/uploads/usd/Kitchen_set/Kitchen_set.usd"
    # filepath = "D:/works/developments/viewline/resources/media/cube1.usd"
    # filepath = "D:/works/developments/viewline/resources/media/char4.usd"
    # filepath = "D:/works/developments/uploads/usd/UsdSkelExamples/HumanFemale/HumanFemale.walk.usd"
    # filepath = "D:/works/developments/uploads/usd/PointInstancedMedCity/PointInstancedMedCity.usd"
    # filepath = "D:/works/developments/uploads/usd/jasmin.usd"
    filepath = "D:/works/developments/uploads/usd/dragon.usd"

    viewer.load_usd(filepath)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
