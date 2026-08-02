"""
Copyright (c) 2026, Motion-Craft Technology All rights reserved.

Author:
    Subin. Gopi (subing85@gmail.com).

Module:
    ./materials/gl_texture.py

Description:
    OpenGL texture management.

    This module provides a lightweight wrapper around OpenGL 2D textures for uploading and displaying image or video frame data.
    It supports dynamic texture allocation, resizing, updating, and resource cleanup.

Responsibilities:
    * Create and configure OpenGL textures.
    * Upload NumPy image buffers.
    * Upload PyAV video frames.
    * Resize textures automatically.
    * Bind textures for rendering.
    * Release GPU resources.

Features:
    * Lazy texture creation.
    * Automatic texture resizing.
    * Supports NumPy arrays.
    * Supports PyAV VideoFrame.
    * Linear texture filtering.
    * Clamp-to-edge wrapping.
    * Efficient texture updates.

Architecture:
    GLTexture
        ├── initialize()
        ├── create()
        ├── upload()
        ├── bind()
        ├── release()
        └── destroy()

Nodes:
    GLTexture
"""

from __future__ import absolute_import

import av
import numpy

from OpenGL import GL


class GLTexture(object):
    """Wrapper around an OpenGL 2D texture.

    The class manages the complete lifetime of a GPU texture, including creation, configuration, image uploads, binding, and cleanup.

    Attributes:
        texture (int):
            OpenGL texture identifier.

        width (int):
            Current texture width.

        height (int):
            Current texture height.

        internal_format (GLenum):
            Internal OpenGL texture format.

        pixel_format (GLenum):
            Pixel format used during uploads.

        pixel_type (GLenum):
            Pixel data type.
    """

    def __init__(self):
        """Initialize an empty OpenGL texture."""

        # OpenGL texture handle.
        self.texture = 0

        # Texture width in pixels.
        self.width = 0

        # Texture height in pixels.
        self.height = 0

        # Internal GPU storage format.
        self.internal_format = GL.GL_RGB8

        # Pixel upload format.
        self.pixel_format = GL.GL_RGB

        # Pixel data type.
        self.pixel_type = GL.GL_UNSIGNED_BYTE

    def initialize(self):
        """Create and configure the OpenGL texture.

        Allocates a texture object and applies the default filtering parameters.

        Returns:
            None
        """

        # Generate a texture object.
        self.texture = GL.glGenTextures(1)

        # Bind the texture.
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)

        # Set linear minification filtering.
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)

        # Set linear magnification filtering.
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)

        # Unbind the texture.
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

    def create(self):
        """Create the texture if it does not already exist.

        The texture uses linear filtering and clamp-to-edge wrapping.

        Returns:
            None
        """

        # Skip if already created.
        if self.texture:
            return

        # Generate the texture object.
        self.texture = GL.glGenTextures(1)

        # Bind the texture.
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)

        # Configure filtering.
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)

        # Prevent texture coordinate wrapping.
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)

        # Unbind the texture.
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

    def destroy(self):
        """Delete the OpenGL texture.

        Releases the GPU resource and resets all cached texture information.

        Returns:
            None
        """

        # Nothing to destroy.
        if not self.texture:
            return

        # Generate the texture object.
        GL.glDeleteTextures([self.texture])

        # Reset texture handle.
        self.texture = 0

        # Reset cached dimensions.
        self.width = 0
        self.height = 0

    def upload(self, image):
        """Upload image data to the GPU texture.

        Accepts either a NumPy array or a PyAV VideoFrame. The texture is resized automatically when the image dimensions change.

        Args:
            image (numpy.ndarray | av.VideoFrame):
                Source image to upload.

        Returns:
            None
        """

        # Lazily create the texture.
        if not self.texture:
            self.create()

        # Convert PyAV frame to RGB NumPy array.
        if isinstance(image, av.VideoFrame):
            image = image.to_ndarray(format="rgb24")

        # Ensure contiguous memory.
        image = numpy.ascontiguousarray(image)

        # Extract image dimensions.
        height, width = image.shape[:2]

        # Bind the texture.
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)

        # Reallocate storage if the image size changes.
        if width != self.width or height != self.height:

            self.width = width
            self.height = height

            GL.glTexImage2D(
                GL.GL_TEXTURE_2D,
                0,
                self.internal_format,
                width,
                height,
                0,
                self.pixel_format,
                self.pixel_type,
                None,
            )

        # Use byte-aligned pixel rows.
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)

        # Upload image pixels.
        GL.glTexSubImage2D(
            GL.GL_TEXTURE_2D,
            0,
            0,
            0,
            width,
            height,
            self.pixel_format,
            self.pixel_type,
            image,
        )

        # Unbind the texture.
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

    def bind(self, unit=0):
        """Bind the texture for rendering.

        Args:
            unit (int, optional):
                Texture unit index. Defaults to ``0``.

        Returns:
            None
        """

        # Activate the requested texture unit.
        GL.glActiveTexture(GL.GL_TEXTURE0 + unit)

        # Bind the texture.
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)

    def release(self):
        """Unbind the texture.

        Returns:
            None
        """

        # Unbind the texture.
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)


if __name__ == "__main__":
    pass
