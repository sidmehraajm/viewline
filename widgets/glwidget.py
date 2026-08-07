"""
Copyright (c) 2026, Motion-Craft Technology All rights reserved.

Author:
    Subin. Gopi (subing85@gmail.com).

Module:
    ./widgets/glwidget.py

Description:
    Common OpenGL viewer base class.

Responsibilities:
    - Provide the common QOpenGLWidget foundation for 2D and 3D viewers.
    - Manage shared viewport state and OpenGL lifecycle handling.
    - Provide common frame, overlay, sketch, and interaction functionality.
    - Define the interface required by specialized viewer implementations.
    - Coordinate common viewer operations without depending on 2D- or 3D-specific
      rendering implementations.

Features:
    - Shared OpenGL widget initialization.
    - Common viewport resize handling.
    - Common frame and playback state management.
    - Shared mouse and keyboard event handling.
    - Sketch and annotation overlay support.
    - Current-frame rendering and capture interface.
    - Viewer clearing and resource reset functionality.
    - Common coordinate conversion interface.
    - Extensible rendering hooks for specialized viewers.

Architecture:
    GLViewer
        │
        ├── GLViewer2d
        │   └── 2D image, video, and image-sequence rendering
        │
        └── GLViewer3d
            └── USD, Hydra, and 3D scene rendering

    The base class owns functionality that is common to both 2D and 3D viewers.
    Specialized rendering behaviour is implemented by subclasses.

    The base class should not contain implementation details that are specific
    to image-based rendering or USD/Hydra rendering. Instead, subclasses
    implement the rendering-specific operations through overridable methods.

Nodes:
    GLViewer
        ├── OpenGL Lifecycle
        │   ├── initializeGL()
        │   ├── resizeGL()
        │   └── paintGL()
        │
        ├── Viewer State
        │   ├── Current Frame
        │   ├── Playback State
        │   └── Viewport State
        │
        ├── User Interaction
        │   ├── Mouse Events
        │   ├── Wheel Events
        │   └── Keyboard Events
        │
        ├── Overlay System
        │   └── Sketch / Annotation Rendering
        │
        └── Specialized Rendering
            ├── GLViewer2d
            │   └── Image / Video Rendering
            │
            └── GLViewer3d
                └── USD / Hydra Rendering
"""

