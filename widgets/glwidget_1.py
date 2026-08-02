class _GLViewer2d(QtOpenGLWidgets.QOpenGLWidget):
    """Modern OpenGL image viewer."""

    render_finished = QtCore.Signal(str)

    def __init__(self, parent=None):
        """Create OpenGL viewer."""

        super().__init__(parent)

        # Expand inside layouts.

        # Configure expanding size policy
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding
        )

        self.setSizePolicy(sizePolicy)

        # Enable multisampling.

        self.set_samples(constants.VIEWER_SAMPLES_RATE)

        self.ocio_processor = None

        # OpenGL resources.
        self.texture = None
        self.shader = None
        self.quad = None
        self.ocio_shader = None  # GPU OCIO shader
        self.use_ocio = False

        # Current image.
        self.numpy_frame = None

        # Image size.
        self.image_width = 0
        self.image_height = 0
        self.channels = None

        # Display rectangle.
        self.display_rect = QtCore.QRect()

        # Timeline.
        self.current_frame = None

        # Camera
        # Current zoom factor.
        # 1.0 = Fit
        # 2.0 = 200%

        self.zoom = 1.0

        # Pan offset (normalized).
        self.pan = QtCore.QPointF(0.0, 0.0)

        # Viewer mode.
        self.fit_mode = True

        self.display_parameter = None
        self.style_parameter = None
        self.filter_parameter = None

        self.is_enabled = False

        # Annotation system.
        self.sketch = Sketch()

    def set_samples(self, samples=8):
        """Configure OpenGL multisampling."""

        surface = QtGui.QSurfaceFormat()
        surface.setSamples(samples)
        self.setFormat(surface)

    def initializeGL(self):
        """Initialize OpenGL resources."""

        # Background colour.
        GL.glClearColor(0.1, 0.1, 0.1, 1.0)

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

    def clear(self):
        """Clear viewer."""

        self.numpy_frame = None

        # self.texture.clear()

        self.sketch.clear_all()

        self.update()

    def set_current_frame(self, frame):
        """Update timeline."""

        self.current_frame = frame

        self.sketch.set_frame(frame)

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

    def wheelEvent(self, event):
        """Mouse wheel zoom."""

        delta = event.angleDelta().y()

        if delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def mousePressEvent(self, event):
        if not self.sketch.enabled:
            return

        point = self.widget_to_image_point(event.position().toPoint())

        self.sketch.mousePressEvent(point)

        self.update()

        event.accept()

    def mouseMoveEvent(self, event):
        if not self.sketch.enabled:
            return

        if not (event.buttons() & QtCore.Qt.LeftButton):
            return

        point = self.widget_to_image_point(event.position().toPoint())

        self.sketch.mouseMoveEvent(point)

        self.update()

        event.accept()

    def mouseReleaseEvent(self, event):

        if not self.sketch.enabled:
            return

        point = self.widget_to_image_point(event.position().toPoint())

        self.sketch.mouseReleaseEvent(point)

        self.update()

        event.accept()

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

    def render_current_frame(self):
        """
        Render source frame with annotations.

        Returns:
            QImage
        """

        if self.numpy_frame is None:
            return None

        # Convert AVFrame -> RGB NumPy image.
        frame = self.numpy_frame.to_ndarray(format="rgb24")
        frame = numpy.ascontiguousarray(frame)

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


#################################


class _GLViewer3d(QtOpenGLWidgets.QOpenGLWidget):

    render_finished = QtCore.Signal(str)

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

        self.current_frame = None
        self.is_enabled = False

        # Display rectangle.
        self.display_rect = QtCore.QRect()

        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding
        )

        self.setSizePolicy(sizePolicy)

        # Annotation system.
        self.sketch = Sketch()

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
        LOGGER.info(f"Hydra engine created: {self.engine}")

        self.create_render_param()

        self.create_lighting_state()
        # self.update_renderer_state()

        LOGGER.info(f"Renderer: {self.engine.GetCurrentRendererId()}")
        LOGGER.info(f"Backend: {self.engine.GetRendererHgiDisplayName()}")

    def resizeGL(self, width, height):
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

        self.render_params.frame = self.current_frame

        self.engine.Render(self.stage.GetPseudoRoot(), self.render_params)

        GL.glFlush()

    def update_camera(self):
        if self.engine is None:
            return

        width = max(self.width(), 1)
        height = max(self.height(), 1)
        aspect = width / height

        # self.camera_state  = True
        view_matrix = self.camera.get_view_matrix()
        projection_matrix = self.create_projection_matrix(aspect)

        self.engine.SetCameraState(view_matrix, projection_matrix)

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

    def load_usd(self, filename):
        """Load a USD stage."""

        self.stage = Usd.Stage.Open(filename)

        if self.stage is None:
            raise RuntimeError(f"Unable to open USD: {filename}")

        up_axis = UsdGeom.GetStageUpAxis(self.stage)
        self.camera.set_up_axis(up_axis)
        self.create_grid(size=20, spacing=1.0)

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

        aspect = max(self.width(), 1) / max(self.height(), 1)

        # Here to update if not bounds

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

    def load_usd(self, filename):
        """Load a USD stage."""

        self.stage = Usd.Stage.Open(filename)

        if self.stage is None:
            raise RuntimeError(f"Unable to open USD: {filename}")

        up_axis = UsdGeom.GetStageUpAxis(self.stage)
        self.camera.set_up_axis(up_axis)
        self.create_grid(size=20, spacing=1.0)

        self.frame_all()

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

            print("\nenabled", self.sketch.enabled)
            if not self.sketch.enabled:
                return

            point = self.widget_to_image_point(event.position().toPoint())
            self.sketch.mousePressEvent(point)

            self.update()

        event.accept()

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

        event.accept()

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

    def set_stage(self, stage):
        """Set a new USD stage."""

        if stage is None:
            return

        self.stage = stage

        up_axis = UsdGeom.GetStageUpAxis(self.stage)

        self.camera.set_up_axis(up_axis)
        self.create_grid(size=20, spacing=1.0)

        # Frame the camera only when loading a new stage.
        self.frame_all()

    def set_frame(self, frame):
        if not self.is_enabled:
            return

        if self.stage is None:
            return

        # Texture upload happens inside paintGL().
        self.update()

    def set_current_frame(self, frame):
        """Update timeline."""

        self.current_frame = frame

    def set_ocio(self, processor):
        pass

    def display_changed(self, parameter):
        pass

    def style_changed(self, parameter):
        pass

    def filter_changed(self, parameter):
        pass

    def undo_strokes(self):
        pass

    def clear_strokes(self):
        pass

    def set_overlay_option(self, checked, key, position, context):
        pass
