# coding: utf-8
"""
Enhanced CAPTCHA Generator
Extended from the original captcha library to support multiple difficulty levels
"""

from __future__ import annotations
import os
import secrets
import typing as t
import math
from PIL.Image import new as createImage, Image, Transform, Resampling
from PIL.ImageDraw import Draw, ImageDraw
from PIL.ImageFilter import SMOOTH, GaussianBlur
from PIL.ImageFont import FreeTypeFont, truetype, load_default
from io import BytesIO
import numpy as np

__all__ = ['EnhancedImageCaptcha']

ColorTuple = t.Union[t.Tuple[int, int, int], t.Tuple[int, int, int, int]]

# Character set for alphanumeric CAPTCHAs
ALPHANUMERIC_CHARS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

# Try to find system fonts automatically
def find_system_fonts():
    """Find available fonts on the system, prioritizing WSL/Ubuntu systems"""
    fonts = []
    
    # Linux font directories (prioritized for WSL/Ubuntu)
    linux_font_dirs = [
        # "/usr/share/fonts",
        # "/usr/local/share/fonts", 
        # "/usr/share/fonts/truetype",
        # "/usr/share/fonts/ttf",
        # "~/.fonts",
        # "~/.local/share/fonts"
    ]
    
    # Windows font directories (fallback)
    windows_font_dirs = [
        # 'C:/Windows/Fonts',
        # 'C:/Windows/System32/Fonts'
    ]
    
    # Combine all directories
    font_dirs = linux_font_dirs + windows_font_dirs
    
    print("🔍 Searching for fonts in system directories...")
    
    for font_dir in font_dirs:
        # Expand user directory
        expanded_dir = os.path.expanduser(font_dir) if font_dir.startswith('~') else font_dir
        
        if os.path.exists(expanded_dir):
            print(f"  📁 Checking: {expanded_dir}")
            try:
                # Get all .ttf and .otf files
                for root, dirs, files in os.walk(expanded_dir):
                    for file in files:
                        if file.lower().endswith(('.ttf', '.otf')):
                            font_path = os.path.join(root, file)
                            # Test if the font can be loaded
                            try:
                                test_font = truetype(font_path, 20)
                                fonts.append(font_path)
                                print(f"    ✅ Found: {file}")
                            except Exception as e:
                                # Skip fonts that can't be loaded
                                continue
            except Exception as e:
                print(f"    ❌ Error accessing {expanded_dir}: {e}")
                continue
        else:
            print(f"    ⚠️  Directory not found: {expanded_dir}")
    
    # Check local fonts directory
    local_fonts_dir = os.path.join(os.getcwd(), 'fonts')
    if os.path.exists(local_fonts_dir):
        print(f"  📁 Checking local fonts directory: {local_fonts_dir}")
        try:
            for file in os.listdir(local_fonts_dir):
                if file.lower().endswith(('.ttf', '.otf')):
                    font_path = os.path.join(local_fonts_dir, file)
                    try:
                        test_font = truetype(font_path, 20)
                        fonts.append(font_path)
                        print(f"    ✅ Found local font: {file}")
                    except Exception as e:
                        print(f"    ❌ Could not load local font {file}: {e}")
        except Exception as e:
            print(f"    ❌ Error accessing local fonts directory: {e}")
    else:
        print(f"  ⚠️  Local fonts directory not found: {local_fonts_dir}")
    
    # Remove duplicates
    fonts = list(set(fonts))
    
    if fonts:
        print(f"🎉 Total fonts found: {len(fonts)}")
        print("📋 Font list:")
        for font in fonts[:10]:  # Show first 10 fonts
            font_name = os.path.basename(font)
            print(f"    • {font_name}")
        if len(fonts) > 10:
            print(f"    ... and {len(fonts) - 10} more fonts")
    else:
        print("⚠️  No system fonts found! Will use PIL default font.")
    
    return fonts if fonts else None

