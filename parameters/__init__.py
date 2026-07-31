"""
Copyright (c) 2026, Motion-Craft Technology All rights reserved.

Author:
    Subin. Gopi (subing85@gmail.com).

Module:
    ./constants/__init__.py

Description:
    Parameter definitions for the Viewline viewer.

    This module defines reusable parameter objects used by the Viewline display system.
    Each parameter stores metadata such as limits, default values, slider conversion, and optional color information.
    These parameter groups are shared by the Display, Style, and Filter widgets.

Responsibilities:
    - Define reusable viewer parameters.
    - Store default values and limits.
    - Convert values to and from Qt sliders.
    - Clamp values within valid ranges.
    - Store optional color information.
    - Provide parameter collections for UI widgets.

Features:
    - Floating-point parameter support.
    - Automatic value clamping.
    - QSlider integer conversion.
    - Reset to default values.
    - Optional color parameters.
    - Reusable parameter collections.

Architecture:
    ParametereSetting
        ├── DisplaySettings
        ├── StyleSettings
        └── FilterSettings

Nodes:
    ParametereSetting
    DisplaySettings
    StyleSettings
    FilterSettings
"""

from __future__ import absolute_import


class ParametereSetting(object):
    """Represents a single configurable viewer parameter.

    This class stores all information required by the user interface and shader system, including value limits,
    slider conversion, default values, and optional color controls.

    Attributes:
        name (str):
            Internal parameter name.

        label (str):
            User-visible parameter label.

        control (str):
            Shader uniform name.

        color_control (str):
            Shader uniform used for color values.

        minimum (float):
            Minimum allowed value.

        maximum (float):
            Maximum allowed value.

        default (float):
            Default parameter value.

        decimals (int):
            Number of decimal places used for slider scaling.

        color (tuple | None):
            Normalized RGB color.

        is_color (bool):
            True if the parameter supports colors.
    """

    def __init__(self, **kwargs):
        """Initialize a viewer parameter.

        Args:
            *args:
                Positional arguments containing parameter information in the following order:

                name (str)
                label (str)
                control (str)
                minimum (float)
                maximum (float)
                default (float)

            **kwargs:
                color_control (str, optional):
                    Shader color uniform.

                decimals (int, optional):
                    Number of decimal places.
        """

        # Store the internal parameter name.
        self.name = kwargs.get("name")

        # Store the user-visible label.
        self.label = kwargs.get("label")

        # Store the shader uniform name.
        self.control = kwargs.get("control")

        # Optional shader color uniform.
        self.color_control = kwargs.get("color_control")

        # Minimum allowed value.
        self.minimum = kwargs.get("minimum")

        # Maximum allowed value.
        self.maximum = kwargs.get("maximum")

        # Default parameter value.
        self.default = kwargs.get("default")

        # Decimal precision used for sliders.
        self.decimals = kwargs.get("decimals") or 2

        # Current parameter value.
        self._value = self.default

        # Initialize optional color support.
        if self.color_control:
            # Default overlay color.
            self.color = (1.0, 0.0, 0.0)

            # Enable color mode.
            self.is_color = True
        else:
            # No associated color.
            self.color = None

            # Disable color mode.
            self.is_color = False

    @property
    def value(self):
        """Return the current parameter value.

        Returns:
            float:
                Current parameter value.
        """

        # Return the stored value.
        return self._value

    @value.setter
    def value(self, value):
        """Assign a new parameter value.

        The assigned value is automatically clamped between the configured minimum and maximum limits.

        Args:
            value (float):
                New parameter value.
        """

        # Clamp the value within valid limits.
        self._value = max(self.minimum, min(float(value), self.maximum))

    def reset(self):
        """Restore the default parameter value."""

        # Reset to the default value.
        self.value = self.default

    def slider_range(self):
        """Return the QSlider integer range.

        Floating-point values are converted into integer values based on the configured decimal precision.

        Returns:
            tuple[int, int]:
                Minimum and maximum slider values.
        """

        # Calculate the scaling factor.
        scale = 10**self.decimals

        # Return the slider range.
        return (int(self.minimum * scale), int(self.maximum * scale))

    def slider_value(self):
        """Convert the current value into a slider value.

        Returns:
            int:
                Integer value used by QSlider.
        """

        # Calculate the scaling factor.
        scale = 10**self.decimals

        # Convert to an integer slider value.
        return int(round(self.value * scale))

    def value_from_slider(self, value):
        """Convert a QSlider value into a float.

        Args:
            value (int):
                Slider value.

        Returns:
            float:
                Floating-point parameter value.
        """

        # Calculate the scaling factor.
        scale = 10**self.decimals

        # Convert to floating-point.
        return float(value) / scale

    def set_color(self, color):
        """Set the parameter color.

        Args:
            color (tuple):
                Normalized RGB color.
        """

        # Store the selected color.
        self.color = color


