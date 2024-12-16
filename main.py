import base64
import json
import functions_framework
from google.oauth2 import service_account
from googleapiclient.discovery import build
from email.mime.text import MIMEText

def create_message(sender, to, subject, message_text):
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

def send_gmail_message(service, user_id, message):
    try:
        message = service.users().messages().send(
            userId=user_id, body=message).execute()
        print(f'Message Id: {message["id"]}')
        return message
    except Exception as e:
        print(f'An error occurred: {e}')
        raise e

@functions_framework.cloud_event
def send_notification(cloud_event):
    try:
        # Get message data from Pub/Sub
        pubsub_message = json.loads(cloud_event.data["message"]["data"])
        event_type = pubsub_message.get('event_type')
        data = pubsub_message.get('data', {})
        user_email = data.get('user_email')

        # Create email content based on event type
        if event_type == 'schedule_created':
            subject = 'New Schedule Created'
            content = f"""
            A new schedule has been created:
            Title: {data.get('title')}
            Start Time: {data.get('start_time')}
            End Time: {data.get('end_time')}
            """
        elif event_type == 'task_created':
            subject = 'New Task Created'
            content = f"""
            A new task has been created:
            Title: {data.get('title')}
            Description: {data.get('description')}
            Due Date: {data.get('due_date')}
            """
        else:
            print(f"Unsupported event type: {event_type}")
            return

        # Create Gmail API service
        credentials = service_account.Credentials.from_service_account_file(
            'credentials/cloud-computing-439018-f1a92afa094f.json',
            scopes=['https://www.googleapis.com/auth/gmail.send']
        )
        service = build('gmail', 'v1', credentials=credentials)

        # Create and send email
        sender = "gl2736@columbia.edu"  # Your email
        message = create_message(sender, user_email, subject, content)
        send_gmail_message(service, 'me', message)
        print(f"Email sent successfully to {user_email}")

    except Exception as e:
        print(f"Error processing message: {str(e)}")
        raise e