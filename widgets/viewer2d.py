"""
Copyright (c) 2026, Motion-Craft Technology All rights reserved.

Author:
    Subin. Gopi (subing85@gmail.com).

Module:
    ./widgets/viewer2d.py

Description:
    2D OpenGL viewer for movie and image-sequence playback.

Responsibilities:
    - Render movie and image-sequence frames using OpenGL.
    - Upload NumPy image data to the GPU as textures.
    - Display images using configurable GLSL shaders.
    - Apply optional OpenColorIO colour transformations.
    - Support display, style, and filter parameters.
    - Render annotations and overlays on top of the image.

Features:
    - Hardware-accelerated image display.
    - Movie and image-sequence frame support.
    - OpenGL texture-based rendering.
    - OpenColorIO shader integration.
    - Display, style, and filter controls.
    - Image fitting and viewport management.
    - Sketch and annotation overlay support.
    - Frame rendering and image export.

Architecture:
    - ``Viewer2dLayout``:
        Provides the 2D viewer layout and menu bar.

    - ``GLViewer2d``:
        Implements the OpenGL-based 2D image viewer.

    - ``GLViewer``:
        Provides common viewer functionality such as camera/view state,
        annotations, overlays, and user interaction.

    - ``GLTexture``:
        Uploads NumPy image data to an OpenGL texture.

    - ``GLShader``:
        Displays the image using the standard display shader.

    - ``OCIOShader``:
        Applies OpenColorIO colour processing during rendering.

    - ``FullscreenQuad``:
        Provides the screen-aligned geometry used to display the texture.

Nodes:
    Viewer2dLayout
        └── Viewer2dMenubar
        └── GLViewer2d
            ├── GLViewer
            ├── GLTexture
            ├── GLShader
            ├── OCIOShader
            └── FullscreenQuad
"""

from __future__ import absolute_import

import numpy

from OpenGL import GL

from PySide6 import QtGui
from PySide6 import QtCore

from viewline import logger

from viewline.widgets.glwidget import GLViewer

from viewline.materials.gl_shader import GLShader
from viewline.materials.gl_texture import GLTexture
from viewline.materials.gl_screen import FullscreenQuad

from viewline.materials.gl_ocio_shader import OCIOShader

from viewline.widgets.menus import Viewer2dMenubar

from viewline.widgets.layouts import VerticalLayout

LOGGER = logger.getLogger(__name__)


class Viewer2dLayout(VerticalLayout):
    """Layout containing the 2D viewer menu bar and OpenGL viewer.

    The layout combines the viewer-specific menu bar with the
    :class:`GLViewer2d` widget used to display movie and image-sequence content.

    Attributes:
        viewer2dMenubar: Menu bar containing 2D viewer controls.
        viewer2d: OpenGL-based 2D image viewer.
    """

    def __init__(self, parent, *args, **kwargs):
        """Create and initialise the 2D viewer layout.

        Args:
            parent: Parent Qt widget.
            *args: Additional layout arguments.
            **kwargs: Additional layout keyword arguments.
        """

        # Initialise the base vertical layout.
        super(Viewer2dLayout, self).__init__(parent, *args, **kwargs)

        # Create the 2D viewer menu bar.
        self.viewer2dMenubar = Viewer2dMenubar(None)

        # Keep the menu bar hidden until it is explicitly enabled.
        self.viewer2dMenubar.setVisible(False)

        # Add the menu bar to the layout.
        self.addWidget(self.viewer2dMenubar)

        # Create the OpenGL-based 2D viewer.
        self.viewer2d = GLViewer2d(None)

        # Add the viewer below the menu bar.
        self.addWidget(self.viewer2d)