# Default fonts - try system fonts first, then fall back to built-in
DEFAULT_FONTS = find_system_fonts()
if not DEFAULT_FONTS:
    # If no system fonts found, we'll use PIL's default font
    DEFAULT_FONTS = []


class EnhancedImageCaptcha:
    """Enhanced Image CAPTCHA generator with multiple difficulty levels."""
    
    # Base configuration (Part 2)
    base_config = {
        'lookup_table': [int(i * 1.97) for i in range(256)],
        'character_offset_dx': (0, 4),
        'character_offset_dy': (0, 6),
        'character_rotate': (-30, 30),
        'character_warp_dx': (0.1, 0.3),
        'character_warp_dy': (0.2, 0.3),
        'word_space_probability': 0.3,
        'word_offset_dx': 0.25,
        'noise_dots': 30,
        'noise_curves': 1
    }
    
    # Part 3 configuration (Medium degradation)
    medium_config = {
        'lookup_table': [int(i * 1.97) for i in range(256)],
        'character_offset_dx': (0, 6),
        'character_offset_dy': (0, 8),
        'character_rotate': (-35, 35),
        'character_warp_dx': (0.1, 0.25),
        'character_warp_dy': (0.15, 0.25),
        'word_space_probability': 0.4,
        'word_offset_dx': 0.35,
        'noise_dots': 35,
        'noise_curves': 2,
        'line_distractors': 2,  # Reduced from 5 to 2
        'complex_background': True
    }
    
    # Part 4 configuration (High degradation)
    hard_config = {
        'lookup_table': [int(i * 1.97) for i in range(256)],
        'character_offset_dx': (0, 8),
        'character_offset_dy': (0, 10),
        'character_rotate': (-45, 45),
        'character_warp_dx': (0.15, 0.35),
        'character_warp_dy': (0.2, 0.35),
        'word_space_probability': 0.4,
        'word_offset_dx': 0.4,
        'noise_dots': 45,  # Reduced from 80
        'noise_curves': 3,  # Reduced from 5
        'line_distractors': 3,  # Reduced from 8
        'complex_background': True,
        'circular_distractors': 2,  # Reduced from 3
        'non_ascii_distractors': 1,  # Reduced from 2
        'blur_effect': False,  # Disabled blur for better readability
        'character_overlap': False  # Disabled overlap for better readability
    }

    def __init__(self,
                 width: int = 160,
                 height: int = 60,
                 fonts: list[str] | None = None,
                 font_sizes: tuple[int, ...] | None = None,
                 difficulty: str = 'part2'):
        self._width = width
        self._height = height
        self._fonts = fonts or DEFAULT_FONTS
        self._font_sizes = font_sizes or (30, 36, 42, 48)
        self.difficulty = difficulty
        
        # Print font information during initialization
        if not hasattr(EnhancedImageCaptcha, '_fonts_printed'):
            print(f"\n🎨 Initializing Enhanced CAPTCHA Generator (Difficulty: {difficulty})")
            print("=" * 60)
            
            if self._fonts:
                print(f"✅ Using {len(self._fonts)} system fonts")
                print("🔤 Font files being used:")
                for i, font_path in enumerate(self._fonts[:5]):  # Show first 5
                    font_name = os.path.basename(font_path)
                    print(f"    {i+1}. {font_name}")
                if len(self._fonts) > 5:
                    print(f"    ... and {len(self._fonts) - 5} more fonts")
            else:
                print("⚠️  WARNING: No system fonts found! Using PIL default font.")
                print("   This may result in poor text quality.")
                print("   Consider installing fonts or placing .ttf files in fonts/ directory")
            
            print(f"📏 Font sizes: {self._font_sizes}")
            print(f"🖼️  Image size: {width}x{height}")
            print("=" * 60)
            
            # Set flag so we only print once per session
            EnhancedImageCaptcha._fonts_printed = True
        
        # Load configuration based on difficulty
        if difficulty == 'part3':
            self.config = self.medium_config.copy()
        elif difficulty == 'part4':
            self.config = self.hard_config.copy()
        else:
            self.config = self.base_config.copy()
        
        self._truefonts: list[FreeTypeFont] = []
        self._challenging_fonts: list[FreeTypeFont] = []

    @property
    def truefonts(self) -> list[FreeTypeFont]:
        if self._truefonts:
            return self._truefonts
            
        if self._fonts:
            try:
                print(f"🔤 Loading fonts for size {self._font_sizes}...")
                loaded_fonts = []
                for font_path in self._fonts:
                    font_name = os.path.basename(font_path)
                    for size in self._font_sizes:
                        try:
                            font = truetype(font_path, size)
                            loaded_fonts.append(font)
                        except Exception as e:
                            print(f"    ⚠️  Could not load {font_name} at size {size}: {e}")
                            continue
                
                if loaded_fonts:
                    self._truefonts = loaded_fonts
                    print(f"    ✅ Successfully loaded {len(loaded_fonts)} font instances")
                else:
                    print("    ❌ Failed to load any fonts, using default")
                    self._truefonts = [load_default()]
                    
            except Exception as e:
                print(f"    ❌ Font loading error: {e}")
                self._truefonts = [load_default()]
        else:
            print("    ⚠️  No fonts provided, using PIL default font")
            self._truefonts = [load_default()]
            
        return self._truefonts

    def generate_text(self, length: int | None = None) -> str:
        """Generate random alphanumeric text of specified length (3-7 chars)."""
        if length is None:
            length = secrets.randbelow(5) + 3  # 3-7 characters
        return ''.join(secrets.choice(ALPHANUMERIC_CHARS) for _ in range(length))

    def create_complex_background(self, image: Image) -> Image:
        """Create a complex background with gradients and patterns."""
        w, h = image.size
        
        # Create very subtle gradient background
        for y in range(h):
            for x in range(w):
                # Create a much more subtle gradient
                r = int(235 + (x / w) * 15)  # Very light gradient
                g = int(240 + (y / h) * 10)
                b = int(245 + ((x + y) / (w + h)) * 10)
                image.putpixel((x, y), (min(255, r), min(255, g), min(255, b)))
        
        return image

    def create_line_distractors(self, image: Image, color: ColorTuple, count: int = 2) -> Image:
        """Add line distractors across the image."""
        draw = Draw(image)
        w, h = image.size
        
        for _ in range(count):
            # Random line type
            line_type = secrets.randbelow(3)
            
            if line_type == 0:  # Diagonal lines
                x1, y1 = secrets.randbelow(w), secrets.randbelow(h)
                x2, y2 = secrets.randbelow(w), secrets.randbelow(h)
            elif line_type == 1:  # Horizontal lines
                y = secrets.randbelow(h)
                x1, x2 = 0, w
                y1, y2 = y, y
            else:  # Vertical lines
                x = secrets.randbelow(w)
                x1, x2 = x, x
                y1, y2 = 0, h
            
            # Use lighter colors and thinner lines for less interference
            width = 1  # Always use thin lines
            alpha = secrets.randbelow(50) + 30  # Lower alpha for subtlety
            line_color = (*color[:3], alpha) if len(color) == 3 else (*color[:3], alpha)
            
            draw.line([(x1, y1), (x2, y2)], fill=line_color, width=width)
        
        return image

    def create_circular_distractors(self, image: Image, color: ColorTuple, count: int = 2) -> Image:
        """Add circular/elliptical distractors."""
        draw = Draw(image)
        w, h = image.size
        
        for _ in range(count):
            # Random position and size
            x = secrets.randbelow(w)
            y = secrets.randbelow(h)
            radius = secrets.randbelow(15) + 8  # Smaller circles
            
            # Create ellipse with random eccentricity
            x1, y1 = x - radius, y - radius
            x2, y2 = x + radius, y + radius
            
            # Use very light transparency
            alpha = secrets.randbelow(40) + 20  # Very subtle
            circle_color = (*color[:3], alpha) if len(color) == 3 else color
            
            # Always use outline only for less interference
            draw.ellipse([(x1, y1), (x2, y2)], outline=circle_color, width=1)
        
        return image

    def add_non_ascii_distractors(self, image: Image, color: ColorTuple, count: int = 1) -> Image:
        """Add non-ASCII character distractors that look similar to alphanumeric chars."""
        draw = Draw(image)
        w, h = image.size
        
        # Limited set of specific non-ASCII characters
        distractors = ['*', '#', '?', '✓']
        
        if self.truefonts:
            for _ in range(count):
                char = secrets.choice(distractors)
                font = secrets.choice(self.truefonts)
                
                # Place distractors away from center where main text is
                if secrets.randbelow(2):
                    x = secrets.randbelow(w // 4)  # Left side
                else:
                    x = secrets.randbelow(w // 4) + 3 * w // 4  # Right side
                
                y = secrets.randbelow(h - 30)
                
                # Very low transparency for distractors
                alpha = secrets.randbelow(40) + 30  # More subtle
                distractor_color = (*color[:3], alpha) if len(color) == 3 else color
                
                try:
                    draw.text((x, y), char, font=font, fill=distractor_color)
                except:
                    # Skip if character can't be rendered
                    continue
        
        return image

    @staticmethod
    def create_noise_curve(image: Image, color: ColorTuple) -> Image:
        """Create noise curves (enhanced version)."""
        w, h = image.size
        x1 = secrets.randbelow(int(w / 5) + 1)
        x2 = secrets.randbelow(w - int(w / 5) + 1) + int(w / 5)
        y1 = secrets.randbelow(h - 2 * int(h / 5) + 1) + int(h / 5)
        y2 = secrets.randbelow(h - y1 - int(h / 5) + 1) + y1
        points = [x1, y1, x2, y2]
        end = secrets.randbelow(41) + 160
        start = secrets.randbelow(21)
        width = secrets.randbelow(3) + 1
        Draw(image).arc(points, start, end, fill=color, width=width)
        return image

    @staticmethod
    def create_noise_dots(image: Image, color: ColorTuple, width: int = 2, number: int = 30) -> Image:
        """Create noise dots (enhanced version)."""
        draw = Draw(image)
        w, h = image.size
        count = 0
        while count < number:
            x1 = secrets.randbelow(w + 1)
            y1 = secrets.randbelow(h + 1)
            
            # Make dots smaller and lighter
            dot_width = 1  # Always use small dots
            
            # Use lighter colors for dots
            if len(color) >= 3:
                light_color = (
                    min(255, color[0] + 50),
                    min(255, color[1] + 50), 
                    min(255, color[2] + 50)
                )
            else:
                light_color = color
                
            draw.line(((x1, y1), (x1, y1)), fill=light_color, width=dot_width)
            count += 1
        return image

    def _draw_character(self, c: str, draw: ImageDraw, color: ColorTuple) -> Image:
        """Draw a single character with transformations."""
        if c == " ":
            # Return a small transparent image for spaces
            return createImage('RGBA', (10, 10))
            
        font = secrets.choice(self.truefonts)
        _, _, w, h = draw.multiline_textbbox((1, 1), c, font=font)

        # Ensure minimum character size based on image dimensions
        min_char_size = min(self._width // 8, self._height // 2)
        if w < min_char_size or h < min_char_size:
            # Find a larger font size if character is too small
            larger_fonts = [f for f in self.truefonts if f.size >= min_char_size]
            if larger_fonts:
                font = secrets.choice(larger_fonts)
                _, _, w, h = draw.multiline_textbbox((1, 1), c, font=font)

        dx1 = secrets.randbelow(self.config['character_offset_dx'][1] - self.config['character_offset_dx'][0] + 1) + self.config['character_offset_dx'][0]
        dy1 = secrets.randbelow(self.config['character_offset_dy'][1] - self.config['character_offset_dy'][0] + 1) + self.config['character_offset_dy'][0]
        im = createImage('RGBA', (int(w) + dx1, int(h) + dy1))
        Draw(im).text((dx1, dy1), c, font=font, fill=color)

        # Enhanced rotation based on difficulty
        im = im.crop(im.getbbox())
        rotation_angle = self.config['character_rotate'][0] + (secrets.randbits(32) / (2**32)) * (self.config['character_rotate'][1] - self.config['character_rotate'][0])
        im = im.rotate(rotation_angle, Resampling.BILINEAR, expand=True)

        # Enhanced warp based on difficulty
        dx2 = w * (secrets.randbits(32) / (2**32)) * (self.config['character_warp_dx'][1] - self.config['character_warp_dx'][0]) + self.config['character_warp_dx'][0]
        dy2 = h * (secrets.randbits(32) / (2**32)) * (self.config['character_warp_dy'][1] - self.config['character_warp_dy'][0]) + self.config['character_warp_dy'][0]
        x1 = int(secrets.randbits(32) / (2**32) * (dx2 - (-dx2)) + (-dx2))
        y1 = int(secrets.randbits(32) / (2**32) * (dy2 - (-dy2)) + (-dy2))
        x2 = int(secrets.randbits(32) / (2**32) * (dx2 - (-dx2)) + (-dx2))
        y2 = int(secrets.randbits(32) / (2**32) * (dy2 - (-dy2)) + (-dy2))
        w2 = w + abs(x1) + abs(x2)
        h2 = h + abs(y1) + abs(y2)
        data = (
            x1, y1,
            -x1, h2 - y2,
            w2 + x2, h2 + y2,
            w2 - x2, -y1,
        )
        im = im.resize((w2, h2))
        im = im.transform((int(w), int(h)), Transform.QUAD, data)
        return im

    def create_captcha_image(self, chars: str, color: ColorTuple, background: ColorTuple) -> Image:
        """Create the CAPTCHA image with all transformations."""
        # Create base image
        image = createImage('RGB', (self._width, self._height), background)
        
        # Apply complex background if enabled
        if self.config.get('complex_background', False):
            image = self.create_complex_background(image)
        
        draw = Draw(image)
        images: list[Image] = []
        
        # Generate character images
        for c in chars:
            if secrets.randbits(32) / (2**32) > self.config['word_space_probability']:
                images.append(self._draw_character(" ", draw, color))
            images.append(self._draw_character(c, draw, color))

        # Remove empty images (spaces)
        images = [im for im in images if im.size[0] > 0 and im.size[1] > 0]
        
        if not images:
            return image

        # Calculate total text width and individual character widths
        char_widths = [im.size[0] for im in images]
        total_char_width = sum(char_widths)
        
        # Calculate spacing between characters based on image width
        num_chars = len(images)
        if num_chars > 1:
            # Reserve space for characters and calculate remaining space for gaps
            available_width = self._width * 0.9  # Use 90% of width, leave 10% margin
            target_char_width = available_width * 0.7  # 70% for characters
            target_spacing_width = available_width * 0.3  # 30% for spacing
            
            # Scale characters if they're too small or too large
            if total_char_width < target_char_width:
                scale_factor = target_char_width / total_char_width
                # Resize characters to better fit the image
                scaled_images = []
                for im in images:
                    new_width = int(im.size[0] * scale_factor)
                    new_height = int(im.size[1] * scale_factor)
                    scaled_images.append(im.resize((new_width, new_height), Resampling.LANCZOS))
                images = scaled_images
                char_widths = [im.size[0] for im in images]
                total_char_width = sum(char_widths)
            
            # Calculate spacing between characters
            spacing_per_gap = int(target_spacing_width / (num_chars - 1))
        else:
            spacing_per_gap = 0
        
        # Calculate starting offset to center the text
        total_width_needed = total_char_width + (spacing_per_gap * (num_chars - 1))
        start_offset = max(10, int((self._width - total_width_needed) / 2))

        # Handle character overlap for part4
        if self.config.get('character_overlap', False):
            overlap_reduction = int(spacing_per_gap * 0.3)  # Reduce spacing by 30%
            spacing_per_gap = max(5, spacing_per_gap - overlap_reduction)

        # Paste characters with proper spacing
        current_offset = start_offset
        for i, im in enumerate(images):
            w, h = im.size
            
            # Add some random vertical offset for more natural look
            vertical_offset = int((self._height - h) / 2) + secrets.randbelow(11) - 5
            vertical_offset = max(0, min(vertical_offset, self._height - h))
            
            # Add small horizontal random variation
            horizontal_variation = secrets.randbelow(11) - 5
            final_offset = max(0, current_offset + horizontal_variation)
            
            mask = im.convert('L').point(self.config['lookup_table'])
            image.paste(im, (final_offset, vertical_offset), mask)
            
            # Update offset for next character
            current_offset += w + spacing_per_gap

        return image

    def generate_image(self, chars: str,
                      bg_color: ColorTuple | None = None,
                      fg_color: ColorTuple | None = None) -> Image:
        """Generate the final CAPTCHA image with all effects."""
        # Generate colors with better contrast
        background = bg_color if bg_color else random_color(240, 255)  # Lighter background
        random_fg_color = random_color(20, 100, secrets.randbelow(36) + 220)  # Darker, more solid text
        color: ColorTuple = fg_color if fg_color else random_fg_color

        # Create base captcha image
        im = self.create_captcha_image(chars, color, background)
        
        # Add noise dots (reduced intensity)
        self.create_noise_dots(im, color, number=self.config['noise_dots'])
        
        # Add noise curves (lighter)
        for _ in range(self.config['noise_curves']):
            # Use lighter color for curves
            if len(color) >= 3:
                light_curve_color = (
                    min(255, color[0] + 80),
                    min(255, color[1] + 80),
                    min(255, color[2] + 80)
                )
            else:
                light_curve_color = color
            self.create_noise_curve(im, light_curve_color)
        
        # Add line distractors (part3 and part4)
        if 'line_distractors' in self.config:
            self.create_line_distractors(im, color, self.config['line_distractors'])
        
        # Add circular distractors (part4 only)
        if 'circular_distractors' in self.config:
            self.create_circular_distractors(im, color, self.config['circular_distractors'])
        
        # Add non-ASCII distractors (part4 only)
        if 'non_ascii_distractors' in self.config:
            self.add_non_ascii_distractors(im, color, self.config['non_ascii_distractors'])
        
        # Apply smooth filter (always apply for better text clarity)
        im = im.filter(SMOOTH)
        
        return im

    def generate(self, chars: str | None = None, format: str = 'PNG',
                bg_color: ColorTuple | None = None,
                fg_color: ColorTuple | None = None) -> BytesIO:
        """Generate CAPTCHA and return as BytesIO."""
        if chars is None:
            chars = self.generate_text()
            
        im = self.generate_image(chars, bg_color=bg_color, fg_color=fg_color)
        out = BytesIO()
        im.save(out, format=format)
        out.seek(0)
        return out

    def write(self, chars: str | None = None, output: str = 'captcha.png', format: str = 'PNG',
              bg_color: ColorTuple | None = None,
              fg_color: ColorTuple | None = None) -> str:
        """Generate CAPTCHA and save to file. Returns the text used."""
        if chars is None:
            chars = self.generate_text()
            
        im = self.generate_image(chars, bg_color=bg_color, fg_color=fg_color)
        im.save(output, format=format)
        return chars


def random_color(start: int, end: int, opacity: int | None = None) -> ColorTuple:
    """Generate random color."""
    red = secrets.randbelow(end - start + 1) + start
    green = secrets.randbelow(end - start + 1) + start
    blue = secrets.randbelow(end - start + 1) + start
    if opacity is None:
        return red, green, blue
    return red, green, blue, opacity