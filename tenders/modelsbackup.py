# tenders/models.py - Fixed version without SubcontractorRecommendation
import logging
import os
import traceback
import json
from django.db import models
from django.utils import timezone
from django.db.models.signals import pre_save, post_save
from django.core.validators import MinValueValidator, MaxValueValidator
from django.dispatch import receiver
from projects.models import Project
from subcontractors.models import Subcontractor
from django.contrib.auth.models import User
from django.utils import timezone

# Configure logger at the module level
logger = logging.getLogger(__name__)

class TenderAnalysis(models.Model):
    """Enhanced AI analysis of tender documents with comprehensive field coverage"""

    RISK_LEVELS = [
        ('LOW', 'Low Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
    ]

    CONTRACT_TYPES = [
        ('JCT_STANDARD', 'JCT Standard Building Contract'),
        ('JCT_DESIGN_BUILD', 'JCT Design and Build Contract'),
        ('JCT_MINOR_WORKS', 'JCT Minor Works Contract'),
        ('NEC4', 'NEC4 Engineering and Construction Contract'),
        ('FIDIC', 'FIDIC Conditions of Contract'),
        ('BESPOKE', 'Bespoke Contract'),
        ('OTHER', 'Other'),
    ]

    # Core fields
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='tender_analysis')
    analysis_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    # Project overview and scope
    project_overview = models.TextField(
        help_text="Comprehensive project overview including client, location, and high-level scope"
    )
    scope_of_work = models.TextField(
        help_text="Detailed scope of work including technical specifications and coordination requirements"
    )

    # Requirements and specifications
    key_requirements = models.JSONField(
        default=list,
        help_text="List of key project requirements including trades, compliance, quality, and safety"
    )
    technical_specifications = models.TextField(
        blank=True,
        help_text="Technical specifications including drawings, standards, and materials"
    )

    # Risk and opportunity analysis
    risk_assessment = models.TextField(
        help_text="Comprehensive risk assessment including identified risks and site conditions"
    )
    risk_level = models.CharField(
        max_length=10,
        choices=RISK_LEVELS,
        default='MEDIUM',
        help_text="Overall project risk level assessment"
    )
    identified_risks = models.JSONField(
        default=list,
        help_text="List of specific identified risks"
    )

    # Financial analysis fields
    estimated_value_range = models.JSONField(
        default=dict,
        help_text="Dictionary containing min/max estimated project values"
    )
    cost_breakdown = models.JSONField(
        default=dict,
        help_text="Detailed cost breakdown by trade/category"
    )
    budget_estimates = models.TextField(
        blank=True,
        help_text="Budget estimates and financial analysis summary"
    )
    estimated_project_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Single estimated project value"
    )

    # Timeline and milestones
    project_duration_weeks = models.IntegerField(
        null=True,
        blank=True,
        help_text="Estimated project duration in weeks"
    )
    critical_milestones = models.JSONField(
        default=list,
        help_text="List of critical project milestones and dates"
    )

    # Standards and compliance
    building_standards = models.JSONField(
        default=list,
        help_text="List of building standards, codes, and regulatory requirements"
    )
    environmental_requirements = models.TextField(
        blank=True,
        help_text="Environmental compliance requirements and standards"
    )
    environmental_considerations = models.TextField(
        blank=True,
        help_text="Environmental requirements and sustainability measures"
    )
    health_safety_requirements = models.TextField(
        blank=True,
        help_text="Comprehensive health and safety requirements and CDM regulations"
    )

    # Contract information
    contract_information = models.JSONField(
        default=dict,
        help_text="Contract details including type, terms, and conditions"
    )
    contract_type = models.CharField(
        max_length=50,
        choices=CONTRACT_TYPES,
        blank=True,
        help_text="Type of construction contract"
    )

    # Quality and compliance (existing fields)
    quality_requirements = models.TextField(
        blank=True,
        help_text="Quality standards and requirements"
    )
    safety_requirements = models.TextField(
        blank=True,
        help_text="Health and safety requirements and regulations"
    )
    compliance_requirements = models.JSONField(
        default=list,
        help_text="List of compliance requirements including regulations and standards"
    )

    # Coordination and procurement (existing fields)
    coordination_requirements = models.TextField(
        blank=True,
        help_text="Multi-trade coordination and interface requirements"
    )
    subcontractor_requirements = models.JSONField(
        default=list,
        help_text="List of subcontractor requirements and qualifications"
    )
    procurement_strategy = models.TextField(
        blank=True,
        help_text="Recommended procurement strategy for subcontractors and materials"
    )

    # Analysis metadata (existing fields)
    documents_analyzed = models.JSONField(
        default=list,
        help_text="List of documents that were analyzed"
    )
    analysis_confidence = models.FloatField(
        default=0.0,
        help_text="AI confidence score (0-100) for the analysis accuracy"
    )
    analysis_method = models.CharField(
        max_length=100,
        default='Claude AI Analysis',
        help_text="Method used for analysis"
    )

    # Recommendations and actions (existing fields)
    recommended_actions = models.JSONField(
        default=list,
        help_text="List of recommended actions based on analysis"
    )
    clarification_needed = models.BooleanField(
        default=False,
        help_text="Whether clarification questions need to be raised"
    )

    class Meta:
        verbose_name = "Tender Analysis"
        verbose_name_plural = "Tender Analyses"
        ordering = ['-analysis_date']

    def __str__(self):
        return f"Analysis for {self.project.name} ({self.analysis_date.strftime('%d/%m/%Y')})"

    @property
    def confidence_level(self):
        """Return text description of confidence level"""
        if self.analysis_confidence >= 80:
            return "High"
        elif self.analysis_confidence >= 60:
            return "Medium"
        else:
            return "Low"

    @property
    def confidence_color(self):
        """Return Bootstrap color class for confidence level"""
        if self.analysis_confidence >= 80:
            return "success"
        elif self.analysis_confidence >= 60:
            return "warning"
        else:
            return "danger"

    @property
    def risk_color(self):
        """Return Bootstrap color class for risk level"""
        risk_colors = {
            'LOW': 'success',
            'MEDIUM': 'warning',
            'HIGH': 'danger'
        }
        return risk_colors.get(self.risk_level, 'secondary')

    @property
    def total_requirements(self):
        """Return total number of key requirements"""
        return len(self.key_requirements) if self.key_requirements else 0

    @property
    def total_risks(self):
        """Return total number of identified risks"""
        return len(self.identified_risks) if self.identified_risks else 0

    @property
    def total_opportunities(self):
        """Return total number of key opportunities"""
        return len(self.key_opportunities) if self.key_opportunities else 0

    @property
    def has_dates(self):
        """Check if any key dates are defined"""
        return any([
            self.possession_date,
            self.start_on_site_date,
            self.practical_completion_date,
            self.handover_date
        ])

    @property
    def has_budget_info(self):
        """Check if budget information is available"""
        return bool(self.estimated_project_value or self.value_range_min or self.value_range_max)

    def get_contract_summary(self):
        """Return a summary of contract information"""
        summary = []
        if self.contract_type:
            summary.append(f"Type: {self.get_contract_type_display()}")
        if self.estimated_project_value:
            summary.append(f"Value: £{self.estimated_project_value:,.0f}")
        if self.project_duration_weeks:
            summary.append(f"Duration: {self.project_duration_weeks} weeks")
        return " | ".join(summary) if summary else "Contract details pending"

    def get_risk_summary(self):
        """Return a summary of risk assessment"""
        risk_count = self.total_risks
        if risk_count > 0:
            return f"{self.get_risk_level_display()} - {risk_count} risks identified"
        else:
            return f"{self.get_risk_level_display()} project"

    def get_progress_summary(self):
        """Return analysis completeness summary"""
        completed_sections = 0
        total_sections = 8

        if self.project_overview: completed_sections += 1
        if self.scope_of_work: completed_sections += 1
        if self.key_requirements: completed_sections += 1
        if self.risk_assessment: completed_sections += 1
        if self.timeline_analysis: completed_sections += 1
        if self.budget_estimates: completed_sections += 1
        if self.contract_information: completed_sections += 1
        if self.technical_specifications: completed_sections += 1

        return {
            'completed': completed_sections,
            'total': total_sections,
            'percentage': (completed_sections / total_sections) * 100
        }


