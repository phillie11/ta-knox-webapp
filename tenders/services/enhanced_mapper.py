"""
Enhanced AI Analysis Field Mapping
Improved mapping of comprehensive AI analysis to TenderAnalysis model fields
"""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class EnhancedAIAnalysisMapper:
    """Enhanced mapping of AI analysis results to TenderAnalysis model fields"""
    
    def __init__(self):
        self.default_trades = [
            'Demolition', 'Groundworks', 'Concrete', 'Brickwork', 'Roofing',
            'Carpentry', 'Steelwork', 'M&E Services', 'Plumbing', 'Electrical',
            'Plastering', 'Flooring', 'Painting', 'Glazing', 'Insulation'
        ]
    
    def map_comprehensive_analysis(self, analysis_results: Dict[str, Any], project) -> Dict[str, Any]:
        """
        Enhanced mapping of AI analysis results to TenderAnalysis model fields
        Captures ALL available data from the AI response
        """
        logger.info("Starting enhanced mapping of AI analysis results")
        
        mapped_data = {}
        
        # 1. Project Overview (TextField) - Enhanced with more detail
        overview_parts = []
        if analysis_results.get('project_overview'):
            overview_parts.append(analysis_results['project_overview'])
        
        if analysis_results.get('project_name'):
            overview_parts.append(f"Project: {analysis_results['project_name']}")
            
        if analysis_results.get('project_location'):
            overview_parts.append(f"Location: {analysis_results['project_location']}")
            
        if analysis_results.get('client_details'):
            overview_parts.append(f"Client: {analysis_results['client_details']}")
            
        if analysis_results.get('project_type'):
            overview_parts.append(f"Type: {analysis_results['project_type']}")
            
        mapped_data['project_overview'] = '\n\n'.join(overview_parts) if overview_parts else f"AI Analysis for {project.name}"
        
        # 2. Scope of Work (TextField) - Enhanced detail
        scope_parts = []
        if analysis_results.get('scope_of_work'):
            scope_parts.append(analysis_results['scope_of_work'])
            
        if analysis_results.get('technical_specifications'):
            scope_parts.append(f"Technical Specifications: {analysis_results['technical_specifications']}")
            
        if analysis_results.get('coordination_requirements'):
            scope_parts.append(f"Coordination: {analysis_results['coordination_requirements']}")
            
        mapped_data['scope_of_work'] = '\n\n'.join(scope_parts) if scope_parts else "Scope to be determined from document analysis"
        
        # 3. Key Requirements (JSONField) - Comprehensive list
        key_requirements = []
        
        # Add requirements from various sources
        if analysis_results.get('key_requirements'):
            if isinstance(analysis_results['key_requirements'], list):
                key_requirements.extend(analysis_results['key_requirements'])
            else:
                key_requirements.append(str(analysis_results['key_requirements']))
        
        if analysis_results.get('required_trades'):
            trades = analysis_results['required_trades']
            if isinstance(trades, list):
                for trade in trades:
                    key_requirements.append(f"Required trade: {trade}")
        
        if analysis_results.get('compliance_requirements'):
            compliance = analysis_results['compliance_requirements']
            if isinstance(compliance, list):
                key_requirements.extend(compliance)
            else:
                key_requirements.append(str(compliance))
                
        if analysis_results.get('quality_requirements'):
            key_requirements.append(f"Quality: {analysis_results['quality_requirements']}")
            
        if analysis_results.get('safety_requirements'):
            key_requirements.append(f"Safety: {analysis_results['safety_requirements']}")
            
        if analysis_results.get('environmental_considerations'):
            key_requirements.append(f"Environmental: {analysis_results['environmental_considerations']}")
        
        mapped_data['key_requirements'] = key_requirements[:20]  # Limit to 20 most important
        
        # 4. Technical Specifications (TextField) - Detailed technical info
        tech_specs = []
        if analysis_results.get('technical_specifications'):
            tech_specs.append(analysis_results['technical_specifications'])
            
        if analysis_results.get('drawings_available'):
            drawings = analysis_results['drawings_available']
            if isinstance(drawings, list):
                tech_specs.append(f"Available drawings: {', '.join(drawings)}")
            elif isinstance(drawings, dict) and 'drawings_available' in drawings:
                drawings_list = drawings['drawings_available']
                if isinstance(drawings_list, list):
                    tech_specs.append(f"Available drawings: {', '.join(drawings_list)}")
        
        mapped_data['technical_specifications'] = '\n\n'.join(tech_specs) if tech_specs else "Technical specifications to be reviewed from documents"
        
        # 5. Risk Assessment (TextField) - Comprehensive risk analysis
        risk_parts = []
        if analysis_results.get('risk_assessment'):
            risk_parts.append(analysis_results['risk_assessment'])
            
        if analysis_results.get('identified_risks'):
            risks = analysis_results['identified_risks']
            if isinstance(risks, list):
                risk_parts.append("Identified Risks:")
                for risk in risks:
                    risk_parts.append(f"• {risk}")
        
        if analysis_results.get('site_conditions'):
            risk_parts.append(f"Site Conditions: {analysis_results['site_conditions']}")
            
        mapped_data['risk_assessment'] = '\n\n'.join(risk_parts) if risk_parts else "Risk assessment pending detailed review"
        
        # 6. Risk Level (CharField) - Enhanced risk determination
        risk_level = analysis_results.get('risk_level', 'MEDIUM')
        if isinstance(risk_level, str):
            risk_level = risk_level.upper()
            if 'LOW' in risk_level:
                mapped_data['risk_level'] = 'LOW'
            elif 'HIGH' in risk_level:
                mapped_data['risk_level'] = 'HIGH'
            elif 'CRITICAL' in risk_level:
                mapped_data['risk_level'] = 'HIGH'  # Map critical to high
            else:
                mapped_data['risk_level'] = 'MEDIUM'
        else:
            mapped_data['risk_level'] = 'MEDIUM'
        
        # 7. Timeline Analysis (TextField) - Project scheduling info
        timeline_parts = []
        if analysis_results.get('timeline_analysis'):
            timeline_parts.append(analysis_results['timeline_analysis'])
            
        if analysis_results.get('project_duration_weeks'):
            duration = analysis_results['project_duration_weeks']
            if isinstance(duration, (int, float)):
                timeline_parts.append(f"Estimated duration: {duration} weeks")
            elif isinstance(duration, str) and duration.strip():
                timeline_parts.append(f"Duration: {duration}")
                
        if analysis_results.get('critical_milestones'):
            milestones = analysis_results['critical_milestones']
            if isinstance(milestones, list):
                timeline_parts.append("Critical Milestones:")
                for milestone in milestones:
                    timeline_parts.append(f"• {milestone}")
        
        mapped_data['timeline_analysis'] = '\n\n'.join(timeline_parts) if timeline_parts else "Timeline analysis pending programme review"
        
        # 8. Budget Estimates (TextField) - Financial analysis
        budget_parts = []
        if analysis_results.get('budget_estimates'):
            budget_parts.append(analysis_results['budget_estimates'])
            
        if analysis_results.get('estimated_value_range'):
            value_range = analysis_results['estimated_value_range']
            if isinstance(value_range, dict):
                min_val = value_range.get('min', 'TBD')
                max_val = value_range.get('max', 'TBD')
                budget_parts.append(f"Estimated range: £{min_val:,} - £{max_val:,}" if isinstance(min_val, (int, float)) and isinstance(max_val, (int, float)) else f"Estimated range: {min_val} - {max_val}")
        
        mapped_data['budget_estimates'] = '\n\n'.join(budget_parts) if budget_parts else "Budget estimates to be developed from quantity analysis"
        
        # 9. Contract Information (JSONField) - Contract details
        contract_info = {}
        if analysis_results.get('contract_information'):
            contract_info.update(analysis_results['contract_information'])
            
        # Add other contract-related fields
        contract_fields = ['contract_type', 'payment_terms', 'insurance_requirements', 'liquidated_damages']
        for field in contract_fields:
            if analysis_results.get(field):
                contract_info[field] = analysis_results[field]
        
        mapped_data['contract_information'] = contract_info
        
        # 10. Analysis Confidence (FloatField)
        confidence = analysis_results.get('analysis_confidence', 70.0)
        if isinstance(confidence, (int, float)):
            mapped_data['analysis_confidence'] = float(confidence)
        else:
            mapped_data['analysis_confidence'] = 70.0
        
        # 11. Estimated Project Value (DecimalField) - Extract from value range
        if analysis_results.get('estimated_value_range'):
            value_range = analysis_results['estimated_value_range']
            if isinstance(value_range, dict):
                max_val = value_range.get('max')
                if isinstance(max_val, (int, float)) and max_val > 0:
                    mapped_data['estimated_project_value'] = float(max_val)
        
        # 12. Contract Type (CharField)
        if analysis_results.get('contract_information', {}).get('contract_type'):
            mapped_data['contract_type'] = str(analysis_results['contract_information']['contract_type'])[:100]
        elif analysis_results.get('contract_type'):
            mapped_data['contract_type'] = str(analysis_results['contract_type'])[:100]
        
        # 13. Project Duration Weeks (IntegerField)
        duration = analysis_results.get('project_duration_weeks')
        if duration:
            mapped_data['project_duration_weeks'] = self._safe_convert_to_int(duration, 26)
        
        # 14. Key Opportunities (JSONField)
        opportunities = []
        if analysis_results.get('key_opportunities'):
            opps = analysis_results['key_opportunities']
            if isinstance(opps, list):
                opportunities.extend(opps)
            else:
                opportunities.append(str(opps))
        
        mapped_data['key_opportunities'] = opportunities
        
        # Log mapping results
        logger.info(f"Enhanced mapping completed - {len(mapped_data)} fields mapped")
        logger.info(f"Key requirements: {len(mapped_data.get('key_requirements', []))}")
        logger.info(f"Risk level: {mapped_data.get('risk_level', 'N/A')}")
        logger.info(f"Confidence: {mapped_data.get('analysis_confidence', 'N/A')}%")
        
        return mapped_data
    
    def _safe_convert_to_int(self, value, default=None):
        """Safely convert value to integer"""
        if value is None or value == "":
            return default
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            number_match = re.search(r'(\d+)', str(value))
            if number_match:
                return int(number_match.group(1))
            return default
        return default
    
    def create_comprehensive_clarification_questions(self, analysis_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate comprehensive clarification questions from analysis"""
        questions = []
        
        # Get questions from AI analysis
        if analysis_results.get('clarification_questions'):
            ai_questions = analysis_results['clarification_questions']
            if isinstance(ai_questions, list):
                for q in ai_questions:
                    if isinstance(q, dict):
                        questions.append({
                            'category': q.get('category', 'TECHNICAL'),
                            'question_text': q.get('question', ''),
                            'priority': q.get('priority', 'MEDIUM'),
                            'reference': q.get('reference', 'General')
                        })
        
        # Add default questions if analysis has gaps
        if analysis_results.get('analysis_confidence', 100) < 80:
            questions.append({
                'category': 'TECHNICAL',
                'question_text': 'Please provide additional technical specifications for unclear areas',
                'priority': 'HIGH',
                'reference': 'Document Review'
            })
        
        if not analysis_results.get('estimated_value_range', {}).get('max'):
            questions.append({
                'category': 'COMMERCIAL',
                'question_text': 'Confirm project budget and target cost expectations',
                'priority': 'HIGH',
                'reference': 'Commercial'
            })
        
        if not analysis_results.get('project_duration_weeks'):
            questions.append({
                'category': 'PROGRAM',
                'question_text': 'Provide detailed programme with key milestones',
                'priority': 'HIGH',
                'reference': 'Programme'
            })
        
        return questions[:20]  # Limit to 20 questions
    
    def generate_enhanced_subcontractor_recommendations(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate enhanced subcontractor recommendations"""
        recommendations = []
        
        # Get required trades from analysis
        required_trades = analysis_results.get('required_trades', self.default_trades)
        if not isinstance(required_trades, list):
            required_trades = self.default_trades
        
        # Create recommendations for each trade
        for trade in required_trades:
            recommendation = {
                'trade_category': trade,
                'priority': 'HIGH' if trade in ['M&E Services', 'Structural', 'Groundworks'] else 'MEDIUM',
                'requirements': f"Specialist {trade} contractor required",
                'experience_needed': f"Minimum 5 years experience in {trade} for similar projects",
                'certifications': self._get_trade_certifications(trade),
                'estimated_value': 'TBD based on detailed scope'
            }
            recommendations.append(recommendation)
        
        return recommendations
    
    def _get_trade_certifications(self, trade: str) -> List[str]:
        """Get required certifications for specific trades"""
        cert_map = {
            'M&E Services': ['NICEIC', 'ECA', 'Gas Safe', 'HVCA'],
            'Electrical': ['NICEIC', 'ECA', '18th Edition'],
            'Plumbing': ['Gas Safe', 'Water Regulations', 'Unvented Hot Water'],
            'Roofing': ['NFRC', 'Competent Roofer Scheme'],
            'Steelwork': ['BCSA', 'CE Marking', 'Welding Qualifications'],
            'Groundworks': ['CITB', 'CPCS', 'Groundwork Specialist'],
            'Demolition': ['NFDC', 'Demolition Specialist'],
        }
        return cert_map.get(trade, ['Relevant trade certification required'])


# Usage in the main TenderAIAnalyzer class
def enhanced_map_analysis_to_model_fields(self, analysis_results: Dict[str, Any], project) -> Dict[str, Any]:
    """
    Enhanced mapping using the new comprehensive mapper
    Replace the existing _map_analysis_to_model_fields method with this
    """
    mapper = EnhancedAIAnalysisMapper()
    return mapper.map_comprehensive_analysis(analysis_results, project)


def enhanced_generate_clarification_questions(self, tender_analysis, clarification_questions):
    """
    Enhanced clarification question generation
    """
    try:
        from tenders.models import TenderQuestion
        
        mapper = EnhancedAIAnalysisMapper()
        
        # Use the analysis results to generate questions
        analysis_data = {
            'clarification_questions': clarification_questions,
            'analysis_confidence': tender_analysis.analysis_confidence,
            'estimated_value_range': {},
            'project_duration_weeks': tender_analysis.project_duration_weeks
        }
        
        comprehensive_questions = mapper.create_comprehensive_clarification_questions(analysis_data)
        
        for q_data in comprehensive_questions:
            TenderQuestion.objects.get_or_create(
                project=tender_analysis.project,  # Use project instead of tender_analysis
                category=q_data['category'],
                question_text=q_data['question_text'],
                defaults={
                    'priority': q_data['priority'],
                }
            )
        
        logger.info(f"Generated {len(comprehensive_questions)} clarification questions")
        
    except Exception as e:
        logger.error(f"Error in enhanced clarification question generation: {str(e)}")


def enhanced_generate_subcontractor_recommendations(self, tender_analysis):
    """
    Enhanced subcontractor recommendation generation
    """
    try:
        # For now, just log that we would generate recommendations
        # The actual SubcontractorRecommendation model needs to be imported properly
        logger.info("Enhanced subcontractor recommendations would be generated here")
        
        mapper = EnhancedAIAnalysisMapper()
        analysis_data = {
            'required_trades': tender_analysis.key_requirements or []
        }
        
        recommendations = mapper.generate_enhanced_subcontractor_recommendations(analysis_data)
        logger.info(f"Would generate {len(recommendations)} subcontractor recommendations")
        
    except Exception as e:
        logger.error(f"Error in enhanced subcontractor generation: {str(e)}")