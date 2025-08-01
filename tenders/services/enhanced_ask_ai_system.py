"""
CORRECTED Enhanced Ask AI System - Compatible with existing codebase
File: tenders/services/enhanced_ask_ai_system.py
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
import anthropic
from django.conf import settings
from django.db import transaction
from django.core.cache import cache
from django.core.exceptions import ValidationError

# Import existing services - using the correct paths from your project
try:
    from .ai_analysis import OptimizedSharePointService, DocumentParser, ClaudeAIService
    SERVICES_AVAILABLE = True
except ImportError:
    # Fallback if services aren't available
    SERVICES_AVAILABLE = False

# Import models
from ..models import TenderAnalysis, AIConversation, AIQuestion
from projects.models import Project

logger = logging.getLogger(__name__)

class EnhancedDocumentQuestionAnswerer:
    """
    Enhanced AI question answering system that analyzes entire SharePoint document suite
    Compatible with existing codebase
    """
    
    def __init__(self):
        if not SERVICES_AVAILABLE:
            raise ImportError("Required services not available")
            
        self.client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
        self.sharepoint_service = OptimizedSharePointService()
        self.document_parser = DocumentParser()
        self.claude_service = ClaudeAIService()
        
    def answer_question_comprehensive(self, project: Project, question: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Answer question using comprehensive analysis of entire SharePoint document suite
        """
        try:
            # Step 1: Get comprehensive document suite
            documents_data = self._get_comprehensive_documents(project, use_cache)
            
            # Step 2: Analyze question context
            question_analysis = self._analyze_question_context(question, documents_data)
            
            # Step 3: Generate comprehensive answer
            answer_data = self._generate_comprehensive_answer(
                question, 
                documents_data, 
                question_analysis,
                project
            )
            
            # Step 4: Save question and answer
            self._save_question_answer(project, question, answer_data)
            
            return answer_data
            
        except Exception as e:
            logger.error(f"Error in comprehensive question answering: {str(e)}")
            return {
                'answer': f'I apologize, but I encountered an error while analyzing the documents: {str(e)}',
                'confidence': 0,
                'sources': [],
                'document_analysis': {},
                'error': str(e)
            }
    
    def _get_comprehensive_documents(self, project: Project, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get comprehensive document suite from SharePoint with caching
        """
        cache_key = f"comprehensive_docs_{project.id}"
        
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"Using cached document data for project {project.id}")
                return cached_data
        
        logger.info(f"Fetching comprehensive document suite for project {project.id}")
        
        try:
            # Use existing SharePoint service methods
            documents = self.sharepoint_service.get_folder_documents_recursive_fast(
                project.sharepoint_folder_url,
                max_depth=10
            )
            
            if not documents:
                raise ValueError("No documents found in SharePoint folder")
            
            # Process documents by category
            document_data = {
                'total_documents': len(documents),
                'documents_by_category': {},
                'document_contents': {},
                'document_metadata': {},
                'folder_structure': {},
                'combined_content': "",
                'processing_summary': {
                    'successful': 0,
                    'failed': 0,
                    'total_size': 0,
                    'document_types': {}
                }
            }
            
            # Process each document using existing methods
            for doc in documents:
                try:
                    # Get document content using existing service
                    content = self.sharepoint_service.download_document_content(doc['download_url'])
                    
                    if content and content.strip():
                        # Extract text using existing parser
                        text = self.document_parser.extract_text(
                            content, 
                            doc.get('mime_type', 'application/octet-stream'), 
                            doc.get('name', '')
                        )
                        
                        if text and text.strip():
                            # Categorize document
                            category = self._categorize_document(doc['name'], text)
                            
                            # Store content
                            document_data['document_contents'][doc['name']] = text
                            document_data['document_metadata'][doc['name']] = {
                                'category': category,
                                'size': len(text),
                                'url': doc.get('download_url', ''),
                                'folder': doc.get('folder_path', ''),
                                'mime_type': doc.get('mime_type', ''),
                                'content_summary': self._summarize_content(text)
                            }
                            
                            # Add to category
                            if category not in document_data['documents_by_category']:
                                document_data['documents_by_category'][category] = []
                            document_data['documents_by_category'][category].append(doc['name'])
                            
                            # Add to combined content
                            document_data['combined_content'] += f"\n\n=== {doc['name']} ({category}) ===\n{text}"
                            
                            # Update processing summary
                            document_data['processing_summary']['successful'] += 1
                            document_data['processing_summary']['total_size'] += len(text)
                            
                            # Track document types
                            file_ext = doc['name'].split('.')[-1].lower() if '.' in doc['name'] else 'unknown'
                            document_data['processing_summary']['document_types'][file_ext] = \
                                document_data['processing_summary']['document_types'].get(file_ext, 0) + 1
                            
                            # Track folder structure
                            folder = doc.get('folder_path', 'Root')
                            if folder not in document_data['folder_structure']:
                                document_data['folder_structure'][folder] = []
                            document_data['folder_structure'][folder].append(doc['name'])
                        
                    else:
                        logger.warning(f"No content extracted from {doc['name']}")
                        document_data['processing_summary']['failed'] += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to process document {doc['name']}: {str(e)}")
                    document_data['processing_summary']['failed'] += 1
                    continue
            
            # Cache the processed data (for 1 hour)
            cache.set(cache_key, document_data, 3600)
            
            logger.info(f"Processed {document_data['processing_summary']['successful']} documents successfully")
            return document_data
            
        except Exception as e:
            logger.error(f"Error getting comprehensive documents: {str(e)}")
            raise
    
    def _categorize_document(self, filename: str, content: str) -> str:
        """
        Categorize document based on filename and content
        """
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        # Define categories and their indicators
        categories = {
            'CONTRACT': ['contract', 'agreement', 'terms', 'conditions', 'jct', 'nec'],
            'DRAWINGS': ['drawing', 'plan', 'elevation', 'section', 'detail', 'dwg'],
            'SPECIFICATIONS': ['specification', 'spec', 'technical', 'standard', 'requirement'],
            'SCHEDULE': ['schedule', 'programme', 'timeline', 'dates', 'milestones'],
            'PRICING': ['pricing', 'rates', 'cost', 'estimate', 'budget', 'bill of quantities', 'boq'],
            'HEALTH_SAFETY': ['health', 'safety', 'cdm', 'risk assessment', 'method statement'],
            'ENVIRONMENTAL': ['environmental', 'sustainability', 'breeam', 'carbon', 'energy'],
            'TENDER_DOCS': ['tender', 'invitation', 'itt', 'itq', 'rfq', 'proposal'],
            'STRUCTURAL': ['structural', 'foundation', 'concrete', 'steel', 'load'],
            'MEP': ['mechanical', 'electrical', 'plumbing', 'hvac', 'services', 'm&e'],
            'PLANNING': ['planning', 'permission', 'consent', 'application', 'approved'],
            'SURVEYS': ['survey', 'investigation', 'report', 'assessment', 'condition'],
            'CORRESPONDENCE': ['email', 'letter', 'memo', 'correspondence', 'meeting']
        }
        
        # Check filename first
        for category, keywords in categories.items():
            if any(keyword in filename_lower for keyword in keywords):
                return category
        
        # Check content for better categorization
        for category, keywords in categories.items():
            keyword_count = sum(1 for keyword in keywords if keyword in content_lower)
            if keyword_count >= 2:
                return category
        
        return 'OTHER'
    
    def _summarize_content(self, content: str) -> str:
        """
        Create a brief summary of document content
        """
        sentences = content.split('.')[:3]
        summary = '. '.join(sentences)
        
        if len(summary) > 200:
            summary = summary[:200] + "..."
        
        return summary
    
    def _analyze_question_context(self, question: str, documents_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze question context to determine best approach
        """
        question_lower = question.lower()
        
        # Identify question type
        question_types = {
            'SPECIFIC_SEARCH': ['what is', 'define', 'explain', 'describe'],
            'COMPARISON': ['compare', 'difference', 'versus', 'vs', 'better'],
            'QUANTITATIVE': ['how much', 'how many', 'cost', 'price', 'value', 'budget'],
            'TEMPORAL': ['when', 'date', 'timeline', 'schedule', 'duration'],
            'LOCATION': ['where', 'location', 'site', 'address'],
            'PROCESS': ['how to', 'process', 'procedure', 'steps', 'method'],
            'RISK': ['risk', 'danger', 'hazard', 'safety', 'problem'],
            'COMPLIANCE': ['regulation', 'compliance', 'standard', 'requirement', 'code']
        }
        
        identified_types = []
        for q_type, keywords in question_types.items():
            if any(keyword in question_lower for keyword in keywords):
                identified_types.append(q_type)
        
        # Identify relevant document categories
        relevant_categories = []
        for category in documents_data['documents_by_category'].keys():
            category_keywords = {
                'CONTRACT': ['contract', 'terms', 'payment', 'legal'],
                'DRAWINGS': ['drawing', 'plan', 'design', 'layout'],
                'SPECIFICATIONS': ['spec', 'technical', 'material', 'standard'],
                'SCHEDULE': ['schedule', 'timeline', 'date', 'programme'],
                'PRICING': ['cost', 'price', 'budget', 'estimate'],
                'HEALTH_SAFETY': ['safety', 'health', 'risk', 'cdm'],
                'ENVIRONMENTAL': ['environmental', 'sustainability', 'carbon'],
                'TENDER_DOCS': ['tender', 'proposal', 'submission'],
                'STRUCTURAL': ['structural', 'foundation', 'concrete'],
                'MEP': ['electrical', 'mechanical', 'services'],
                'PLANNING': ['planning', 'permission', 'consent'],
                'SURVEYS': ['survey', 'condition', 'investigation']
            }
            
            keywords = category_keywords.get(category, [])
            if any(keyword in question_lower for keyword in keywords):
                relevant_categories.append(category)
        
        return {
            'question_types': identified_types,
            'relevant_categories': relevant_categories if relevant_categories else list(documents_data['documents_by_category'].keys()),
            'complexity': 'HIGH' if len(identified_types) > 1 else 'MEDIUM' if identified_types else 'LOW',
            'requires_cross_reference': any(t in identified_types for t in ['COMPARISON', 'COMPLIANCE', 'RISK'])
        }
    
    def _generate_comprehensive_answer(self, question: str, documents_data: Dict[str, Any], 
                                     question_analysis: Dict[str, Any], project: Project) -> Dict[str, Any]:
        """
        Generate comprehensive answer using existing Claude service
        """
        try:
            # Prepare context based on question analysis
            relevant_content = self._prepare_relevant_content(documents_data, question_analysis)
            
            # Use existing Claude service for analysis
            prompt = f"""
You are an expert construction project analyst. Analyze the complete document collection and provide a detailed answer.

PROJECT: {project.name}
QUESTION: {question}

DOCUMENTS ANALYZED: {documents_data['total_documents']} documents across {len(documents_data['documents_by_category'])} categories

Please provide a comprehensive response with:
1. Direct answer to the question
2. Key findings from the documents
3. Specific document references
4. Confidence level (0-100)
5. Any recommendations

Document content: {relevant_content[:15000]}
"""
            
            # Use existing Claude service
            response = self.claude_service.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=3000,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            
            answer_text = response.content[0].text
            
            # Parse response
            answer_data = {
                'answer': answer_text,
                'confidence': self._calculate_confidence(answer_text),
                'source_documents': list(documents_data['document_contents'].keys())[:5],
                'document_analysis': {
                    'total_documents_analyzed': documents_data['total_documents'],
                    'document_categories': list(documents_data['documents_by_category'].keys()),
                    'relevant_categories': question_analysis['relevant_categories'],
                    'question_complexity': question_analysis['complexity'],
                    'processing_summary': documents_data['processing_summary']
                },
                'analysis_type': 'COMPREHENSIVE'
            }
            
            return answer_data
            
        except Exception as e:
            logger.error(f"Error generating comprehensive answer: {str(e)}")
            raise
    
    def _prepare_relevant_content(self, documents_data: Dict[str, Any], 
                                question_analysis: Dict[str, Any]) -> str:
        """
        Prepare relevant content based on question analysis
        """
        relevant_content = ""
        
        # Prioritize relevant categories
        for category in question_analysis['relevant_categories']:
            if category in documents_data['documents_by_category']:
                relevant_content += f"\n\n=== {category} DOCUMENTS ===\n"
                
                for doc_name in documents_data['documents_by_category'][category]:
                    if doc_name in documents_data['document_contents']:
                        content = documents_data['document_contents'][doc_name]
                        # Limit content per document
                        if len(content) > 3000:
                            content = content[:3000] + "...[truncated]"
                        relevant_content += f"\n--- {doc_name} ---\n{content}\n"
        
        # If no specific categories, use all content (limited)
        if not relevant_content.strip():
            relevant_content = documents_data['combined_content'][:20000]
        
        return relevant_content
    
    def _calculate_confidence(self, text: str) -> float:
        """
        Calculate analysis confidence based on content detail
        """
        confidence_factors = {
            'specific_dates': 10,
            'specific_values': 15,
            'detailed_specs': 10,
            'client_info': 5,
            'contract_terms': 10,
            'risk_details': 5
        }
        
        base_confidence = 50.0
        text_lower = text.lower()
        
        # Check for specific information
        if re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', text):
            base_confidence += confidence_factors['specific_dates']
        
        if re.search(r'£[\d,]+', text):
            base_confidence += confidence_factors['specific_values']
        
        if len(text) > 2000:
            base_confidence += confidence_factors['detailed_specs']
        
        # Cap at 95%
        return min(base_confidence, 95.0)
    
    def _save_question_answer(self, project: Project, question: str, answer_data: Dict[str, Any]) -> None:
        """
        Save question and answer for future reference
        """
        try:
            # Get or create conversation
            conversation, created = AIConversation.objects.get_or_create(
                project=project,
                defaults={
                    'title': f"Questions about {project.name}",
                    'created_date': datetime.now()
                }
            )
            
            # Save question
            AIQuestion.objects.create(
                conversation=conversation,
                question_text=question,
                answer_text=answer_data['answer'],
                confidence_score=int(answer_data['confidence']),
                source_documents=answer_data.get('source_documents', []),
                document_references=answer_data.get('document_references', []),
                analysis_metadata=answer_data
            )
            
            logger.info(f"Saved question/answer for project {project.id}")
            
        except Exception as e:
            logger.warning(f"Failed to save question/answer: {str(e)}")
    
    def clear_document_cache(self, project: Project) -> None:
        """
        Clear cached document data for a project
        """
        cache_key = f"comprehensive_docs_{project.id}"
        cache.delete(cache_key)
        logger.info(f"Cleared document cache for project {project.id}")


# Helper functions
def get_enhanced_question_answerer():
    """Get enhanced question answerer instance"""
    try:
        return EnhancedDocumentQuestionAnswerer()
    except Exception as e:
        logger.error(f"Failed to initialize enhanced question answerer: {str(e)}")
        return None

def ask_comprehensive_question(project: Project, question: str) -> Dict[str, Any]:
    """
    Main function to ask comprehensive questions
    """
    answerer = get_enhanced_question_answerer()
    if not answerer:
        return {
            'answer': 'AI question answering service is not available',
            'confidence': 0,
            'error': 'Service unavailable'
        }
    
    return answerer.answer_question_comprehensive(project, question)