# Video Models

Capability columns: **T2V** = Text-to-Video, **I2V** = Single-Image-to-Video,
**SE** = Start/End Frame Interpolation, **MI** = Multi-Image Reference Video.

| Model | model_id | T2V | I2V | SE | MI |
|-------|----------|-----|-----|----|----|
| Seedance 1.0 Lite | `doubao-seedance-1-0-lite` | Y | Y | Y | - |
| Seedance 1.0 Pro Fast | `doubao-seedance-1-0-pro-fast` | Y | Y | - | - |
| Seedance 1.0 Pro | `doubao-seedance-1-0-pro` | Y | Y | - | - |
| Seedance 1.5 Pro | `doubao-seedance-1-5-pro` | Y | Y | Y | - |
| Kling 2.1 Master | `kling-v2-1-master` | Y | Y | - | - |
| Kling 2.1 | `kling-v2-1` | Y | Y | - | - |
| Kling 2.5 Turbo | `kling-v2-5-turbo` | Y | Y | - | Y |
| Kling 3.0 Omni | `kling-v3-omni` | - | - | - | Y |
| Kling 3.0 | `kling-v3` | Y | Y | - | - |
| Kling O1 | `kling-video-o1` | Y | Y | Y | Y |
| Kling 2.6 | `klingv2-6` | Y | Y | - | - |
| Hailuo 02 | `minimax-hailuo-02` | Y | Y | - | - |
| Hailuo 2.3 Fast | `minimax-hailuo-2.3-fast` | - | Y | - | - |
| Hailuo 2.3 | `minimax-hailuo-2.3` | Y | Y | - | - |
| Pixverse v4.5 | `pixverse-v4.5` | Y | Y | - | - |
| Veo 3 Fast | `veo-3.0-fast-generate-preview` | Y | Y | - | - |
| Veo 3 | `veo-3.0-generate-preview` | Y | Y | - | - |
| Veo 3.1 Fast | `veo-3.1-fast-generate-preview` | Y | Y | - | - |
| Veo 3.1 | `veo-3.1-generate-preview` | Y | Y | Y | Y |
| Vidu 2.0 | `vidu-2-0` | - | Y | Y | Y |
| Vidu Q2 Turbo | `viduq2-turbo` | - | - | Y | Y |
| Vidu Q2 | `viduq2` | - | - | - | Y |
| Wan 2.5 | `wan-2-5-video` | Y | Y | - | - |
| Wan 2.6 | `wan-2-6-video` | Y | Y | - | - |

## Resolution Support

- `720p`
- `1080p` (default)
- `auto`

## Aspect Ratio Support

`1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `9:16`, `16:9`, `21:9`, `auto`

- **Text-to-Video**: defaults to `16:9`
- **Image-conditioned tasks** (I2V / SE / MI): defaults to `auto` (preserves source image ratio)

## Duration

Model-dependent. Common supported values: 4, 5, 6, 8, 10 seconds. SDK default: `5`.

If the requested duration is not supported by the model, round to the nearest supported value and inform the user.

## Audio

All video tasks support `audio_enable` (bool, default `False`).

When `audio_enable=True`, you can optionally provide `audio_prompt` (str) via `**extra` kwargs to describe the desired audio:

```python
result = await text2video(
    client,
    prompt="A jazz band performing",
    model_id="kling-v3",
    audio_enable=True,
    audio_prompt="Smooth jazz with saxophone",  # via **extra
)
```

If `audio_enable=False`, do **not** include `audio_prompt`.
