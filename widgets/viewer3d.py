"""
Copyright (c) 2026, Motion-Craft Technology All rights reserved.

Author:
    Subin. Gopi (subing85@gmail.com).

Module:
    ./widgets/viewer3d.py

Description:
    OpenGL-based USD viewer for 3D scene playback.

Responsibilities:
    - Render USD stages through Hydra.
    - Manage the Hydra rendering engine and render parameters.
    - Control the 3D camera and viewport navigation.
    - Configure head-light illumination for scene rendering.
    - Display a viewport grid with axis indicators.
    - Support USD animation frame updates.
    - Render sketch annotations and overlays on top of the 3D view.

Features:
    - Hydra-based USD rendering.
    - Smooth shaded geometry rendering.
    - Y-up and Z-up USD stage support.
    - Camera orbit, pan, zoom, and framing.
    - Camera-based head lighting.
    - Configurable viewport grid.
    - X-axis and up-axis colour indicators.
    - USD animation playback.
    - Sketch and annotation overlays.
    - Framebuffer-based frame rendering.

Architecture:
    - ``Viewer3dLayout``:
        Provides the 3D viewer layout and menu bar.

    - ``GLViewer3d``:
        Provides the OpenGL viewport and Hydra rendering integration.

    - ``GLViewer``:
        Provides common viewer functionality such as annotations,
        overlays, interaction, and shared view state.

    - ``UsdImagingGL.Engine``:
        Renders the USD stage through the Hydra imaging framework.

    - ``ViewCamera``:
        Manages camera position, orientation, projection, and framing.

Nodes:
    Viewer3dLayout
        └── Viewer3dMenubar
        └── GLViewer3d
            ├── GLViewer
            ├── UsdImagingGL.Engine
            ├── ViewCamera
            ├── Glf.SimpleLight
            ├── Glf.SimpleMaterial
            └── USD Viewport Grid
"""

from __future__ import absolute_import

import math

from PySide6 import QtGui
from PySide6 import QtCore

from OpenGL import GL

from pxr import Gf
from pxr import Glf
from pxr import Usd
from pxr import UsdGeom
from pxr import UsdImagingGL

from viewline import logger

from viewline.widgets.glwidget import GLViewer

from viewline.widgets.menus import Viewer3dMenubar

from viewline.widgets.layouts import VerticalLayout

LOGGER = logger.getLogger(__name__)


class Viewer3dLayout(VerticalLayout):
    """Layout containing the 3D viewer menu bar and viewport.

    The layout combines the 3D viewer menu bar with the
    :class:`GLViewer3d` widget used to display USD scenes.

    Attributes:
        viewer3dMenubar: Menu bar containing 3D viewer controls.
        viewer3d: OpenGL-based USD viewer.
    """

    def __init__(self, parent, *args, **kwargs):
        """Create and initialise the 3D viewer layout.

        Args:
            parent: Parent Qt widget.
            *args: Additional layout arguments.
            **kwargs: Additional layout keyword arguments.
        """

        # Initialise the base vertical layout.
        super(Viewer3dLayout, self).__init__(parent, *args, **kwargs)

        # Create the 3D viewer menu bar.
        self.viewer3dMenubar = Viewer3dMenubar(None)

        # Keep the menu bar hidden until explicitly enabled.
        self.viewer3dMenubar.setVisible(False)

        # Add the menu bar to the layout.
        self.addWidget(self.viewer3dMenubar)

        # Create the OpenGL-based USD viewer.
        self.viewer3d = GLViewer3d(None)

        # Add the viewer below the menu bar.
        self.addWidget(self.viewer3d)

        self.viewer3dMenubar.shading_changed.connect(self.viewer3d.set_shading_mode)
        self.viewer3dMenubar.complexity_changed.connect(self.viewer3d.set_complexity)
        self.viewer3dMenubar.purposes_changed.connect(self.viewer3d.set_purposes)
        self.viewer3dMenubar.materials_enable.connect(self.viewer3d.set_materials_enabled)
        self.viewer3dMenubar.grid_enable.connect(self.viewer3d.set_grid_enabled)

        self.viewer3d.stage_loaded.connect(self.viewer3dMenubar.set_cameras)

        self.viewer3dMenubar.camera_changed.connect(self.viewer3d.set_current_camera)


