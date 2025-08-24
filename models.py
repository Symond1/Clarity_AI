import uuid
from datetime import datetime
import random

# In-memory databases
users_db = {}
tickets_db = {}
negotiations_db = {}

def create_user(name, email, picture=""):
    """Create a new user"""
    user_id = str(uuid.uuid4())
    user = {
        'id': user_id,
        'name': name,
        'email': email,
        'picture': picture,
        'created_at': datetime.utcnow().isoformat(),
        'role': 'admin'  # All users are admins for demo purposes
    }
    users_db[user_id] = user
    return user

def get_user_by_email(email):
    """Get user by email"""
    for user in users_db.values():
        if user['email'] == email:
            return user
    return None

def create_ticket(title, description, customer_email, dispute_value, category="general"):
    """Create a new dispute ticket"""
    ticket_id = str(uuid.uuid4())
    ticket = {
        'id': ticket_id,
        'title': title,
        'description': description,
        'customer_email': customer_email,
        'dispute_value': dispute_value,
        'category': category,
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'ai_proposal': None,
        'ethical_score': None,
        'risk_level': 'medium',
        'human_decision': None,
        'resolution': None
    }
    tickets_db[ticket_id] = ticket
    return ticket

def update_ticket(ticket_id, updates):
    """Update a ticket"""
    if ticket_id in tickets_db:
        tickets_db[ticket_id].update(updates)
        tickets_db[ticket_id]['updated_at'] = datetime.utcnow().isoformat()
        return tickets_db[ticket_id]
    return None

def get_all_tickets():
    """Get all tickets"""
    return list(tickets_db.values())

def get_ticket_by_id(ticket_id):
    """Get ticket by ID"""
    return tickets_db.get(ticket_id)

def create_negotiation_log(ticket_id, agent_type, action, details):
    """Create a negotiation log entry"""
    log_id = str(uuid.uuid4())
    log = {
        'id': log_id,
        'ticket_id': ticket_id,
        'agent_type': agent_type,  # 'planning' or 'execution'
        'action': action,
        'details': details,
        'timestamp': datetime.utcnow().isoformat()
    }
    if ticket_id not in negotiations_db:
        negotiations_db[ticket_id] = []
    negotiations_db[ticket_id].append(log)
    return log

def get_negotiations_for_ticket(ticket_id):
    """Get all negotiation logs for a ticket"""
    return negotiations_db.get(ticket_id, [])

def init_sample_data():
    """Initialize sample dispute tickets for demo"""
    sample_tickets = [
        {
            'title': 'Defective Product - Wireless Headphones',
            'description': 'Customer received wireless headphones that stopped working after 2 days. Requesting full refund of $150.',
            'customer_email': 'john.doe@email.com',
            'dispute_value': 150.00,
            'category': 'product_defect'
        },
        {
            'title': 'Late Delivery Compensation',
            'description': 'Package was delivered 5 days late for an important event. Customer demands compensation for inconvenience.',
            'customer_email': 'sarah.smith@email.com',
            'dispute_value': 75.00,
            'category': 'shipping'
        },
        {
            'title': 'Unauthorized Charge Dispute',
            'description': 'Customer claims they never authorized a subscription charge of $29.99/month. Requesting immediate refund.',
            'customer_email': 'mike.jones@email.com',
            'dispute_value': 89.97,
            'category': 'billing'
        },
        {
            'title': 'Service Quality Complaint',
            'description': 'Customer unsatisfied with cleaning service quality. Requesting 50% refund and service redo.',
            'customer_email': 'lisa.brown@email.com',
            'dispute_value': 200.00,
            'category': 'service'
        },
        {
            'title': 'Wrong Item Shipped',
            'description': 'Customer ordered blue shirt size L but received red shirt size M. Wants correct item plus expedited shipping.',
            'customer_email': 'david.wilson@email.com',
            'dispute_value': 45.00,
            'category': 'shipping'
        },
        {
            'title': 'Damaged Goods on Arrival',
            'description': 'Electronics package arrived with visible damage. Customer requesting replacement and shipping refund.',
            'customer_email': 'emily.davis@email.com',
            'dispute_value': 320.00,
            'category': 'product_defect'
        },
        {
            'title': 'Subscription Cancellation Issue',
            'description': 'Customer tried to cancel subscription but was still charged. Requesting refund for last 3 months.',
            'customer_email': 'robert.taylor@email.com',
            'dispute_value': 147.00,
            'category': 'billing'
        },
        {
            'title': 'Installation Service Problems',
            'description': 'Technician arrived late and installation was incomplete. Customer wants partial refund and rework.',
            'customer_email': 'jennifer.moore@email.com',
            'dispute_value': 180.00,
            'category': 'service'
        },
        {
            'title': 'Gift Card Balance Dispute',
            'description': 'Customer claims gift card balance disappeared without any purchases. Requesting balance restoration.',
            'customer_email': 'chris.anderson@email.com',
            'dispute_value': 100.00,
            'category': 'billing'
        },
        {
            'title': 'Event Ticket Cancellation',
            'description': 'Event was cancelled due to weather but customer not offered full refund. Requesting complete reimbursement.',
            'customer_email': 'amanda.white@email.com',
            'dispute_value': 250.00,
            'category': 'service'
        },
        {
            'title': 'Food Delivery Quality Issue',
            'description': 'Food arrived cold and order was incomplete. Customer requesting full refund and future discount.',
            'customer_email': 'kevin.martinez@email.com',
            'dispute_value': 35.00,
            'category': 'service'
        },
        {
            'title': 'Software License Overpayment',
            'description': 'Customer was charged for enterprise license instead of standard license. Requesting price difference refund.',
            'customer_email': 'michelle.garcia@email.com',
            'dispute_value': 890.00,
            'category': 'billing'
        },
        {
            'title': 'Hotel Reservation Mishap',
            'description': 'Hotel room was double-booked and customer had to find alternative accommodation. Seeking compensation.',
            'customer_email': 'daniel.rodriguez@email.com',
            'dispute_value': 420.00,
            'category': 'service'
        },
        {
            'title': 'Warranty Claim Denial',
            'description': 'Product failed within warranty period but claim was denied. Customer disputing warranty decision.',
            'customer_email': 'stephanie.lee@email.com',
            'dispute_value': 275.00,
            'category': 'product_defect'
        },
        {
            'title': 'Overcharged Shipping Fees',
            'description': 'Customer was charged express shipping but received standard delivery. Requesting shipping fee refund.',
            'customer_email': 'brian.clark@email.com',
            'dispute_value': 25.00,
            'category': 'shipping'
        }
    ]
    
    for ticket_data in sample_tickets:
        create_ticket(**ticket_data)
    
    print(f"Initialized {len(sample_tickets)} sample dispute tickets")
