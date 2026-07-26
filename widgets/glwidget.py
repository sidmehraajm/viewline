from __future__ import absolute_import

import numpy

from OpenGL import GL

from PySide6 import QtGui
from PySide6 import QtCore
from PySide6 import QtWidgets
from PySide6 import QtOpenGLWidgets

from viewline import utils
from viewline import logger
from viewline import constants

from viewline.widgets.annotations import Sketch

LOGGER = logger.getLogger(__name__)


class GLViewer(QtOpenGLWidgets.QOpenGLWidget):
    """Modern OpenGL image viewer."""

    render_finished = QtCore.Signal(str)

    def __init__(self, parent=None):
        """Create OpenGL viewer."""

        # super(GLViewer, self).__init__(parent)
        super().__init__(parent)

        # Expand inside layouts.

        # Configure expanding size policy
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding
        )

        self.setSizePolicy(sizePolicy)

        # Current image.
        self.numpy_frame = None

        # Timeline.
        self.current_frame = None

        self.is_enabled = False

        # Viewer mode.
        self.fit_mode = True

        self.zoom = 1.0

        self.display_parameter = None
        self.style_parameter = None
        self.filter_parameter = None

        # Pan offset (normalized).
        self.pan = QtCore.QPointF(0.0, 0.0)

        # Display rectangle.
        self.display_rect = QtCore.QRect()

        # Set samples
        self.set_samples(constants.VIEWER_SAMPLES_RATE)

        # Annotation system.
        self.sketch = Sketch()

        self.set_samples(constants.VIEWER_SAMPLES_RATE)

    def set_samples(self, samples=8):
        """Configure OpenGL multisampling."""

        surface = QtGui.QSurfaceFormat()
        surface.setSamples(samples)
        self.setFormat(surface)

    def initializeGL(self):
        """Initialize OpenGL and the Hydra engine."""

        pass

    def resizeGL(self, width, height):
        """Handle OpenGL viewport resize."""

        pass

    def paintGL(self):
        """Render the current USD stage."""

        pass

    def clear(self):
        """Clear viewer."""

        # self.is_enabled = False

        # Clear the OpenGL framebuffer.
        self.makeCurrent()

        try:
            GL.glClearColor(*self.background_color)
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
            GL.glFlush()

        finally:
            self.doneCurrent()

        self.sketch.clear_all()

        self.update()

    def mousePressEvent(self, event):
        """Handle mouse press for viewport navigation or sketching."""

        self.setFocus()

        modifiers = event.modifiers()

        if modifiers & QtCore.Qt.KeyboardModifier.AltModifier:
            # Viewport navigation mode
            self.last_mouse_position = event.position()
        else:
            # Sketch mode

            if not self.sketch.enabled:
                return

            point = self.widget_to_image_point(event.position().toPoint())
            self.sketch.mousePressEvent(point)

            self.update()

        # event.accept()

    def mouseMoveEvent(self, event):
        """Handle mouse movement for viewport navigation or sketching."""

        modifiers = event.modifiers()

        # Viewport navigation mode
        if modifiers & QtCore.Qt.KeyboardModifier.AltModifier:
            if self.last_mouse_position is None:
                return

            current = event.position()
            delta = current - self.last_mouse_position
            dx = delta.x()
            dy = delta.y()

            buttons = event.buttons()

            if buttons & QtCore.Qt.MouseButton.LeftButton:
                # Alt + Left drag → Orbit
                self.camera.orbit(
                    dx,
                    dy,
                )
                self.update_view()
            elif buttons & QtCore.Qt.MouseButton.MiddleButton:
                # Alt + Middle drag → Pan
                self.camera.pan(dx, dy)
                self.update_view()

            self.last_mouse_position = current

        # Sketch mode
        else:
            if not self.sketch.enabled:
                return

            if not (event.buttons() & QtCore.Qt.MouseButton.LeftButton):
                return

            point = self.widget_to_image_point(event.position().toPoint())
            self.sketch.mouseMoveEvent(point)
            self.update()

        # event.accept()

    def mouseReleaseEvent(self, event):
        """Handle mouse release for navigation or sketching."""

        modifiers = event.modifiers()

        # Viewport navigation
        if modifiers & QtCore.Qt.KeyboardModifier.AltModifier:
            self.last_mouse_position = None

        # Sketch mode
        else:
            if self.sketch.enabled:
                point = self.widget_to_image_point(event.position().toPoint())
                self.sketch.mouseReleaseEvent(point)
                self.update()

        # event.accept()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()

        self.camera.zoom(delta)
        self.update_view()

        event.accept()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_F:
            self.frame_all()
            self.update_view()

            event.accept()
            return

        super().keyPressEvent(event)

    def set_current_frame(self, frame):
        """Update timeline."""

        self.current_frame = frame

        self.sketch.set_frame(frame)

    def fit_to_window(self):
        """Fit image inside viewer."""

        self.fit_mode = True
        self.zoom = 1.0

        self.pan = QtCore.QPointF()

        self.update()

    def set_actual_size(self):
        """Display image at 100%."""

        self.fit_mode = False
        self.zoom = 1.0

        self.pan = QtCore.QPointF()

        self.update()

    def set_zoom(self, zoom):
        """Set viewer zoom.

        Args:
            zoom (float):
                Zoom factor.
        """

        self.fit_mode = False
        self.zoom = max(0.05, min(zoom, 32.0))

        self.update()

    def zoom_in(self):
        """Increase zoom."""

        self.set_zoom(self.zoom * 1.25)

    def zoom_out(self):
        """Decrease zoom."""

        self.set_zoom(self.zoom / 1.25)

    def set_pan(self, x, y):
        """Move camera.

        Args:
            x (float):
                Horizontal offset.

            y (float):
                Vertical offset.
        """

        self.pan = QtCore.QPointF(x, y)

        self.update()

    def reset_view(self):
        """Reset camera."""

        self.zoom = 1.0
        self.pan = QtCore.QPointF()
        self.fit_mode = True

        self.update()

    def undo_strokes(self):
        """
        Undo current frame annotation.
        """

        self.sketch.undo()

        self.update()

    def clear_strokes(self):
        """
        clear current frame annotation.
        """

        self.sketch.clear_all()

        self.update()

    def draw_overlay(self):
        """
        Draw all overlays.

        This method handles:
            - Text overlays
            - Image overlays
            - Overlay antialiasing
            - Overlay positioning
        """

        # Create painter
        painter = QtGui.QPainter(self)

        # Enable render quality
        # painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        # painter.setRenderHint(QtGui.QPainter.TextAntialiasing, True)
        # painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)

        # Draw pencil annotations
        self.sketch.draw(
            painter, point_converter=self.image_to_widget_point, rect=self.display_rect
        )

        painter.end()

    def set_overlay_options(self, watermarks):
        self.sketch.set_overlays(watermarks)
        self.update()

    def set_overlay_option(self, checked, key, position, context):
        self.sketch.set_overlay(checked, key, position, context)
        self.update()

    def set_sketch_enabled(self, tool, enabled, font):
        """
        Enable or disable pencil tool.

        Args:
            enabled (bool): Pencil tool state.
        """

        if not self.current_frame:
            return

        self.sketch.set_tool(tool)
        self.sketch.set_enabled(enabled)

        self.sketch.set_image_size(self.image_width, self.image_height)
        self.sketch.set_eraser_radius(10)
        self.sketch.set_txt_font(font)

    def widget_to_image_point(self, point):
        """
        Convert widget position to normalized image space.
        """

        rect = self.display_rect

        x = (point.x() - rect.left()) / float(rect.width())
        y = (point.y() - rect.top()) / float(rect.height())

        x = max(0.0, min(1.0, x))
        y = max(0.0, min(1.0, y))

        return (x, y)

    def image_to_widget_point(self, point):
        """
        Convert normalized image space to widget coordinates.
        """

        rect = self.display_rect

        x = rect.left() + (point[0] * rect.width())
        y = rect.top() + (point[1] * rect.height())

        return QtCore.QPointF(x, y)

    def save_frame(self, filepath, post_process=False):
        image = self.render_current_frame()

        if image:
            utils.makedirs(filepath)
            image.save(filepath)
            LOGGER.info(f"Succeed, render to {filepath}")

            if post_process:
                self.render_finished.emit(filepath)
        else:
            LOGGER.error(f"Failure render to {filepath}")

            if post_process:
                self.render_finished.emit(None)


if __name__ == "__main__":
    pass
