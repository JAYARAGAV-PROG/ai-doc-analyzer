"""
Document profiler: Analyze document type, themes, purpose, and structure
"""
import re
import logging
from typing import Dict, List, Optional
from collections import Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentProfiler:
    """Generate document profiles for high-level understanding"""
    
    # Document type keywords
    DOCUMENT_TYPES = {
        'annual_report': [
            'annual report', 'fiscal year', 'financial statements', 'balance sheet',
            'income statement', 'cash flow', 'shareholders', 'revenue', 'earnings',
            'consolidated', 'fiscal', 'quarterly'
        ],
        'audit_report': [
            'audit', 'auditor', 'opinion', 'assurance', 'compliance', 'internal controls',
            'material misstatement', 'audit opinion', 'independent auditor', 'examination'
        ],
        'legal_document': [
            'contract', 'agreement', 'legal', 'terms and conditions', 'whereas',
            'party', 'parties', 'jurisdiction', 'liability', 'indemnity', 'covenant',
            'hereby', 'herein', 'clause'
        ],
        'financial_statement': [
            'balance sheet', 'income statement', 'cash flow statement', 'assets',
            'liabilities', 'equity', 'revenue', 'expenses', 'profit', 'loss'
        ],
        'sales_report': [
            'sales', 'revenue', 'units sold', 'market share', 'customer',
            'product performance', 'sales target', 'quarter', 'growth'
        ]
    }
    
    # Section keywords
    SECTION_KEYWORDS = {
        'introduction': ['introduction', 'overview', 'executive summary', 'summary'],
        'financial': ['financial', 'revenue', 'profit', 'loss', 'assets', 'liabilities'],
        'risk': ['risk', 'risks', 'risk factors', 'uncertainties', 'challenges'],
        'operations': ['operations', 'business operations', 'operational'],
        'management': ['management', 'board of directors', 'governance'],
        'legal': ['legal', 'compliance', 'regulatory', 'litigation'],
        'conclusion': ['conclusion', 'summary', 'outlook', 'future']
    }
    
    def __init__(self):
        pass
    
    def profile_document(self, text: str, filename: str = "") -> Dict:
        """
        Generate comprehensive document profile
        
        Returns: {
            'document_type': str,
            'confidence': float,
            'themes': List[str],
            'purpose': str,
            'scope': str,
            'key_sections': List[str],
            'summary': str
        }
        """
        if not text or len(text.strip()) < 100:
            return self._empty_profile()
        
        # Normalize text for analysis
        text_lower = text.lower()
        
        # Identify document type
        doc_type, confidence = self._identify_document_type(text_lower)
        
        # Extract themes
        themes = self._extract_themes(text_lower)
        
        # Identify key sections
        sections = self._identify_sections(text_lower)
        
        # Generate purpose and scope
        purpose = self._infer_purpose(doc_type, themes)
        scope = self._infer_scope(text_lower, doc_type)
        
        # Generate summary
        summary = self._generate_summary(doc_type, themes, sections)
        
        profile = {
            'document_type': doc_type,
            'confidence': confidence,
            'themes': themes,
            'purpose': purpose,
            'scope': scope,
            'key_sections': sections,
            'summary': summary,
            'filename': filename
        }
        
        logger.info(f"Document profile: {doc_type} (confidence: {confidence:.2f})")
        return profile
    
    def _identify_document_type(self, text: str) -> tuple[str, float]:
        """Identify document type based on keyword matching"""
        scores = {}
        
        for doc_type, keywords in self.DOCUMENT_TYPES.items():
            score = sum(1 for keyword in keywords if keyword in text)
            scores[doc_type] = score
        
        if not scores or max(scores.values()) == 0:
            return 'general_document', 0.5
        
        best_type = max(scores, key=scores.get)
        max_score = scores[best_type]
        total_keywords = len(self.DOCUMENT_TYPES[best_type])
        confidence = min(1.0, max_score / (total_keywords * 0.3))
        
        return best_type, confidence
    
    def _extract_themes(self, text: str) -> List[str]:
        """Extract main themes from document"""
        themes = []
        
        # Financial themes
        if any(word in text for word in ['revenue', 'profit', 'financial', 'earnings']):
            themes.append('Financial Performance')
        
        # Risk themes
        if any(word in text for word in ['risk', 'uncertainty', 'challenge', 'threat']):
            themes.append('Risk Management')
        
        # Growth themes
        if any(word in text for word in ['growth', 'expansion', 'increase', 'development']):
            themes.append('Business Growth')
        
        # Compliance themes
        if any(word in text for word in ['compliance', 'regulatory', 'legal', 'audit']):
            themes.append('Compliance & Regulation')
        
        # Operations themes
        if any(word in text for word in ['operations', 'operational', 'efficiency', 'process']):
            themes.append('Operations')
        
        # Strategy themes
        if any(word in text for word in ['strategy', 'strategic', 'vision', 'mission']):
            themes.append('Strategic Planning')
        
        return themes[:5]  # Return top 5 themes
    
    def _identify_sections(self, text: str) -> List[str]:
        """Identify key sections present in document"""
        sections = []
        
        for section_name, keywords in self.SECTION_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                sections.append(section_name.title())
        
        return sections
    
    def _infer_purpose(self, doc_type: str, themes: List[str]) -> str:
        """Infer document purpose based on type and themes"""
        purpose_map = {
            'annual_report': 'To provide stakeholders with a comprehensive overview of the company\'s financial performance and operations for the fiscal year.',
            'audit_report': 'To provide an independent assessment of the accuracy and compliance of financial statements.',
            'legal_document': 'To establish legal terms, conditions, and obligations between parties.',
            'financial_statement': 'To present the financial position and performance of the organization.',
            'sales_report': 'To analyze sales performance, trends, and market dynamics.',
            'general_document': 'To provide information and analysis on business-related topics.'
        }
        
        return purpose_map.get(doc_type, purpose_map['general_document'])
    
    def _infer_scope(self, text: str, doc_type: str) -> str:
        """Infer document scope"""
        # Look for time period indicators
        year_pattern = r'\b(20\d{2}|19\d{2})\b'
        years = re.findall(year_pattern, text)
        
        if years:
            year_range = f"{min(years)} to {max(years)}" if len(set(years)) > 1 else years[0]
            return f"Covers period: {year_range}"
        
        # Look for scope indicators
        if 'comprehensive' in text or 'complete' in text:
            return "Comprehensive coverage"
        elif 'summary' in text or 'overview' in text:
            return "Summary overview"
        else:
            return "Standard scope"
    
    def _generate_summary(self, doc_type: str, themes: List[str], sections: List[str]) -> str:
        """Generate a brief summary of the document"""
        doc_type_readable = doc_type.replace('_', ' ').title()
        themes_str = ', '.join(themes) if themes else 'various topics'
        sections_str = ', '.join(sections[:3]) if sections else 'multiple sections'
        
        summary = f"This {doc_type_readable} covers {themes_str}. "
        summary += f"Key sections include: {sections_str}."
        
        return summary
    
    def _empty_profile(self) -> Dict:
        """Return empty profile for invalid documents"""
        return {
            'document_type': 'unknown',
            'confidence': 0.0,
            'themes': [],
            'purpose': 'Unknown',
            'scope': 'Unknown',
            'key_sections': [],
            'summary': 'Unable to generate profile for this document.',
            'filename': ''
        }


# Global instance
_profiler = None


def get_profiler() -> DocumentProfiler:
    """Get or create document profiler instance"""
    global _profiler
    if _profiler is None:
        _profiler = DocumentProfiler()
    return _profiler


if __name__ == "__main__":
    # Test profiler
    profiler = get_profiler()
    test_text = """
    Annual Report 2023
    
    This annual report provides a comprehensive overview of our financial performance
    for the fiscal year ending December 31, 2023. Our revenue increased by 15% to
    $500 million, driven by strong sales growth in our core markets.
    
    Risk Factors:
    The company faces various risks including market volatility and regulatory changes.
    """
    
    profile = profiler.profile_document(test_text)
    print("Document Profile:")
    for key, value in profile.items():
        print(f"  {key}: {value}")