class SubcontractorRecommendation(models.Model):
    """AI recommendations for subcontractors based on tender analysis"""

    TRADE_CATEGORIES = [
        ('GROUNDWORKS', 'Groundworks'),
        ('CONCRETE', 'Concrete Works'),
        ('BRICKWORK', 'Brickwork'),
        ('ROOFING', 'Roofing'),
        ('CARPENTRY', 'Carpentry'),
        ('STEELWORK', 'Steelwork'),
        ('M&E', 'Mechanical & Electrical'),
        ('PLUMBING', 'Plumbing'),
        ('ELECTRICAL', 'Electrical'),
        ('PLASTERING', 'Plastering'),
        ('FLOORING', 'Flooring'),
        ('PAINTING', 'Painting & Decorating'),
        ('GLAZING', 'Glazing'),
        ('INSULATION', 'Insulation'),
        ('DEMOLITION', 'Demolition'),
        ('SCAFFOLDING', 'Scaffolding'),
        ('PLANT_HIRE', 'Plant Hire'),
        ('WASTE_MANAGEMENT', 'Waste Management'),
        ('SECURITY', 'Security'),
        ('CLEANING', 'Cleaning'),
        ('OTHER', 'Other Specialist Trade'),
    ]

    PRIORITY_LEVELS = [
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High Priority'),
        ('MEDIUM', 'Medium Priority'),
        ('LOW', 'Low Priority'),
    ]

    tender_analysis = models.ForeignKey(
        TenderAnalysis,
        on_delete=models.CASCADE,
        related_name='subcontractor_recommendations'
    )
    subcontractor = models.ForeignKey(
        Subcontractor,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Specific subcontractor recommendation (optional)"
    )
    trade_category = models.CharField(
        max_length=50,
        choices=TRADE_CATEGORIES,
        help_text="Trade category for this recommendation"
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_LEVELS,
        default='MEDIUM',
        help_text="Priority level for this trade package"
    )

    # Recommendation scoring (0-100)
    suitability_score = models.FloatField(
        default=0.0,
        help_text="Overall suitability score (0-100)"
    )
    experience_match = models.FloatField(
        default=0.0,
        help_text="Experience match score (0-100)"
    )
    location_proximity = models.FloatField(
        default=0.0,
        help_text="Location proximity score (0-100)"
    )
    past_performance = models.FloatField(
        default=0.0,
        help_text="Past performance score (0-100)"
    )
    capacity_score = models.FloatField(
        default=0.0,
        help_text="Current capacity score (0-100)"
    )

    # Requirements and qualifications
    required_experience = models.TextField(
        blank=True,
        help_text="Required experience for this trade"
    )
    required_certifications = models.JSONField(
        default=list,
        help_text="List of required certifications"
    )
    estimated_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated package value"
    )

    # Recommendation reasoning
    strengths = models.JSONField(
        default=list,
        help_text="List of subcontractor strengths"
    )
    concerns = models.JSONField(
        default=list,
        help_text="List of potential concerns"
    )
    recommendation_notes = models.TextField(
        blank=True,
        help_text="Additional recommendation notes"
    )

    # Status and actions
    is_recommended = models.BooleanField(
        default=True,
        help_text="Whether this subcontractor is recommended"
    )
    is_contacted = models.BooleanField(
        default=False,
        help_text="Whether the subcontractor has been contacted"
    )
    response_received = models.BooleanField(
        default=False,
        help_text="Whether a response has been received"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who created this recommendation"
    )

    class Meta:
        unique_together = ['tender_analysis', 'subcontractor', 'trade_category']
        ordering = ['-priority', '-suitability_score', 'trade_category']
        verbose_name = "Subcontractor Recommendation"
        verbose_name_plural = "Subcontractor Recommendations"

    def __str__(self):
        if self.subcontractor:
            return f"{self.subcontractor.company} - {self.get_trade_category_display()} ({self.suitability_score:.0f}%)"
        else:
            return f"{self.get_trade_category_display()} - General Recommendation"

    @property
    def priority_color(self):
        """Return Bootstrap color class for priority level"""
        priority_colors = {
            'CRITICAL': 'danger',
            'HIGH': 'warning',
            'MEDIUM': 'info',
            'LOW': 'secondary'
        }
        return priority_colors.get(self.priority, 'secondary')

    @property
    def score_color(self):
        """Return Bootstrap color class for suitability score"""
        if self.suitability_score >= 80:
            return "success"
        elif self.suitability_score >= 60:
            return "warning"
        else:
            return "danger"

    @property
    def overall_rating(self):
        """Calculate overall rating based on all scores"""
        scores = [
            self.suitability_score,
            self.experience_match,
            self.location_proximity,
            self.past_performance,
            self.capacity_score
        ]
        valid_scores = [s for s in scores if s > 0]
        return sum(valid_scores) / len(valid_scores) if valid_scores else 0


