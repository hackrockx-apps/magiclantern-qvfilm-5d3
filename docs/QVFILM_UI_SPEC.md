# QVFilm Magic Lantern — 5D3 Cinema RAW Edition

## v0.1.0 baseline

### Target body and firmware

- Camera: Canon EOS 5D Mark III (5D3).
- Target Magic Lantern platform: `5D3.123`.
- The camera's photographed firmware line reads `9.0.1 A6(34)`.
- ExifTool's Canon MPU mapping identifies 5D III `1.2.3` as internal MPU `9.0.1`, revision `A6`. This is a strong match for Canon firmware 1.2.3, not a Canon firmware version numbered 9.0.1.
- Runtime camera detection in the firmware (`is_camera("5D3", "1.2.3")`) remains the final compatibility check. Do not flash or update Canon firmware as part of this project.

### Source baseline

- Fork: `hackrockx-apps/magiclantern-qvfilm-5d3`
- Upstream: `arnaud-sintes/magiclantern_asintes`
- Base branch: `master`
- Working branch: `qvfilm/v0.1.0-ui-prototype`
- Relevant source:
  - `modules/mlv_lite/mlv_lite.c`
  - `modules/mlv_lite/Makefile`
  - `src/menu.h`
  - `src/menu.c`
  - `src/bmp.h`
  - `platform/5D3.123/features.h`
  - `platform/5D3.123/Makefile`

### Verified implementation hooks

- MLV Lite registers the existing RAW controls under the `Movie` menu in `raw_rec_init()`.
- The module already detects 5D3 firmware 1.1.3 and 1.2.3 separately.
- The RAW width presets include 3072 pixels.
- RAW output modes include native 14-bit, uncompressed 12/10-bit, 14-bit lossless, 12-bit lossless and auto bit-depth lossless.
- Magic Lantern's menu API supports custom drawing with `menu_display_info.custom_drawing = CUSTOM_DRAW_THIS_MENU`.
- The bitmap API provides `bmp_fill`, `bmp_printf`, `big_bmp_printf`, `FONT_MED_LARGE`, `FONT_LARGE` and the standard color palette.
- The normal bitmap canvas is 720x480. Drawing must stay within the documented bounds.

### UI direction

Create a dedicated `QVFIL` top-level tab while retaining the original `Movie` menu as a fallback/reference.

Planned screens:
1. Dashboard — resolution, aspect ratio, FPS, RAW bit-depth/compression, recording state, card/buffer status, exposure summary.
2. Record — simplified access to validated MLV Lite settings.
3. Exposure — ISO, shutter, aperture and white-balance readouts; controls only where a stable API is available.
4. Monitor — only monitoring aids confirmed to work on 5D3 firmware 1.2.3.
5. System — card, buffer, battery and firmware diagnostics where reliable APIs exist.

Visual design:
- Black background; high-contrast white labels.
- Yellow selection/highlight.
- Red only for actionable warnings/errors.
- Large, readable typography; concise labels; no unnecessary animation.
- ASCII/English labels for the first build until font encoding support is verified.
- Camera LCD is the primary target; do not assume touch input.

### Safety and engineering constraints

- Preserve the original `Movie` menu and all RAW recording algorithms.
- Do not modify `mlv_rec`, EDMAC, compression, buffer scheduling, or camera-specific register code for the first UI milestone.
- Do not expose a setting in QVFIL unless it maps to a real, validated MLV Lite configuration variable or API.
- Do not display guessed values. Unknown telemetry must be labelled unavailable or omitted.
- Do not install experimental firmware on the camera before a successful matching-platform build and offline review.
- Test first on a dedicated, backed-up card. Keep the original Magic Lantern card/build untouched.
- Treat build success, menu visibility, and actual RAW recording stability as separate acceptance gates.

### v0.1.0 acceptance criteria

- Confirm the fork builds the unmodified `5D3.123` target.
- Record the toolchain/build instructions and exact source revision.
- Add the QVFilm UI in an isolated implementation area.
- Keep the original RAW menu and recording path unchanged.
- Produce a reviewable UI prototype before any camera installation.

### Explicit non-goals for v0.1.0

- No changes to Canon firmware.
- No firmware downgrade/upgrade procedure.
- No claims that every 3K aspect ratio or frame rate is sustainable.
- No unverified waveform, false-colour, zebra, or focus-peaking implementation.
- No camera installation until the build is verified.
