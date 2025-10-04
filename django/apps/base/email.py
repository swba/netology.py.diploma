import logging
from typing import TypedDict

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class EmailParams(TypedDict, total=False):
    """Optional parameters to send email."""
    subject: str # Email subject.
    from_email: str # Email sender.
    cc: str|list[str]
    bcc: str|list[str]
    attachments: list

def send_email(key: str, to: str|list[str], *, params: EmailParams|None = None,
        context: dict|None = None) -> int:
    """Sends an email.

    Args:
        key: Unique email type key. Should start with "{app_name}_" to
            avoid collisions.
        to: Email recipient(s).
        params: Additional email parameters.
        context: Context for rendering email message(s).

    Returns:
        Either the result of the immediate email sending or ID of the
        corresponding Celery task if settings.EMAIL_ASYNC is set to
        True.
    """
    if type(to) is not list:
        to = [to]
    subject = params.get('subject')
    from_email = params.get('from_email', settings.DEFAULT_FROM_EMAIL)
    cc = params.get('cc')
    if cc and type(cc) is not list:
        cc = [cc]
    bcc = params.get('bcc')
    if bcc and type(bcc) is not list:
        bcc = [bcc]
    attachments = params.get('attachments')

    text_message = html_message = ''
    try:
        text_message = render_to_string(f'emails/{key}.txt', context)
    except (TemplateDoesNotExist, TemplateSyntaxError) as e:
        logger.error(e.message)
    try:
        html_message = render_to_string(f'emails/{key}.html', context)
    except (TemplateDoesNotExist, TemplateSyntaxError) as e:
        logger.error(e.message)

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

    if settings.EMAIL_ASYNC: # Send email using Celery.
        return -1
    else:
        return message.send()
