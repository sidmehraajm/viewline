"""
Copyright (c) 2026, Motion-Craft Technology All rights reserved.

Author:
    Subin. Gopi (subing85@gmail.com).

Module:
    ./materials/gl_texture3D.py

Description:
    OpenGL 3D texture management.

    This module provides a lightweight wrapper around an OpenGL 3D texture used primarily for GPU lookup tables (LUTs),
    such as OpenColorIO (OCIO) color transforms. It supports texture creation, LUT uploads, and binding for shader usage.

Responsibilities:
    * Create OpenGL 3D textures.
    * Configure texture sampling parameters.
    * Upload 3D LUT data to GPU memory.
    * Bind textures to shader texture units.

Features:
    * Supports floating-point 3D textures.
    * Linear interpolation filtering.
    * Clamp-to-edge texture wrapping.
    * Optimized for OCIO GPU LUTs.
    * Minimal OpenGL resource management.

Architecture:
    GLTexture3D
        ├── initialize()
        ├── upload()
        └── bind()

Nodes:
    GLTexture3D
"""

from __future__ import absolute_import

from OpenGL import GL


class GLTexture3D(object):
    """Wrapper around an OpenGL 3D texture.

    The class manages a GPU 3D texture commonly used to store color lookup tables (3D LUTs).
    It is primarily intended for GPU-based color management pipelines such as OpenColorIO.

    Attributes:
        texture (int | None):
            OpenGL texture identifier.
    """

    def __init__(self):
        """Initialize an empty 3D texture object."""

        # OpenGL texture handle.
        self.texture = None

    def initialize(self):
        """Create and configure the OpenGL 3D texture.

        Allocates a new 3D texture object and applies default filtering and wrapping parameters suitable for color lookup tables.

        Returns:
            None
        """

        # Generate a 3D texture object.
        self.texture = GL.glGenTextures(1)

        # Bind the texture.
        GL.glBindTexture(GL.GL_TEXTURE_3D, self.texture)

        # Enable linear interpolation during minification.
        GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)

        # Enable linear interpolation during magnification.
        GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)

        # Clamp texture coordinates along the S axis.
        GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)

        # Clamp texture coordinates along the T axis.
        GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)

        # Clamp texture coordinates along the R axis.
        GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_WRAP_R, GL.GL_CLAMP_TO_EDGE)

        # Unbind the texture.
        GL.glBindTexture(GL.GL_TEXTURE_3D, 0)

    def upload(self, lut, size):
        """Upload a 3D LUT to GPU memory.

        The LUT is uploaded as a floating-point RGB texture using the
        ``GL_RGB32F`` internal format.

        Args:
            lut (numpy.ndarray):
                Flattened floating-point LUT data.

            size (int):
                Width, height, and depth of the cubic LUT.

        Returns:
            None
        """

        # Bind the texture.
        GL.glBindTexture(GL.GL_TEXTURE_3D, self.texture)

        # Upload the complete 3D LUT.
        GL.glTexImage3D(
            GL.GL_TEXTURE_3D,
            0,
            GL.GL_RGB32F,
            size,
            size,
            size,
            0,
            GL.GL_RGB,
            GL.GL_FLOAT,
            lut,
        )

        # Unbind the texture.
        GL.glBindTexture(GL.GL_TEXTURE_3D, 0)

    def bind(self, unit):
        """Bind the 3D texture to a texture unit.

        Args:
            unit (int):
                OpenGL texture unit index.

        Returns:
            None
        """

        # Activate the requested texture unit.
        GL.glActiveTexture(GL.GL_TEXTURE0 + unit)

        # Bind the 3D texture.
        GL.glBindTexture(GL.GL_TEXTURE_3D, self.texture)


if __name__ == "__main__":
    pass
