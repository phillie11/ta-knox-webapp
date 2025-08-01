import re
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class QuestionAnalyzer:
    """Analyze user questions to determine intent and relevant document categories"""
    
    def __init__(self):
        self.category_keywords = {
            'technical': ['technical', 'specification', 'material', 'equipment', 'system', 'method'],
            'commercial': ['cost', 'price', 'budget', 'payment', 'value', 'tender', 'bid'],
            'programme': ['schedule', 'timeline', 'duration', 'milestone', 'date', 'completion'],
            'drawings': ['drawing', 'plan', 'layout', 'design', 'detail', 'section'],
            'contracts': ['contract', 'terms', 'conditions', 'clause', 'liability', 'insurance'],
            'health_safety': ['safety', 'health', 'risk', 'hazard', 'protection', 'welfare'],
            'scope': ['scope', 'work', 'inclusion', 'exclusion', 'boundary', 'responsibility'],
            'quality': ['quality', 'standard', 'compliance', 'testing', 'inspection']
        }
        
        self.complexity_indicators = {
            'simple': ['what is', 'where', 'when', 'who'],
            'moderate': ['how', 'why', 'explain', 'describe'],
            'complex': ['analyze', 'compare', 'evaluate', 'assess', 'recommend']
        }
    
    def analyze_question(self, question: str) -> Dict[str, Any]:
        """Analyze question to understand intent and complexity"""
        question_lower = question.lower()
        
        # Determine relevant categories
        relevant_categories = []
        for category, keywords in self.category_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                relevant_categories.append(category)
        
        # If no specific categories found, include all
        if not relevant_categories:
            relevant_categories = ['general', 'technical', 'commercial']
        
        # Determine complexity
        complexity = 'simple'
        for level, indicators in self.complexity_indicators.items():
            if any(indicator in question_lower for indicator in indicators):
                complexity = level
                break
        
        # Extract key terms for search
        key_terms = self._extract_key_terms(question)
        
        return {
            'relevant_categories': relevant_categories,
            'complexity': complexity,
            'key_terms': key_terms,
            'question_type': self._classify_question_type(question_lower),
            'requires_cross_reference': len(relevant_categories) > 1
        }
    
    def _extract_key_terms(self, question: str) -> List[str]:
        """Extract meaningful terms from question"""
        stop_words = {'the', 'is', 'are', 'what', 'where', 'when', 'how', 'why', 'can', 'will', 'would', 'should'}
        words = re.findall(r'\b\w+\b', question.lower())
        key_terms = [word for word in words if len(word) > 3 and word not in stop_words]
        return key_terms[:10]  # Limit to top 10 terms
    
    def _classify_question_type(self, question: str) -> str:
        """Classify the type of question"""
        if any(word in question for word in ['what', 'define', 'explain']):
            return 'informational'
        elif any(word in question for word in ['how much', 'cost', 'price']):
            return 'financial'
        elif any(word in question for word in ['when', 'schedule', 'timeline']):
            return 'temporal'
        elif any(word in question for word in ['where', 'location', 'site']):
            return 'spatial'
        elif any(word in question for word in ['how', 'process', 'method']):
            return 'procedural'
        else:
            return 'general'













