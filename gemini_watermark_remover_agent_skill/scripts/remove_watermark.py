#!/usr/bin/env python3
"""
Google Gemini Watermark Remover
Removes the visible watermark from Gemini-generated images losslessly using
Reverse Alpha Blending.
"""

import sys
import argparse
import json
import os
import math
import numpy as np
from PIL import Image

# Algorithm Constants
ALPHA_NOISE_FLOOR = 3.0 / 255.0
ALPHA_THRESHOLD = 0.002
MAX_ALPHA = 0.99
LOGO_VALUE = 255.0
DEFAULT_MAX_PASSES = 4
NEAR_BLACK_THRESHOLD = 5

def create_gemini_sizes():
    return [
        # 1k
        {"width": 1024, "height": 1024, "tier": "1k"},
        {"width": 512, "height": 2064, "tier": "1k"},
        {"width": 352, "height": 2928, "tier": "1k"},
        {"width": 848, "height": 1264, "tier": "1k"},
        {"width": 1264, "height": 848, "tier": "1k"},
        {"width": 896, "height": 1200, "tier": "1k"},
        {"width": 2064, "height": 512, "tier": "1k"},
        {"width": 1200, "height": 896, "tier": "1k"},
        {"width": 928, "height": 1152, "tier": "1k"},
        {"width": 1152, "height": 928, "tier": "1k"},
        {"width": 2928, "height": 352, "tier": "1k"},
        {"width": 768, "height": 1376, "tier": "1k"},
        {"width": 1376, "height": 768, "tier": "1k"},
        {"width": 1408, "height": 768, "tier": "1k"},
        {"width": 1584, "height": 672, "tier": "1k"},
        
        # 2k
        {"width": 2048, "height": 2048, "tier": "2k"},
        {"width": 512, "height": 2048, "tier": "2k"},
        {"width": 384, "height": 3072, "tier": "2k"},
        {"width": 1696, "height": 2528, "tier": "2k"},
        {"width": 2528, "height": 1696, "tier": "2k"},
        {"width": 1792, "height": 2400, "tier": "2k"},
        {"width": 2048, "height": 512, "tier": "2k"},
        {"width": 2400, "height": 1792, "tier": "2k"},
        {"width": 1856, "height": 2304, "tier": "2k"},
        {"width": 2304, "height": 1856, "tier": "2k"},
        {"width": 3072, "height": 384, "tier": "2k"},
        {"width": 1536, "height": 2752, "tier": "2k"},
        {"width": 2752, "height": 1536, "tier": "2k"},
        {"width": 3168, "height": 1344, "tier": "2k"},

        # 0.5k
        {"width": 512, "height": 512, "tier": "0.5k"},
        {"width": 256, "height": 1024, "tier": "0.5k"},
        {"width": 192, "height": 1536, "tier": "0.5k"},
        {"width": 424, "height": 632, "tier": "0.5k"},
        {"width": 632, "height": 424, "tier": "0.5k"},
        {"width": 448, "height": 600, "tier": "0.5k"},
        {"width": 1024, "height": 256, "tier": "0.5k"},
        {"width": 600, "height": 448, "tier": "0.5k"},
        {"width": 464, "height": 576, "tier": "0.5k"},
        {"width": 576, "height": 464, "tier": "0.5k"},
        {"width": 1536, "height": 192, "tier": "0.5k"},
        {"width": 384, "height": 688, "tier": "0.5k"},
        {"width": 688, "height": 384, "tier": "0.5k"},
        {"width": 792, "height": 168, "tier": "0.5k"},
    ]

# The default watermark configurations matching the JS catalog
WATERMARK_CONFIGS = {
    '0.5k': {'logo_size': 48, 'margin_right': 32, 'margin_bottom': 32},
    '1k': {'logo_size': 96, 'margin_right': 64, 'margin_bottom': 64},
    '2k': {'logo_size': 96, 'margin_right': 64, 'margin_bottom': 64},
    '4k': {'logo_size': 96, 'margin_right': 64, 'margin_bottom': 64},
}