class DisplaySettings(object):
    """Collection of display adjustment parameters.

    This class groups together all display-related parameters used by the 2D viewer.
    These settings control basic image appearance such as exposure, gamma, brightness, contrast, saturation, gain, offset, and overlay opacity.

    The parameters are shared with the Color Filter widget and are passed directly to the OpenGL display shader.

    Attributes:
        exposure (ParametereSetting):
            Exposure adjustment.

        gamma (ParametereSetting):
            Gamma correction.

        brightness (ParametereSetting):
            Brightness adjustment.

        contrast (ParametereSetting):
            Contrast adjustment.

        saturation (ParametereSetting):
            Color saturation adjustment.

        hue (ParametereSetting):
            Hue rotation adjustment.

        gain (ParametereSetting):
            RGB gain multiplier.

        offset (ParametereSetting):
            RGB offset value.

        overlay_opacity (ParametereSetting):
            Overlay opacity and color control.
    """

    def __init__(self):
        """Initialize all display parameters."""

        # Exposure adjustment.
        self.exposure = ParametereSetting(
            name="exposure",
            label="Exposure",
            control="uExposure",
            minimum=-10.0,
            maximum=10.0,
            default=0.0,
            decimals=2,
        )

        # Gamma correction.
        self.gamma = ParametereSetting(
            name="gamma",
            label="Gamma",
            control="uGamma",
            minimum=0.1,
            maximum=5.0,
            default=1.0,
            decimals=2,
        )

        # Brightness adjustment.
        self.brightness = ParametereSetting(
            name="brightness",
            label="Brightness",
            control="uExposure",
            minimum=-1.0,
            maximum=1.0,
            default=0.0,
            decimals=2,
        )

        # Contrast adjustment.
        self.contrast = ParametereSetting(
            name="contrast",
            label="Contrast",
            control="uContrast",
            minimum=0.0,
            maximum=3.0,
            default=1.0,
            decimals=2,
        )

        # Saturation adjustment.
        self.saturation = ParametereSetting(
            name="saturation",
            label="Saturation",
            control="uSaturation",
            minimum=0.0,
            maximum=2.0,
            default=1.0,
            decimals=2,
        )

        # Hue rotation.
        self.hue = ParametereSetting(
            name="hue",
            label="Hue",
            control="uHue",
            minimum=-180.0,
            maximum=180.0,
            default=0.0,
            decimals=1,
        )

        # Gain multiplier.
        self.gain = ParametereSetting(
            name="gain",
            label="Gain",
            control="uGain",
            minimum=0.0,
            maximum=4.0,
            default=1.0,
            decimals=2,
        )

        # Color offset.
        self.offset = ParametereSetting(
            name="offset",
            label="Offset",
            control="uOffset",
            minimum=-1.0,
            maximum=1.0,
            default=0.0,
            decimals=2,
        )

        # Overlay opacity and color.
        self.overlay_opacity = ParametereSetting(
            name="overlay",
            label="Overlay",
            control="uOverlayOpacity",
            color_control="uOverlayColor",
            minimum=0.0,
            maximum=1.0,
            default=0.0,
            decimals=2,
        )

    def parameters(self):
        """Return all display parameters.

        The returned list preserves the display order used by the Color Filter widget.

        Returns:
            list[ParametereSetting]:
                Ordered display parameter collection.
        """

        # Return all display parameters.
        result = [
            self.exposure,
            self.gamma,
            self.brightness,
            self.contrast,
            self.saturation,
            self.hue,
            self.gain,
            self.offset,
            self.overlay_opacity,
        ]

        return result