class GLViewer2d(GLViewer):
    """OpenGL viewer for movies and image sequences.

    The viewer receives decoded frames as NumPy arrays, uploads them to the GPU as OpenGL textures, and displays them through GLSL shaders.

    Optional OpenColorIO processing can be applied during rendering.
    Viewer annotations and overlays are rendered on top of the image using the functionality provided by the base :class:`GLViewer`.

    Attributes:
        numpy_frame: Current image frame stored as a NumPy array.
        ocio_processor: OpenColorIO processor used for colour management.
        texture: OpenGL texture containing the current image frame.
        shader: Standard image display shader.
        quad: Fullscreen quad used to render the image texture.
        ocio_shader: Shader used for OpenColorIO processing.
        use_ocio: Whether OpenColorIO processing is enabled.
        current_frame: Current frame number.
        background_color: OpenGL viewport background colour.
        image_width: Width of the current image in pixels.
        image_height: Height of the current image in pixels.
        channels: Number of channels in the current image.
    """

    def __init__(self, parent=None):
        """Create OpenGL viewer."""

        # Initialise the common viewer functionality.
        super().__init__(parent)

        # Store the current image frame.
        self.numpy_frame = None

        # Store the active OpenColorIO processor.
        self.ocio_processor = None

        # OpenGL texture used to store the current frame.
        self.texture = None

        # Standard image display shader.
        self.shader = None

        # Screen-aligned geometry used to render the image.
        self.quad = None

        # OpenColorIO colour-processing shader.
        self.ocio_shader = None  # GPU OCIO shader

        # Enable or disable OpenColorIO processing.
        self.use_ocio = False

        # Store the current frame number.
        self.current_frame = None

        # Background colour used to clear the OpenGL framebuffer.
        self.background_color = (0.1, 0.1, 0.1, 1.0)

        # Store the current image width in pixels.
        self.image_width = 0

        # Store the current image height in pixels.
        self.image_height = 0

        # Store the number of image channels.
        self.channels = None

    def initializeGL(self):
        """Initialise OpenGL resources required by the 2D viewer.

        Creates the fullscreen quad, image texture, standard display shader, and optional OpenColorIO shader used during frame rendering.
        """

        # Set the default OpenGL framebuffer background colour.
        GL.glClearColor(*self.background_color)

        # Enable alpha blending for image and overlay rendering.
        GL.glEnable(GL.GL_BLEND)

        # Configure standard source-over alpha blending.
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

        # Create the screen-aligned rendering geometry.
        self.quad = FullscreenQuad()

        # Initialise the fullscreen quad OpenGL resources.
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
        """Update the OpenGL viewport after the widget is resized.

        Args:
            width: New viewport width.
            height: New viewport height.
        """

        # Update the OpenGL viewport to match the widget dimensions.
        GL.glViewport(0, 0, width, height)

    def paintGL(self):
        """Render the current movie or image-sequence frame.

        Uploads the current NumPy frame to the GPU, configures the active display shader, renders the image texture,
        and draws annotations and overlays on top of the image.

        Clear the colour and depth buffers.
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

        # Nothing can be rendered when no frame is available.
        if self.numpy_frame is None:
            return

        # Upload the current NumPy frame to the OpenGL texture.
        self.texture.upload(self.numpy_frame)

        # Calculate the image rectangle inside the viewer.
        self.update_display_rect()

        # Bind the image texture to texture unit zero.
        self.texture.bind(0)

        # Select the active shader based on the OCIO state.
        if self.use_ocio:
            self.active_shader = self.ocio_shader
        else:
            self.active_shader = self.shader

        # Activate the selected shader.
        self.active_shader.bind()

        # Get the device-pixel-ratio-aware viewport dimensions.
        dpr = self.devicePixelRatioF()

        viewport_width = int(self.width() * dpr)
        viewport_height = int(self.height() * dpr)

        # Pass the viewport size to the shader.
        self.active_shader.set_uniform_vec2(
            "viewportSize", float(viewport_width), float(viewport_height)
        )

        # Pass the image display rectangle to the shader.
        self.active_shader.set_uniform_vec4(
            "displayRect",
            (
                float(self.display_rect.left()),
                float(self.display_rect.top()),
                float(self.display_rect.width()),
                float(self.display_rect.height()),
            ),
        )

        # Tell the shader that the image is bound to texture unit zero.
        self.active_shader.set_uniform_int("imageTexture", 0)

        # Apply the active display parameter.
        if self.display_parameter:
            self.active_shader.set_uniform_float(
                self.display_parameter.control, self.display_parameter.value
            )

            # Apply the colour value when the parameter represents a colour.
            if self.display_parameter.is_color:
                self.active_shader.set_uniform_vec3(
                    self.display_parameter.color_control, *self.display_parameter.color
                )

        # Apply the active style parameter.
        if self.style_parameter:
            self.active_shader.set_uniform_float(
                self.style_parameter.control, self.style_parameter.value
            )

        # Apply the active image filter parameter.
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

        # Render the image texture on the fullscreen quad.
        self.quad.draw()

        # Release the active shader.
        self.active_shader.release()

        # Release the image texture.
        self.texture.release()

        # Draw annotations and other overlays on top of the image.
        self.draw_overlay()

        # Ensure all pending OpenGL commands are completed.
        GL.glFlush()

    def clear(self):
        """Clear the current image frame and viewer rendering state.

        The base viewer is cleared first, followed by the removal of the current image frame and frame number.
        """

        # Clear the common viewer state and OpenGL framebuffer.
        super().clear()

        # Remove the current image frame.
        self.numpy_frame = None

        # Reset the current frame number.
        self.current_frame = None

    def update_display_rect(self):
        """Calculate the image rectangle inside the viewer viewport.

        Maintains the original image aspect ratio while fitting the image within the available viewport area.
        """

        # Do not calculate a rectangle when no image is loaded.
        if self.numpy_frame is None:
            return

        # Get the device pixel ratio of the current display.
        dpr = self.devicePixelRatioF()

        # Calculate the viewport dimensions in device pixels.
        viewport_width = int(self.width() * dpr)
        viewport_height = int(self.height() * dpr)

        # Calculate the image and viewport aspect ratios.
        image_aspect = self.image_width / self.image_height

        viewport_aspect = viewport_width / viewport_height

        # Fit the image horizontally when it is wider than the viewport.
        if image_aspect > viewport_aspect:
            draw_width = viewport_width
            draw_height = int(draw_width / image_aspect)

        # Otherwise, fit the image vertically.
        else:
            draw_height = viewport_height
            draw_width = int(draw_height * image_aspect)

        # Centre the image inside the viewport.
        x = int((viewport_width - draw_width) / 2)
        y = int((viewport_height - draw_height) / 2)

        # Store the display rectangle in logical widget coordinates.
        self.display_rect = QtCore.QRect(
            int(x / dpr), int(y / dpr), int(draw_width / dpr), int(draw_height / dpr)
        )

    def set_ocio(self, processor):
        """Set the OpenColorIO processor used by the viewer.

        Args:
            processor: OpenColorIO processor used to build the display shader.
        """

        # Store the new OpenColorIO processor.
        self.ocio_processor = processor

        # Rebuild the OCIO shader using the new processor.
        self.build_ocio_shader()

        # Request a repaint using the updated colour-processing state.
        self.update()

    def build_ocio_shader(self):
        """Build the OpenColorIO display shader.

        Creates the OCIO shader from the current processor and updates the viewer's OCIO enabled state.
        """

        if self.ocio_shader is not None:
            self.ocio_shader.release()

        # Create the OpenColorIO shader.
        self.ocio_shader = OCIOShader(None)

        # Build the shader using the current OCIO processor.
        self.ocio_shader.build(self.ocio_processor)

        # Release temporary shader resources after building.
        self.ocio_shader.release()

        # Enable OCIO processing when the processor is enabled.
        self.use_ocio = self.ocio_processor.enabled

    def display_changed(self, parameter):
        """Update the active display parameter.

        Args:
            parameter: Display parameter passed to the active shader.
        """

        # Store the new display parameter.
        self.display_parameter = parameter

        # Request a repaint using the updated display setting.
        self.update()

    def style_changed(self, parameter):
        """Update the active image style parameter.

        Args:
            parameter: Style parameter passed to the active shader.
        """

        # Store the new style parameter.
        self.style_parameter = parameter

        # Request a repaint using the updated style setting.
        self.update()

    def filter_changed(self, parameter):
        """Update the active image filter parameter.

        Args:
            parameter: Filter parameter passed to the active shader.
        """

        # Store the new filter parameter.
        self.filter_parameter = parameter

        # Request a repaint using the updated filter setting.
        self.update()

    def set_frame(self, frame):
        """Set the current movie or image-sequence frame.

        Args:
            frame: Image frame stored as a NumPy array.
        """

        # Ignore frame updates while the viewer is disabled.
        if not self.is_enabled:
            return

        # Store the new image frame.
        self.numpy_frame = frame

        # Ignore empty frame values.
        if frame is None:
            return

        # Store the image dimensions and channel count.
        self.image_height, self.image_width, self.channels = frame.shape

        # Request a repaint for the new frame.
        self.update()

    def set_sketch_enabled(self, tool, enabled, font):
        """Configure the sketch annotation tool.

        Args:
            tool: Sketch tool to activate.
            enabled: Whether the sketch tool is enabled.
            font: Font used by text annotation tools.
        """

        # Delegate sketch configuration to the common viewer.
        super().set_sketch_enabled(tool, enabled, font)

    def render_current_frame(self):
        """Render the current frame into a Qt image.

        Converts the current NumPy frame into a ``QImage`` and draws the current frame annotations on top of the image.

        Returns:
            QtGui.QImage or None:
                Rendered image, or ``None`` when no frame is available.
        """

        # Return no image when no frame is currently loaded.
        if self.numpy_frame is None:
            return None

        # Ensure the frame memory is contiguous for QImage access.
        frame = numpy.ascontiguousarray(self.numpy_frame)

        # Read the image dimensions and channel count.
        height, width, channels = frame.shape

        # Create an RGBA image for four-channel input.
        if channels == 4:
            image = QtGui.QImage(
                frame.data, width, height, width * 4, QtGui.QImage.Format_RGBA8888
            ).copy()

        # Create an RGB image for three-channel input.
        else:
            image = QtGui.QImage(
                frame.data,
                width,
                height,
                width * 3,
                QtGui.QImage.Format_RGB888,
            ).copy()

        # Create a painter for drawing annotations on the image.
        painter = QtGui.QPainter(image)

        # Synchronise annotations with the current frame.
        self.sketch.set_frame(self.current_frame)

        # Define the full image drawing area.
        image_rect = QtCore.QRect(0, 0, width, height)

        # Draw annotations using normalized image coordinates.
        self.sketch.draw(
            painter,
            point_converter=lambda point: QtCore.QPointF(point[0] * width, point[1] * height),
            rect=image_rect,
        )

        # Finish the painting operation.
        painter.end()

        return image


if __name__ == "__main__":
    pass