gemini_sizes = create_gemini_sizes()

def load_alpha_maps(base_dir):
    try:
        a48 = np.load(os.path.join(base_dir, 'alpha_maps', 'alpha_48.npy'))
        a96 = np.load(os.path.join(base_dir, 'alpha_maps', 'alpha_96.npy'))
        # Reshape flat arrays to 2D
        return {
            48: a48.reshape((48, 48)),
            96: a96.reshape((96, 96))
        }
    except Exception as e:
        print(f"Error loading alpha maps: {e}", file=sys.stderr)
        sys.exit(1)

def detect_watermark_config(width, height):
    # Match official exact sizes
    for entry in gemini_sizes:
        if width == entry['width'] and height == entry['height']:
            return WATERMARK_CONFIGS[entry['tier']]
    
    # Fallback heuristic
    if width > 1024 and height > 1024:
        return {'logo_size': 96, 'margin_right': 64, 'margin_bottom': 64}
    return {'logo_size': 48, 'margin_right': 32, 'margin_bottom': 32}

def calc_near_black_ratio(region_rgb):
    """Calculate the ratio of pixels that are near black (<=5 on all RGB channels)."""
    r, g, b = region_rgb[:,:,0], region_rgb[:,:,1], region_rgb[:,:,2]
    near_black_mask = (r <= NEAR_BLACK_THRESHOLD) & (g <= NEAR_BLACK_THRESHOLD) & (b <= NEAR_BLACK_THRESHOLD)
    return np.count_nonzero(near_black_mask) / (region_rgb.shape[0] * region_rgb.shape[1])

def ncc(a, b):
    """Normalized cross-correlation of two 1D or 2D arrays."""
    a_flat = a.flatten()
    b_flat = b.flatten()
    if a_flat.size != b_flat.size or a_flat.size == 0:
        return 0.0
    
    a_mean = np.mean(a_flat)
    b_mean = np.mean(b_flat)
    a_var = np.var(a_flat)
    b_var = np.var(b_flat)
    
    den = math.sqrt(a_var * b_var) * a_flat.size
    if den < 1e-8:
        return 0.0
        
    num = np.sum((a_flat - a_mean) * (b_flat - b_mean))
    return num / den

def compute_spatial_correlation(rgb_region, alpha_map):
    """Verify watermark presence by checking correlation with expected pattern."""
    gray = 0.2126 * rgb_region[:,:,0] + 0.7152 * rgb_region[:,:,1] + 0.0722 * rgb_region[:,:,2]
    gray = gray / 255.0
    return ncc(gray, alpha_map)

def remove_watermark_pass(img_array, alpha_map, x, y, size, alpha_gain=1.0):
    """Perform reverse alpha blending to remove the watermark layer."""
    result = img_array.copy()
    region = result[y:y+size, x:x+size, 0:3].astype(np.float32)

    # Process alpha map like JS (denoise using NOISE_FLOOR and clip)
    denoised_alpha = np.maximum(0, alpha_map - ALPHA_NOISE_FLOOR) * alpha_gain
    active_mask = denoised_alpha >= ALPHA_THRESHOLD
    
    alpha = np.minimum(alpha_map * alpha_gain, MAX_ALPHA)
    one_minus_alpha = 1.0 - alpha
    
    # Process only rgb
    for c in range(3):
        watermarked = region[:,:,c]
        original = (watermarked - alpha * LOGO_VALUE) / one_minus_alpha
        region[:,:,c] = np.where(active_mask, np.clip(np.round(original), 0, 255), watermarked)
    
    result[y:y+size, x:x+size, 0:3] = region.astype(np.uint8)
    return result

