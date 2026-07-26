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

from viewline.widgets.glwidget import GLViewer
from viewline.widgets.annotations import Sketch

from viewline.materials.gl_shader import GLShader
from viewline.materials.gl_texture import GLTexture
from viewline.materials.gl_screen import FullscreenQuad

from viewline.materials.gl_ocio_shader import OCIOShader

from viewline.widgets.menus import Viewer2dMenubar

from viewline.widgets.layouts import VerticalLayout

LOGGER = logger.getLogger(__name__)


class Viewer2dLayout(VerticalLayout):

    def __init__(self, parent, *args, **kwargs):
        super(Viewer2dLayout, self).__init__(parent, *args, **kwargs)

        self.viewer2dMenubar = Viewer2dMenubar(None)
        self.viewer2dMenubar.setVisible(False)
        self.addWidget(self.viewer2dMenubar)

        self.viewer2d = GLViewer2d(None)
        self.addWidget(self.viewer2d)


class GLViewer2d(GLViewer):
    """Modern OpenGL image viewer."""

    def __init__(self, parent=None):
        """Create OpenGL viewer."""

        super().__init__(parent)
        # super(GLViewer2d, self).__init__(parent)

        # Current image.
        self.numpy_frame = None

        self.ocio_processor = None

        # OpenGL resources.
        self.texture = None
        self.shader = None
        self.quad = None
        self.ocio_shader = None  # GPU OCIO shader
        self.use_ocio = False

        # Timeline.
        self.current_frame = None

        self.background_color = (0.1, 0.1, 0.1, 1.0)

        # Image size.
        self.image_width = 0
        self.image_height = 0
        self.channels = None

    def initializeGL(self):
        """Initialize OpenGL resources."""

        # Background colour.
        GL.glClearColor(*self.background_color)

        # Enable alpha blending.
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

        # Create fullscreen quad.
        self.quad = FullscreenQuad()
        self.quad.initialize()

        # Create texture.
        self.texture = GLTexture()
        self.texture.initialize()

        # Compile default shader.
        self.shader = GLShader()
        self.shader.initialize(name="display")

        # if self.ocio_processor:
        self.build_ocio_shader()

    def resizeGL(self, width, height):
        """Viewport resized."""

        GL.glViewport(0, 0, width, height)

    def paintGL(self):
        """Render current frame.

        Rendering Pipeline

            CPU Image
                │
                ▼
            GL Texture
                │
                ▼
            Fragment Shader
                │
                ▼
            Fullscreen Quad
                │
                ▼
            Screen
        """

        # Clear framebuffer.
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        # Nothing to draw.
        if self.numpy_frame is None:
            return

        self.texture.upload(self.numpy_frame)

        # Calculate display rectangle.
        self.update_display_rect()

        # Bind texture.
        self.texture.bind(0)

        if self.use_ocio:
            self.active_shader = self.ocio_shader
        else:
            self.active_shader = self.shader

        # Use texture shader.
        self.active_shader.bind()

        dpr = self.devicePixelRatioF()

        viewport_width = int(self.width() * dpr)
        viewport_height = int(self.height() * dpr)

        # Physical OpenGL viewport size.
        self.active_shader.set_uniform_vec2(
            "viewportSize",
            float(viewport_width),
            float(viewport_height),
        )

        # Fitted image rectangle.
        self.active_shader.set_uniform_vec4(
            "displayRect",
            (
                float(self.display_rect.left()),
                float(self.display_rect.top()),
                float(self.display_rect.width()),
                float(self.display_rect.height()),
            ),
        )

        # Texture unit.
        self.active_shader.set_uniform_int("imageTexture", 0)

        if self.display_parameter:
            self.active_shader.set_uniform_float(
                self.display_parameter.control, self.display_parameter.value
            )

            if self.display_parameter.is_color:
                self.active_shader.set_uniform_vec3(
                    self.display_parameter.color_control, *self.display_parameter.color
                )

        if self.style_parameter:
            self.active_shader.set_uniform_float(
                self.style_parameter.control, self.style_parameter.value
            )

        if self.filter_parameter:
            self.active_shader.set_uniform_vec2(
                "uTexelSize", 1.0 / self.image_width, 1.0 / self.image_height
            )

            self.active_shader.set_uniform_vec2(
                "uResolution",
                float(self.image_width),
                float(self.image_height),
            )

            self.active_shader.set_uniform_float(
                self.filter_parameter.control, self.filter_parameter.value
            )

        # Draw fullscreen quad.
        self.quad.draw()

        # Release shader.
        self.active_shader.release()

        # Release texture.
        self.texture.release()

        # Draw overlays.
        self.draw_overlay()

    def clear(self):
        """Clear viewer."""

        super().clear()

        self.numpy_frame = None
        self.current_frame = None

    def update_display_rect(self):
        """Calculate fitted display rectangle."""

        if self.numpy_frame is None:
            return

        # Device scale.
        dpr = self.devicePixelRatioF()

        viewport_width = int(self.width() * dpr)
        viewport_height = int(self.height() * dpr)

        # Image aspect.
        image_aspect = self.image_width / self.image_height

        viewport_aspect = viewport_width / viewport_height

        # Fit image.
        if image_aspect > viewport_aspect:
            draw_width = viewport_width
            draw_height = int(draw_width / image_aspect)
        else:
            draw_height = viewport_height
            draw_width = int(draw_height * image_aspect)

        # Center image.
        x = int((viewport_width - draw_width) / 2)
        y = int((viewport_height - draw_height) / 2)

        # Logical coordinates.
        self.display_rect = QtCore.QRect(
            int(x / dpr), int(y / dpr), int(draw_width / dpr), int(draw_height / dpr)
        )

    def set_ocio(self, processor):
        """Update the active OCIO display transform."""

        self.ocio_processor = processor

        # Rebuild GPU shader if OpenGL already exists.
        self.build_ocio_shader()

        self.update()

    def build_ocio_shader(self):
        """Build GPU OCIO shader."""

        # if not self.ocio_processor:
        #     return

        self.ocio_shader = OCIOShader(None)
        self.ocio_shader.build(self.ocio_processor)

        self.ocio_shader.release()

        self.use_ocio = self.ocio_processor.enabled

    def display_changed(self, parameter):
        self.display_parameter = parameter
        self.update()

    def style_changed(self, parameter):
        self.style_parameter = parameter
        self.update()

    def filter_changed(self, parameter):
        self.filter_parameter = parameter
        self.update()

    def set_frame(self, frame):
        """Update current image.

        Args:
            frame (numpy.ndarray):
                RGB or RGBA image.
        """

        if not self.is_enabled:
            return

        # Store frame.
        self.numpy_frame = frame

        if frame is None:
            return

        # Image size.
        self.image_height, self.image_width, self.channels = frame.shape

        # Texture upload happens inside paintGL().
        self.update()

    def set_sketch_enabled(self, tool, enabled, font):
        """
        Enable or disable pencil tool.

        Args:
            enabled (bool): Pencil tool state.
        """

        super().set_sketch_enabled(tool, enabled, font)

    def render_current_frame(self):
        """
        Render source frame with annotations.

        Returns:
            QImage
        """

        if self.numpy_frame is None:
            return None

        # Convert AVFrame -> RGB NumPy image.
        # frame = self.numpy_frame.to_ndarray(format="rgb24")

        # Ensure contiguous memory.
        frame = numpy.ascontiguousarray(self.numpy_frame)

        height, width, channels = frame.shape
        frame = numpy.ascontiguousarray(frame)

        if channels == 4:
            image = QtGui.QImage(
                frame.data, width, height, width * 4, QtGui.QImage.Format_RGBA8888
            ).copy()
        else:
            image = QtGui.QImage(
                frame.data,
                width,
                height,
                width * 3,
                QtGui.QImage.Format_RGB888,
            ).copy()

        painter = QtGui.QPainter(image)
        self.sketch.set_frame(self.current_frame)

        image_rect = QtCore.QRect(0, 0, width, height)
        self.sketch.draw(
            painter,
            point_converter=lambda point: QtCore.QPointF(
                point[0] * width,
                point[1] * height,
            ),
            rect=image_rect,
        )

        painter.end()

        return image


if __name__ == "__main__":
    pass
