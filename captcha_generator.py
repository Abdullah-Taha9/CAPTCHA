#!/usr/bin/env python3
# coding: utf-8
"""
CAPTCHA Generator Script
Usage: python captcha_generator.py --config generator_config.yaml --part part2 part3 part4
"""

import argparse
import yaml
import json
import os
from pathlib import Path
from typing import List, Dict, Any
from enhanced_captcha import EnhancedImageCaptcha


class CaptchaGenerator:
    def __init__(self, config_path: str):
        """Initialize the CAPTCHA generator with configuration."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Create output directory
        self.output_dir = Path(self.config.get('output_dir', 'data_generated'))
        self.output_dir.mkdir(exist_ok=True)
        
    def generate_part(self, part: str) -> None:
        """Generate CAPTCHAs for a specific part."""
        print(f"Generating {part}...")
        
        # Get part-specific configuration
        part_config = self.config['parts'][part]
        
        # Create part directory structure
        part_dir = self.output_dir / part
        images_dir = part_dir / 'images'
        images_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize CAPTCHA generator with part-specific settings
        captcha = EnhancedImageCaptcha(
            width=part_config.get('width', 160),
            height=part_config.get('height', 60),
            fonts=part_config.get('fonts', None),
            font_sizes=tuple(part_config.get('font_sizes', [30, 36, 42, 48])),
            difficulty=part
        )
        
        # Generate CAPTCHAs
        labels = []
        num_samples = part_config.get('num_samples', 1000)
        
        for i in range(num_samples):
            # Generate image filename
            image_id = f"{i+1:06d}"
            image_filename = f"{image_id}.png"
            image_path = images_dir / image_filename
            
            # Generate CAPTCHA text (3-7 characters)
            min_length = part_config.get('min_length', 3)
            max_length = part_config.get('max_length', 7)
            text_length = min_length + (i % (max_length - min_length + 1))
            
            captcha_text = captcha.generate_text(text_length)
            
            # Generate and save image
            try:
                captcha.write(
                    chars=captcha_text,
                    output=str(image_path),
                    format='PNG',
                    bg_color=part_config.get('bg_color', None),
                    fg_color=part_config.get('fg_color', None)
                )
                
                # Add to labels
                labels.append({
                    "height": part_config.get('height', 60),
                    "width": part_config.get('width', 160),
                    "image_id": image_id,
                    "captcha_string": captcha_text,
                    "filename": image_filename,
                    "difficulty": part
                })
                
                # Progress indicator
                if (i + 1) % 100 == 0:
                    print(f"  Generated {i + 1}/{num_samples} images for {part}")
                    
            except Exception as e:
                print(f"  Error generating image {image_id}: {e}")
                continue
        
        # Save labels.json
        labels_path = part_dir / 'labels.json'
        with open(labels_path, 'w') as f:
            json.dump(labels, f, indent=2)
        
        print(f"  Completed {part}: {len(labels)} images generated")
        print(f"  Images saved to: {images_dir}")
        print(f"  Labels saved to: {labels_path}")


def main():
    parser = argparse.ArgumentParser(description='Enhanced CAPTCHA Generator')
    parser.add_argument('--config', required=True, help='Path to configuration YAML file')
    parser.add_argument('--part', nargs='+', choices=['part2', 'part3', 'part4'], 
                       required=True, help='Parts to generate (part2, part3, part4)')
    
    args = parser.parse_args()
    
    # Check if config file exists
    if not os.path.exists(args.config):
        print(f"Error: Configuration file '{args.config}' not found.")
        return
    
    try:
        generator = CaptchaGenerator(args.config)
        
        print("Starting CAPTCHA generation...")
        print(f"Output directory: {generator.output_dir}")
        print(f"Parts to generate: {args.part}")
        print("-" * 50)
        
        for part in args.part:
            generator.generate_part(part)
            print("-" * 50)
        
        print("CAPTCHA generation completed!")
        
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == '__main__':
    main()
