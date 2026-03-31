# Watermark Removal Algorithm

## Reverse Alpha Blending
Gemini adds watermarks using standard alpha compositing:
`watermarked = α × logo_color + (1 - α) × original_pixel`

Because the logo is purely white (`logo_color = 255`), we can invert the formula to recover the original pixel exactly:
`original_pixel = (watermarked - α × 255) / (1 - α)`

This requires a perfect pre-calculated alpha map (`α`) of the watermark itself.

## Multi-Pass
Some stronger watermarks require multiple passes of the above formula to fully eliminate the artifact. The script does this up to 4 times, checking the spatial correlation after each pass. If the spatial correlation drops below a specific threshold (e.g. 0.25), the watermark is considered removed and the pass loop terminates.

## Watermark Configurations
Gemini uses finite generation sizes, organized into "tiers" like 0.5k, 1k, 2k, and 4k. 
The size of the watermark correlates with the tier of the output.
- 1k, 2k, 4k tier sizes default to a `96x96` watermark with `margin_right: 64, margin_bottom: 64`.
- 0.5k tier sizes (and some mobile optimized outputs) use a `48x48` watermark with `margin_right: 32, margin_bottom: 32`.

The Python script uses a pre-populated map of these exact pixel dimensions to instantly classify the incoming file and fetch the correct alpha map.
