import os
import time
from typing import Dict, List, Optional, Any, Tuple
import structlog
from io import BytesIO
import tempfile
import base64

# Image processing imports
try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageStat
    from PIL.ExifTags import TAGS
except ImportError:
    Image = None

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

try:
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")
except ImportError:
    openai = None

logger = structlog.get_logger()

class ImageProcessor:
    """Advanced image processing with AI model support"""
    
    def __init__(self):
        self.pil_available = Image is not None
        self.cv2_available = cv2 is not None and np is not None
        self.openai_enabled = openai is not None and os.getenv("OPENAI_API_KEY")
        
        if not self.pil_available:
            logger.warning("PIL not available - image processing capabilities limited")
    
    def load_image_from_bytes(self, image_data: bytes) -> Image.Image:
        """Load PIL Image from bytes"""
        if not self.pil_available:
            raise ImportError("PIL is required for image processing")
        
        try:
            return Image.open(BytesIO(image_data))
        except Exception as e:
            logger.error("Failed to load image from bytes", error=str(e))
            raise
    
    def get_basic_info(self, image: Image.Image, original_size_bytes: int) -> Dict[str, Any]:
        """Extract basic image information"""
        width, height = image.size
        
        return {
            "dimensions": {
                "width": width,
                "height": height,
                "aspect_ratio": round(width / height, 3) if height > 0 else 0
            },
            "format": {
                "mode": image.mode,
                "format": getattr(image, 'format', 'Unknown'),
                "has_transparency": image.mode in ('RGBA', 'LA') or 'transparency' in image.info
            },
            "size": {
                "bytes": original_size_bytes,
                "megapixels": round((width * height) / 1000000, 2)
            }
        }
    
    def extract_metadata(self, image: Image.Image) -> Dict[str, Any]:
        """Extract EXIF metadata from image"""
        metadata = {}
        
        try:
            exifdata = image.getexif()
            if exifdata:
                for tag_id in exifdata:
                    tag = TAGS.get(tag_id, tag_id)
                    data = exifdata.get(tag_id)
                    
                    # Convert bytes to string for some tags
                    if isinstance(data, bytes):
                        try:
                            data = data.decode()
                        except UnicodeDecodeError:
                            data = str(data)
                    
                    metadata[tag] = data
                    
        except Exception as e:
            logger.warning("Failed to extract EXIF data", error=str(e))
        
        # Add other metadata
        if hasattr(image, 'info'):
            for key, value in image.info.items():
                if key not in metadata:
                    metadata[key] = value
        
        return metadata
    
    def analyze_colors(self, image: Image.Image) -> Dict[str, Any]:
        """Analyze color properties of the image"""
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                rgb_image = image.convert('RGB')
            else:
                rgb_image = image
            
            # Get color statistics
            stat = ImageStat.Stat(rgb_image)
            
            # Mean color values
            mean_colors = stat.mean
            
            # Get dominant colors using simple quantization
            dominant_colors = self._get_dominant_colors(rgb_image)
            
            # Calculate brightness
            brightness = sum(mean_colors) / 3 / 255
            
            # Simple color temperature estimation
            r, g, b = mean_colors
            color_temp = "warm" if r > b else "cool" if b > r else "neutral"
            
            return {
                "mean_rgb": [round(c, 2) for c in mean_colors],
                "brightness": round(brightness, 3),
                "color_temperature": color_temp,
                "dominant_colors": dominant_colors,
                "color_variance": [round(v, 2) for v in stat.var] if hasattr(stat, 'var') else []
            }
            
        except Exception as e:
            logger.error("Color analysis failed", error=str(e))
            return {"error": "Color analysis failed"}
    
    def _get_dominant_colors(self, image: Image.Image, num_colors: int = 5) -> List[Dict[str, Any]]:
        """Extract dominant colors using simple quantization"""
        try:
            # Resize for faster processing
            image = image.resize((150, 150))
            
            # Get all pixels
            pixels = list(image.getdata())
            
            # Simple clustering by rounding colors
            color_counts = {}
            for r, g, b in pixels:
                # Round to reduce color space
                key = (r // 32 * 32, g // 32 * 32, b // 32 * 32)
                color_counts[key] = color_counts.get(key, 0) + 1
            
            # Get top colors
            sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
            
            dominant = []
            total_pixels = len(pixels)
            
            for (r, g, b), count in sorted_colors[:num_colors]:
                percentage = count / total_pixels
                hex_color = f"#{r:02x}{g:02x}{b:02x}"
                
                dominant.append({
                    "rgb": [r, g, b],
                    "hex": hex_color,
                    "percentage": round(percentage * 100, 1)
                })
            
            return dominant
            
        except Exception as e:
            logger.error("Dominant color extraction failed", error=str(e))
            return []
    
    def analyze_quality(self, image: Image.Image) -> Dict[str, Any]:
        """Analyze image quality metrics"""
        try:
            quality_metrics = {}
            
            # Basic quality checks
            width, height = image.size
            
            # Resolution quality
            megapixels = (width * height) / 1000000
            quality_metrics["resolution_quality"] = (
                "high" if megapixels > 5 else
                "medium" if megapixels > 1 else "low"
            )
            
            # Aspect ratio check
            aspect_ratio = width / height if height > 0 else 1
            quality_metrics["aspect_ratio_standard"] = abs(aspect_ratio - 16/9) < 0.1 or abs(aspect_ratio - 4/3) < 0.1 or abs(aspect_ratio - 1) < 0.1
            
            # Brightness analysis
            if image.mode in ('RGB', 'L'):
                stat = ImageStat.Stat(image)
                brightness = sum(stat.mean) / len(stat.mean) / 255
                
                quality_metrics["brightness_analysis"] = {
                    "level": brightness,
                    "status": (
                        "overexposed" if brightness > 0.9 else
                        "underexposed" if brightness < 0.1 else
                        "good"
                    )
                }
            
            # If OpenCV is available, add more advanced metrics
            if self.cv2_available:
                quality_metrics.update(self._analyze_quality_cv2(image))
            
            return quality_metrics
            
        except Exception as e:
            logger.error("Quality analysis failed", error=str(e))
            return {"error": "Quality analysis failed"}
    
    def _analyze_quality_cv2(self, pil_image: Image.Image) -> Dict[str, Any]:
        """Advanced quality analysis using OpenCV"""
        try:
            # Convert PIL to OpenCV format
            cv_image = np.array(pil_image.convert('RGB'))
            cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
            
            # Blur detection using Laplacian variance
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            blur_score = min(10, max(0, laplacian_var / 100))
            blur_status = (
                "sharp" if laplacian_var > 500 else
                "moderate" if laplacian_var > 100 else "blurry"
            )
            
            # Noise estimation
            noise_level = self._estimate_noise(gray)
            
            # Contrast analysis
            contrast = gray.std()
            contrast_status = (
                "high" if contrast > 50 else
                "low" if contrast < 20 else "moderate"
            )
            
            return {
                "blur_analysis": {
                    "laplacian_variance": round(laplacian_var, 2),
                    "blur_score": round(blur_score, 1),
                    "status": blur_status
                },
                "noise_level": round(noise_level, 2),
                "contrast_analysis": {
                    "standard_deviation": round(contrast, 2),
                    "status": contrast_status
                }
            }
            
        except Exception as e:
            logger.error("OpenCV quality analysis failed", error=str(e))
            return {}
    
    def _estimate_noise(self, gray_image) -> float:
        """Estimate noise level in grayscale image"""
        try:
            # Use Laplacian to estimate noise
            laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
            noise = laplacian.var()
            return min(100, noise / 100)  # Normalize to 0-100 scale
        except:
            return 0.0
    
    def detect_objects_simple(self, image: Image.Image) -> List[Dict[str, Any]]:
        """Simple object detection using basic image analysis"""
        try:
            # This is a mock implementation - in real scenarios, you'd use:
            # - YOLO models
            # - TensorFlow Object Detection API
            # - OpenAI Vision API
            # - Other pre-trained models
            
            width, height = image.size
            
            # Mock object detection based on image properties
            objects = []
            
            # Simple heuristics based on image characteristics
            if image.mode == 'RGBA':
                objects.append({
                    "label": "transparent_object",
                    "confidence": 0.7,
                    "bbox": [width//4, height//4, width//2, height//2]
                })
            
            # Analyze dominant colors to guess content
            colors = self.analyze_colors(image)
            if colors and "dominant_colors" in colors:
                dominant = colors["dominant_colors"][0] if colors["dominant_colors"] else None
                if dominant:
                    r, g, b = dominant["rgb"]
                    if g > r and g > b:  # Greenish
                        objects.append({
                            "label": "vegetation",
                            "confidence": 0.6,
                            "bbox": [0, 0, width, height]
                        })
                    elif b > r and b > g:  # Bluish
                        objects.append({
                            "label": "sky_or_water",
                            "confidence": 0.6,
                            "bbox": [0, 0, width, height//2]
                        })
            
            # Add generic object based on image size
            if width > 800 and height > 600:
                objects.append({
                    "label": "scene",
                    "confidence": 0.8,
                    "bbox": [0, 0, width, height]
                })
            
            return objects
            
        except Exception as e:
            logger.error("Object detection failed", error=str(e))
            return []
    
    async def generate_caption_ai(self, image: Image.Image) -> Dict[str, Any]:
        """Generate image caption using AI models"""
        try:
            if self.openai_enabled:
                return await self._caption_with_openai(image)
            else:
                return self._generate_simple_caption(image)
                
        except Exception as e:
            logger.error("AI captioning failed, using simple method", error=str(e))
            return self._generate_simple_caption(image)
    
    async def _caption_with_openai(self, image: Image.Image) -> Dict[str, Any]:
        """Generate caption using OpenAI Vision API"""
        try:
            # Convert image to base64
            buffered = BytesIO()
            image.save(buffered, format="JPEG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe this image in detail. Focus on the main subjects, setting, colors, and mood."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            caption = response.choices[0].message.content.strip()
            
            return {
                "caption": caption,
                "method": "openai_vision",
                "confidence": 0.9,
                "word_count": len(caption.split())
            }
            
        except Exception as e:
            logger.error("OpenAI vision captioning failed", error=str(e))
            raise
    
    def _generate_simple_caption(self, image: Image.Image) -> Dict[str, Any]:
        """Generate simple caption based on image analysis"""
        try:
            width, height = image.size
            aspect_ratio = width / height if height > 0 else 1
            
            # Analyze image properties
            colors = self.analyze_colors(image)
            quality = self.analyze_quality(image)
            
            # Build caption parts
            caption_parts = []
            
            # Orientation description
            if aspect_ratio > 1.5:
                caption_parts.append("A wide")
            elif aspect_ratio < 0.7:
                caption_parts.append("A tall")
            else:
                caption_parts.append("A")
            
            # Resolution description
            megapixels = (width * height) / 1000000
            if megapixels > 5:
                caption_parts.append("high-resolution")
            elif megapixels < 1:
                caption_parts.append("low-resolution")
            
            # Color description
            if colors and "color_temperature" in colors:
                if colors["brightness"] > 0.7:
                    caption_parts.append("bright")
                elif colors["brightness"] < 0.3:
                    caption_parts.append("dark")
                
                caption_parts.append(colors["color_temperature"])
            
            # Format description
            caption_parts.append("image")
            
            # Add size information
            if megapixels >= 1:
                caption_parts.append(f"({width}x{height} pixels)")
            
            caption = " ".join(caption_parts)
            
            return {
                "caption": caption,
                "method": "rule_based",
                "confidence": 0.6,
                "word_count": len(caption.split())
            }
            
        except Exception as e:
            logger.error("Simple caption generation failed", error=str(e))
            return {
                "caption": "An image file",
                "method": "fallback",
                "confidence": 0.3,
                "word_count": 3
            }
    
    def enhance_image(self, image: Image.Image, enhancement_type: str = "auto") -> Tuple[Image.Image, Dict[str, Any]]:
        """Apply image enhancements"""
        try:
            enhanced = image.copy()
            operations = []
            
            if enhancement_type == "auto" or enhancement_type == "brightness":
                # Auto brightness adjustment
                stat = ImageStat.Stat(image)
                brightness = sum(stat.mean) / len(stat.mean) / 255
                
                if brightness < 0.4:  # Too dark
                    enhancer = ImageEnhance.Brightness(enhanced)
                    enhanced = enhancer.enhance(1.3)
                    operations.append("brightness_increase")
                elif brightness > 0.8:  # Too bright
                    enhancer = ImageEnhance.Brightness(enhanced)
                    enhanced = enhancer.enhance(0.8)
                    operations.append("brightness_decrease")
            
            if enhancement_type == "auto" or enhancement_type == "contrast":
                # Auto contrast adjustment
                enhancer = ImageEnhance.Contrast(enhanced)
                enhanced = enhancer.enhance(1.1)
                operations.append("contrast_enhance")
            
            if enhancement_type == "auto" or enhancement_type == "sharpness":
                # Sharpness enhancement
                enhancer = ImageEnhance.Sharpness(enhanced)
                enhanced = enhancer.enhance(1.2)
                operations.append("sharpness_enhance")
            
            enhancement_info = {
                "operations_applied": operations,
                "enhancement_type": enhancement_type,
                "success": True
            }
            
            return enhanced, enhancement_info
            
        except Exception as e:
            logger.error("Image enhancement failed", error=str(e))
            return image, {"success": False, "error": str(e)}
    
    def resize_image(self, image: Image.Image, max_size: Tuple[int, int] = (1920, 1080), maintain_aspect: bool = True) -> Tuple[Image.Image, Dict[str, Any]]:
        """Resize image while maintaining aspect ratio"""
        try:
            original_size = image.size
            
            if maintain_aspect:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                new_size = image.size
            else:
                image = image.resize(max_size, Image.Resampling.LANCZOS)
                new_size = max_size
            
            resize_info = {
                "original_size": original_size,
                "new_size": new_size,
                "resize_ratio": new_size[0] / original_size[0] if original_size[0] > 0 else 1,
                "bytes_saved_estimate": self._estimate_size_reduction(original_size, new_size)
            }
            
            return image, resize_info
            
        except Exception as e:
            logger.error("Image resize failed", error=str(e))
            return image, {"error": str(e)}
    
    def _estimate_size_reduction(self, original_size: Tuple[int, int], new_size: Tuple[int, int]) -> float:
        """Estimate file size reduction percentage"""
        original_pixels = original_size[0] * original_size[1]
        new_pixels = new_size[0] * new_size[1]
        
        if original_pixels == 0:
            return 0
        
        reduction = (1 - new_pixels / original_pixels) * 100
        return round(reduction, 2)