# tenders/services/rfi_generator.py
import logging
import json
from typing import Dict, List, Any, Optional
from django.utils import timezone
from ..models import TenderAnalysis, RFIItem
from .ai_analysis import ClaudeAIService

logger = logging.getLogger(__name__)

class IntelligentRFIGenerator:
    """Generate targeted RFI items from AI analysis to eliminate provisional sums"""
    
    def __init__(self):
        self.claude_service = ClaudeAIService()
    
    def generate_comprehensive_rfis(self, tender_analysis: TenderAnalysis, created_by: str = None) -> Dict[str, Any]:
        """Generate comprehensive RFI items from analysis"""
        
        logger.info(f"🔍 Generating RFIs for project: {tender_analysis.project.name}")
        
        try:
            # Check if RFIs already exist
            existing_rfis = RFIItem.objects.filter(tender_analysis=tender_analysis).count()
            if existing_rfis > 0:
                return {
                    'success': False,
                    'message': f'RFIs already generated for this project ({existing_rfis} items exist)',
                    'rfi_count': existing_rfis
                }
            
            # Generate RFIs from analysis
            generated_rfis = self._analyze_and_generate_rfis(tender_analysis)
            
            # Create RFI items in database
            created_rfis = self._create_rfi_items(tender_analysis, generated_rfis, created_by)
            
            return {
                'success': True,
                'message': f'Successfully generated {len(created_rfis)} RFI items',
                'rfi_count': len(created_rfis),
                'categories': self._summarize_by_category(created_rfis)
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating RFIs: {str(e)}")
            return {
                'success': False,
                'message': f'Error generating RFIs: {str(e)}',
                'rfi_count': 0
            }
    
    def _analyze_and_generate_rfis(self, tender_analysis: TenderAnalysis) -> List[Dict[str, Any]]:
        """Use AI to analyze tender and generate specific RFI questions"""
        
        # Prepare analysis context
        analysis_context = self._prepare_analysis_context(tender_analysis)
        
        if self.claude_service.claude_available:
            return self._generate_rfis_with_claude(analysis_context)
        else:
            return self._generate_rfis_with_fallback(analysis_context)
    
    def _prepare_analysis_context(self, tender_analysis: TenderAnalysis) -> Dict[str, Any]:
        """Prepare comprehensive context for RFI generation"""
        
        context = {
            'project_name': tender_analysis.project.name,
            'project_location': tender_analysis.project.location,
            'project_overview': tender_analysis.project_overview,
            'scope_of_work': tender_analysis.scope_of_work,
            'key_requirements': tender_analysis.key_requirements or [],
            'identified_risks': tender_analysis.identified_risks or [],
            'technical_specifications': tender_analysis.technical_specifications,
            'documents_analyzed': tender_analysis.documents_analyzed or [],
            'analysis_confidence': tender_analysis.analysis_confidence,
            'contract_information': getattr(tender_analysis, 'contract_information', {}),
            'building_standards': getattr(tender_analysis, 'building_standards', []),
            'environmental_requirements': getattr(tender_analysis, 'environmental_requirements', ''),
            'critical_milestones': getattr(tender_analysis, 'critical_milestones', [])
        }
        
        return context
    
    def _generate_rfis_with_claude(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate RFIs using Claude AI"""
        
        prompt = self._create_rfi_generation_prompt(context)
        
        try:
            response = self.claude_service._call_claude_with_retry(prompt, max_retries=2)
            return self._parse_claude_rfi_response(response)
            
        except Exception as e:
            logger.warning(f"Claude RFI generation failed: {str(e)}, using fallback")
            return self._generate_rfis_with_fallback(context)
    
    def _create_rfi_generation_prompt(self, context: Dict[str, Any]) -> str:
        """Create comprehensive prompt for RFI generation"""
        
        return f"""
You are an expert construction estimator reviewing tender documents for accurate pricing. Your goal is to identify ALL missing information that could lead to provisional sums, exclusions, or inaccurate estimates.

PROJECT: {context['project_name']}
LOCATION: {context['project_location']}

ANALYSIS SUMMARY:
{context['project_overview'][:1000]}

SCOPE OF WORK:
{context['scope_of_work'][:1000]}

KEY REQUIREMENTS:
{context.get('key_requirements', [])}

TECHNICAL SPECIFICATIONS:
{context.get('technical_specifications', '')[:1000]}

Generate specific RFI questions that address:

1. CRITICAL PRICING CLARIFICATIONS
- Missing quantities or specifications that prevent accurate pricing
- Unclear scope boundaries that could lead to disputes
- Ambiguous material specifications requiring provisional allowances

2. PROGRAMME & TIMING CLARIFICATIONS  
- Missing start dates, completion requirements, or phasing
- Unclear access arrangements or working hours
- Missing coordination requirements with other trades

3. TECHNICAL SPECIFICATION GAPS
- Incomplete material specifications or performance requirements
- Missing technical drawings or details
- Unclear quality standards or testing requirements

4. COMMERCIAL CLARIFICATIONS
- Unclear payment terms or milestone definitions
- Missing insurance or bonding requirements
- Unclear variation procedures or risk allocation

5. HEALTH & SAFETY REQUIREMENTS
- Missing CDM requirements or site-specific safety measures
- Unclear temporary works requirements
- Missing environmental or noise restrictions

6. SCOPE EXCLUSIONS & INCLUSIONS
- Items that appear excluded but may be contractor responsibility
- FF&E or equipment supply arrangements
- Utility connections and temporary services

For each RFI, provide:
- category: One of [TECHNICAL, COMMERCIAL, PROGRAMME, SPECIFICATION, DRAWING, HEALTH_SAFETY, ENVIRONMENTAL, QUALITY, SCOPE, ACCESS, COORDINATION, EXCLUSIONS]
- priority: CRITICAL (affects bid validity), HIGH (affects pricing), MEDIUM (affects risk), LOW (minor)
- question: Clear, specific question
- context: Why this clarification is needed for accurate pricing
- document_reference: Which document (if any) contains the ambiguity
- pricing_impact: HIGH/MEDIUM/LOW impact on cost accuracy
- risk_if_unresolved: What happens if this isn't clarified

Focus on questions that eliminate the need for provisional sums and ensure competitive, accurate pricing.

Return as JSON array of RFI objects.
"""
    
    def _parse_claude_rfi_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse Claude's RFI response into structured data"""
        
        try:
            # Look for JSON array in response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response[json_start:json_end]
                rfis = json.loads(json_text)
                
                # Validate and clean RFI data
                cleaned_rfis = []
                for rfi in rfis:
                    if self._validate_rfi_data(rfi):
                        cleaned_rfis.append(self._clean_rfi_data(rfi))
                
                logger.info(f"✅ Parsed {len(cleaned_rfis)} RFIs from Claude response")
                return cleaned_rfis
            else:
                # Parse from text format
                return self._parse_text_rfi_response(response)
                
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed: {str(e)}, trying text parsing")
            return self._parse_text_rfi_response(response)
    
    def _generate_rfis_with_fallback(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate RFIs using rule-based fallback"""
        
        rfis = []
        
        # Standard construction project RFIs
        standard_rfis = [
            {
                'category': 'PROGRAMME',
                'priority': 'CRITICAL',
                'question': 'What is the confirmed start on site date and required completion date?',
                'context': 'Essential for programme planning and resource allocation',
                'pricing_impact': 'HIGH',
                'risk_if_unresolved': 'Cannot price time-related costs or assess programme risk'
            },
            {
                'category': 'TECHNICAL',
                'priority': 'HIGH', 
                'question': 'Please provide complete technical specifications for all major building elements',
                'context': 'Current specifications appear incomplete for accurate material pricing',
                'pricing_impact': 'HIGH',
                'risk_if_unresolved': 'May require provisional sums for unspecified elements'
            },
            {
                'category': 'SCOPE',
                'priority': 'CRITICAL',
                'question': 'Please clarify the exact scope boundaries and any exclusions from contractor works',
                'context': 'Scope boundaries are unclear which could lead to disputes',
                'pricing_impact': 'HIGH',
                'risk_if_unresolved': 'Risk of pricing gaps or overlaps with other contractors'
            },
            {
                'category': 'COMMERCIAL',
                'priority': 'HIGH',
                'question': 'Please confirm payment terms, retention percentages and milestone definitions',
                'context': 'Commercial terms affect cash flow and pricing strategy',
                'pricing_impact': 'MEDIUM',
                'risk_if_unresolved': 'Cannot assess commercial risk or price accordingly'
            },
            {
                'category': 'ACCESS',
                'priority': 'HIGH',
                'question': 'Please provide site access arrangements, working hours and any restrictions',
                'context': 'Access limitations affect logistics and programme costs',
                'pricing_impact': 'MEDIUM',
                'risk_if_unresolved': 'May underestimate logistics and programme costs'
            }
        ]
        
        # Add context-specific RFIs based on analysis
        if 'live environment' in context.get('project_overview', '').lower():
            standard_rfis.append({
                'category': 'COORDINATION',
                'priority': 'HIGH',
                'question': 'Please detail coordination requirements with ongoing operations and other contractors',
                'context': 'Live environment requires careful coordination planning',
                'pricing_impact': 'HIGH',
                'risk_if_unresolved': 'Cannot price coordination and protection measures'
            })
        
        return standard_rfis[:12]  # Limit to most important
    
    def _validate_rfi_data(self, rfi: Dict[str, Any]) -> bool:
        """Validate RFI data structure"""
        required_fields = ['category', 'priority', 'question']
        return all(field in rfi and rfi[field] for field in required_fields)
    
    def _clean_rfi_data(self, rfi: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and standardize RFI data"""
        
        # Standardize category
        category_mapping = {
            'TECHNICAL': 'TECHNICAL',
            'COMMERCIAL': 'COMMERCIAL', 
            'PROGRAM': 'PROGRAMME',
            'PROGRAMME': 'PROGRAMME',
            'SPECIFICATION': 'SPECIFICATION',
            'DRAWING': 'DRAWING',
            'HEALTH_SAFETY': 'HEALTH_SAFETY',
            'ENVIRONMENTAL': 'ENVIRONMENTAL',
            'QUALITY': 'QUALITY',
            'SCOPE': 'SCOPE',
            'ACCESS': 'ACCESS',
            'COORDINATION': 'COORDINATION',
            'EXCLUSIONS': 'EXCLUSIONS'
        }
        
        rfi['category'] = category_mapping.get(rfi.get('category', '').upper(), 'TECHNICAL')
        
        # Standardize priority
        priority_mapping = {
            'CRITICAL': 'CRITICAL',
            'HIGH': 'HIGH',
            'MEDIUM': 'MEDIUM', 
            'LOW': 'LOW'
        }
        
        rfi['priority'] = priority_mapping.get(rfi.get('priority', '').upper(), 'MEDIUM')
        
        # Ensure required fields exist
        rfi.setdefault('context', 'Clarification required for accurate estimation')
        rfi.setdefault('document_reference', 'General')
        rfi.setdefault('pricing_impact', 'MEDIUM')
        rfi.setdefault('risk_if_unresolved', 'May affect pricing accuracy')
        
        return rfi
    
    def _create_rfi_items(self, tender_analysis: TenderAnalysis, rfis: List[Dict[str, Any]], created_by: str = None) -> List[RFIItem]:
        """Create RFI items in the database"""
        
        created_items = []
        
        for rfi_data in rfis:
            try:
                rfi_item = RFIItem.objects.create(
                    project=tender_analysis.project,
                    tender_analysis=tender_analysis,
                    category=rfi_data['category'],
                    priority=rfi_data['priority'],
                    question=rfi_data['question'],
                    context=rfi_data.get('context', ''),
                    document_reference=rfi_data.get('document_reference', ''),
                    location_in_document=rfi_data.get('location_in_document', ''),
                    pricing_impact=rfi_data.get('pricing_impact', 'MEDIUM'),
                    risk_if_unresolved=rfi_data.get('risk_if_unresolved', ''),
                    created_by=created_by or 'System Generated',
                    status='PENDING'
                )
                created_items.append(rfi_item)
                
            except Exception as e:
                logger.error(f"Failed to create RFI item: {str(e)}")
                continue
        
        logger.info(f"✅ Created {len(created_items)} RFI items")
        return created_items
    
    def _summarize_by_category(self, rfi_items: List[RFIItem]) -> Dict[str, int]:
        """Summarize RFI counts by category"""
        summary = {}
        for item in rfi_items:
            category = item.get_category_display()
            summary[category] = summary.get(category, 0) + 1
        return summary
    
    def regenerate_rfis(self, tender_analysis: TenderAnalysis, created_by: str = None) -> Dict[str, Any]:
        """Regenerate RFIs after deleting existing ones"""
        
        # Delete existing RFIs
        deleted_count = RFIItem.objects.filter(tender_analysis=tender_analysis).count()
        RFIItem.objects.filter(tender_analysis=tender_analysis).delete()
        
        logger.info(f"🗑️ Deleted {deleted_count} existing RFI items")
        
        # Generate new RFIs
        return self.generate_comprehensive_rfis(tender_analysis, created_by)