class StyleSettings(object):
    """Collection of image style effect parameters.

    This class groups together all style-related parameters used by the Viewline viewer. These parameters control artistic image effects that are applied by the display shader.

    The settings are shared with the Color Filter widget and allow users to adjust stylized rendering effects in real time.

    Attributes:
        sepia (ParametereSetting):
            Sepia tone intensity.

        negate (ParametereSetting):
            Color inversion amount.

        posterize (ParametereSetting):
            Posterization level.

        gradient (ParametereSetting):
            Gradient mapping intensity.

        cartoon (ParametereSetting):
            Cartoon effect intensity.
    """

    def __init__(self):
        """Initialize all style parameters."""

        # Sepia tone effect.
        self.sepia = ParametereSetting(
            name="sepia",
            label="Sepia",
            control="uSepia",
            minimum=-0.0,
            maximum=1.0,
            default=0.0,
            decimals=2,
        )

        # Color inversion effect.
        self.negate = ParametereSetting(
            name="negate",
            label="Negate Colors",
            control="uNegate",
            minimum=0.0,
            maximum=1.0,
            default=0.0,
            decimals=2,
        )

        # Posterization effect.
        self.posterize = ParametereSetting(
            name="posterize",
            label="Posterize",
            control="uPosterize",
            minimum=0.0,
            maximum=32.0,
            default=0.0,
            decimals=0,
        )

        # Gradient mapping effect.
        self.gradient = ParametereSetting(
            name="gradient",
            label="Gradient",
            control="uGradient",
            minimum=0.0,
            maximum=1.0,
            default=0.0,
            decimals=2,
        )

        # Cartoon rendering effect.
        self.cartoon = ParametereSetting(
            name="cartoon",
            label="Cartoon",
            control="uCartoon",
            minimum=0.0,
            maximum=1.0,
            default=0.0,
            decimals=2,
        )

    def parameters(self):
        """Return all style parameters.

        The returned list preserves the display order used by the Style tab of the Color Filter widget.

        Returns:
            list[ParametereSetting]:
                Ordered collection of style parameters.
        """

        # Return all style parameters.
        return [
            self.sepia,
            self.negate,
            self.posterize,
            self.gradient,
            self.cartoon,
        ]


class FilterSettings(object):
    """Collection of image filter parameters.

    This class groups together all image filter parameters used by the Viewline viewer.
    These parameters control image processing effects that are applied after the image is rendered, allowing users to enhance or soften the final result.

    The settings are shared with the Color Filter widget and are passed directly to the OpenGL filter shader.

    Attributes:
        sharpen (ParametereSetting):
            Image sharpening intensity.

        blur (ParametereSetting):
            Blur filter intensity.

        motion_blur (ParametereSetting):
            Motion blur intensity.

        noise (ParametereSetting):
            Procedural noise intensity.

        denoiser (ParametereSetting):
            Image denoising intensity.
    """

    def __init__(self):
        """Initialize all filter parameters."""

        # Image sharpening amount.
        self.sharpen = ParametereSetting(
            name="sharpen",
            label="Sharpen",
            control="uSharpen",
            minimum=0.0,
            maximum=10.0,
            default=0.0,
            decimals=2,
        )

        # Blur filter amount.
        self.blur = ParametereSetting(
            name="blur",
            label="Blur",
            control="uBlur",
            minimum=0.0,
            maximum=1.0,
            default=0.0,
            decimals=2,
        )

        # Motion blur amount.
        self.motion_blur = ParametereSetting(
            name="motion_blur",
            label="Motion Blur",
            control="uMotionBlur",
            minimum=0.0,
            maximum=1.0,
            default=0.0,
            decimals=2,
        )

        # Noise effect amount.
        self.noise = ParametereSetting(
            name="noise",
            label="Noise",
            control="uNoise",
            minimum=0.0,
            maximum=1.0,
            default=0.0,
            decimals=2,
        )

        # Image denoising amount.
        self.denoiser = ParametereSetting(
            name="denoiser",
            label="Denoiser",
            control="uDenoiser",
            minimum=0.0,
            maximum=1.0,
            default=0.0,
            decimals=2,
        )

    def parameters(self):
        """Return all enabled filter parameters.

        The returned list preserves the display order used by the Filter tab.
        Parameters that are still under development can be temporarily omitted without affecting the remaining UI.

        Returns:
            list[ParametereSetting]:
                Ordered collection of enabled filter parameters.
        """

        # Return the enabled filter parameters.
        return [
            self.sharpen,
            self.blur,
            # Temporarily disabled until implemented.
            # self.motion_blur,
            self.noise,
            self.denoiser,
        ]


if __name__ == "__main__":
    pass
