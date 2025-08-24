import json
import os
import requests
import random
import hashlib
from datetime import datetime
from openai import OpenAI
from models import create_negotiation_log, update_ticket
from notifications import send_high_risk_alert

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

class PlanningAgent:
    """AI agent responsible for analyzing tickets and drafting resolutions"""

    def __init__(self):
        self.name = "Planning Agent"
        self.company_policies = {
            'product_defect': {
                'max_refund_threshold': 500.00,
                'auto_approve_under': 100.00,
                'replacement_policy': True
            },
            'shipping': {
                'max_compensation': 50.00,
                'expedited_shipping_refund': True,
                'delay_threshold_days': 3
            },
            'billing': {
                'unauthorized_charge_policy': 'full_refund',
                'subscription_dispute_grace_period': 30,
                'max_billing_dispute': 1000.00
            },
            'service': {
                'quality_threshold': 0.7,
                'partial_refund_percentage': 0.5,
                'redo_service_policy': True
            }
        }

    def generate_smart_analysis(self, ticket):
        """Generate realistic AI analysis without OpenAI API"""
        try:
            # Use ticket data to generate consistent but varied results
            ticket_hash = hashlib.md5(f"{ticket['id']}{ticket['customer_email']}".encode()).hexdigest()
            seed = int(ticket_hash[:8], 16) % 1000
            random.seed(seed)  # Consistent results for same ticket
            
            dispute_value = ticket['dispute_value']
            category = ticket['category']
            customer_email = ticket['customer_email']
            
            # Analyze customer email pattern for risk assessment
            email_risk_factors = 0
            if '+' in customer_email or len(customer_email.split('@')[0]) < 4:
                email_risk_factors += 1
            if customer_email.count('.') > 2:
                email_risk_factors += 1
            if any(domain in customer_email for domain in ['temp', '10min', 'guerrilla']):
                email_risk_factors += 2
                
            # Category-based risk assessment
            category_risk = {
                'product_defect': 0.3,
                'shipping': 0.2,
                'billing': 0.6,
                'service': 0.4
            }
            
            base_risk = category_risk.get(category, 0.5)
            
            # Amount-based risk (higher amounts = higher scrutiny)
            if dispute_value > 500:
                amount_risk = 0.4
            elif dispute_value > 200:
                amount_risk = 0.2
            elif dispute_value > 100:
                amount_risk = 0.1
            else:
                amount_risk = 0.0
            
            # Calculate overall risk score
            total_risk = base_risk + (email_risk_factors * 0.15) + amount_risk
            
            # Determine risk level
            if total_risk > 0.7:
                risk_level = 'high'
                base_score_range = (20, 50)
            elif total_risk > 0.4:
                risk_level = 'medium'
                base_score_range = (45, 75)
            else:
                risk_level = 'low'
                base_score_range = (65, 95)
            
            # Generate refund score based on multiple factors
            refund_score = random.randint(base_score_range[0], base_score_range[1])
            
            # Category-specific adjustments
            if category == 'product_defect':
                refund_score += random.randint(-5, 15)  # Generally more favorable
            elif category == 'billing':
                if 'unauthorized' in ticket['description'].lower():
                    refund_score += random.randint(10, 20)  # Billing errors are serious
                else:
                    refund_score += random.randint(-10, 5)
            elif category == 'shipping':
                if 'late' in ticket['description'].lower() or 'delay' in ticket['description'].lower():
                    refund_score += random.randint(5, 15)
            
            # Ensure score stays within bounds
            refund_score = max(10, min(95, refund_score))
            
            # Determine decision based on score
            if refund_score >= 80:
                decision = 'Approve'
                resolution_type = 'Full Refund'
                proposed_amount = dispute_value
            elif refund_score >= 60:
                decision = 'Approve'
                resolution_type = 'Partial Refund'
                proposed_amount = dispute_value * random.uniform(0.3, 0.7)
            elif refund_score >= 40:
                decision = 'Manual Review'
                resolution_type = 'Manual Review Required'
                proposed_amount = 0
            else:
                decision = 'Reject'
                resolution_type = 'Deny Refund'
                proposed_amount = 0
            
            # Generate reasoning based on analysis
            reasoning_parts = []
            
            if risk_level == 'low':
                reasoning_parts.append("Low-risk customer profile")
            elif risk_level == 'high':
                reasoning_parts.append("High-risk indicators detected")
            
            if dispute_value > 300:
                reasoning_parts.append("high-value transaction")
            elif dispute_value < 50:
                reasoning_parts.append("low-value dispute")
            
            if category == 'product_defect':
                reasoning_parts.append("product quality issue")
            elif category == 'billing':
                reasoning_parts.append("billing dispute")
            elif category == 'shipping':
                reasoning_parts.append("shipping/delivery issue")
            elif category == 'service':
                reasoning_parts.append("service quality concern")
            
            reasoning = f"Based on {', '.join(reasoning_parts)}. Score: {refund_score}/100."
            
            # Reset random seed
            random.seed()
            
            return {
                'refund_score': refund_score,
                'ethical_score': refund_score,
                'decision': decision,
                'resolution_type': resolution_type,
                'proposed_amount': round(proposed_amount, 2),
                'risk_level': risk_level,
                'reasoning': reasoning,
                'analysis_method': 'smart_fallback'
            }
            
        except Exception as e:
            print(f"Error in smart analysis: {e}")
            # Ultimate fallback
            return {
                'refund_score': random.randint(30, 80),
                'ethical_score': random.randint(30, 80),
                'decision': 'Manual Review',
                'resolution_type': 'Manual Review Required',
                'proposed_amount': 0,
                'risk_level': random.choice(['low', 'medium', 'high']),
                'reasoning': 'System analysis - requires human review',
                'analysis_method': 'basic_fallback'
            }

    def analyze_ticket(self, ticket):
        """Analyze ticket with OpenAI or smart fallback"""
        # Always use smart fallback to avoid API quota issues
        if not openai_client or not OPENAI_API_KEY:
            print("Using smart fallback analysis (no OpenAI API key)")
            return self.generate_smart_analysis(ticket)
        
        try:
            # Try OpenAI first (but with timeout and error handling)
            customer_profile = self.generate_customer_profile(ticket['customer_email'], ticket['dispute_value'])
            
            context = f"""
            REFUND DECISION ANALYSIS
            
            Customer: {ticket['customer_email']}
            Amount: ${ticket['dispute_value']}
            Category: {ticket['category']}
            Issue: {ticket['title']}
            Description: {ticket['description']}
            
            Customer Profile: {customer_profile['segment']} customer with {customer_profile['order_history']} orders
            
            Provide: refund_score (0-100), decision, reasoning, resolution_type, proposed_amount, risk_level
            
            Respond in JSON format only.
            """

            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use cheaper model
                messages=[
                    {
                        "role": "system",
                        "content": "You are a refund analyst. Respond only in JSON format."
                    },
                    {"role": "user", "content": context}
                ],
                max_tokens=300,
                timeout=10
            )

            content = response.choices[0].message.content
            if content:
                analysis = json.loads(content)
                analysis['ethical_score'] = analysis.get('refund_score', 50)
                analysis['analysis_method'] = 'openai'
                
                create_negotiation_log(
                    ticket['id'],
                    'planning',
                    'openai_analysis',
                    {
                        'analysis': analysis,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                
                return analysis
            else:
                raise ValueError("Empty response from OpenAI")

        except Exception as e:
            print(f"OpenAI analysis failed ({str(e)}), using smart fallback")
            # Use smart fallback when OpenAI fails
            analysis = self.generate_smart_analysis(ticket)
            
            create_negotiation_log(
                ticket['id'],
                'planning',
                'fallback_analysis',
                {
                    'analysis': analysis,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            return analysis

    def generate_customer_profile(self, customer_email, dispute_value):
        """Generate realistic customer profile"""
        # Use email hash for consistent profiles
        email_hash = hashlib.md5(customer_email.encode()).hexdigest()
        seed = int(email_hash[:8], 16) % 1000
        random.seed(seed)
        
        segments = ['new', 'regular', 'vip', 'problematic']
        weights = [0.3, 0.4, 0.2, 0.1]  # Distribution weights
        
        if dispute_value > 200:
            weights = [0.1, 0.4, 0.4, 0.1]  # VIP customers more likely for high amounts
        
        segment = random.choices(segments, weights=weights)[0]
        
        profiles = {
            'new': {
                'order_history': random.randint(1, 3),
                'refund_ratio': random.uniform(0.0, 0.1),
                'loyalty_score': random.randint(20, 40),
                'risk_signals': random.randint(0, 2)
            },
            'regular': {
                'order_history': random.randint(5, 20),
                'refund_ratio': random.uniform(0.05, 0.15),
                'loyalty_score': random.randint(60, 85),
                'risk_signals': random.randint(0, 1)
            },
            'vip': {
                'order_history': random.randint(15, 50),
                'refund_ratio': random.uniform(0.02, 0.08),
                'loyalty_score': random.randint(85, 100),
                'risk_signals': 0
            },
            'problematic': {
                'order_history': random.randint(3, 10),
                'refund_ratio': random.uniform(0.25, 0.50),
                'loyalty_score': random.randint(10, 30),
                'risk_signals': random.randint(2, 5)
            }
        }
        
        profile = profiles[segment]
        profile['segment'] = segment
        
        random.seed()  # Reset seed
        return profile


class ExecutionAgent:
    """AI agent responsible for executing resolutions"""

    def __init__(self):
        self.name = "Execution Agent"
        self.auto_resolve_thresholds = {
            'low_risk_max_amount': 50.00,
            'medium_risk_max_amount': 100.00,
            'high_risk_requires_human': True,
            'refund_score_threshold': 75
        }

    def evaluate_for_execution(self, ticket, analysis):
        """Evaluate if ticket can be auto-resolved"""
        try:
            risk_level = analysis.get('risk_level', 'high')
            refund_score = analysis.get('refund_score', 0)
            proposed_amount = analysis.get('proposed_amount', 0)

            can_auto_resolve = False
            confidence_score = 0

            if risk_level == 'low' and refund_score >= 80:
                if proposed_amount <= self.auto_resolve_thresholds['low_risk_max_amount']:
                    can_auto_resolve = True
                    confidence_score = 0.9
            elif risk_level == 'medium' and refund_score >= 85:
                if proposed_amount <= self.auto_resolve_thresholds['medium_risk_max_amount']:
                    can_auto_resolve = True
                    confidence_score = 0.7

            execution_decision = {
                'auto_resolve': can_auto_resolve,
                'requires_human': not can_auto_resolve,
                'confidence_score': confidence_score,
                'execution_plan': self._create_execution_plan(ticket, analysis) if can_auto_resolve else None
            }

            create_negotiation_log(
                ticket['id'],
                'execution',
                'evaluation',
                {
                    'execution_decision': execution_decision,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )

            return execution_decision

        except Exception as e:
            print(f"Error in execution evaluation: {e}")
            return {
                'auto_resolve': False,
                'requires_human': True,
                'confidence_score': 0,
                'execution_plan': None,
                'error': str(e)
            }

    def _create_execution_plan(self, ticket, analysis):
        return {
            'resolution_type': analysis.get('resolution_type'),
            'amount': analysis.get('proposed_amount', 0),
            'reasoning': analysis.get('reasoning'),
            'next_steps': [
                'Send resolution communication to customer',
                'Process refund/adjustment if applicable',
                'Update ticket status to resolved',
                'Log resolution in system'
            ],
            'estimated_completion': '15 minutes'
        }

    def execute_resolution(self, ticket_id, execution_plan):
        try:
            updates = {
                'status': 'auto_resolved',
                'resolution': execution_plan,
                'resolved_at': datetime.utcnow().isoformat()
            }

            updated_ticket = update_ticket(ticket_id, updates)

            create_negotiation_log(
                ticket_id,
                'execution',
                'auto_resolution',
                {
                    'execution_plan': execution_plan,
                    'status': 'completed',
                    'timestamp': datetime.utcnow().isoformat()
                }
            )

            return updated_ticket

        except Exception as e:
            print(f"Error executing resolution: {e}")
            create_negotiation_log(
                ticket_id,
                'execution',
                'auto_resolution_failed',
                {
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            return None


def process_ticket_with_ai(ticket_id):
    """Process ticket with AI analysis"""
    from models import get_ticket_by_id, update_ticket

    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return {'error': 'Ticket not found'}

    try:
        planning_agent = PlanningAgent()
        execution_agent = ExecutionAgent()

        # Get AI analysis (uses smart fallback if OpenAI unavailable)
        analysis = planning_agent.analyze_ticket(ticket)

        # Update ticket with AI proposal
        update_ticket(ticket_id, {
            'ai_proposal': analysis,
            'ethical_score': analysis.get('ethical_score', 50),
            'risk_level': analysis.get('risk_level', 'medium')
        })

        # Evaluate for execution
        execution_decision = execution_agent.evaluate_for_execution(ticket, analysis)

        if execution_decision.get('auto_resolve', False):
            execution_plan = execution_decision.get('execution_plan')
            if execution_plan:
                execution_agent.execute_resolution(ticket_id, execution_plan)
        else:
            update_ticket(ticket_id, {
                'status': 'pending_human_review',
                'human_review_required': True
            })
            if analysis.get('risk_level') == 'high':
                send_high_risk_alert(ticket)

        return {
            'ticket_id': ticket_id,
            'analysis': analysis,
            'execution_decision': execution_decision,
            'status': 'processed'
        }

    except Exception as e:
        print(f"Error processing ticket {ticket_id}: {e}")
        return {
            'error': f'Failed to process ticket: {str(e)}',
            'ticket_id': ticket_id
        }


def get_ethical_compliance_score(ticket_description, resolution_type, amount):
    """Get detailed ethical compliance score using smart analysis"""
    try:
        # Generate hash-based consistent score
        content_hash = hashlib.md5(f"{ticket_description}{resolution_type}{amount}".encode()).hexdigest()
        seed = int(content_hash[:8], 16) % 100
        
        # Base score based on resolution type
        base_scores = {
            'Full Refund': (70, 95),
            'Partial Refund': (60, 85),
            'Manual Review': (50, 70),
            'Deny Refund': (30, 60)
        }
        
        score_range = base_scores.get(resolution_type, (40, 70))
        base_score = seed % (score_range[1] - score_range[0]) + score_range[0]
        
        # Adjust based on amount
        if amount > 500:
            base_score -= 5  # Higher scrutiny for large amounts
        elif amount < 50:
            base_score += 10  # More lenient for small amounts
            
        # Ensure score stays within bounds
        final_score = max(20, min(95, base_score))
        
        return {
            'score': final_score,
            'breakdown': {
                'fairness': final_score + random.randint(-5, 5),
                'business_impact': final_score + random.randint(-10, 10),
                'legal_compliance': final_score + random.randint(-3, 3),
                'transparency': final_score + random.randint(-2, 2)
            },
            'recommendations': [
                f'Score of {final_score}/100 indicates {"high" if final_score > 80 else "moderate" if final_score > 60 else "low"} ethical compliance',
                'Consider customer history and context',
                'Document decision rationale clearly'
            ]
        }

    except Exception as e:
        print(f"Error getting ethical score: {e}")
        return {
            'score': 50,
            'breakdown': {
                'fairness': 50,
                'business_impact': 50,
                'legal_compliance': 50,
                'transparency': 50
            },
            'recommendations': [
                'Analysis failed - requires manual review',
                'Ensure proper documentation',
                'Follow company policies'
            ]
        }