import os
import random
import secrets
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from notes.models import NoteCollaboratorInvite

from .models import User


@shared_task
def send_verification_email(user_id):
    """Send email verification link to user."""
    try:
        user = User.objects.get(id=user_id)

        token = secrets.token_urlsafe(32)
        user.email_verification_token = token
        user.save(update_fields=["email_verification_token"])

        verification_url = f"http://localhost:3000/verify-email/{token}/"

        subject = "Email Verification - FundooNotes"
        message = f"""
Hello {user.name},

Please click the link below to verify your email:
{verification_url}

This link will expire in 24 hours.

If you didn't create this account, please ignore this email.

Best regards,
FundooNotes Team
"""

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return f"Verification email sent to {user.email}"
    except User.DoesNotExist:
        return f"User {user_id} not found"
    except Exception as e:
        return f"Error sending email: {str(e)}"


@shared_task
def cleanup_expired_tokens():
    """Remove verification tokens that are too old."""
    cutoff_time = timezone.now() - timedelta(days=1)
    User.objects.filter(
        email_verification_token__isnull=False,
        updated_at__lt=cutoff_time,
    ).update(email_verification_token=None)
    return "Cleaned up expired tokens"


@shared_task
def send_otp_email(user_id):
    """Generate and send 6-digit OTP for email verification."""
    try:
        user = User.objects.get(id=user_id)

        otp = f"{random.randint(0, 999999):06d}"
        user.otp_code = otp
        user.otp_expires_at = timezone.now() + timedelta(minutes=10)
        user.save(update_fields=["otp_code", "otp_expires_at"])

        subject = "Your FundooNotes Verification OTP"
        message = f"""
Hello {user.name},

Your OTP is: {otp}

This OTP is valid for 10 minutes.

If you did not request this, please ignore this email.
"""

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return f"OTP sent to {user.email}"
    except User.DoesNotExist:
        return f"User {user_id} not found"
    except Exception as e:
        return f"Error sending OTP: {str(e)}"


@shared_task
def send_note_collaborator_added_email(invite_id):
    """Send a collaborator invitation email notification (action in dashboard)."""
    try:
        invite = NoteCollaboratorInvite.objects.select_related(
            "invited_user",
            "invited_by",
            "note",
        ).get(pk=invite_id)
        user = invite.invited_user

        access_text = "can edit" if invite.access_level == "edit" else "can view"

        subject = f"Invitation to collaborate on: {invite.note.title}"
        message = f"""
Hello {user.name or user.email},

You have been invited to collaborate on this note.

Note: {invite.note.title}
Owner: {invite.invited_by.name or invite.invited_by.email}
Access: {access_text}

To accept or decline this invitation, please log in to FundooNotes and go to your dashboard where you can manage pending invitations.

Best regards,
FundooNotes Team
"""
        html_message = f"""
<html>
  <body style="font-family: Arial, sans-serif; color: #202124; line-height: 1.5;">
    <div style="max-width: 560px; margin: 0 auto; padding: 24px; border: 1px solid #dadce0; border-radius: 16px;">
      <h2 style="margin: 0 0 16px;">FundooNotes invitation</h2>
      <p>Hello {user.name or user.email},</p>
      <p>You have been invited to collaborate on this note.</p>
      <p><strong>Note:</strong> {invite.note.title}<br/>
      <strong>Owner:</strong> {invite.invited_by.name or invite.invited_by.email}<br/>
      <strong>Access:</strong> {access_text}</p>
      <p>To accept or decline this invitation, please <strong>log in to FundooNotes</strong> and visit your dashboard. You will find all pending invitations in the Invitations section where you can manage them.</p>
      <p style="color:#5f6368;font-size:12px;">This is an automated notification. Please do not reply to this email.</p>
    </div>
  </body>
</html>
"""

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=html_message,
        )
        return f"Invitation email sent to {user.email}"
    except User.DoesNotExist:
        return "User not found for invite"
    except Exception as e:
        return f"Error sending collaborator invitation email: {str(e)}"
