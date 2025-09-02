#!/usr/bin/env python3
# coding: utf-8
"""
Demo script for Enhanced CAPTCHA Generator
This script demonstrates the different difficulty levels and generates sample images
"""

import os
from pathlib import Path
from enhanced_captcha import EnhancedImageCaptcha


def create_demo_samples():
    """Create demonstration samples for each difficulty level."""
    
    # Create demo directory
    demo_dir = Path('demo_samples')
    demo_dir.mkdir(exist_ok=True)
    
    parts = ['part2', 'part3', 'part4']
    sample_texts = ['A7X9', '3K2M5', 'B9F4L', '7N8Q2', 'X5Y1Z']
    
    print("Generating demo samples...")
    print("=" * 50)
    
    for part in parts:
        print(f"\nGenerating {part} samples...")
        
        # Create part-specific directory
        part_dir = demo_dir / part
        part_dir.mkdir(exist_ok=True)
        
        # Initialize CAPTCHA generator
        captcha = EnhancedImageCaptcha(
            width=160 if part == 'part2' else 180 if part == 'part3' else 200,
            height=60 if part == 'part2' else 80 if part == 'part3' else 100,
            difficulty=part
        )
        
        # Generate samples
        for i, text in enumerate(sample_texts):
            filename = f"{part}_sample_{i+1:02d}_{text}.png"
            filepath = part_dir / filename
            
            try:
                generated_text = captcha.write(
                    chars=text,
                    output=str(filepath),
                    format='PNG'
                )
                print(f"  ✓ Generated: {filename}")
            except Exception as e:
                print(f"  ✗ Error generating {filename}: {e}")
        
        # Generate some random samples
        for i in range(3):
            filename = f"{part}_random_{i+1:02d}.png"
            filepath = part_dir / filename
            
            try:
                generated_text = captcha.write(output=str(filepath))
                print(f"  ✓ Generated: {filename} (text: {generated_text})")
            except Exception as e:
                print(f"  ✗ Error generating {filename}: {e}")
    
    print(f"\nDemo samples created in: {demo_dir}")
    print("=" * 50)


def test_character_generation():
    """Test the character generation functionality."""
    print("\nTesting character generation:")
    print("-" * 30)
    
    captcha = EnhancedImageCaptcha()
    
    # Test different lengths
    for length in range(3, 8):
        text = captcha.generate_text(length)
        print(f"Length {length}: {text}")
    
    # Test random length generation
    print("\nRandom lengths:")
    for i in range(5):
        text = captcha.generate_text()
        print(f"Random {i+1}: {text} (length: {len(text)})")


def test_difficulty_comparison():
    """Create comparison images to show difficulty progression."""
    print("\nGenerating difficulty comparison...")
    print("-" * 40)
    
    comparison_dir = Path('comparison_samples')
    comparison_dir.mkdir(exist_ok=True)
    
    test_text = "5K7M2"
    parts = ['part2', 'part3', 'part4']
    
    for part in parts:
        captcha = EnhancedImageCaptcha(
            width=200,
            height=100,
            difficulty=part
        )
        
        # Generate multiple samples of the same text to show variation
        for i in range(3):
            filename = f"comparison_{part}_sample{i+1}_{test_text}.png"
            filepath = comparison_dir / filename
            
            try:
                captcha.write(
                    chars=test_text,
                    output=str(filepath),
                    format='PNG'
                )
                print(f"  ✓ Generated: {filename}")
            except Exception as e:
                print(f"  ✗ Error: {e}")
    
    print(f"Comparison samples saved to: {comparison_dir}")


def print_configuration_info():
    """Print information about the configuration for each part."""
    print("\nConfiguration Information:")
    print("=" * 50)
    
    captcha_part2 = EnhancedImageCaptcha(difficulty='part2')
    captcha_part3 = EnhancedImageCaptcha(difficulty='part3')
    captcha_part4 = EnhancedImageCaptcha(difficulty='part4')
    
    parts_info = [
        ("Part 2 (Basic Enhanced)", captcha_part2.config),
        ("Part 3 (Medium Degradation)", captcha_part3.config),
        ("Part 4 (High Degradation)", captcha_part4.config)
    ]
    
    for name, config in parts_info:
        print(f"\n{name}:")
        print(f"  Character rotation: {config['character_rotate']}")
        print(f"  Character warp (dx): {config['character_warp_dx']}")
        print(f"  Character warp (dy): {config['character_warp_dy']}")
        print(f"  Noise dots: {config['noise_dots']}")
        print(f"  Noise curves: {config['noise_curves']}")
        
        if 'line_distractors' in config:
            print(f"  Line distractors: {config['line_distractors']}")
        if 'circular_distractors' in config:
            print(f"  Circular distractors: {config['circular_distractors']}")
        if 'non_ascii_distractors' in config:
            print(f"  Non-ASCII distractors: {config['non_ascii_distractors']}")
        if config.get('blur_effect'):
            print(f"  Blur effect: Enabled")
        if config.get('character_overlap'):
            print(f"  Character overlap: Enabled")


def main():
    print("Enhanced CAPTCHA Generator - Demo Script")
    print("=" * 50)
    
    # Test basic functionality
    test_character_generation()
    
    # Show configuration information
    print_configuration_info()
    
    # Create demo samples
    create_demo_samples()
    
    # Create difficulty comparison
    test_difficulty_comparison()
    
    print("\n" + "=" * 50)
    print("Demo completed!")
    print("\nTo generate full datasets, use:")
    print("python captcha_generator.py --config generator_config.yaml --part part2 part3 part4")
    print("\nTo generate specific parts only:")
    print("python captcha_generator.py --config generator_config.yaml --part part2")
    print("python captcha_generator.py --config generator_config.yaml --part part3 part4")


if __name__ == '__main__':
    main()
