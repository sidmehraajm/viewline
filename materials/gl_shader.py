"""
Copyright (c) 2026, Motion-Craft Technology All rights reserved.

Author:
    Subin. Gopi (subing85@gmail.com).

Module:
    ./materials/gl_shader.py

Description:
    OpenGL shader management for the Viewline renderer.

    This module provides a lightweight wrapper around OpenGL shader programs.
    It handles shader compilation, program linking, binding, uniform updates, and resource cleanup for the Viewline rendering pipeline.

Responsibilities:
    - Compile GLSL vertex and fragment shaders.
    - Create and manage shader programs.
    - Bind and release shader programs.
    - Upload uniform values.
    - Validate shader compilation and linking.
    - Release OpenGL shader resources.

Features:
    - Vertex and fragment shader compilation.
    - Automatic program linking.
    - Uniform helper methods.
    - Matrix and vector uniform support.
    - Compile and link error reporting.
    - Resource cleanup.

Architecture:
    GLShader
        ├── initialize()
        ├── compile()
        ├── destroy()
        ├── bind()
        ├── release()
        ├── uniform_location()
        ├── set_uniform_*
        ├── _check_shader()
        └── _check_program()

Nodes:
    GLShader
"""

from __future__ import absolute_import

from OpenGL import GL

from viewline import resources


