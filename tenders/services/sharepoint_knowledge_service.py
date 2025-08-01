import logging
import time
from typing import Dict, List, Any, Optional
from django.core.cache import cache
from django.conf import settings
from .ai_analysis import OptimizedSharePointService, DocumentParser, ClaudeAIService

logger = logging.getLogger(__name__)

class SharePointKnowledgeService:
    """Enhanced service for creating comprehensive project knowledge from SharePoint documents"""
    
    def __init__(self):
        self.sharepoint_service = OptimizedSharePointService()
        self.document_parser = DocumentParser()
        self.claude_service = ClaudeAIService()
        self.cache_timeout = getattr(settings, 'KNOWLEDGE_CACHE_TIMEOUT', 3600)
    
    def build_project_knowledge_base(self, project, force_refresh=False):
        """Build comprehensive knowledge base from all SharePoint documents"""
        cache_key = f"project_knowledge_{project.id}"
        
        if not force_refresh:
            cached_knowledge = cache.get(cache_key)
            if cached_knowledge:
                logger.info(f"Using cached knowledge base for project {project.name}")
                return cached_knowledge
        
        logger.info(f"Building fresh knowledge base for project {project.name}")
        
        try:
            # Get all documents recursively from SharePoint
            documents = self.sharepoint_service.get_folder_documents_recursive(
                project.sharepoint_folder_url, max_depth=5
            )
            
            if not documents:
                raise ValueError("No documents found in SharePoint folder")
            
            # Initialize knowledge base structure
            knowledge_base = {
                'project_info': {
                    'name': project.name,
                    'location': project.location,
                    'reference': project.reference,
                    'sharepoint_url': project.sharepoint_folder_url
                },
                'documents_by_category': {},
                'document_contents': {},
                'document_metadata': {},
                'search_index': {},
                'processing_summary': {
                    'total_documents': len(documents),
                    'processed_successfully': 0,
                    'processing_errors': 0,
                    'total_content_length': 0,
                    'document_types': {}
                }
            }
            
            # Process each document
            for doc in documents[:50]:  # Limit to 50 documents for performance
                try:
                    doc_name = doc.get('name', 'Unknown')
                    doc_category = self._categorize_document(doc_name)
                    
                    # Download and extract content
                    content = self.sharepoint_service.download_document_content(doc['download_url'])
                    
                    if content:
                        text = self.document_parser.extract_text(
                            content,
                            doc.get('mime_type', 'application/octet-stream'),
                            doc_name
                        )
                        
                        if text and len(text.strip()) > 50:
                            # Store content by category
                            if doc_category not in knowledge_base['documents_by_category']:
                                knowledge_base['documents_by_category'][doc_category] = []
                            
                            knowledge_base['documents_by_category'][doc_category].append({
                                'name': doc_name,
                                'content': text[:8000],  # Limit content length
                                'path': doc.get('path', ''),
                                'size': len(text),
                                'type': doc.get('mime_type', '')
                            })
                            
                            # Store full content for search
                            knowledge_base['document_contents'][doc_name] = text
                            
                            # Build search index
                            self._add_to_search_index(knowledge_base['search_index'], doc_name, text)
                            
                            # Update processing summary
                            knowledge_base['processing_summary']['processed_successfully'] += 1
                            knowledge_base['processing_summary']['total_content_length'] += len(text)
                            
                            doc_type = doc.get('mime_type', 'unknown').split('/')[-1]
                            knowledge_base['processing_summary']['document_types'][doc_type] = \
                                knowledge_base['processing_summary']['document_types'].get(doc_type, 0) + 1
                
                except Exception as e:
                    logger.warning(f"Error processing document {doc.get('name', 'unknown')}: {str(e)}")
                    knowledge_base['processing_summary']['processing_errors'] += 1
            
            # Cache the knowledge base
            cache.set(cache_key, knowledge_base, self.cache_timeout)
            
            logger.info(f"Knowledge base built: {knowledge_base['processing_summary']['processed_successfully']} documents processed")
            return knowledge_base
            
        except Exception as e:
            logger.error(f"Error building knowledge base: {str(e)}")
            raise
    
    def _categorize_document(self, doc_name):
        """Categorize document based on name patterns"""
        doc_name_lower = doc_name.lower()
        
        if any(term in doc_name_lower for term in ['drawing', 'plan', 'dwg', 'pdf']):
            return 'drawings'
        elif any(term in doc_name_lower for term in ['spec', 'specification', 'technical']):
            return 'specifications'
        elif any(term in doc_name_lower for term in ['contract', 'terms', 'conditions']):
            return 'contracts'
        elif any(term in doc_name_lower for term in ['schedule', 'programme', 'timeline']):
            return 'schedules'
        elif any(term in doc_name_lower for term in ['cost', 'budget', 'price', 'bill']):
            return 'commercial'
        elif any(term in doc_name_lower for term in ['health', 'safety', 'risk']):
            return 'health_safety'
        else:
            return 'general'
    
    def _add_to_search_index(self, search_index, doc_name, content):
        """Build simple search index for quick content lookup"""
        words = content.lower().split()
        for word in words:
            if len(word) > 3:  # Only index meaningful words
                if word not in search_index:
                    search_index[word] = []
                if doc_name not in search_index[word]:
                    search_index[word].append(doc_name)
    
    def search_knowledge_base(self, knowledge_base, query_terms):
        """Search knowledge base for relevant documents"""
        relevant_docs = set()
        
        for term in query_terms:
            term_lower = term.lower()
            if term_lower in knowledge_base['search_index']:
                relevant_docs.update(knowledge_base['search_index'][term_lower])
        
        return list(relevant_docs)













