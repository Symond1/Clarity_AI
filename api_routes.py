import os
import json
import jwt
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from models import get_all_tickets, get_ticket_by_id, update_ticket, get_negotiations_for_ticket
from ai_agents import process_ticket_with_ai, get_ethical_compliance_score

api_bp = Blueprint('api', __name__)

JWT_SECRET = os.environ.get("JWT_SECRET", "your-jwt-secret")

# JWT helper
def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Auth decorator
def require_auth(f):
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({'error': 'Invalid token'}), 401
        
        g.current_user = payload
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__  # Fixed this line
    return decorated_function

# --- Ticket routes ---
@api_bp.route('/tickets', methods=['GET'])
@require_auth
def get_tickets():
    try:
        tickets = get_all_tickets()
        return jsonify({'tickets': tickets, 'total': len(tickets)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tickets/<ticket_id>', methods=['GET'])
@require_auth
def get_ticket(ticket_id):
    try:
        ticket = get_ticket_by_id(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        negotiations = get_negotiations_for_ticket(ticket_id)
        return jsonify({'ticket': ticket, 'negotiations': negotiations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tickets/<ticket_id>/process', methods=['POST'])
@require_auth
def process_ticket(ticket_id):
    try:
        result = process_ticket_with_ai(ticket_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tickets/<ticket_id>/human-decision', methods=['POST'])
@require_auth
def human_decision(ticket_id):
    try:
        data = request.get_json()
        decision = data.get('decision')
        comments = data.get('comments', '')
        
        if decision == 'approve':
            # Update ticket status to resolved
            update_ticket(ticket_id, {
                'status': 'resolved',
                'human_decision': {
                    'decision': 'approve',
                    'comments': comments,
                    'timestamp': datetime.utcnow().isoformat()
                },
                'resolved_at': datetime.utcnow().isoformat()
            })
        elif decision == 'override':
            # Update ticket with override resolution
            override_resolution = data.get('override_resolution', {})
            update_ticket(ticket_id, {
                'status': 'resolved',
                'human_decision': {
                    'decision': 'override',
                    'override_resolution': override_resolution,
                    'comments': comments,
                    'timestamp': datetime.utcnow().isoformat()
                },
                'resolved_at': datetime.utcnow().isoformat()
            })
        
        return jsonify({'message': 'Decision processed successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Analytics endpoint (was missing)
@api_bp.route('/analytics/dashboard', methods=['GET'])
@require_auth
def get_analytics():
    try:
        tickets = get_all_tickets()
        
        total_tickets = len(tickets)
        pending_tickets = len([t for t in tickets if t['status'] in ['pending', 'pending_human_review']])
        resolved_tickets = len([t for t in tickets if t['status'] in ['resolved', 'auto_resolved']])
        high_risk_tickets = len([t for t in tickets if t.get('risk_level') == 'high'])
        
        analytics = {
            'overview': {
                'total_tickets': total_tickets,
                'pending_tickets': pending_tickets,
                'resolved_tickets': resolved_tickets,
                'high_risk_tickets': high_risk_tickets
            }
        }
        
        return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500