class TenderQuestion(models.Model):
    """Questions generated by AI for tender clarification"""

    CATEGORIES = [
        ('TECHNICAL', 'Technical'),
        ('COMMERCIAL', 'Commercial'),
        ('PROGRAM', 'Programme'),
        ('RISK', 'Risk Management'),
        ('COMPLIANCE', 'Compliance'),
        ('QUALITY', 'Quality'),
        ('SAFETY', 'Health & Safety'),
        ('ENVIRONMENTAL', 'Environmental'),
        ('COORDINATION', 'Coordination'),
        ('OTHER', 'Other')
    ]

    PRIORITIES = [
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High Priority'),
        ('MEDIUM', 'Medium Priority'),
        ('LOW', 'Low Priority'),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tender_questions'
    )
    tender_analysis = models.ForeignKey(
        TenderAnalysis,
        on_delete=models.CASCADE,
        related_name='clarification_questions',
        null=True,
        blank=True
    )

    category = models.CharField(
        max_length=20,
        choices=CATEGORIES,
        help_text="Question category"
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITIES,
        default='MEDIUM',
        help_text="Question priority level"
    )

    question_text = models.TextField(
        help_text="The clarification question"
    )
    reference_document = models.CharField(
        max_length=200,
        blank=True,
        help_text="Reference document or section"
    )

    # Response tracking
    is_answered = models.BooleanField(
        default=False,
        help_text="Whether this question has been answered"
    )
    answer_text = models.TextField(
        blank=True,
        help_text="Answer to the question"
    )
    answered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='answered_questions'
    )
    answered_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the question was answered"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_questions'
    )

    class Meta:
        ordering = ['-priority', '-created_at']
        verbose_name = "Tender Question"
        verbose_name_plural = "Tender Questions"

    def __str__(self):
        return f"{self.get_category_display()} - {self.question_text[:50]}..."

    @property
    def priority_color(self):
        """Return Bootstrap color class for priority level"""
        priority_colors = {
            'CRITICAL': 'danger',
            'HIGH': 'warning',
            'MEDIUM': 'info',
            'LOW': 'secondary'
        }
        return priority_colors.get(self.priority, 'secondary')

    @property
    def status_color(self):
        """Return Bootstrap color class for answer status"""
        return "success" if self.is_answered else "danger"

    def mark_answered(self, answer, user):
        """Mark question as answered"""
        self.is_answered = True
        self.answer_text = answer
        self.answered_by = user
        self.answered_at = timezone.now()
        self.save()

