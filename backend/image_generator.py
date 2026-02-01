"""Generate custom images using Gemini 2.5 Flash Image AI (Nano-Banana)"""
import os
import time
from typing import Optional
from pathlib import Path
from google import genai
from google.genai import types

class ImageGenerator:
    """Uses the modern google-genai client to generate actual illustrations"""
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.client = None
            return
            
        try:
            self.client = genai.Client(api_key=api_key)
            self.model_id = "gemini-2.5-flash-image"
            print(f"✓ ImageGenerator initialized with {self.model_id} (Nano-Banana)")
        except Exception as e:
            print(f"⚠ ImageGenerator init failed: {e}")
            self.client = None

    def generate_image(self, title: str, category: str, output_path: Path, layout: str = "SQUARE") -> bool:
        """Prompts Nano-Banana to generate a professional newspaper-style image"""
        
        if not self.client:
            return False

        prompt = f"""Generate a professional, minimalist editorial illustration for a high-end AI newspaper.

ARTICLE: {title}
CATEGORY: {category}
LAYOUT: {layout}

STYLE: 
- Professional newsprint style.
- High contrast, minimalist composition.
- Use abstract geometric shapes and tech-inspired lines.
- Color palette: Deep blacks, crisp whites, and a single subtle accent color.
- No text or labels in the image.
- Cinematic, high-quality rendering suitable for a prestige publication."""

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            response_modalities=[
                "IMAGE",
                "TEXT",
            ],
        )

        try:
            # Respect rate limits
            time.sleep(2)
            
            # Using the streaming method as provided in the snippet
            for chunk in self.client.models.generate_content_stream(
                model=self.model_id,
                contents=contents,
                config=generate_content_config,
            ):
                if (
                    chunk.candidates is None
                    or chunk.candidates[0].content is None
                    or chunk.candidates[0].content.parts is None
                ):
                    continue
                
                # Look for inline_data (image)
                for part in chunk.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.data:
                        with open(output_path, 'wb') as f:
                            f.write(part.inline_data.data)
                        return True
            
            return False
            
        except Exception as e:
            print(f"  ✗ Nano-Banana generation failed for '{title[:20]}': {e}")
            return False

class PlaceholderImageGenerator:
    """Standard SVG generator for fallbacks"""
    
    CATEGORIES_COLORS = {
        "Breaking Vectors": "#f0f0f0",
        "Model Architectures": "#e8f0fe",
        "Neural Horizons": "#fef7e0",
        "Lab Outputs": "#e6fffa",
        "Inference Corner": "#fff5f5"
    }
    
    @staticmethod
    def generate_svg_placeholder(title: str, category: str, layout: str = "SQUARE") -> str:
        dims = {"WIDE": (800, 400), "TALL": (400, 600), "SQUARE": (500, 500)}
        width, height = dims.get(layout, (500, 500))
        color = PlaceholderImageGenerator.CATEGORIES_COLORS.get(category, "#f9f9f9")
        display_title = title[:50] + "..." if len(title) > 50 else title
        
        return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{width}" height="{height}" fill="{color}" stroke="#ccc" stroke-width="1"/>
  <text x="20" y="{height - 20}" fill="#666" font-size="12" font-family="serif" font-style="italic">{display_title} [NANO-BANANA FALLBACK]</text>
</svg>"""

    @staticmethod
    def save_placeholder(title: str, category: str, output_path: str, layout: str = "SQUARE") -> str:
        svg = PlaceholderImageGenerator.generate_svg_placeholder(title, category, layout)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(svg)
        return output_path