def main():
    parser = argparse.ArgumentParser(description="Remove Gemini watermark.")
    parser.add_argument("input", help="Path to the input image")
    parser.add_argument("--output", help="Path to save the output image")
    parser.add_argument("--json", action="store_true", help="Output metadata as JSON")
    parser.add_argument("--max-passes", type=int, default=DEFAULT_MAX_PASSES, help="Max removal passes (default 4)")
    args = parser.parse_args()

    out_path = args.output
    if not out_path:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}_clean{ext}"

    script_dir = os.path.dirname(os.path.abspath(__file__))
    alpha_maps = load_alpha_maps(script_dir)

    # 1. Load image
    try:
        img = Image.open(args.input).convert('RGBA')
    except Exception as e:
        print(f"Failed to open image: {e}", file=sys.stderr)
        sys.exit(1)
        
    width, height = img.size
    img_array = np.array(img)

    # 2. Detect candidate configs
    config48 = {'logo_size': 48, 'margin_right': 32, 'margin_bottom': 32}
    config96 = {'logo_size': 96, 'margin_right': 64, 'margin_bottom': 64}
    
    primary_config = detect_watermark_config(width, height)
    alternate_config = config48 if primary_config['logo_size'] == 96 else config96
    
    best_config = primary_config
    best_score = -1.0
    
    for candidate_config in [primary_config, alternate_config]:
        c_size = candidate_config['logo_size']
        if c_size not in alpha_maps: continue
            
        c_x = width - candidate_config['margin_right'] - c_size
        c_y = height - candidate_config['margin_bottom'] - c_size
        
        if c_x < 0 or c_y < 0 or c_x + c_size > width or c_y + c_size > height:
            continue
            
        c_region = img_array[c_y:c_y+c_size, c_x:c_x+c_size, 0:3]
        score = compute_spatial_correlation(c_region, alpha_maps[c_size])
        
        if score > best_score:
            best_score = score
            best_config = candidate_config
            
    config = best_config
    size = config['logo_size']
    x = width - config['margin_right'] - size
    y = height - config['margin_bottom'] - size
    alpha_map = alpha_maps[size]
    initial_score = best_score
    region_rgb = img_array[y:y+size, x:x+size, 0:3]
    
    # Simple threshold derived from the original JS detection threshold = ~0.35. (JS uses multiple checks, this is simplified)
    if initial_score < 0.2:
        if args.json:
            print(json.dumps({"applied": False, "reason": "No watermark detected", "score": initial_score}))
        else:
            print(f"No watermark detected (Score {initial_score:.3f}). Skipping.")
        sys.exit(0)

    # 4. Multi-pass removal loop
    base_near_black = calc_near_black_ratio(region_rgb)
    max_near_black = min(1.0, base_near_black + 0.5) # Prevent extreme burnout, but tolerate normal removal artifact
    current_img = img_array
    
    applied_passes = 0
    stop_reason = "max-passes"
    passes_records = []
    
    for pass_idx in range(args.max_passes):
        candidate = remove_watermark_pass(current_img, alpha_map, x, y, size)
        
        region_after = candidate[y:y+size, x:x+size, 0:3]
        score_after = compute_spatial_correlation(region_after, alpha_map)
        nb_after = calc_near_black_ratio(region_after)
        
        passes_records.append({
            "pass": pass_idx + 1,
            "after_score": score_after,
            "near_black_ratio": nb_after
        })
        
        if nb_after > max_near_black:
            stop_reason = "safety-near-black"
            break
            
        current_img = candidate
        applied_passes += 1
        
        if abs(score_after) <= 0.25:
            stop_reason = "residual-low"
            break

    # 5. Save output
    out_img = Image.fromarray(current_img)
    out_img.save(out_path)
    
    # 6. Report JSON
    if args.json:
        print(json.dumps({
            "applied": True,
            "file": out_path,
            "decision": config,
            "position": {"x": x, "y": y, "width": size, "height": size},
            "initial_score": initial_score,
            "passes_applied": applied_passes,
            "stop_reason": stop_reason,
            "pass_details": passes_records
        }))
    else:
        print(f"Removed watermark successfully in {applied_passes} passes ({stop_reason}).")
        print(f"Output saved to: {out_path}")

if __name__ == '__main__':
    main()