class GLShader(object):
    """Wrapper around an OpenGL shader program.

    This class simplifies shader management by handling shader compilation, program linking, uniform uploads, and cleanup.
    It is shared by the 2D viewer, OCIO shader, and other OpenGL rendering components.

    Attributes:
        program (int):
            OpenGL program identifier.

        vertex_shader (int):
            Vertex shader object identifier.

        fragment_shader (int):
            Fragment shader object identifier.
    """

    def __init__(self):
        """Initialize the shader object."""

        # OpenGL shader program.
        self.program = 0

        # Vertex shader handle.
        self.vertex_shader = 0

        # Fragment shader handle.
        self.fragment_shader = 0

    def initialize(self, name="display"):
        """Load and compile a shader program.

        Args:
            name (str):
                Shader resource name.
        """

        # Read the shader source files.
        vertex_source, fragment_source = resources.readShader(name)

        # Compile the shader program.
        self.compile(vertex_source, fragment_source)

    def compile(self, vertex_source, fragment_source):
        """Compile and link the shader program.

        Args:
            vertex_source (str):
                Vertex shader source.

            fragment_source (str):
                Fragment shader source.
        """

        # Release any existing shader resources.
        self.destroy()

        # Create the vertex shader.
        self.vertex_shader = GL.glCreateShader(GL.GL_VERTEX_SHADER)

        # Upload the source code.
        GL.glShaderSource(self.vertex_shader, vertex_source)

        # Compile the shader.
        GL.glCompileShader(self.vertex_shader)

        # Validate compilation.
        self._check_shader(self.vertex_shader, "Vertex Shader")

        # Create the fragment shader.
        self.fragment_shader = GL.glCreateShader(GL.GL_FRAGMENT_SHADER)

        # Upload the source code.
        GL.glShaderSource(self.fragment_shader, fragment_source)

        # Compile the shader.
        GL.glCompileShader(self.fragment_shader)

        # Validate compilation.
        self._check_shader(self.fragment_shader, "Fragment Shader")

        # Create the shader program.
        self.program = GL.glCreateProgram()

        # Attach the compiled vertex shader.
        GL.glAttachShader(self.program, self.vertex_shader)

        # Attach the compiled fragment shader.
        GL.glAttachShader(self.program, self.fragment_shader)

        # Link the shader program.
        GL.glLinkProgram(self.program)

        # Validate linking.
        self._check_program()

    def destroy(self):
        """Release all OpenGL shader resources."""

        # Delete the shader program.
        if self.program:
            GL.glDeleteProgram(self.program)

        # Delete the vertex shader.
        if self.vertex_shader:
            GL.glDeleteShader(self.vertex_shader)

        # Delete the fragment shader.
        if self.fragment_shader:
            GL.glDeleteShader(self.fragment_shader)

        # Reset program handle.
        self.program = 0

        # Reset vertex shader handle.
        self.vertex_shader = 0

        # Reset fragment shader handle.
        self.fragment_shader = 0

    def bind(self):
        """Activate the shader program."""

        # Bind the shader program.
        GL.glUseProgram(self.program)

    def release(self):
        """Deactivate the current shader program."""

        # Unbind the shader program.
        GL.glUseProgram(0)

    def uniform_location(self, name):
        """Return a uniform variable location.

        Args:
            name (str):
                Uniform variable name.

        Returns:
            int:
                Uniform location.
        """

        # Query the uniform location.
        return GL.glGetUniformLocation(self.program, name)

    def has_uniform(self, name):
        location = GL.glGetUniformLocation(self.program, name)

        return location != -1

    def set_uniform_int(self, name, value):
        """Upload an integer uniform.

        Args:
            name (str):
                Uniform name.

            value (int):
                Integer value.
        """

        # Lookup the uniform.
        location = self.uniform_location(name)

        # Upload the value.
        GL.glUniform1i(location, value)

    def set_uniform_float(self, name, value):
        """Upload a floating-point uniform.

        Args:
            name (str):
                Uniform name.

            value (float):
                Float value.
        """

        # Lookup the uniform.
        location = self.uniform_location(name)

        # Upload the value.
        GL.glUniform1f(location, value)

    def set_uniform_vec2(self, name, x, y):
        """Upload a vec2 uniform.

        Args:
            name (str):
                Uniform name.

            x (float):
                X component.

            y (float):
                Y component.
        """

        # Lookup the uniform.
        location = self.uniform_location(name)

        # Upload the vector.
        GL.glUniform2f(location, x, y)

    def set_uniform_vec3(self, name, x, y, z):
        """Upload a vec3 uniform.

        Args:
            name (str):
                Uniform name.

            x (float):
                X component.

            y (float):
                Y component.

            z (float):
                Z component.
        """

        # Lookup the uniform.
        location = self.uniform_location(name)

        # Upload the vector.
        GL.glUniform3f(location, x, y, z)

    def set_uniform_vec4(self, name, value):
        """Upload a vec4 uniform.

        Args:
            name (str):
                Uniform name.

            value (tuple):
                Four-component vector.
        """

        # Lookup the uniform location.
        location = GL.glGetUniformLocation(self.program, name)

        # Upload the vector.
        GL.glUniform4f(
            location,
            float(value[0]),
            float(value[1]),
            float(value[2]),
            float(value[3]),
        )

    def set_uniform_mat4(self, name, matrix):
        """Upload a 4×4 matrix uniform.

        Args:
            name (str):
                Uniform name.

            matrix:
                Matrix data.
        """

        # Lookup the uniform.
        location = self.uniform_location(name)

        # Upload the matrix.
        GL.glUniformMatrix4fv(location, 1, False, matrix)

    def _check_shader(self, shader, label):
        """Validate shader compilation.

        Args:
            shader (int):
                Shader object.

            label (str):
                Shader description.

        Raises:
            RuntimeError:
                If compilation fails.
        """

        # Query the compile status.
        status = GL.glGetShaderiv(shader, GL.GL_COMPILE_STATUS)

        # Compilation succeeded.
        if status:
            return

        # Retrieve the compiler log.
        log = GL.glGetShaderInfoLog(shader)

        # Raise the compile error.
        raise RuntimeError(f"{label} Compile Error\n\n{log.decode()}")

    def _check_program(self):
        """Validate shader program linking.

        Raises:
            RuntimeError:
                If program linking fails.
        """

        # Query the link status.
        status = GL.glGetProgramiv(self.program, GL.GL_LINK_STATUS)

        # Linking succeeded.
        if status:
            return

        # Retrieve the linker log.
        log = GL.glGetProgramInfoLog(self.program)

        # Raise the link error.
        raise RuntimeError(f"Shader Link Error\n\n{log.decode()}")


if __name__ == "__main__":
    pass
