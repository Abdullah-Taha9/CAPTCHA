# Enhanced CAPTCHA Generator

An advanced CAPTCHA generation system with three progressive difficulty levels, built upon the original captcha library architecture.

## Features

### Part 2: Enhanced Alphanumeric CAPTCHAs
- Clean alphanumeric characters (0-9, A-Z)
- Variable length (3-7 characters)
- Moderate rotations (-30° to +30°)
- Basic noise and curve distractors
- Standard character warping

### Part 3: Medium Degradation
- All Part 2 features plus:
- Larger character rotations (-45° to +45°)
- Line distractors (diagonal, horizontal, vertical)
- Complex gradient backgrounds
- Enhanced noise patterns
- Increased character warping

### Part 4: High Degradation
- All Part 3 features plus:
- Extreme character rotations (-60° to +60°)
- Circular and elliptical distractors
- Non-ASCII character distractors (÷, ×, ±, ≠, etc.)
- Gaussian blur effects
- Character overlap
- Maximum noise and distortion

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure you have the required files:
   - `enhanced_captcha.py` - Core CAPTCHA generation module
   - `captcha_generator.py` - Command-line generator script
   - `generator_config.yaml` - Configuration file
   - `demo.py` - Demonstration script

## Usage

### Quick Demo
Generate sample images to see all difficulty levels:
```bash
python demo.py
```

### Full Dataset Generation
Generate complete datasets for all parts:
```bash
python captcha_generator.py --config generator_config.yaml --part part2 part3 part4
```

Generate specific parts only:
```bash
python captcha_generator.py --config generator_config.yaml --part part2
python captcha_generator.py --config generator_config.yaml --part part3 part4
```

### Output Structure
```
data_generated/
├── part2/
│   ├── images/
│   │   ├── 000001.png
│   │   ├── 000002.png
│   │   └── ...
│   └── labels.json
├── part3/
│   ├── images/
│   │   └── ...
│   └── labels.json
└── part4/
    ├── images/
    │   └── ...
    └── labels.json
```

### Labels Format
Each `labels.json` contains:
```json
[
  {
    "height": 60,
    "width": 160,
    "image_id": "000001",
    "captcha_string": "2CUVK",
    "filename": "000001.png",
    "difficulty": "part2"
  }
]
```

## Configuration

Edit `generator_config.yaml` to customize:

- **Number of samples**: Adjust `num_samples` for each part
- **Image dimensions**: Modify `width` and `height`
- **Text length**: Set `min_length` and `max_length`
- **Colors**: Specify `bg_color` and `fg_color` or leave `null` for random
- **Fonts**: Add custom font paths or leave empty for auto-detection

### Example Configuration
```yaml
parts:
  part2:
    num_samples: 1000
    width: 160
    height: 60
    min_length: 3
    max_length: 7
    bg_color: [240, 240, 240]  # Light gray
    fg_color: [50, 50, 50]     # Dark gray
```

## Programmatic Usage

```python
from enhanced_captcha import EnhancedImageCaptcha

# Create generator for specific difficulty
captcha = EnhancedImageCaptcha(
    width=160, 
    height=60, 
    difficulty='part2'
)

# Generate random text and save image
text = captcha.write(output='captcha.png')
print(f"Generated CAPTCHA: {text}")

# Generate specific text
captcha.write(chars='A7X9K', output='specific.png')

# Generate image in memory
from io import BytesIO
buffer = captcha.generate(chars='B2M5N')
```

## Font Handling

The system automatically detects system fonts from common directories:
- **Windows**: `C:/Windows/Fonts/`
- **Linux/Mac**: `/usr/share/fonts/`, `/System/Library/Fonts/`

Supported font types: `.ttf` files

To use custom fonts, specify them in the configuration:
```yaml
parts:
  part2:
    fonts: ["/path/to/custom1.ttf", "/path/to/custom2.ttf"]
```

## Requirements

- Python 3.7+
- Pillow (PIL) 9.0+
- PyYAML 6.0+
- NumPy 1.21+ (optional, for enhanced effects)

## Difficulty Progression Examples

| Part | Rotation Range | Noise Level | Special Effects |
|------|----------------|-------------|-----------------|
| 2    | ±30°          | Basic       | None            |
| 3    | ±45°          | Medium      | Lines, Complex BG |
| 4    | ±60°          | High        | All effects     |

## Technical Details

### Character Set
- Alphanumeric only: `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ`
- No ambiguous characters (configurable)
- Length: 3-7 characters (configurable)

### Image Processing Pipeline
1. Character rendering with random fonts
2. Individual character transformations (rotation, warping)
3. Character positioning with optional overlap
4. Background generation (solid or complex)
5. Noise addition (dots, curves, lines)
6. Distractor placement (circles, non-ASCII chars)
7. Final effects (blur, smooth filter)

### Performance
- Generates ~100 images per minute (depends on complexity and hardware)
- Memory efficient - processes one image at a time
- Supports batch generation with progress tracking

## Troubleshooting

**Font loading issues**: If no system fonts are found, the generator falls back to PIL's default font.

**Memory issues**: For large batches, the generator processes images individually to maintain low memory usage.

**Permission errors**: Ensure write permissions for the output directory.

## License

Built upon the original captcha library. Maintains compatibility with existing captcha library interfaces while adding enhanced functionality.# CAPTCHA
