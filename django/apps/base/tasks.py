from celery import shared_task
from django.core.mail import EmailMultiAlternatives


@shared_task
def send_email_task(
        subject: str,
        text_message: str,
        html_message: str,
        from_email: str,
        to: str,
        cc: str = None,
        bcc: str = None,
        attachments: list = None
) -> int:
    """Sends an email using Celery."""
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_message,
        from_email=from_email,
        to=to,
        cc=cc,
        bcc=bcc,
        attachments=attachments,
        alternatives=[(html_message, 'text/html')],
    )
    return message.send()