class TenderInvitation(models.Model):

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('DECLINED', 'Declined'),
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='invitations')
    subcontractor = models.ForeignKey(Subcontractor, on_delete=models.CASCADE, related_name='tender_invitations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    email_sent = models.DateTimeField(null=True, blank=True)
    email_opened = models.BooleanField(default=False)
    email_opened_at = models.DateTimeField(null=True, blank=True)
    documents_downloaded = models.BooleanField(default=False)
    documents_downloaded_at = models.DateTimeField(null=True, blank=True)
    response_date = models.DateTimeField(null=True, blank=True)

    # Communication tracking
    sent_by = models.CharField(max_length=100, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    custom_message = models.TextField(blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)

    # Additional fields
    notes = models.TextField(blank=True, help_text="Notes about communication with this subcontractor")
    tender_returned = models.BooleanField(default=False, help_text="Whether the subcontractor has returned their tender")
    returned_at = models.DateTimeField(null=True, blank=True, help_text="When the tender was returned")
    tender_attachments = models.JSONField(null=True, blank=True, help_text="Information about returned tender attachments")

    class Meta:
        unique_together = ['project', 'subcontractor']

    def __str__(self):
        return f"{self.project.name} - {self.subcontractor.company}"

class TenderDocument(models.Model):
    DOCUMENT_TYPES = [
        ('TENDER', 'Tender Document'),
        ('DRAWING', 'Drawing'),
        ('SPECIFICATION', 'Specification'),
        ('CONTRACT', 'Contract Document'),
        ('OTHER', 'Other'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tender_documents')
    title = models.CharField(max_length=255)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default='TENDER')
    file = models.FileField(upload_to='tender_documents/%Y/%m/')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.project.name}"

class TenderAddendum(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tender_addenda')
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    sent_by = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Addendum: {self.title} - {self.project.name}"

# Optional models that may not exist in all installations
class RFIItem(models.Model):
    """Request for Information items"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='rfi_items')
    category = models.CharField(max_length=100)
    priority = models.CharField(max_length=20, choices=[
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low')
    ], default='MEDIUM')
    question = models.TextField()
    response = models.TextField(blank=True)
    contractor_response = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('OPEN', 'Open'),
        ('ANSWERED', 'Answered'),
        ('CLOSED', 'Closed')
    ], default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"RFI: {self.category} - {self.project.name}"

class DocumentQuestion(models.Model):
    """Questions asked about project documents"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='document_questions')
    question_text = models.TextField()
    answer_text = models.TextField(blank=True)
    asked_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Question for {self.project.name}"

# Signal handlers
@receiver(post_save, sender=TenderInvitation)
def log_tender_invitation_status_change(sender, instance, created, **kwargs):
    """Log when tender invitation status changes"""
    if not created:
        logger.info(f"Tender invitation status changed to {instance.status} for {instance.subcontractor.company} on {instance.project.name}")

@receiver(pre_save, sender=TenderInvitation)
def set_response_date(sender, instance, **kwargs):
    """Set response date when status changes from PENDING"""
    if instance.pk:
        try:
            old_instance = TenderInvitation.objects.get(pk=instance.pk)
            if old_instance.status == 'PENDING' and instance.status != 'PENDING':
                instance.response_date = timezone.now()
        except TenderInvitation.DoesNotExist:
            pass

class AIConversation(models.Model):
    """AI conversation tracking for enhanced Ask AI"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='ai_conversations')
    title = models.CharField(max_length=200, default="AI Conversation")
    created_date = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_activity']
        db_table = 'tenders_ai_conversation'

    def __str__(self):
        return f"{self.project.name} - {self.title}"

class AIQuestion(models.Model):
    """Individual AI questions and answers for enhanced Ask AI"""
    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name='ai_questions')
    question_text = models.TextField()
    answer_text = models.TextField()
    confidence_score = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    source_documents = models.JSONField(default=list, blank=True)
    document_references = models.JSONField(default=list, blank=True)
    analysis_metadata = models.JSONField(default=dict, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_date']
        db_table = 'tenders_ai_question'

    def __str__(self):
        return f"Q: {self.question_text[:50]}..."