"""Helper functions for setting up notification system."""

from typing import Optional
from src.config import settings
from src.notifications.manager import NotificationManager
from src.notifications.slack import SlackNotifier
from src.notifications.discord import DiscordNotifier
from src.notifications.email import EmailNotifier
from src.notifications.pagerduty import PagerDutyNotifier


def create_notification_manager() -> NotificationManager:
    """
    Create and configure notification manager based on settings.

    Returns:
        Configured NotificationManager instance
    """
    manager = NotificationManager()

    if not settings.notifications_enabled:
        return manager

    # Setup Slack
    if settings.slack_webhook_url or settings.slack_api_token:
        try:
            slack = SlackNotifier(
                webhook_url=settings.slack_webhook_url,
                api_token=settings.slack_api_token,
                channel=settings.slack_channel,
            )
            manager.add_channel(slack)
        except Exception as e:
            print(f"Warning: Failed to initialize Slack notifier: {e}")

    # Setup Discord
    if settings.discord_webhook_url:
        try:
            discord = DiscordNotifier(
                webhook_url=settings.discord_webhook_url,
            )
            manager.add_channel(discord)
        except Exception as e:
            print(f"Warning: Failed to initialize Discord notifier: {e}")

    # Setup Email
    if settings.smtp_host and settings.smtp_to_emails:
        try:
            to_emails = [email.strip() for email in settings.smtp_to_emails.split(",")]
            email = EmailNotifier(
                smtp_host=settings.smtp_host,
                smtp_port=settings.smtp_port,
                smtp_user=settings.smtp_user or "",
                smtp_password=settings.smtp_password or "",
                from_email=settings.smtp_from_email or settings.smtp_user or "",
                to_emails=to_emails,
            )
            manager.add_channel(email)
        except Exception as e:
            print(f"Warning: Failed to initialize Email notifier: {e}")

    # Setup PagerDuty
    if settings.pagerduty_integration_key:
        try:
            pagerduty = PagerDutyNotifier(
                integration_key=settings.pagerduty_integration_key,
            )
            manager.add_channel(pagerduty)
        except Exception as e:
            print(f"Warning: Failed to initialize PagerDuty notifier: {e}")

    return manager


# Global notification manager instance
notification_manager: Optional[NotificationManager] = None


def get_notification_manager() -> NotificationManager:
    """
    Get global notification manager instance (singleton).

    Returns:
        NotificationManager instance
    """
    global notification_manager
    if notification_manager is None:
        notification_manager = create_notification_manager()
    return notification_manager
