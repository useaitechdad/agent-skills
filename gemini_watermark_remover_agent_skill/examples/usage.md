# Example Usages

## Basic Execution
Command:
```bash
python scripts/remove_watermark.py /path/to/my_image.webp --output /path/to/clean_image.webp
```

Output:
```text
Removed watermark successfully in 1 passes (residual-low).
Output saved to: /path/to/clean_image.webp
```

## JSON Output for Agent Context
Command:
```bash
python scripts/remove_watermark.py /path/to/my_image.png --json
```

Output:
```json
{
  "applied": true,
  "file": "/path/to/my_image_clean.png",
  "decision": {
    "logo_size": 96,
    "margin_right": 64,
    "margin_bottom": 64
  },
  "position": {
    "x": 864,
    "y": 864,
    "width": 96,
    "height": 96
  },
  "initial_score": 0.5891398579051466,
  "passes_applied": 1,
  "stop_reason": "residual-low",
  "pass_details": [
    {
      "pass": 1,
      "after_score": 0.0512,
      "near_black_ratio": 0.0123
    }
  ]
}
```

## No Watermark Detected
Command:
```bash
python scripts/remove_watermark.py /path/to/random_image.jpg --json
```

Output:
```json
{"applied": false, "reason": "No watermark detected", "score": -0.1234}
```

