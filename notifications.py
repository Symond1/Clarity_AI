import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Slack configuration
SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
SLACK_CHANNEL_ID = os.environ.get('SLACK_CHANNEL_ID')

# Email configuration
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')

def send_slack_notification(message, channel_id=None):
    """Send notification to Slack channel"""
    if not SLACK_BOT_TOKEN:
        print("Slack notification skipped: SLACK_BOT_TOKEN not configured")
        return False
    
    try:
        client = WebClient(token=SLACK_BOT_TOKEN)
        channel = channel_id or SLACK_CHANNEL_ID
        
        if not channel:
            print("Slack notification skipped: No channel configured")
            return False
        
        response = client.chat_postMessage(
            channel=channel,
            text=message,
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message
                    }
                }
            ]
        )
        
        print(f"Slack notification sent successfully: {response['ts']}")
        return True
        
    except SlackApiError as e:
        print(f"Slack notification failed: {e.response['error']}")
        return False
    except Exception as e:
        print(f"Slack notification error: {str(e)}")
        return False

def send_email_notification(subject, body, recipient_email=None):
    """Send email notification"""
    if not EMAIL_USER or not EMAIL_PASSWORD:
        print("Email notification skipped: Email credentials not configured")
        return False
    
    try:
        recipient = recipient_email or ADMIN_EMAIL
        if not recipient:
            print("Email notification skipped: No recipient configured")
            return False
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = recipient
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        
        text = msg.as_string()
        server.sendmail(EMAIL_USER, recipient, text)
        server.quit()
        
        print(f"Email notification sent to {recipient}")
        return True
        
    except Exception as e:
        print(f"Email notification error: {str(e)}")
        return False

def send_high_risk_alert(ticket):
    """Send alert for high-risk dispute tickets"""
    try:
        # Prepare alert message
        slack_message = f"""
🚨 *HIGH RISK DISPUTE ALERT* 🚨

*Ticket ID:* {ticket['id']}
*Title:* {ticket['title']}
*Customer:* {ticket['customer_email']}
*Dispute Value:* ${ticket['dispute_value']:.2f}
*Risk Level:* {ticket.get('risk_level', 'high').upper()}
*Ethical Score:* {ticket.get('ethical_score', 'N/A')}

*Description:*
{ticket['description'][:200]}{'...' if len(ticket['description']) > 200 else ''}

*AI Proposal:*
{ticket.get('ai_proposal', {}).get('resolution_type', 'Pending analysis')}

⚠️ *This ticket requires immediate human review* ⚠️
        """
        
        # Email version
        email_subject = f"HIGH RISK DISPUTE ALERT - Ticket {ticket['id']}"
        email_body = f"""
        <html>
        <body>
        <h2 style="color: #d32f2f;">🚨 HIGH RISK DISPUTE ALERT 🚨</h2>
        
        <table style="border-collapse: collapse; width: 100%;">
        <tr><td style="font-weight: bold;">Ticket ID:</td><td>{ticket['id']}</td></tr>
        <tr><td style="font-weight: bold;">Title:</td><td>{ticket['title']}</td></tr>
        <tr><td style="font-weight: bold;">Customer:</td><td>{ticket['customer_email']}</td></tr>
        <tr><td style="font-weight: bold;">Dispute Value:</td><td>${ticket['dispute_value']:.2f}</td></tr>
        <tr><td style="font-weight: bold;">Risk Level:</td><td style="color: #d32f2f;">{ticket.get('risk_level', 'high').upper()}</td></tr>
        <tr><td style="font-weight: bold;">Ethical Score:</td><td>{ticket.get('ethical_score', 'N/A')}</td></tr>
        </table>
        
        <h3>Description:</h3>
        <p>{ticket['description']}</p>
        
        <h3>AI Proposal:</h3>
        <p>{ticket.get('ai_proposal', {}).get('resolution_type', 'Pending analysis')}</p>
        
        <p style="color: #d32f2f; font-weight: bold;">⚠️ This ticket requires immediate human review ⚠️</p>
        
        <p>Please log into the Clarity AI dashboard to review and take action.</p>
        </body>
        </html>
        """
        
        # Send notifications
        slack_sent = send_slack_notification(slack_message)
        email_sent = send_email_notification(email_subject, email_body)
        
        return {
            'slack_sent': slack_sent,
            'email_sent': email_sent,
            'message': 'High risk alert processed'
        }
        
    except Exception as e:
        print(f"Error sending high risk alert: {str(e)}")
        return {
            'slack_sent': False,
            'email_sent': False,
            'error': str(e)
        }

def send_resolution_update(ticket, resolution_type):
    """Send notification when a ticket is resolved"""
    try:
        message = f"""
✅ *DISPUTE RESOLVED* ✅

*Ticket ID:* {ticket['id']}
*Customer:* {ticket['customer_email']}
*Resolution:* {resolution_type}
*Value:* ${ticket['dispute_value']:.2f}
*Status:* {ticket['status']}

Resolution completed successfully.
        """
        
        send_slack_notification(message)
        
        return True
        
    except Exception as e:
        print(f"Error sending resolution update: {str(e)}")
        return False

def send_daily_summary():
    """Send daily summary of dispute resolution activities"""
    try:
        from models import get_all_tickets
        from datetime import datetime, timedelta
        
        tickets = get_all_tickets()
        today = datetime.utcnow().date()
        
        # Filter today's activities
        today_tickets = []
        for ticket in tickets:
            ticket_date = datetime.fromisoformat(ticket['created_at'].replace('Z', '+00:00')).date()
            if ticket_date == today:
                today_tickets.append(ticket)
        
        resolved_today = len([t for t in today_tickets if t['status'] in ['resolved', 'auto_resolved']])
        pending_review = len([t for t in tickets if t['status'] == 'pending_human_review'])
        
        summary_message = f"""
📊 *DAILY DISPUTE SUMMARY* - {today.strftime('%Y-%m-%d')}

*Today's Activity:*
• New Tickets: {len(today_tickets)}
• Resolved: {resolved_today}
• Pending Human Review: {pending_review}

*Overall Status:*
• Total Active Tickets: {len([t for t in tickets if t['status'] != 'resolved'])}
• Auto-Resolution Rate: {(len([t for t in tickets if t['status'] == 'auto_resolved']) / len(tickets) * 100):.1f}%

Have a great day! 🌟
        """
        
        send_slack_notification(summary_message)
        
        return True
        
    except Exception as e:
        print(f"Error sending daily summary: {str(e)}")
        return False