class GLViewer3d(GLViewer):
    """OpenGL viewport for rendering USD scenes through Hydra.

    The viewer manages the USD stage, Hydra rendering engine, camera, lighting state, viewport grid, and USD animation frame updates.

    Attributes:
        stage: Currently loaded USD stage.
        engine: Hydra imaging engine used to render the USD stage.
        last_mouse_position: Previous mouse position used for navigation.
        render_params: Hydra rendering configuration.
        head_light: Camera-mounted light used for viewport illumination.
        lights: Collection of active Hydra lights.
        material: Material state used by the Hydra renderer.
        scene_ambient: Ambient scene lighting value.
        background_color: OpenGL viewport background colour.
        camera: Camera used to control the USD viewport.
    """

    stage_loaded = QtCore.Signal(list)

    def __init__(self, parent=None):
        """Create and initialise the USD OpenGL viewer.

        Args:
            parent: Parent Qt widget.
        """

        # Initialise the common viewer functionality.
        super().__init__(parent)

        # Store the currently loaded USD stage.
        self.stage = None

        # Store the Hydra imaging engine.
        self.engine = None

        # Store the previous mouse position during navigation.
        self.last_mouse_position = None

        # Store the camera-mounted viewport light.
        self.headLight = None

        # Store the Hydra render configuration.
        self.render_params = None

        # Store the camera-mounted viewport light.
        self.head_light = None

        # Store the active lighting collection.
        self.lights = list()

        # Store the material state used by Hydra lighting.
        self.material = None

        # Store the ambient scene lighting value.
        self.scene_ambient = None

        # Store the OpenGL viewport background colour.
        self.background_color = (0.2, 0.2, 0.2, 1.0)

        self.guide_stage = None

        # Create the viewport camera.
        self.camera = ViewCamera()

        self.scene_camera = None
        self.use_scene_camera = False

    def initializeGL(self):
        """Initialise the OpenGL and Hydra rendering environment.

        Creates the Hydra engine, render parameters, and lighting state after the OpenGL context has been created.
        """

        # Set the default OpenGL framebuffer background colour.
        GL.glClearColor(*self.background_color)

        # Create the Hydra imaging engine.
        self.engine = UsdImagingGL.Engine()

        logger.nextline()

        LOGGER.info(f"Hydra engine created: {self.engine}")

        # Configure the Hydra render parameters.
        self.create_render_param()

        # Configure the viewport lighting state.
        self.create_lighting_state()

        # Log the active Hydra renderer.
        LOGGER.info(f"Renderer: {self.engine.GetCurrentRendererId()}")

        # Log the active Hydra rendering backend.
        LOGGER.info(f"Backend: {self.engine.GetRendererHgiDisplayName()}")

    def resizeGL(self, width, height):
        """Update the Hydra viewport after the widget is resized.

        Args:
            width: New viewport width.
            height: New viewport height.
        """

        # Ignore resize events before Hydra has been initialised.
        if self.engine is None:
            return

        # Update the Hydra render buffer dimensions.
        self.engine.SetRenderBufferSize(Gf.Vec2i(width, height))

        # Update the Hydra render viewport.
        self.engine.SetRenderViewport(Gf.Vec4d(0, 0, width, height))

        # Apply the updated camera and lighting state.
        self.update_renderer_state()

        # Request a repaint after the resize.
        self.update()

    def paintGL(self):
        """Render the current USD stage through Hydra.

        Clears the OpenGL framebuffer, updates the current render frame, renders the USD stage, and draws viewer overlays.
        """

        # Clear the colour and depth buffers.
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        # Do not render without a loaded USD stage.
        if self.stage is None:
            return

        # Do not render before Hydra has been initialised.
        if self.engine is None:
            return

        # Update the camera for the current animation frame.
        self.update_camera()

        # Update the viewport display rectangle.
        self.update_display_rect()

        # Apply the current animation frame to the Hydra render parameters.
        self.render_params.frame = self.current_frame

        # Render the USD stage through Hydra.
        # self.engine.Render(self.stage.GetPseudoRoot(), self.render_params)

        root = self.stage.GetDefaultPrim()
        self.engine.Render(root, self.render_params)

        # Draw annotations and other viewer overlays.
        self.draw_overlay()

        # Ensure all pending OpenGL commands are completed.
        GL.glFlush()

    def clear(self):
        """Clear the current USD stage and reset the viewer contents."""

        # Clear common viewer state and the OpenGL framebuffer.
        # super().clear()

        self.makeCurrent()

        GL.glClearColor(*self.background_color)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        # Ensure all pending OpenGL commands are completed.
        GL.glFlush()

        self.stage = None
        self.current_frame = None
        self.use_scene_camera = False
        self.camera = ViewCamera()

        self.engine = UsdImagingGL.Engine()
        self.engine.SetRenderBufferSize(Gf.Vec2i(self.width(), self.height()))
        self.engine.SetRenderViewport(Gf.Vec4d(0, 0, self.width(), self.height()))

        self.doneCurrent()

        self.update()

    def update_display_rect(self):
        """Update the display rectangle to cover the entire viewport."""

        # Get the current device pixel ratio.
        dpr = self.devicePixelRatioF()

        # Calculate the viewport dimensions in device pixels.
        viewport_width = int(self.width() * dpr)
        viewport_height = int(self.height() * dpr)

        # Store the viewport rectangle in logical widget coordinates.
        self.display_rect = QtCore.QRect(
            0,
            0,
            int(viewport_width / dpr),
            int(viewport_height / dpr),
        )

    def set_stage(self, stage):
        """Set the USD stage displayed by the viewer.

        The stage up-axis is read and applied to the camera before the viewport grid and initial camera framing are configured.

        Args:
            stage: USD stage to display.
        """

        # Ignore empty stage values.
        if stage is None:
            return

        # self.engine = UsdImagingGL.Engine()

        self.engine.ClearSelected()

        # Store the new USD stage.
        self.stage = stage
        self.stage.Reload()

        # Read the stage up-axis.
        up_axis = UsdGeom.GetStageUpAxis(self.stage)

        # Configure the camera for the stage coordinate system.
        self.camera.set_up_axis(up_axis)

        # Frame the loaded scene in the viewport.
        self.frame_all()

        camera_prims = self.get_camera_prims()

        self.stage_loaded.emit(camera_prims)

    def get_camera_prims(self):
        result = list()

        for prim in self.stage.TraverseAll():
            if not prim.IsA(UsdGeom.Camera):
                continue
            result.append((prim.GetName(), prim.GetPath().pathString, False))

        return result

    def create_render_param(self):
        """Create and configure Hydra rendering parameters.

        Configures shaded rendering, scene visibility, complexity, culling, and other viewport display options.
        """

        # Create the Hydra render parameter object.
        self.render_params = UsdImagingGL.RenderParams()

        # Use smooth shaded rendering.
        self.render_params.drawMode = UsdImagingGL.DrawMode.DRAW_SHADED_SMOOTH

        # Enable renderer lighting.
        self.render_params.enableLighting = True

        # Disable USD scene material evaluation.
        self.render_params.enableSceneMaterials = False

        # Display proxy geometry.
        self.render_params.showProxy = False

        # Display guide geometry.
        self.render_params.showGuides = True

        # Hide render-purpose geometry.
        self.render_params.showRender = False

        # Disable geometry culling.
        self.render_params.cullStyle = UsdImagingGL.CullStyle.CULL_STYLE_NOTHING

        # Set the Hydra scene complexity.
        self.render_params.complexity = 1.0  # low

        # Disable automatic gamma correction.
        self.render_params.gammaCorrectColors = False

    def set_current_camera(self, camera):
        """Use a camera prim from the USD stage."""

        if camera == "/default":
            self.use_scene_camera = False
        else:
            prim = self.stage.GetPrimAtPath(camera)

            if not prim or not prim.IsA(UsdGeom.Camera):
                return False

            self.scene_camera = UsdGeom.Camera(prim)
            self.use_scene_camera = True

            self.update_view()

        return True

    def update_camera(self):
        """Update the Hydra camera from the current viewport camera."""

        # Ignore camera updates before Hydra initialisation.
        if self.engine is None:
            return

        # Protect against invalid viewport dimensions.
        width = max(self.width(), 1)
        height = max(self.height(), 1)

        # Calculate the current viewport aspect ratio.
        aspect = width / height

        if self.use_scene_camera:
            view_matrix, projection_matrix = self.get_scene_camera_matrices(aspect)

        else:
            # Generate the current camera view matrix.
            view_matrix = self.camera.get_view_matrix()

            # Generate the current projection matrix.
            projection_matrix = self.create_projection_matrix(aspect)

        # Apply the camera state to Hydra.
        self.engine.SetCameraState(view_matrix, projection_matrix)

    def get_scene_camera_matrices(self, aspect):
        if self.scene_camera is None:
            raise RuntimeError("No scene camera assigned.")

        # Evaluate the camera at the current frame.
        time = Usd.TimeCode(self.current_frame)

        # Returns a fully evaluated Gf.Camera.
        gf_camera = self.scene_camera.GetCamera(time)

        # Camera frustum.
        frustum = gf_camera.frustum

        # View matrix.
        view_matrix = frustum.ComputeViewMatrix()

        # Projection matrix.
        # projection_matrix = frustum.ComputeProjectionMatrix()
        projection_matrix = Gf.Matrix4d(frustum.ComputeProjectionMatrix())

        return view_matrix, projection_matrix

    def create_lighting_state(self):
        """Create the viewport head light and material state.

        Configures a camera-mounted light, material properties, and ambient scene lighting for consistent viewport illumination.
        """

        # Create the camera-mounted viewport light.
        self.head_light = Glf.SimpleLight()

        # Configure the ambient component of the head light.
        self.head_light.ambient = Gf.Vec4f(0.2, 0.2, 0.2, 1.0)

        # Configure the diffuse component of the head light.
        self.head_light.diffuse = Gf.Vec4f(1.0, 1.0, 1.0, 1.0)

        # Configure a low-intensity specular component.
        self.head_light.specular = Gf.Vec4f(0.01, 0.01, 0.01, 1.0)

        # Create the material state used by the renderer.
        self.material = Glf.SimpleMaterial()

        # Configure the material ambient response.
        self.material.ambient = Gf.Vec4f(0.2, 0.2, 0.2, 1.0)

        # Configure the material diffuse response.
        self.material.diffuse = Gf.Vec4f(0.8, 0.8, 0.8, 1.0)

        # Configure the material specular response.
        self.material.specular = Gf.Vec4f(0.01, 0.01, 0.01, 1.0)

        # Configure the material shininess.
        self.material.shininess = 32.0

        # Configure the ambient scene illumination.
        self.scene_ambient = Gf.Vec4f(0.2, 0.2, 0.2, 1.0)

        # Store the head light in the active lighting collection.
        self.lights = [self.head_light]

    def update_head_light(self):
        """Update the viewport head light from the camera position."""

        # Ignore lighting updates before Hydra initialisation.
        if self.engine is None:
            return

        # Do not update lighting without active lights.
        if not self.lights:
            return

        # Get the current camera position.
        camera_position = self.camera.get_position()

        # Move the head light to the camera position.
        self.head_light.position = Gf.Vec4f(
            camera_position[0], camera_position[1], camera_position[2], 0
        )

        # Apply the updated lighting state to Hydra.
        self.engine.SetLightingState(self.lights, self.material, self.scene_ambient)

    def update_renderer_state(self):
        """Update the Hydra camera and lighting state."""

        # Update the Hydra camera.
        self.update_camera()

        # Update the camera-mounted head light.
        self.update_head_light()

    def update_view(self):
        """Update the renderer state and request a viewport repaint."""

        # Apply the current camera and lighting state.
        self.update_renderer_state()

        # Request a new viewport render.
        self.update()

    def create_projection_matrix(self, aspect):
        """Create a perspective projection matrix.

        Args:
            aspect: Viewport width-to-height aspect ratio.

        Returns:
            Gf.Matrix4d:
                Perspective projection matrix.
        """

        # Convert the camera field of view to radians.
        fov = math.radians(self.camera.fov)

        # Calculate the perspective scale factor.
        f = 1.0 / math.tan(fov * 0.5)

        # Read the camera clipping planes.
        near = self.camera.near_clip
        far = self.camera.far_clip

        # Build and return the perspective projection matrix.
        return Gf.Matrix4d(
            f / aspect,
            0.0,
            0.0,
            0.0,
            0.0,
            f,
            0.0,
            0.0,
            0.0,
            0.0,
            (far + near) / (near - far),
            -1.0,
            0.0,
            0.0,
            (2.0 * far * near) / (near - far),
            0.0,
        )

    def frame_all(self):
        """Frame the complete USD stage inside the viewport.

        Calculates the world-space bounding box of the stage and updates
        the camera so the complete scene fits within the current viewport.
        """

        # Do not frame an empty stage.
        if self.stage is None:
            return

        # Create a bounding-box cache for the current USD stage.
        bbox_cache = UsdGeom.BBoxCache(
            self.stage.GetTimeCodesPerSecond(), [UsdGeom.Tokens.default_]
        )

        # Calculate the world-space bounds of the stage.
        bbox = bbox_cache.ComputeWorldBound(self.stage.GetPseudoRoot())

        # Convert the bounds to an aligned range.
        bounds = bbox.ComputeAlignedRange()

        # Calculate the current viewport aspect ratio.
        aspect = max(self.width(), 1) / max(self.height(), 1)

        # Frame the scene using the camera and viewport aspect ratio.
        self.camera.frame(bounds, aspect=aspect, padding=1.2)

        # Apply the updated camera and lighting state.
        self.update_renderer_state()

    def create_grid(self, size=20, spacing=1.0):
        """Create the USD viewport grid and axis indicators.

        Args:
            size: Number of grid intervals in each direction.
            spacing: Distance between adjacent grid lines.
        """

        # Define the root transform for viewport-only geometry.
        grid_path = "/__Viewport/Grid"

        self.guide_stage = Usd.Stage.CreateInMemory()

        # Create the grid transform prim.
        UsdGeom.Xform.Define(self.guide_stage, grid_path)

        # Create the minor grid lines.
        self.create_grid_lines(
            f"{grid_path}/MinorLines",
            size=size,
            spacing=spacing,
            width=10.0,
            color=Gf.Vec3f(0.35, 0.35, 0.35),
        )

        # Create the red X-axis line.
        self.create_grid_lines(
            f"{grid_path}/XAxis",
            size=size,
            spacing=spacing,
            width=1.0,
            color=Gf.Vec3f(1.0, 0.0, 0.0),
            axis="x",
        )

        # Select the horizontal axis based on the stage up-axis.
        other_axis = "z" if self.camera.up_axis == UsdGeom.Tokens.y else "y"

        # Create the blue horizontal/up-axis indicator.
        self.create_grid_lines(
            f"{grid_path}/{other_axis.upper()}Axis",
            size=size,
            spacing=spacing,
            width=1.0,
            color=Gf.Vec3f(0.0, 0.0, 1.0),
            axis=other_axis,
        )

    def create_grid_lines(self, path, size, spacing, width, color, axis=None):
        """Create USD basis curves for grid or axis lines.

        Args:
            path: USD path where the curve prim is created.
            size: Number of grid intervals in each direction.
            spacing: Distance between adjacent grid lines.
            width: Curve width used by the renderer.
            color: Display colour assigned to the curves.
            axis: Optional axis name for creating a primary axis line.
        """

        # Create the USD basis curves prim.
        curves = UsdGeom.BasisCurves.Define(self.stage, path)

        # Store the generated curve points.
        points = list()

        # Store the number of vertices for each curve.
        vertex_counts = list()

        # Calculate the total grid extent.
        extent = size * spacing

        # Create secondary grid lines.
        if axis is None:

            # Generate grid lines on both horizontal axes.
            for index in range(-size, size + 1):

                # Skip the central axes.
                if index == 0:
                    continue

                # Calculate the current grid-line position.
                value = index * spacing

                # Generate lines on the Y-up ground plane. (XZ floor)
                if self.camera.up_axis == UsdGeom.Tokens.y:
                    points.extend(
                        [
                            Gf.Vec3f(-extent, 0.0, value),
                            Gf.Vec3f(extent, 0.0, value),
                            Gf.Vec3f(value, 0.0, -extent),
                            Gf.Vec3f(value, 0.0, extent),
                        ]
                    )

                # Generate lines on the Z-up ground plane. (XY floor)
                else:
                    points.extend(
                        [
                            Gf.Vec3f(-extent, value, 0.0),
                            Gf.Vec3f(extent, value, 0.0),
                            Gf.Vec3f(value, -extent, 0.0),
                            Gf.Vec3f(value, extent, 0.0),
                        ]
                    )

                # Each generated line contains two vertices.
                vertex_counts.extend([2, 2])

        # Create the X axis.
        elif axis == "x":
            # The X axis is horizontal in both Y-up and Z-up systems.
            if self.camera.up_axis == UsdGeom.Tokens.y:
                points.extend(
                    [
                        Gf.Vec3f(-extent, 0.0, 0.0),
                        Gf.Vec3f(extent, 0.0, 0.0),
                    ]
                )
            else:
                points.extend(
                    [
                        Gf.Vec3f(-extent, 0.0, 0.0),
                        Gf.Vec3f(extent, 0.0, 0.0),
                    ]
                )

            # Define the axis as one line segment.
            vertex_counts.append(2)

        # Create the secondary primary axis.
        elif axis in ("y", "z"):

            # Create the Z axis on a Y-up ground plane.
            if self.camera.up_axis == UsdGeom.Tokens.y:
                # Z-axis
                points.extend(
                    [
                        Gf.Vec3f(0.0, 0.0, -extent),
                        Gf.Vec3f(0.0, 0.0, extent),
                    ]
                )

            # Create the Y axis on a Z-up ground plane.
            else:
                # Y-axis
                points.extend(
                    [
                        Gf.Vec3f(0.0, -extent, 0.0),
                        Gf.Vec3f(0.0, extent, 0.0),
                    ]
                )

            # Define the axis as one line segment.
            vertex_counts.append(2)

        # Set the curve point positions.
        curves.CreatePointsAttr(points)

        # Set the number of vertices per curve.
        curves.CreateCurveVertexCountsAttr(vertex_counts)

        # Configure linear curve geometry.
        curves.CreateTypeAttr(UsdGeom.Tokens.linear)

        # Set the curve width.
        curves.CreateWidthsAttr([width])

        # Use one constant width for the curves.
        curves.SetWidthsInterpolation(UsdGeom.Tokens.constant)

        # Create the display colour primvar.
        display_color = curves.CreateDisplayColorPrimvar(UsdGeom.Tokens.constant)
        # Assign the requested curve colour.
        display_color.Set([color])

    def set_frame(self, frame):
        """Update the USD animation frame.

        Args:
            frame: Current animation frame.
        """

        # Ignore frame updates while the viewer is disabled.
        if not self.is_enabled:
            return

        # Ignore frame updates when no USD stage is loaded.
        if self.stage is None:
            return

        # Store the current animation frame.
        self.current_frame = frame

        # Request a repaint using the current animation frame.
        self.update()

    def set_sketch_enabled(self, tool, enabled, font):
        """Configure sketch annotations for the 3D viewport.

        Args:
            tool: Sketch tool to activate.
            enabled: Whether sketching is enabled.
            font: Font used by text annotations.
        """

        # Use the current viewport size as the sketch coordinate space.
        self.image_height, self.image_width = self.width(), self.height()

        # Apply the common sketch configuration.
        super().set_sketch_enabled(tool, enabled, font)

    def render_current_frame(self):
        """Render the current USD viewport into a Qt image.

        Captures the current OpenGL framebuffer and draws the active sketch annotations on top of the captured image.

        Returns:
            QtGui.QImage or None:
                Captured viewport image, or ``None`` if capture fails.
        """

        # Request an updated viewport render.
        self.update()

        # Capture the current OpenGL framebuffer.
        image = self.grabFramebuffer()

        # Return no image when framebuffer capture fails.
        if image.isNull():
            return None

        # Synchronise annotations with the current frame.
        self.sketch.set_frame(self.current_frame)

        # Define the full captured image rectangle.
        image_rect = QtCore.QRect(0, 0, image.width(), image.height())

        # Create a painter for drawing annotations.
        painter = QtGui.QPainter(image)

        # Draw annotations using normalized viewport coordinates.
        self.sketch.draw(
            painter,
            point_converter=lambda point: QtCore.QPointF(
                point[0] * image.width(),
                point[1] * image.height(),
            ),
            rect=image_rect,
        )

        # Finish the annotation drawing operation.
        painter.end()

        return image

    def set_shading_mode(self, mode):
        draw_mode = getattr(UsdImagingGL.DrawMode, mode)
        self.render_params.drawMode = draw_mode
        self.update()

    def set_complexity(self, value):
        self.render_params.complexity = value
        self.update()

    def set_purposes(self, value):
        setattr(self.render_params, value, True)
        self.update()

    def set_materials_enabled(self, enabled):
        self.render_params.enableSceneMaterials = enabled
        self.update()

    def set_grid_enabled(self, enabled):
        pass


