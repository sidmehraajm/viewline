"""
Copyright (c) 2026, Motion-Craft Technology All rights reserved.

Author:
    Subin. Gopi (subing85@gmail.com).

Module:
    ./materials/gl_screen.py

Description:
    Fullscreen OpenGL rendering quad.

    This module provides a reusable fullscreen quad used for image-based rendering.
    The quad covers the entire normalized device coordinate (NDC) viewport and is commonly used
    for displaying textures, applying GPU shaders, post-processing effects, and OCIO color transforms.

Responsibilities:
    * Create fullscreen geometry.
    * Upload vertex data to GPU buffers.
    * Configure vertex attributes.
    * Render a fullscreen triangle pair.
    * Manage OpenGL VAO/VBO resources.

Features:
    * Fullscreen textured quad.
    * Efficient GPU vertex buffers.
    * Texture coordinate support.
    * Simple draw interface.
    * Resource cleanup.

Architecture:
    FullscreenQuad
        ├── initialize()
        ├── draw()
        └── destroy()

        Texture
           │
           ▼
    Fullscreen Quad
           │
           ▼
       Fragment Shader
           │
           ▼
         Screen

Nodes:
    FullscreenQuad
"""

from __future__ import absolute_import

import numpy
import ctypes

from OpenGL import GL


class FullscreenQuad(object):
    """OpenGL fullscreen rendering quad.

    A reusable fullscreen quad consisting of two triangles. The quad is rendered in normalized
    device coordinates (NDC) and provides both vertex positions and texture coordinates for fragment shaders.

    Attributes:
        vao (int):
            Vertex Array Object identifier.

        vbo (int):
            Vertex Buffer Object identifier.
    """

    def __init__(self):
        """Initialize the fullscreen quad."""

        # Vertex Array Object.
        self.vao = 0

        # Vertex Buffer Object.
        self.vbo = 0

    def initialize(self):
        """Create the fullscreen quad geometry.

        Allocates the OpenGL vertex array and vertex buffer, uploads the vertex data, and configures the vertex attribute layout.

        Vertex Layout:
            location 0:
                vec2 position

            location 1:
                vec2 texture coordinates
        """

        # Fullscreen quad vertices.
        vertices = numpy.array(
            [
                # x     y      u     v
                -1.0,
                -1.0,
                0.0,
                1.0,
                1.0,
                -1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                0.0,
                -1.0,
                -1.0,
                0.0,
                1.0,
                1.0,
                1.0,
                1.0,
                0.0,
                -1.0,
                1.0,
                0.0,
                0.0,
            ],
            dtype=numpy.float32,
        )

        # Create the Vertex Array Object.
        self.vao = GL.glGenVertexArrays(1)

        # Create the Vertex Buffer Object.
        self.vbo = GL.glGenBuffers(1)

        # Bind the VAO.
        GL.glBindVertexArray(self.vao)

        # Bind the vertex buffer.
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)

        # Upload the vertex data to the GPU.
        GL.glBufferData(GL.GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL.GL_STATIC_DRAW)

        # Four floats per vertex.
        stride = 4 * 4

        # Position attribute (location 0).
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, False, stride, ctypes.c_void_p(0))

        # UV attribute (location 1).
        GL.glEnableVertexAttribArray(1)
        GL.glVertexAttribPointer(1, 2, GL.GL_FLOAT, False, stride, ctypes.c_void_p(8))

        # Unbind the VAO.
        GL.glBindVertexArray(0)

    def draw(self):
        """Render the fullscreen quad.

        Draws two triangles that cover the entire viewport.

        Returns:
            None
        """

        # Bind the vertex array.
        GL.glBindVertexArray(self.vao)

        # Render two triangles.
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)

        # Unbind the vertex array.
        GL.glBindVertexArray(0)

    def destroy(self):
        """Release OpenGL resources.

        Deletes the vertex buffer and vertex array objects and resets their handles to zero.

        Returns:
            None
        """

        # Delete the vertex buffer.
        if self.vbo:
            GL.glDeleteBuffers(1, [self.vbo])

        # Delete the vertex array.
        if self.vao:
            GL.glDeleteVertexArrays(1, [self.vao])

        # Reset the VBO handle.
        self.vbo = 0

        # Reset the VAO handle.
        self.vao = 0


if __name__ == "__main__":
    pass
