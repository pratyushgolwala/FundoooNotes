import secrets
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import User

@shared_task
def send_verification_email(user_id):
    """Send email verification link to user"""
    try:
        user = User.objects.get(id=user_id)
        
        # Generate verification token
        token = secrets.token_urlsafe(32)
        user.email_verification_token = token
        user.save(update_fields=['email_verification_token'])
        
        # Build verification URL
        verification_url = f"http://127.0.0.1:8000/verify-email/{token}/"
        
        # Send email
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
    """Remove verification tokens that are too old"""
    cutoff_time = timezone.now() - timedelta(days=1)
    User.objects.filter(
        email_verification_token__isnull=False,
        updated_at__lt=cutoff_time
    ).update(email_verification_token=None)
    return "Cleaned up expired tokens"