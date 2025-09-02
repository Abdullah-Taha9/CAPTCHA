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
    """Find available fonts on the system"""
    fonts = []
    
    # Common font directories by OS
    font_dirs = []
    if os.name == 'nt':  # Windows
        font_dirs = [
            'C:/Windows/Fonts',
            'C:/Windows/System32/Fonts'
        ]
    elif os.name == 'posix':  # Linux/Mac
        font_dirs = [
            '/usr/share/fonts',
            '/System/Library/Fonts',
            '/usr/local/share/fonts',
            '~/.fonts'
        ]
    
    # Look for common font files
    font_names = ['arial.ttf', 'Arial.ttf', 'times.ttf', 'Times.ttf', 
                  'calibri.ttf', 'Calibri.ttf', 'helvetica.ttf', 'Helvetica.ttf',
                  'DejaVuSans.ttf', 'LiberationSans-Regular.ttf']
    
    for font_dir in font_dirs:
        if os.path.exists(font_dir):
            for font_name in font_names:
                font_path = os.path.join(font_dir, font_name)
                if os.path.exists(font_path):
                    fonts.append(font_path)
    
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
        'character_offset_dx': (0, 8),
        'character_offset_dy': (0, 10),
        'character_rotate': (-45, 45),
        'character_warp_dx': (0.2, 0.4),
        'character_warp_dy': (0.3, 0.4),
        'word_space_probability': 0.4,
        'word_offset_dx': 0.35,
        'noise_dots': 50,
        'noise_curves': 3,
        'line_distractors': 5,
        'complex_background': True
    }
    
    # Part 4 configuration (High degradation)
    hard_config = {
        'lookup_table': [int(i * 1.97) for i in range(256)],
        'character_offset_dx': (0, 12),
        'character_offset_dy': (0, 15),
        'character_rotate': (-60, 60),
        'character_warp_dx': (0.3, 0.6),
        'character_warp_dy': (0.4, 0.6),
        'word_space_probability': 0.5,
        'word_offset_dx': 0.45,
        'noise_dots': 80,
        'noise_curves': 5,
        'line_distractors': 8,
        'complex_background': True,
        'circular_distractors': 3,
        'non_ascii_distractors': 2,
        'blur_effect': True,
        'character_overlap': True
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
                self._truefonts = [
                    truetype(n, s)
                    for n in self._fonts
                    for s in self._font_sizes
                ]
            except:
                # If loading fonts fails, use default font
                self._truefonts = [load_default() for _ in self._font_sizes]
        else:
            self._truefonts = [load_default() for _ in self._font_sizes]
            
        return self._truefonts

    def generate_text(self, length: int | None = None) -> str:
        """Generate random alphanumeric text of specified length (3-7 chars)."""
        if length is None:
            length = secrets.randbelow(5) + 3  # 3-7 characters
        return ''.join(secrets.choice(ALPHANUMERIC_CHARS) for _ in range(length))

    def create_complex_background(self, image: Image) -> Image:
        """Create a complex background with gradients and patterns."""
        w, h = image.size
        
        # Create gradient background
        for y in range(h):
            for x in range(w):
                # Create a subtle gradient
                r = int(220 + (x / w) * 35)
                g = int(230 + (y / h) * 25)
                b = int(240 + ((x + y) / (w + h)) * 15)
                image.putpixel((x, y), (min(255, r), min(255, g), min(255, b)))
        
        return image

    def create_line_distractors(self, image: Image, color: ColorTuple, count: int = 5) -> Image:
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
            
            # Vary line width and transparency
            width = secrets.randbelow(3) + 1
            alpha = secrets.randbelow(100) + 50
            line_color = (*color[:3], alpha) if len(color) == 3 else color
            
            draw.line([(x1, y1), (x2, y2)], fill=line_color, width=width)
        
        return image

    def create_circular_distractors(self, image: Image, color: ColorTuple, count: int = 3) -> Image:
        """Add circular/elliptical distractors."""
        draw = Draw(image)
        w, h = image.size
        
        for _ in range(count):
            # Random position and size
            x = secrets.randbelow(w)
            y = secrets.randbelow(h)
            radius = secrets.randbelow(20) + 10
            
            # Create ellipse with random eccentricity
            x1, y1 = x - radius, y - radius
            x2, y2 = x + radius, y + radius
            
            # Vary transparency
            alpha = secrets.randbelow(80) + 30
            circle_color = (*color[:3], alpha) if len(color) == 3 else color
            
            # Randomly choose filled or outline
            if secrets.randbelow(2):
                draw.ellipse([(x1, y1), (x2, y2)], outline=circle_color, width=2)
            else:
                draw.ellipse([(x1, y1), (x2, y2)], fill=circle_color)
        
        return image

    def add_non_ascii_distractors(self, image: Image, color: ColorTuple, count: int = 2) -> Image:
        """Add non-ASCII character distractors that look similar to alphanumeric chars."""
        draw = Draw(image)
        w, h = image.size
        
        # Similar-looking characters
        distractors = ['÷', '×', '±', '≠', '≈', '∞', '∑', '∏', '∆', '∇', '∈', '∉']
        
        if self.truefonts:
            for _ in range(count):
                char = secrets.choice(distractors)
                font = secrets.choice(self.truefonts)
                
                x = secrets.randbelow(w - 20)
                y = secrets.randbelow(h - 20)
                
                # Lower transparency for distractors
                alpha = secrets.randbelow(60) + 40
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
    def create_noise_dots(image: Image, color: ColorTuple, width: int = 3, number: int = 30) -> Image:
        """Create noise dots (enhanced version)."""
        draw = Draw(image)
        w, h = image.size
        while number:
            x1 = secrets.randbelow(w + 1)
            y1 = secrets.randbelow(h + 1)
            dot_width = secrets.randbelow(width) + 1
            draw.line(((x1, y1), (x1 - 1, y1 - 1)), fill=color, width=dot_width)
            number -= 1
        return image

    def _draw_character(self, c: str, draw: ImageDraw, color: ColorTuple) -> Image:
        """Draw a single character with transformations."""
        font = secrets.choice(self.truefonts)
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

        # Calculate positioning
        text_width = sum([im.size[0] for im in images])
        width = max(text_width, self._width)
        image = image.resize((width, self._height))

        average = int(text_width / len(chars)) if chars else 0
        rand = int(self.config['word_offset_dx'] * average)
        offset = int(average * 0.1)

        # Handle character overlap for part4
        if self.config.get('character_overlap', False):
            overlap_factor = 0.7  # Characters can overlap by 30%
        else:
            overlap_factor = 1.0

        # Paste characters
        for im in images:
            w, h = im.size
            mask = im.convert('L').point(self.config['lookup_table'])
            image.paste(im, (offset, int((self._height - h) / 2)), mask)
            offset = offset + int(w * overlap_factor) + (-secrets.randbelow(rand + 1))

        if width > self._width:
            image = image.resize((self._width, self._height))

        return image

    def generate_image(self, chars: str,
                      bg_color: ColorTuple | None = None,
                      fg_color: ColorTuple | None = None) -> Image:
        """Generate the final CAPTCHA image with all effects."""
        # Generate colors
        background = bg_color if bg_color else random_color(230, 255)
        random_fg_color = random_color(10, 180, secrets.randbelow(36) + 200)
        color: ColorTuple = fg_color if fg_color else random_fg_color

        # Create base captcha image
        im = self.create_captcha_image(chars, color, background)
        
        # Add noise dots
        self.create_noise_dots(im, color, number=self.config['noise_dots'])
        
        # Add noise curves
        for _ in range(self.config['noise_curves']):
            self.create_noise_curve(im, color)
        
        # Add line distractors (part3 and part4)
        if 'line_distractors' in self.config:
            self.create_line_distractors(im, color, self.config['line_distractors'])
        
        # Add circular distractors (part4 only)
        if 'circular_distractors' in self.config:
            self.create_circular_distractors(im, color, self.config['circular_distractors'])
        
        # Add non-ASCII distractors (part4 only)
        if 'non_ascii_distractors' in self.config:
            self.add_non_ascii_distractors(im, color, self.config['non_ascii_distractors'])
        
        # Apply smooth filter
        im = im.filter(SMOOTH)
        
        # Apply blur effect (part4 only)
        if self.config.get('blur_effect', False):
            blur_radius = secrets.randbelow(2) + 1
            im = im.filter(GaussianBlur(radius=blur_radius))
        
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