from __future__ import absolute_import

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
    """Common OpenGL viewer base class for 2D and 3D viewers.

    Responsibilities:
        - Provide shared viewer functionality for specialized OpenGL viewers.
        - Manage common viewport and playback state.
        - Define the common rendering and frame-update interface.
        - Handle shared user interaction and overlay functionality.
        - Provide a consistent viewer API for both 2D and 3D implementations.

    Features:
        - Common QOpenGLWidget lifecycle management.
        - Shared frame and playback handling.
        - Common viewport resizing.
        - Shared mouse, wheel, and keyboard interaction.
        - Sketch and annotation overlay support.
        - Viewer clearing and reset functionality.
        - Extensible rendering hooks for subclasses.

    Architecture:
        GLViewer is an abstract/common foundation for specialized viewers.

        GLViewer2d extends this class to provide image, video, and image sequence viewing functionality.

        GLViewer3d extends this class to provide USD scene rendering through Hydra and UsdImagingGL.

        Rendering-specific implementation should remain in the subclasses.
        The base class should only contain behaviour that is meaningful forboth 2D and 3D viewers.

    Subclasses:
        GLViewer2d:
            Implements 2D image and video rendering.

        GLViewer3d:
            Implements 3D USD scene rendering and Hydra integration.

    """

    # Signal emitted when render finished (to save the image)
    render_finished = QtCore.Signal(str)

    def __init__(self, parent=None):
        """Initialize the common OpenGL viewer state.

        Args:
            parent: Optional parent Qt widget.

        The base class initializes only state shared by both 2D and 3D viewers.
        Rendering-specific resources are created by the subclasses after the OpenGL context becomes available.
        """

        super().__init__(parent)

        # Expand inside layouts.

        # Configure expanding size policy
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding
        )
        self.setSizePolicy(sizePolicy)

        # Stores the current video/image frame as a NumPy array.
        self.numpy_frame = None

        # Stores the current frame number displayed by the viewer.
        self.current_frame = None

        # Indicates whether the viewer is currently enabled for rendering and interaction.
        self.is_enabled = False

        # Determines whether the content should automatically fit within the viewport.
        self.fit_mode = True

        # Stores the current viewport zoom factor.
        self.zoom = 1.0

        # Stores additional parameters controlling the content display.
        self.display_parameter = None

        # Stores style-related parameters used to customize the viewer appearance.
        self.style_parameter = None

        # Stores filtering parameters applied to the displayed content.
        self.filter_parameter = None

        # Stores the normalized pan offset used to translate the displayed content.
        self.pan = QtCore.QPointF(0.0, 0.0)

        # Stores the rectangle occupied by the displayed content within the viewport.
        self.display_rect = QtCore.QRect()

        # Configure the requested multisample anti-aliasing level for the OpenGL surface.
        self.set_samples(constants.VIEWER_SAMPLES_RATE)

        # Provides the annotation and sketch system used to draw over the displayed content.
        self.sketch = Sketch()

    def set_samples(self, samples=8):
        """Configure multisample anti-aliasing for the OpenGL surface.

        Sets the number of multisample samples used by the OpenGL surface format.
        Multisampling helps reduce jagged edges when rendering geometry and other graphical elements.

        This method should be called before the OpenGL context is created, typically during widget initialization.

        Args:
            samples: Number of multisampling samples to request. A value of
                ``0`` disables multisampling. Common values include ``2``,
                ``4``, and ``8``.

        Note:
            The requested sample count is a hint to the graphics system.
            The actual number of samples used may depend on the graphics hardware and platform capabilities.
        """

        # Create a surface format configuration for the OpenGL widget.
        surface = QtGui.QSurfaceFormat()

        # Request the specified multisample anti-aliasing level.
        surface.setSamples(samples)

        # Apply the configured surface format to this OpenGL widget.
        self.setFormat(surface)

    def initializeGL(self):
        """Initialize the OpenGL rendering environment.

        Creates the resources required for rendering after the OpenGL context has been created and made current.
        """

        pass

    def resizeGL(self, width, height):
        """Handle changes to the OpenGL viewport size.

        Updates the viewport-dependent rendering state when the widget size changes.
        Subclasses should use this method to update their renderer, projection matrix, render target, or other size-dependent resources.

        Args:
            width: New viewport width in device-independent pixels.
            height: New viewport height in device-independent pixels.

        Note:
            ``QOpenGLWidget`` may temporarily report a zero width or height during initialization or layout changes.
            Implementations should protect against invalid dimensions before calculating aspect ratios or allocating size-dependent resources.
        """

        pass

    def paintGL(self):
        """Render the current viewer contents.

        Called automatically by ``QOpenGLWidget`` whenever the widget requires repainting.
        The implementation is responsible for clearing the current framebuffer and rendering the active viewer content.

        The base implementation provides the common rendering entry point.
        Specialized viewers should override this method to render their respective content:

        * ``GLViewer2d`` renders images, videos, or image sequences.
        * ``GLViewer3d`` renders USD scenes through Hydra and
            ``UsdImagingGL.Engine``.

        The method should not perform expensive rendering work outside the current OpenGL context.
        """

        pass

    def clear(self):
        """Clear the viewer contents and reset the OpenGL framebuffer.

        Removes all active sketch annotations and requests the viewer to repaint the cleared state.
        """

        # Skip GL operations until the widget has a valid OpenGL context
        # (e.g. clear() called during startup before the viewport is shown).
        if not self.isValid():
            self.sketch.clear_all()
            return

        # Make the OpenGL context current before issuing OpenGL commands.
        self.makeCurrent()

        try:
            # Clear the colour and depth buffers using the configured background colour.
            GL.glClearColor(*self.background_color)
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

            # Ensure all pending OpenGL commands are completed.
            GL.glFlush()

        finally:
            # Release the OpenGL context after framebuffer operations are complete.
            self.doneCurrent()

        # Remove all annotations from the sketch system.
        self.sketch.clear_all()

        # Request a repaint so the cleared state is displayed.
        self.update()

    def mousePressEvent(self, event):
        """Handle mouse press for viewport navigation or sketching.

        Alt-click enables viewport navigation. Otherwise, the mouse event is forwarded to the sketch system when sketching is enabled.
        """

        # Ensure the viewer receives keyboard focus for navigation shortcuts.
        self.setFocus()

        # Alt enables viewport navigation mode.
        modifiers = event.modifiers()

        if modifiers & QtCore.Qt.KeyboardModifier.AltModifier:
            # Store the initial mouse position for drag-based navigation.
            self.last_mouse_position = event.position()

        # Without Alt, handle the event as a sketching operation.
        else:
            # Ignore the event when sketching is disabled.
            if not self.sketch.enabled:
                return

            # Convert the widget position to the content coordinate system.
            point = self.widget_to_image_point(event.position().toPoint())

            # Forward the mouse press to the sketch system.
            self.sketch.mousePressEvent(point)

            # Request a repaint to display the updated sketch.
            self.update()

        # Mark the event as handled.
        event.accept()

    def mouseMoveEvent(self, event):
        """Handle mouse movement for viewport navigation or sketching.

        Alt-drag is used for camera navigation. Without Alt, mouse movement is forwarded to the sketch system while the left mouse button is pressed.
        """

        # Alt enables viewport navigation mode.
        modifiers = event.modifiers()

        # Handle viewport navigation when Alt is pressed.
        if modifiers & QtCore.Qt.KeyboardModifier.AltModifier:

            # A navigation drag cannot be processed without a previous position.
            if self.last_mouse_position is None:
                return

            current = event.position()

            # Calculate the mouse movement since the previous event.
            delta = current - self.last_mouse_position
            dx = delta.x()
            dy = delta.y()

            buttons = event.buttons()

            # Alt + Left Mouse Button: orbit the camera around the target.
            if buttons & QtCore.Qt.MouseButton.LeftButton:
                # Alt + Left drag → Orbit
                self.camera.orbit(dx, dy)
                self.update_view()

            # Alt + Middle Mouse Button: pan the camera view.
            elif buttons & QtCore.Qt.MouseButton.MiddleButton:
                self.camera.pan(dx, dy)
                self.update_view()

            # Store the current position for the next mouse-move event.
            self.last_mouse_position = current

        # Handle sketch interaction when Alt is not pressed.
        else:

            # Ignore movement when sketching is disabled.
            if not self.sketch.enabled:
                return

            # Sketch strokes are created only while the left button is held.
            if not (event.buttons() & QtCore.Qt.MouseButton.LeftButton):
                return

            # Convert the widget position to the content coordinate system.
            point = self.widget_to_image_point(event.position().toPoint())

            # Forward the mouse movement to the sketch system.
            self.sketch.mouseMoveEvent(point)

            # Request a repaint to display the updated stroke.
            self.update()

        # Mark the event as handled.
        event.accept()

    def mouseReleaseEvent(self, event):
        """Handle mouse release for viewport navigation or sketching.

        Ends the current camera navigation gesture or forwards the release event to the sketch system when sketching is enabled.
        """

        # Alt enables viewport navigation mode.
        modifiers = event.modifiers()

        # End the current viewport navigation gesture.
        if modifiers & QtCore.Qt.KeyboardModifier.AltModifier:
            self.last_mouse_position = None

        # Complete the current sketch stroke.
        else:
            if self.sketch.enabled:

                # Convert the widget position to the content coordinate system.
                point = self.widget_to_image_point(event.position().toPoint())

                # Forward the mouse release to the sketch system.
                self.sketch.mouseReleaseEvent(point)

                # Request a repaint to display the completed stroke.
                self.update()

        # Mark the event as handled.
        event.accept()

    def wheelEvent(self, event):
        """Handle mouse-wheel input for camera zooming.

        The wheel delta is forwarded to the camera, which updates the current zoom level before the viewport is redrawn.
        """

        # Read the vertical mouse-wheel movement.
        delta = event.angleDelta().y()

        # Update the camera zoom based on the wheel direction.
        self.camera.zoom(delta)

        # Apply the updated camera state and request a repaint.
        self.update_view()

        # Mark the event as handled.
        event.accept()

    def keyPressEvent(self, event):
        """Handle keyboard input for viewport actions.

        Pressing ``F`` frames the complete scene within the viewport.
        Other keyboard events are forwarded to the base Qt widget implementation.
        """

        # Frame the complete scene when the F key is pressed.
        if event.key() == QtCore.Qt.Key.Key_F:
            self.frame_all()

            # Apply the updated camera state and redraw the viewport.
            self.update_view()

            # Mark the event as handled.
            event.accept()
            return

        # Forward unhandled key events to the parent implementation.
        super().keyPressEvent(event)

    def set_current_frame(self, frame):
        """Update the current frame displayed by the viewer.

        Args:
            frame: Frame number to display.
        """

        # Store the current frame for the viewer.
        self.current_frame = frame

        # Update the sketch system to match the current frame.
        self.sketch.set_frame(frame)

    def fit_to_window(self):
        """Fit the displayed content within the viewer viewport.

        Resets the zoom and pan values before enabling automatic fit mode.
        """

        # Enable automatic content fitting.
        self.fit_mode = True

        # Reset the zoom to the default scale.
        self.zoom = 1.0

        # Reset the content position to the viewport centre.
        self.pan = QtCore.QPointF()

        # Request a repaint using the updated view settings.
        self.update()

    def set_actual_size(self):
        """Display the content at its original 100% size.

        Disables automatic fit mode and resets the view transform to its default zoom and pan position.
        """

        # Disable automatic fitting.
        self.fit_mode = False

        # Display the content at its original size.
        self.zoom = 1.0

        # Reset the content position to the viewport centre.
        self.pan = QtCore.QPointF()

        # Request a repaint using the updated view settings.
        self.update()

    def set_zoom(self, zoom):
        """Set the viewer zoom factor.

        Args:
            zoom: Zoom factor to apply. The value is clamped to the supported
                viewer range.
        """

        # Manual zoom disables automatic fit mode.
        self.fit_mode = False

        # Clamp the zoom factor to prevent invalid or excessive scaling.
        self.zoom = max(0.05, min(zoom, 32.0))

        # Request a repaint using the new zoom factor.
        self.update()

    def zoom_in(self):
        """Increase the current viewer zoom level."""

        # Increase the zoom by 25%.
        self.set_zoom(self.zoom * 1.25)

    def zoom_out(self):
        """Decrease the current viewer zoom level."""

        # Decrease the zoom by 20%.
        self.set_zoom(self.zoom / 1.25)

    def set_pan(self, x, y):
        """ "Set the content pan offset.

        Args:
            x (float):
                Horizontal offset.

            y (float):
                Vertical offset.
        """

        # Store the new content position.
        self.pan = QtCore.QPointF(x, y)

        # Request a repaint using the updated pan position.
        self.update()

    def reset_view(self):
        """Reset the viewer to its default view state.

        Restores the default zoom, pan position, and automatic fit mode.
        """

        # Reset the zoom to the default scale.
        self.zoom = 1.0

        # Reset the content position to the viewport centre.
        self.pan = QtCore.QPointF()

        # Re-enable automatic content fitting.
        self.fit_mode = True

        # Request a repaint using the default view settings.
        self.update()

    def undo_strokes(self):
        """Undo the most recent annotation on the current frame.

        Removes the latest stroke from the sketch history and requests a repaint to display the updated annotation state.
        """

        # Remove the most recent annotation stroke.
        self.sketch.undo()

        # Redraw the viewer without the removed stroke.
        self.update()

    def clear_strokes(self):
        """Clear all annotations from the current sketch.

        Removes all stored annotation strokes and requests a repaint to display the cleared annotation state.
        """

        # Remove all annotation strokes from the sketch system.
        self.sketch.clear_all()

        # Redraw the viewer without any annotations.
        self.update()

    def draw_overlay(self):
        """Draw the viewer overlays and sketch annotations.

        The overlay is rendered on top of the current viewer content using the active display rectangle and coordinate conversion system.

        This method handles:
            - Text overlays
            - Image overlays
            - Overlay antialiasing
            - Overlay positioning
        """

        # Create a painter for drawing directly on the viewer widget.
        painter = QtGui.QPainter(self)

        # Draw all sketch annotations using image-to-widget coordinates.
        self.sketch.draw(
            painter, point_converter=self.image_to_widget_point, rect=self.display_rect
        )

        # Release the painter and finish the overlay drawing operation.
        painter.end()

    def set_overlay_options(self, watermarks):
        """Set the available overlay and watermark configuration.

        Args:
            watermarks: Overlay configuration data passed to the sketch system.
        """

        # Update the active overlay configuration.
        self.sketch.set_overlays(watermarks)

        # Redraw the viewer with the updated overlays.
        self.update()

    def set_overlay_option(self, checked, key, position, context):
        """Update the state of an individual overlay option.

        Args:
            checked: Whether the overlay is enabled.
            key: Identifier of the overlay option.
            position: Position where the overlay should be displayed.
            context: Additional context associated with the overlay.
        """

        # Update the selected overlay configuration.
        self.sketch.set_overlay(checked, key, position, context)

        # Redraw the viewer with the updated overlay state.
        self.update()

    def set_sketch_enabled(self, tool, enabled, font):
        """Enable or disable the sketch annotation tool.

        Configures the selected drawing tool and updates its display settings using the dimensions of the currently loaded image.

        Args:
            tool: Sketch tool to activate.
            enabled: Whether the sketch tool should be enabled.
            font: Font used for text-based annotation tools.
        """

        # Do not configure sketching when no frame is currently available.
        if not self.current_frame:
            return

        # Set the active sketch tool.
        self.sketch.set_tool(tool)

        # Enable or disable sketch interaction.
        self.sketch.set_enabled(enabled)

        # Provide the current image dimensions for coordinate conversion.
        self.sketch.set_image_size(self.image_width, self.image_height)

        # Configure the default eraser radius.
        self.sketch.set_eraser_radius(10)

        # Configure the font used by text annotations.
        self.sketch.set_txt_font(font)

    def widget_to_image_point(self, point):
        """Convert widget coordinates to normalized image coordinates.

        The returned coordinates are normalized to the range ``0.0`` to ``1.0`` relative to the current display rectangle.

        Args:
            point: Widget position to convert.

        Returns:
            tuple[float, float]:
                Normalized image coordinates as ``(x, y)``.
        """

        # Get the rectangle occupied by the displayed image.
        rect = self.display_rect

        # Convert the widget position into normalized image coordinates.
        x = (point.x() - rect.left()) / float(rect.width())
        y = (point.y() - rect.top()) / float(rect.height())

        # Clamp the coordinates to the valid normalized image range.
        x = max(0.0, min(1.0, x))
        y = max(0.0, min(1.0, y))

        return (x, y)

    def image_to_widget_point(self, point):
        """Convert normalized image coordinates to widget coordinates.

        Args:
            point: Normalized image coordinates in the range ``0.0`` to ``1.0``.

        Returns:
            QtCore.QPointF:
                Corresponding position in widget coordinates.
        """

        # Get the rectangle occupied by the displayed image.
        rect = self.display_rect

        # Convert normalized image coordinates to widget coordinates.
        x = rect.left() + (point[0] * rect.width())
        y = rect.top() + (point[1] * rect.height())

        return QtCore.QPointF(x, y)

    def save_frame(self, filepath, post_process=False):
        """Render and save the current viewer frame.

        Args:
            filepath: Destination path for the rendered frame.
            post_process: Whether to emit ``render_finished`` after rendering.
        """

        # Render the current frame into an image.
        image = self.render_current_frame()

        if image:
            # Ensure the destination directory exists.
            utils.makedirs(filepath)

            # Save the rendered image to disk.
            image.save(filepath)
            LOGGER.info(f"Succeed, render to {filepath}")

            # Notify listeners when post-processing is requested.
            if post_process:
                self.render_finished.emit(filepath)
        else:
            # Report the rendering failure.
            LOGGER.error(f"Failure render to {filepath}")

            # Notify listeners that rendering failed.
            if post_process:
                self.render_finished.emit(None)


if __name__ == "__main__":
    pass
