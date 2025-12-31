"""
PDF extraction pipeline with multiple fallback mechanisms
"""
import io
import base64
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# PDF extraction libraries
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from pdfminer.high_level import extract_text as pdfminer_extract
except ImportError:
    pdfminer_extract = None

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFExtractor:
    """PDF content extraction with fallback mechanisms"""
    
    def __init__(self):
        self.methods = [
            ('pdfplumber', self._extract_with_pdfplumber),
            ('PyMuPDF', self._extract_with_pymupdf),
            ('pdfminer', self._extract_with_pdfminer),
            ('OCR', self._extract_with_ocr),
        ]
    
    def extract(self, pdf_path: str) -> Dict[str, any]:
        """
        Extract content from PDF using fallback pipeline
        Returns: {
            'text': str,
            'pages': int,
            'method': str,
            'images': List[str],  # base64 encoded images
            'tables': List[Dict],
            'success': bool,
            'error': Optional[str]
        }
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            return {
                'success': False,
                'error': f'File not found: {pdf_path}',
                'text': '',
                'pages': 0,
                'method': None
            }
        
        # Try each extraction method in order
        for method_name, method_func in self.methods:
            try:
                logger.info(f"Attempting extraction with {method_name}...")
                result = method_func(pdf_path)
                
                if result and result.get('text') and len(result['text'].strip()) > 50:
                    result['method'] = method_name
                    result['success'] = True
                    logger.info(f"✓ Successfully extracted with {method_name}")
                    return result
                else:
                    logger.warning(f"✗ {method_name} extracted insufficient content")
            except Exception as e:
                logger.warning(f"✗ {method_name} failed: {str(e)}")
                continue
        
        # All methods failed
        return {
            'success': False,
            'error': 'All extraction methods failed',
            'text': '',
            'pages': 0,
            'method': None,
            'images': [],
            'tables': []
        }
    
    def _extract_with_pdfplumber(self, pdf_path: Path) -> Dict:
        """Extract using pdfplumber (best for tables and structured content)"""
        if not pdfplumber:
            raise ImportError("pdfplumber not available")
        
        text_parts = []
        tables = []
        images = []
        
        with pdfplumber.open(pdf_path) as pdf:
            pages = len(pdf.pages)
            
            for page_num, page in enumerate(pdf.pages):
                # Extract text
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"\n--- Page {page_num + 1} ---\n{page_text}")
                
                # Extract tables
                page_tables = page.extract_tables()
                if page_tables:
                    for table in page_tables:
                        tables.append({
                            'page': page_num + 1,
                            'data': table
                        })
        
        return {
            'text': '\n'.join(text_parts),
            'pages': pages,
            'images': images,
            'tables': tables
        }
    
    def _extract_with_pymupdf(self, pdf_path: Path) -> Dict:
        """Extract using PyMuPDF (good for images and general text)"""
        if not fitz:
            raise ImportError("PyMuPDF not available")
        
        text_parts = []
        images = []
        
        doc = fitz.open(pdf_path)
        pages = len(doc)
        
        for page_num in range(pages):
            page = doc[page_num]
            
            # Extract text
            page_text = page.get_text()
            if page_text:
                text_parts.append(f"\n--- Page {page_num + 1} ---\n{page_text}")
            
            # Extract images
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
                    images.append(f"data:image/png;base64,{image_b64}")
                except Exception as e:
                    logger.warning(f"Failed to extract image {img_index} from page {page_num + 1}: {e}")
        
        doc.close()
        
        return {
            'text': '\n'.join(text_parts),
            'pages': pages,
            'images': images,
            'tables': []
        }
    
    def _extract_with_pdfminer(self, pdf_path: Path) -> Dict:
        """Extract using pdfminer (fallback for text extraction)"""
        if not pdfminer_extract:
            raise ImportError("pdfminer not available")
        
        text = pdfminer_extract(str(pdf_path))
        
        # Estimate page count (rough approximation)
        pages = max(1, len(text) // 2000)
        
        return {
            'text': text,
            'pages': pages,
            'images': [],
            'tables': []
        }
    
    def _extract_with_ocr(self, pdf_path: Path) -> Dict:
        """Extract using OCR (last resort for scanned PDFs)"""
        if not pytesseract or not Image or not fitz:
            raise ImportError("OCR dependencies not available")
        
        text_parts = []
        doc = fitz.open(pdf_path)
        pages = len(doc)
        
        for page_num in range(pages):
            page = doc[page_num]
            
            # Convert page to image
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Perform OCR
            page_text = pytesseract.image_to_string(img)
            if page_text:
                text_parts.append(f"\n--- Page {page_num + 1} (OCR) ---\n{page_text}")
        
        doc.close()
        
        return {
            'text': '\n'.join(text_parts),
            'pages': pages,
            'images': [],
            'tables': []
        }


def extract_pdf_content(pdf_path: str) -> Dict:
    """
    Main function to extract PDF content
    """
    extractor = PDFExtractor()
    return extractor.extract(pdf_path)


if __name__ == "__main__":
    # Test extraction
    import sys
    if len(sys.argv) > 1:
        result = extract_pdf_content(sys.argv[1])
        print(f"Success: {result['success']}")
        print(f"Method: {result['method']}")
        print(f"Pages: {result['pages']}")
        print(f"Text length: {len(result['text'])}")
        print(f"Images: {len(result.get('images', []))}")
        print(f"Tables: {len(result.get('tables', []))}")