class ViewCamera(object):
    """Interactive orbit camera for USD scene navigation.

    Responsibilities:
        Manage the camera position, orientation, orbit controls, zoom,
        panning, framing, and view-matrix generation for a USD viewport.

    Features:
        - Supports both Y-up and Z-up USD stages.
        - Provides orbit, zoom, and pan navigation.
        - Automatically frames scene bounds within the viewport.
        - Generates a USD-compatible look-at view matrix.
        - Maintains a camera-relative coordinate basis for navigation.

    Architecture:
        The camera uses an orbit model defined by a target point, distance,
        azimuth, and elevation. The camera position is calculated relative
        to the target and transformed according to the active USD stage
        up-axis convention.

    Nodes:
        ViewCamera
            ├── Target
            ├── Orbit
            ├── Zoom
            ├── Pan
            ├── Frame
            └── View Matrix

    Args:
        None.
    """

    def __init__(self):
        """Initialize the camera with default navigation parameters."""

        # Point around which the camera orbits.
        self.target = Gf.Vec3d(0.0, 0.0, 0.0)

        # Distance between the camera and its target.
        self.distance = 10.0

        # Horizontal orbit angle in degrees.
        self.azimuth = 45.0

        # Vertical orbit angle in degrees.
        self.elevation = 20.0

        # Vertical field of view in degrees.
        self.fov = 45.0

        # Near clipping plane distance.
        self.near_clip = 1.000  # 10.0  # 0.01

        # Far clipping plane distance.
        self.far_clip = 2000000.000  # 100000.0

        # Active USD stage up-axis.
        self.up_axis = UsdGeom.Tokens.y

    def set_up_axis(self, up_axis):
        """Set the active USD stage up-axis.

        Args:
            up_axis (Tf.Token):
                USD stage up-axis. Supported values are ``Y`` and ``Z``.
        """

        # Store the stage coordinate-system convention.
        self.up_axis = up_axis

        if up_axis == UsdGeom.Tokens.z:
            self.azimuth = 45.0
            self.elevation = 20.0
        else:
            self.azimuth = 45.0
            self.elevation = 20.0

    def get_world_up(self):
        """Return the world-up vector for the active coordinate system.

        Returns:
            Gf.Vec3d:
                World-up direction matching the USD stage up-axis.
        """

        # Z-up USD stage.
        if self.up_axis == UsdGeom.Tokens.z:
            return Gf.Vec3d(0.0, 0.0, 1.0)

        # Default Y-up USD stage.
        return Gf.Vec3d(0.0, 1.0, 0.0)

    def get_position(self):
        """Calculate the camera position from orbit parameters.

        Returns:
            Gf.Vec3d:
                World-space camera position.
        """

        # Convert orbit angles from degrees to radians.
        azimuth = math.radians(self.azimuth)
        elevation = math.radians(self.elevation)

        offset = Gf.Vec3d(
            self.distance * math.cos(elevation) * math.sin(azimuth),
            self.distance * math.sin(elevation),
            self.distance * math.cos(elevation) * math.cos(azimuth),
        )

        # Calculate the horizontal distance from the target.
        horizontal = self.distance * math.cos(elevation)

        # Calculate the vertical distance from the target.
        vertical = self.distance * math.sin(elevation)

        # Calculate the camera offset for a Y-up coordinate system.
        if self.up_axis == UsdGeom.Tokens.y:
            offset = Gf.Vec3d(
                horizontal * math.sin(azimuth),
                vertical,
                horizontal * math.cos(azimuth),
            )

        # Calculate the camera offset for a Z-up coordinate system.
        else:
            offset = Gf.Vec3d(
                horizontal * math.sin(azimuth),
                -horizontal * math.cos(azimuth),
                vertical,
            )

        # Convert the local orbit offset into world space.
        return self.target + offset

    def get_up_axis_transform(self):
        """Return the coordinate transform for the active up-axis.

        Returns:
            Gf.Rotation:
                Rotation used to describe the active stage orientation.
        """

        # Z-up requires a rotation relative to the default Y-up convention.
        if self.up_axis == UsdGeom.Tokens.z:
            return Gf.Rotation(Gf.Vec3d(1.0, 0.0, 0.0), 90.0)

        # Y-up is the default coordinate system.
        return Gf.Rotation()

    def get_view_matrix(self):
        """Build the camera view matrix.

        Returns:
            Gf.Matrix4d:
                World-to-camera view transformation matrix.
        """

        # Calculate the current camera position.
        position = self.get_position()

        # Build a look-at matrix using the active world-up direction.
        result = Gf.Matrix4d(1.0).SetLookAt(position, self.target, self.get_world_up())

        return result

    def orbit(self, delta_x, delta_y, sensitivity=0.5):
        """Orbit the camera around the target.

        Args:
            delta_x (float):
                Horizontal mouse movement in pixels.

            delta_y (float):
                Vertical mouse movement in pixels.

            sensitivity (float):
                Orbit rotation sensitivity.
        """

        # Horizontal mouse movement rotates around the world-up axis.
        self.azimuth -= delta_x * sensitivity

        # Vertical mouse movement changes the camera elevation.
        self.elevation += delta_y * sensitivity

        # Prevent the camera from flipping over the poles.
        self.elevation = max(-89.0, min(89.0, self.elevation))

    def zoom(self, delta):
        """Move the camera closer to or farther from the target.

        Args:
            delta (float):
                Mouse-wheel movement value.
        """

        # Move the camera closer to the target.
        if delta > 0:
            self.distance *= 0.9

        # Move the camera farther from the target.
        else:
            self.distance *= 1.1

        # Prevent the camera from reaching or crossing the target.
        self.distance = max(self.distance, 0.001)

    def frame(self, bounds, aspect=1.0, padding=1.2):
        """Frame a USD bounding box within the camera viewport.

        Args:
            bounds (Gf.Range3d):
                World-space bounding box to frame.

            aspect (float):
                Viewport width-to-height aspect ratio.

            padding (float):
                Additional distance multiplier around the framed object.
        """

        # Extract the bounding-box limits.
        minimum = bounds.GetMin()
        maximum = bounds.GetMax()

        # Position the orbit target at the center of the bounds.
        self.target = (minimum + maximum) * 0.5

        # Calculate the bounding sphere radius.
        radius = (maximum - minimum).GetLength() * 0.5

        # Convert the vertical field of view to radians.
        fov_y = math.radians(self.fov)

        # Calculate the horizontal field of view from the viewport aspect.
        fov_x = 2.0 * math.atan(math.tan(fov_y * 0.5) * aspect)

        # Use the smaller field of view to guarantee the object fits.
        fit_fov = min(fov_x, fov_y)

        # Calculate the required camera distance.
        self.distance = (radius / math.sin(fit_fov * 0.5)) * padding

        # Optional clipping planes
        # self.near_clip = max(0.01, self.distance - radius * 2.0)
        # self.far_clip = self.distance + radius * 4.0

    def get_basis(self):
        """Calculate the camera's local coordinate basis.

        Returns:
            tuple[Gf.Vec3d, Gf.Vec3d, Gf.Vec3d]:
                A tuple containing ``right``, ``up``, and ``forward`` vectors.
        """

        # Get the current camera position.
        position = self.get_position()

        # Calculate the direction from the camera toward the target.
        forward = self.target - position

        # Normalize the forward direction.
        forward.Normalize()

        # Get the active world-up direction.
        world_up = self.get_world_up()

        # Calculate the camera-right direction.
        right = Gf.Cross(forward, world_up)

        # Normalize the right direction.
        right.Normalize()

        # Calculate the camera-up direction.
        up = Gf.Cross(right, forward)

        # Normalize the up direction.
        up.Normalize()

        # Return the camera coordinate basis.
        return right, up, forward

    def pan(self, delta_x, delta_y, sensitivity=0.002):
        """Move the camera target parallel to the view plane.

        Args:
            delta_x (float):
                Horizontal mouse movement in pixels.

            delta_y (float):
                Vertical mouse movement in pixels.

            sensitivity (float):
                Panning sensitivity relative to camera distance.
        """

        # Get the camera's local coordinate basis.
        right, up, _ = self.get_basis()

        # Scale panning based on the current camera distance.
        scale = self.distance * sensitivity

        # Move the target horizontally.
        self.target += right * (-delta_x * scale)

        # Move the target vertically.
        self.target += up * (delta_y * scale)


if __name__ == "__main__":
    pass
