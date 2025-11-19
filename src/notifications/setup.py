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

    # Check if notifications feature is enabled
    if not settings.feature_flags.notifications:
        return manager

    # Setup Slack
    if settings.notifications.slack.enabled:
        try:
            slack = SlackNotifier(
                webhook_url=settings.notifications.slack.webhook_url or "",
                api_token=settings.notifications.slack.token or "",
                channel=settings.notifications.slack.channel or "#alerts",
            )
            manager.add_channel(slack)
        except Exception as e:
            print(f"Warning: Failed to initialize Slack notifier: {e}")

    # Setup Discord
    if settings.notifications.discord.enabled:
        try:
            discord = DiscordNotifier(
                webhook_url=settings.notifications.discord.webhook_url or "",
            )
            manager.add_channel(discord)
        except Exception as e:
            print(f"Warning: Failed to initialize Discord notifier: {e}")

    # Setup Email
    if settings.notifications.email.enabled:
        try:
            email = EmailNotifier(
                smtp_host=settings.notifications.email.smtp_host,
                smtp_port=settings.notifications.email.smtp_port,
                smtp_user=settings.notifications.email.smtp_user or "",
                smtp_password=settings.notifications.email.smtp_password or "",
                from_email=settings.notifications.email.from_address,
                to_emails=settings.notifications.email.to_addresses,
            )
            manager.add_channel(email)
        except Exception as e:
            print(f"Warning: Failed to initialize Email notifier: {e}")

    # Setup PagerDuty
    if settings.notifications.pagerduty.enabled:
        try:
            pagerduty = PagerDutyNotifier(
                integration_key=settings.notifications.pagerduty.integration_key or "",
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
