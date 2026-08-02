
<p style="text-align: justify;">
<span style="color:green;">Viewline</span> is a modern GPU-accelerated media viewer for animation, VFX, and OpenUSD workflows. It provides high-performance playback of video files, image sequences, and OpenUSD scenes through a unified OpenGL-based viewer.
</p>

---

### Supported formats:

>**Video**
>>* MP4
>>* MOV
>>* AVI

>**Image Sequences**
>>* PNG
>>* JPEG
>>* EXR

>**3D Scene**
>>* USD
>>* USDA
>>* USDC
>>* USDZ

---

### Color Management
<p style="text-align: justify;">
Viewline integrates OpenColorIO (OCIO) for consistent color management across all supported media types.
</p>

>**Features**
>>* <span style="color:green;">OpenColorIO integration</p>
>>* <span style="color:green;">ACES workflow architecture</p>
>>* <span style="color:green;">Input color space selection</p>
>>* <span style="color:green;">Display transform selection</p>

>**Recommended Configuration**
>>ACES 1.3 OCIO Config

---

### System Architecture

```text

                        Media Source

             (Video / Image Sequence / OpenUSD)
                              │
                              ▼
                        Media Reader
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
        Video / Image Pipeline       OpenUSD Pipeline
                │                           │
                ▼                           ▼
            GPU Upload                Hydra Renderer
                │                           │
                ▼                           ▼
            GLTexture                 Render Delegate
                │                           │
                ▼                           ▼
            GLShader                     GLScreen
                │                           │
                └─────────────┬─────────────┘
                              ▼
                          GLScreen
                              │
                              ▼
                        QOpenGLWidget
                              │
                              ▼
               Display Output / Interactive 3D View

```


### Rendering Architecture
<p style="text-align: justify;">
Viewline uses a fully GPU-based rendering architecture where each rendering component has a dedicated responsibility.
</p>

### Core Components
> <strong>QOpenGLWidget</strong>
>>* Creates the OpenGL context
>>* Handles resize events
>>* Displays the rendered output
>>* Processes user interaction

> <strong>GLScreen</strong> 
>>* Responsible for:
>>>* Render pass management
>>>* Frame presentation
>>>* Viewport updates
>>>* GPU resource coordination

> <strong>GLTexture</strong>
>>* Responsible for:
>>>* GPU texture allocation
>>>* Texture uploads
>>>* Texture updates
>>>* Texture lifecycle management

> <strong>GLShader</strong>
>>* Responsible for:
>>>* Shader compilation
>>>* Color processing
>>>* OpenColorIO transforms
>>>* GPU rendering

---

### Viewer Settings
><strong>Video / Image</strong>

>> <strong>Display Settings</strong>

>>>* Exposure
>>>* Gamma
>>>* Brightness
>>>* Contrast
>>>* Saturation
>>>* Hue
>>>* Gain
>>>* Offset
>>>* Overlay

>> <strong>Style Settings</strong>

>>>* Sepia
>>>* Negative
>>>* Posterize
>>>* Gradient
>>>* Cartoon

>> <strong>Filter Settings</strong>

>>>* Sharpen
>>>* Blur
>>>* Motion Blur
>>>* Noise
>>>* Denoiser

><strong>OpenUSD Viewer</strong>

>> <strong>Display Settings</strong>

>>> <strong>Shading Mode</strong>

>>>>* Shaded Smooth
>>>>* Shaded Flat
>>>>* Wireframe
>>>>* Wireframe on Surface
>>>>* Points
>>>>* Geom Only
>>>>* Geom Smooth
>>>>* Geom Flat

>>> <strong>Complexity</strong>

>>>>* Low
>>>>* Medium
>>>>* High
>>>>* Very High

>>> <strong>Display Purposes</strong>
>>>>* Guide
>>>>* Proxy
>>>>* Render

>>> <strong>Enable Scene Materials</strong>

>> <strong>Camera</strong>

>>>* Default Camera
>>>* Stage Cameras

---

### Rendering Backends

| Media Type | Reader | GPU Backend |
|------------|--------|-------------|
| Video | PyAV | Hardware Decode → OpenGL |
| Image Sequence | OpenImageIO | OpenGL Texture Rendering |
| OpenUSD | OpenUSD | Hydra Rendering |


### Python Requirements

>[Python-3.10.10](https://www.python.org/downloads/release/python-31010/) or +


### Dependencies

>| Library     | Purpose                 |
>| ----------- | ----------------------- |
>| PySide6     | UI framework            |
>| PyOpenGL    | OpenGL rendering        |
>| NumPy       | Image buffer processing |
>| PyAV        | Video decoding          |
>| OpenImageIO | Image sequence reading  |
>| OpenColorIO | Color management        |
>| OpenUSD     | 3D Objects              |


### Required Libraries

```yml

    requests: 2.32.2

        certifi: 2024.2.2 or +
        idna: 3.7 or +
        urllib3: 2.2.1 or +
        charset-normalizer: 3.3.2 or +

    PySide6: 6.9.0 or +

        shiboken6: 6.9.0 or +
        PySide6-Essentials: 6.9.0 or +
        PySide6-Addons: 6.9.0 or +

    pyqtdarktheme: 2.1.0 or +

        darkdetect: 0.7.1 or +

    OpenImageIO: 3.0.4.0 or +

    PyOpenGL: 3.1.9 or +

    opencolorio: 2.5.0 or +

    av: 17.0.0 or +

    OpenUSD: 26.05

    numpy: 1.26.4 or +

```

---

### Recommended OCIO Config ACES 1.3

> Official repository:

> <https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES>


### Open EXR Support

> The player currently supports:

> * Single-layer EXR
> * Multi-layer EXR
> * RGB layer extraction
> * Basic AOV switching

> The EXR reader automatically searches for valid RGB layers.

> Example supported channel patterns:
```text
    R G B
    beauty.R beauty.G beauty.B
    rgba.R rgba.G rgba.B
    Ci.R Ci.G Ci.B
```

---

### Current Limitations

This project is currently an early playback framework.

Known limitations:

* No threaded decoding
* Image decoding may load many frames into memory
* EXR playback currently converts float images into uint8 previews
* No HDR display pipeline yet

---

### Design Notes
* Fully GPU-based rendering pipeline.
* Unified viewer for video, image sequences, and OpenUSD.
* Modular rendering architecture.
* OpenGL shaders used throughout the rendering pipeline.
* Hydra-based rendering for OpenUSD scenes.
* OpenColorIO integration for color-managed workflows.
* No legacy glDrawPixels() rendering.
* Extensible architecture for future rendering backends.


---

**© Support, subing85@gmail.com.**

---
