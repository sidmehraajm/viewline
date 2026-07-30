import math

from PySide6 import QtGui
from PySide6 import QtCore
from PySide6 import QtOpenGLWidgets

from OpenGL import GL

from pxr import Gf
from pxr import Glf
from pxr import Usd
from pxr import UsdGeom
from pxr import UsdImagingGL

from viewline import constants


class USDViewWidget(QtOpenGLWidgets.QOpenGLWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.stage = None
        self.engine = None

        self.camera = ViewCamera()

        self.set_samples(constants.VIEWER_SAMPLES_RATE)

        self.last_mouse_position = None
        self.headLight = None

        self.render_params = None
        self.head_light = None
        self.lights = list()
        self.material = None
        self.scene_ambient = None

        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

    def set_samples(self, samples=8):
        """Configure OpenGL multisampling."""

        surface = QtGui.QSurfaceFormat()
        surface.setSamples(samples)
        self.setFormat(surface)

    def create_render_param(self):
        self.render_params = UsdImagingGL.RenderParams()

        self.render_params.drawMode = UsdImagingGL.DrawMode.DRAW_SHADED_SMOOTH
        self.render_params.enableLighting = True
        self.render_params.enableSceneMaterials = False

        self.render_params.showProxy = True
        self.render_params.showGuides = True
        self.render_params.showRender = False

        self.render_params.cullStyle = UsdImagingGL.CullStyle.CULL_STYLE_NOTHING
        self.render_params.complexity = 1.0
        self.render_params.gammaCorrectColors = False

    def create_lighting_state(self):
        self.head_light = Glf.SimpleLight()

        self.head_light.ambient = Gf.Vec4f(0.2, 0.2, 0.2, 1.0)
        self.head_light.diffuse = Gf.Vec4f(1.0, 1.0, 1.0, 1.0)
        self.head_light.specular = Gf.Vec4f(0.01, 0.01, 0.01, 1.0)
        # self.head_light.position = Gf.Vec4f(0, 0, 10, 0)

        self.material = Glf.SimpleMaterial()
        self.material.ambient = Gf.Vec4f(0.2, 0.2, 0.2, 1.0)
        self.material.diffuse = Gf.Vec4f(0.8, 0.8, 0.8, 1.0)
        self.material.specular = Gf.Vec4f(0.01, 0.01, 0.01, 1.0)
        self.material.shininess = 32.0

        self.scene_ambient = Gf.Vec4f(0.2, 0.2, 0.2, 1.0)

        self.lights = [self.head_light]

    def initializeGL(self):
        """Initialize OpenGL and the Hydra engine."""

        GL.glClearColor(
            0.2,
            0.2,
            0.2,
            1.0,
        )

        self.engine = UsdImagingGL.Engine()
        print("Hydra engine created:", self.engine)

        self.create_render_param()

        self.create_lighting_state()
        self.update_renderer_state()

        print("Renderer :", self.engine.GetCurrentRendererId())
        print("Backend  :", self.engine.GetRendererHgiDisplayName())

    def resizeGL(self, width: int, height: int):
        """Handle OpenGL viewport resize."""

        if self.engine is None:
            return

        self.engine.SetRenderBufferSize(Gf.Vec2i(width, height))
        self.engine.SetRenderViewport(Gf.Vec4d(0, 0, width, height))

        self.update_renderer_state()

        self.update()

    def paintGL(self):
        """Render the current USD stage."""

        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        if self.stage is None:
            return

        if self.engine is None:
            return

        self.engine.Render(self.stage.GetPseudoRoot(), self.render_params)

        GL.glFlush()

    def update_camera(self):
        if self.engine is None:
            return

        width = max(self.width(), 1)
        height = max(self.height(), 1)
        aspect = width / height

        view_matrix = self.camera.get_view_matrix()
        projection_matrix = self.create_projection_matrix(aspect)

        self.engine.SetCameraState(view_matrix, projection_matrix)

        view_matrix = self.camera.get_view_matrix()
        projection_matrix = self.create_projection_matrix(aspect)

    def update_head_light(self):
        if self.engine is None:
            return

        if not self.lights:
            return

        camera_position = self.camera.get_position()
        self.head_light.position = Gf.Vec4f(
            camera_position[0], camera_position[1], camera_position[2], 0
        )

        self.engine.SetLightingState(self.lights, self.material, self.scene_ambient)

    def update_renderer_state(self):
        """Update the Hydra camera state."""

        self.update_camera()
        self.update_head_light()

    def update_view(self):
        self.update_renderer_state()
        self.update()

    def _load_usd(self, filename):
        """Load a USD stage."""

        self.stage = Usd.Stage.Open(filename)

        if self.stage is None:
            raise RuntimeError(f"Unable to open USD: {filename}")

        up_axis = UsdGeom.GetStageUpAxis(self.stage)
        self.camera.set_up_axis(up_axis)

        self.create_grid(size=20, spacing=1.0)

        self.frame_all()

        self.update()

    def load_usd(self, filename):

        self.stage = Usd.Stage.Open(filename)

        if self.stage is None:
            raise RuntimeError(f"Unable to open USD: {filename}")

        self.start_time = self.stage.GetStartTimeCode()
        self.end_time = self.stage.GetEndTimeCode()

        if self.start_time == Usd.TimeCode.Default().GetValue():
            self.start_time = 1.0

        if self.end_time == Usd.TimeCode.Default().GetValue():
            self.end_time = self.start_time

        self.current_time = self.start_time

        self.frame_all()

        self.update()

    def create_projection_matrix(self, aspect):
        """Create a perspective projection matrix."""

        fov = math.radians(self.camera.fov)

        f = 1.0 / math.tan(fov * 0.5)

        near = self.camera.near_clip
        far = self.camera.far_clip

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
        if self.stage is None:
            return

        bbox_cache = UsdGeom.BBoxCache(
            self.stage.GetTimeCodesPerSecond(), [UsdGeom.Tokens.default_]
        )
        bbox = bbox_cache.ComputeWorldBound(self.stage.GetPseudoRoot())
        bounds = bbox.ComputeAlignedRange()

        # minimum = bounds.GetMin()
        # maximum = bounds.GetMax()
        # center = (minimum + maximum) * 0.5
        # size = maximum - minimum

        # radius = max(size[0], size[1], size[2]) * 0.5

        # aspect = max(self.width(), 1) / max(self.height(), 1)

        aspect = max(self.width(), 1) / max(self.height(), 1)

        # self.camera._frame(bounds)
        self.camera.frame(bounds, aspect=aspect, padding=1.2)

        self.update_renderer_state()

    def create_grid(self, size=20, spacing=1.0):
        """Create a viewport grid aligned with the stage up-axis."""

        grid_path = "/__Viewport/Grid"
        UsdGeom.Xform.Define(self.stage, grid_path)

        self.create_grid_lines(
            f"{grid_path}/MinorLines",
            size=size,
            spacing=spacing,
            width=10.0,
            color=Gf.Vec3f(0.35, 0.35, 0.35),
        )

        self.create_grid_lines(
            f"{grid_path}/XAxis",
            size=size,
            spacing=spacing,
            width=1.0,
            color=Gf.Vec3f(1.0, 0.0, 0.0),
            axis="x",
        )

        other_axis = "z" if self.camera.up_axis == UsdGeom.Tokens.y else "y"

        self.create_grid_lines(
            f"{grid_path}/{other_axis.upper()}Axis",
            size=size,
            spacing=spacing,
            width=1.0,
            color=Gf.Vec3f(0.0, 0.0, 1.0),
            axis=other_axis,
        )

    def create_grid_lines(self, path, size, spacing, width, color, axis=None):
        """Create a BasisCurves grid component."""

        curves = UsdGeom.BasisCurves.Define(self.stage, path)

        points = list()
        vertex_counts = list()

        extent = size * spacing

        # Create only the minor grid lines.
        # The two center lines are created separately.

        if axis is None:
            for index in range(-size, size + 1):
                if index == 0:
                    continue

                value = index * spacing
                if self.camera.up_axis == UsdGeom.Tokens.y:
                    # XZ floor
                    points.extend(
                        [
                            Gf.Vec3f(-extent, 0.0, value),
                            Gf.Vec3f(extent, 0.0, value),
                            Gf.Vec3f(value, 0.0, -extent),
                            Gf.Vec3f(value, 0.0, extent),
                        ]
                    )
                else:

                    # XY floor
                    points.extend(
                        [
                            Gf.Vec3f(-extent, value, 0.0),
                            Gf.Vec3f(extent, value, 0.0),
                            Gf.Vec3f(value, -extent, 0.0),
                            Gf.Vec3f(value, extent, 0.0),
                        ]
                    )

                vertex_counts.extend([2, 2])

        # X axis
        elif axis == "x":
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

            vertex_counts.append(2)

        # Other floor axis
        elif axis in ("y", "z"):
            if self.camera.up_axis == UsdGeom.Tokens.y:
                # Z-axis
                points.extend(
                    [
                        Gf.Vec3f(0.0, 0.0, -extent),
                        Gf.Vec3f(0.0, 0.0, extent),
                    ]
                )

            else:
                # Y-axis
                points.extend(
                    [
                        Gf.Vec3f(0.0, -extent, 0.0),
                        Gf.Vec3f(0.0, extent, 0.0),
                    ]
                )

            vertex_counts.append(2)

        # USD attributes
        curves.CreatePointsAttr(points)
        curves.CreateCurveVertexCountsAttr(vertex_counts)
        curves.CreateTypeAttr(UsdGeom.Tokens.linear)

        curves.CreateWidthsAttr([width])
        curves.SetWidthsInterpolation(UsdGeom.Tokens.constant)

        # curves.CreateDisplayColorAttr([color])
        display_color = curves.CreateDisplayColorPrimvar(UsdGeom.Tokens.constant)
        display_color.Set([color])

    def mousePressEvent(self, event):
        self.last_mouse_position = event.position()
        self.setFocus()
        event.accept()

    def mouseMoveEvent(self, event):

        if self.last_mouse_position is None:
            return

        current = event.position()

        delta = current - self.last_mouse_position
        dx = delta.x()
        dy = delta.y()

        buttons = event.buttons()

        if buttons & QtCore.Qt.MouseButton.LeftButton:
            self.camera.orbit(dx, dy)
            self.update_view()

        elif buttons & QtCore.Qt.MouseButton.MiddleButton:
            self.camera.pan(dx, dy)
            self.update_view()

        self.last_mouse_position = current

        event.accept()

    def mouseReleaseEvent(self, event):
        self.last_mouse_position = None
        event.accept()

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


class ViewCamera(object):
    """Orbit camera for a 3D viewport."""

    def __init__(self):
        self.target = Gf.Vec3d(0.0, 0.0, 0.0)
        self.distance = 10.0
        self.azimuth = 45.0
        self.elevation = 20.0
        self.fov = 45.0
        self.near_clip = 10.0  # 0.01
        self.far_clip = 100000000.0  # 100000.0

        self.up_axis = UsdGeom.Tokens.y

    def set_up_axis(self, up_axis):
        """Set the camera world up-axis."""

        self.up_axis = up_axis

        if up_axis == UsdGeom.Tokens.z:
            self.azimuth = 45.0
            self.elevation = 20.0
        else:
            self.azimuth = 45.0
            self.elevation = 20.0

    def get_world_up(self):
        """Return the world up vector."""

        if self.up_axis == UsdGeom.Tokens.z:
            return Gf.Vec3d(0.0, 0.0, 1.0)

        return Gf.Vec3d(0.0, 1.0, 0.0)

    def get_position(self):
        """Return the camera position around the target."""

        azimuth = math.radians(self.azimuth)
        elevation = math.radians(self.elevation)

        # Canonical camera orbit:
        #   Y = up
        #   X = horizontal
        #   Z = depth
        offset = Gf.Vec3d(
            self.distance * math.cos(elevation) * math.sin(azimuth),
            self.distance * math.sin(elevation),
            self.distance * math.cos(elevation) * math.cos(azimuth),
        )

        horizontal = self.distance * math.cos(elevation)
        vertical = self.distance * math.sin(elevation)

        if self.up_axis == UsdGeom.Tokens.y:
            offset = Gf.Vec3d(
                horizontal * math.sin(azimuth),
                vertical,
                horizontal * math.cos(azimuth),
            )
        else:
            offset = Gf.Vec3d(
                horizontal * math.sin(azimuth),
                -horizontal * math.cos(azimuth),
                vertical,
            )

        return self.target + offset

    def get_up_axis_transform(self):
        """Return the transform from the canonical camera space."""

        if self.up_axis == UsdGeom.Tokens.z:
            # Convert canonical Y-up to Z-up.
            # Canonical:
            #   Y = up
            #   Z = depth

            # Z-up:
            #   Z = up
            #   Y = depth
            return Gf.Rotation(Gf.Vec3d(1.0, 0.0, 0.0), 90.0)

        return Gf.Rotation()

    def get_view_matrix(self):
        """Return the world-to-camera matrix."""

        position = self.get_position()

        # result = Gf.Matrix4d(1.0).SetLookAt(position, self.target, Gf.Vec3d(0.0, 1.0, 0.0))
        result = Gf.Matrix4d(1.0).SetLookAt(position, self.target, self.get_world_up())

        return result

    def orbit(self, delta_x, delta_y, sensitivity=0.5):
        """Orbit the camera around the target."""

        self.azimuth -= delta_x * sensitivity
        self.elevation += delta_y * sensitivity

        self.elevation = max(-89.0, min(89.0, self.elevation))

    def zoom(
        self,
        delta,
    ):
        """Move the camera toward or away from the target."""

        if delta > 0:
            self.distance *= 0.9
        else:
            self.distance *= 1.1

        self.distance = max(self.distance, 0.001)

    def frame(self, bounds, aspect=1.0, padding=1.2):
        """Frame the specified bounds."""

        minimum = bounds.GetMin()
        maximum = bounds.GetMax()

        self.target = (minimum + maximum) * 0.5

        # Bounding sphere radius
        radius = (maximum - minimum).GetLength() * 0.5

        # Vertical FOV
        fov_y = math.radians(self.fov)

        # Horizontal FOV
        fov_x = 2.0 * math.atan(math.tan(fov_y * 0.5) * aspect)

        # Use the smaller FOV so the object fits both width and height
        fit_fov = min(fov_x, fov_y)

        self.distance = (radius / math.sin(fit_fov * 0.5)) * padding

        # Optional clipping planes
        # self.near_clip = max(0.01, self.distance - radius * 2.0)
        # self.far_clip = self.distance + radius * 4.0

    def get_basis(self):
        """Return camera right, up, and forward vectors."""

        position = self.get_position()

        forward = self.target - position
        forward.Normalize()

        world_up = (
            Gf.Vec3d(0.0, 0.0, 1.0) if self.up_axis == UsdGeom.Tokens.z else Gf.Vec3d(0.0, 1.0, 0.0)
        )

        right = Gf.Cross(forward, world_up)
        right.Normalize()

        up = Gf.Cross(right, forward)
        up.Normalize()

        return right, up, forward

    def pan(self, delta_x, delta_y, sensitivity=0.002):
        """Pan the camera target in screen space."""

        right, up, _ = self.get_basis()
        scale = self.distance * sensitivity
        self.target += right * (-delta_x * scale)
        self.target += up * (delta_y * scale)
