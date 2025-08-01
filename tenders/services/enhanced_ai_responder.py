import logging
import time
import re
from typing import Dict, List, Any, Optional
from django.conf import settings
from .sharepoint_knowledge_service import SharePointKnowledgeService
from .question_analyzer import QuestionAnalyzer
from .ai_analysis import ClaudeAIService

logger = logging.getLogger(__name__)

class EnhancedAIResponder:
    """Generate comprehensive AI responses using full SharePoint project knowledge"""
    
    def __init__(self):
        self.knowledge_service = SharePointKnowledgeService()
        self.question_analyzer = QuestionAnalyzer()
        self.claude_service = ClaudeAIService()
    
    def generate_comprehensive_response(self, project, question: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Generate comprehensive AI response using full project knowledge"""
        start_time = time.time()
        
        try:
            # Analyze the question
            question_analysis = self.question_analyzer.analyze_question(question)
            logger.info(f"Question analysis: {question_analysis}")
            
            # Build/get knowledge base
            knowledge_base = self.knowledge_service.build_project_knowledge_base(
                project, force_refresh=force_refresh
            )
            
            # Find relevant documents
            relevant_docs = self.knowledge_service.search_knowledge_base(
                knowledge_base, question_analysis['key_terms']
            )
            
            # Prepare context for AI
            context = self._prepare_ai_context(
                knowledge_base, question_analysis, relevant_docs, question
            )
            
            # Generate AI response
            ai_response = self._generate_ai_response(context, question, project)
            
            # Store conversation
            self._store_conversation(project, question, ai_response)
            
            processing_time = round(time.time() - start_time, 2)
            
            response = {
                'success': True,
                'answer': ai_response.get('answer', ''),
                'confidence': ai_response.get('confidence', 50),
                'key_findings': ai_response.get('key_findings', []),
                'source_documents': relevant_docs[:5],
                'document_references': ai_response.get('document_references', []),
                'cross_references': ai_response.get('cross_references', []),
                'recommendations': ai_response.get('recommendations', []),
                'follow_up_questions': ai_response.get('follow_up_questions', []),
                'knowledge_base_stats': {
                    'total_documents': knowledge_base['processing_summary']['total_documents'],
                    'processed_documents': knowledge_base['processing_summary']['processed_successfully'],
                    'document_categories': list(knowledge_base['documents_by_category'].keys()),
                    'relevant_documents_found': len(relevant_docs)
                },
                'processing_time': processing_time,
                'analysis_type': 'COMPREHENSIVE_SHAREPOINT'
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating comprehensive response: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to generate response: {str(e)}',
                'analysis_type': 'ERROR'
            }
    
    def _prepare_ai_context(self, knowledge_base, question_analysis, relevant_docs, question):
        """Prepare comprehensive context for AI analysis"""
        relevant_content = ""
        
        # Include content from relevant categories
        for category in question_analysis['relevant_categories']:
            if category in knowledge_base['documents_by_category']:
                relevant_content += f"\n\n=== {category.upper()} DOCUMENTS ===\n"
                for doc in knowledge_base['documents_by_category'][category][:3]:
                    relevant_content += f"\n--- {doc['name']} ---\n{doc['content'][:2000]}\n"
        
        # Include specific relevant documents
        for doc_name in relevant_docs[:5]:
            if doc_name in knowledge_base['document_contents']:
                relevant_content += f"\n\n=== {doc_name} ===\n"
                relevant_content += knowledge_base['document_contents'][doc_name][:3000]
        
        return {
            'project_info': knowledge_base['project_info'],
            'question': question,
            'question_analysis': question_analysis,
            'relevant_content': relevant_content[:25000],
            'knowledge_stats': knowledge_base['processing_summary'],
            'available_categories': list(knowledge_base['documents_by_category'].keys())
        }
    
    def _generate_ai_response(self, context, question, project):
        """Generate AI response using Claude"""
        prompt = f"""
You are an expert construction project analyst with access to comprehensive project documentation. 
Analyze the complete project knowledge base and provide a detailed, accurate response.

PROJECT: {context['project_info']['name']}
LOCATION: {context['project_info'].get('location', 'Not specified')}

QUESTION: {question}

AVAILABLE DOCUMENT CATEGORIES: {', '.join(context['available_categories'])}
DOCUMENTS ANALYZED: {context['knowledge_stats']['processed_successfully']} documents

RELEVANT PROJECT CONTENT:
{context['relevant_content']}

Please provide a comprehensive response with:

1. **DIRECT ANSWER**: Clear, specific answer to the question
2. **KEY FINDINGS**: Important points discovered in the documents  
3. **DOCUMENT REFERENCES**: Specific documents that support your answer
4. **CROSS REFERENCES**: Related information from other documents
5. **RECOMMENDATIONS**: Actionable recommendations based on the analysis
6. **FOLLOW-UP QUESTIONS**: Suggested questions for deeper understanding
7. **CONFIDENCE LEVEL**: Your confidence in the answer (0-100)

Format your response clearly with headings and bullet points where appropriate.
Reference specific document names and quote relevant sections when possible.
"""
        
        try:
            if self.claude_service.claude_available:
                response = self.claude_service.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                response_text = response.content[0].text
                return self._parse_ai_response(response_text)
            else:
                return {
                    'answer': 'AI service unavailable. Please check configuration.',
                    'confidence': 0,
                    'key_findings': [],
                    'document_references': [],
                    'cross_references': [],
                    'recommendations': [],
                    'follow_up_questions': []
                }
                
        except Exception as e:
            logger.error(f"Error calling Claude AI: {str(e)}")
            return {
                'answer': f'Error generating AI response: {str(e)}',
                'confidence': 0,
                'key_findings': [],
                'document_references': [],
                'cross_references': [],
                'recommendations': [],
                'follow_up_questions': []
            }
    
    def _parse_ai_response(self, response_text):
        """Parse structured AI response"""
        sections = {
            'answer': self._extract_section(response_text, r'DIRECT ANSWER[:\s]*(.+?)(?=\*\*|$)', ''),
            'key_findings': self._extract_list_section(response_text, r'KEY FINDINGS[:\s]*(.+?)(?=\*\*|$)'),
            'document_references': self._extract_list_section(response_text, r'DOCUMENT REFERENCES[:\s]*(.+?)(?=\*\*|$)'),
            'cross_references': self._extract_list_section(response_text, r'CROSS REFERENCES[:\s]*(.+?)(?=\*\*|$)'),
            'recommendations': self._extract_list_section(response_text, r'RECOMMENDATIONS[:\s]*(.+?)(?=\*\*|$)'),
            'follow_up_questions': self._extract_list_section(response_text, r'FOLLOW-UP QUESTIONS[:\s]*(.+?)(?=\*\*|$)'),
            'confidence': self._extract_confidence(response_text)
        }
        
        return sections
    
    def _extract_section(self, text, pattern, default):
        """Extract a text section using regex"""
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return default
    
    def _extract_list_section(self, text, pattern):
        """Extract a list section using regex"""
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            items = re.split(r'[•\-\*]\s*|^\d+\.\s*', content, flags=re.MULTILINE)
            return [item.strip() for item in items if item.strip()]
        return []
    
    def _extract_confidence(self, text):
        """Extract confidence level from response"""
        confidence_match = re.search(r'CONFIDENCE[:\s]*(\d+)', text, re.IGNORECASE)
        if confidence_match:
            return int(confidence_match.group(1))
        return 75
    
    def _store_conversation(self, project, question, ai_response):
        """Store conversation in database"""
        try:
            from ..models import AIConversation, AIQuestion
            
            conversation, created = AIConversation.objects.get_or_create(
                project=project,
                defaults={'title': f'AI Conversation - {project.name}'}
            )
            
            AIQuestion.objects.create(
                conversation=conversation,
                question_text=question,
                answer_text=ai_response.get('answer', ''),
                confidence_score=ai_response.get('confidence', 50),
                source_documents=ai_response.get('document_references', []),
                document_references=ai_response.get('cross_references', []),
                analysis_metadata={
                    'key_findings': ai_response.get('key_findings', []),
                    'recommendations': ai_response.get('recommendations', []),
                    'follow_up_questions': ai_response.get('follow_up_questions', [])
                }
            )
            
        except Exception as e:
            logger.warning(f"Error storing conversation: {str(e)}")













