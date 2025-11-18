"""Email notification channel."""

from typing import List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from src.notifications.base import (
    NotificationChannel,
    Alert,
    NotificationResult,
    NotificationStatus,
    NotificationPriority,
)


class EmailNotifier(NotificationChannel):
    """Send notifications via email (SMTP)."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_password: str = "",
        from_email: str = "",
        to_emails: List[str] = None,
        use_tls: bool = True,
        enabled: bool = True,
    ) -> None:
        """
        Initialize email notifier.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            from_email: Sender email address
            to_emails: List of recipient email addresses
            use_tls: Use TLS encryption
            enabled: Whether channel is enabled
        """
        super().__init__("email", enabled)
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email or smtp_user
        self.to_emails = to_emails or []
        self.use_tls = use_tls

    async def send(self, alert: Alert) -> NotificationResult:
        """Send alert via email."""
        if not self.should_send(alert):
            return NotificationResult(
                success=False,
                channel=self.name,
                status=NotificationStatus.THROTTLED,
                message="Alert not sent (channel disabled or filtered)",
            )

        if not self.to_emails:
            return NotificationResult(
                success=False,
                channel=self.name,
                status=NotificationStatus.FAILED,
                message="No recipient emails configured",
            )

        try:
            msg = self._build_email(alert)

            # Send email synchronously (in async wrapper)
            import asyncio
            await asyncio.to_thread(self._send_email, msg)

            return NotificationResult(
                success=True,
                channel=self.name,
                status=NotificationStatus.SENT,
                message=f"Alert sent to {len(self.to_emails)} recipients",
                sent_at=datetime.utcnow(),
                metadata={"recipients": self.to_emails},
            )

        except Exception as e:
            return NotificationResult(
                success=False,
                channel=self.name,
                status=NotificationStatus.FAILED,
                message=f"Failed to send email: {str(e)}",
                error=str(e),
            )

    def _build_email(self, alert: Alert) -> MIMEMultipart:
        """Build email message."""
        msg = MIMEMultipart("alternative")

        # Subject
        priority_prefix = {
            NotificationPriority.LOW: "[INFO]",
            NotificationPriority.MEDIUM: "[WARNING]",
            NotificationPriority.HIGH: "[ERROR]",
            NotificationPriority.CRITICAL: "[CRITICAL]",
        }
        prefix = priority_prefix.get(alert.priority, "[ALERT]")
        msg["Subject"] = f"{prefix} {alert.title}"
        msg["From"] = self.from_email
        msg["To"] = ", ".join(self.to_emails)

        # Plain text version
        text_body = self._build_text_body(alert)
        text_part = MIMEText(text_body, "plain")
        msg.attach(text_part)

        # HTML version
        html_body = self._build_html_body(alert)
        html_part = MIMEText(html_body, "html")
        msg.attach(html_part)

        return msg

    def _build_text_body(self, alert: Alert) -> str:
        """Build plain text email body."""
        body = f"{alert.title}\n"
        body += "=" * len(alert.title) + "\n\n"
        body += f"{alert.message}\n\n"
        body += f"Priority: {alert.priority.value.upper()}\n"
        body += f"Source: {alert.source}\n"
        body += f"Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"

        if alert.tags:
            body += f"Tags: {', '.join(alert.tags)}\n"

        if alert.metadata:
            body += "\nDetails:\n"
            for key, value in alert.metadata.items():
                body += f"  {key}: {value}\n"

        body += "\n---\nPlant AI System Analyzer\n"

        return body

    def _build_html_body(self, alert: Alert) -> str:
        """Build HTML email body."""
        color = self._get_color(alert.priority)

        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background-color: {color}; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
              <h2 style="margin: 0;">{alert.title}</h2>
              <p style="margin: 5px 0 0 0; opacity: 0.9;">{alert.priority.value.upper()} PRIORITY</p>
            </div>

            <div style="background-color: #f5f5f5; padding: 20px; border-radius: 0 0 5px 5px;">
              <p style="font-size: 16px; margin-top: 0;">{alert.message}</p>

              <table style="width: 100%; margin-top: 20px; border-collapse: collapse;">
                <tr>
                  <td style="padding: 8px; background-color: #e0e0e0; font-weight: bold;">Source</td>
                  <td style="padding: 8px; background-color: white;">{alert.source}</td>
                </tr>
                <tr>
                  <td style="padding: 8px; background-color: #e0e0e0; font-weight: bold;">Time</td>
                  <td style="padding: 8px; background-color: white;">{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</td>
                </tr>
        """

        if alert.tags:
            html += f"""
                <tr>
                  <td style="padding: 8px; background-color: #e0e0e0; font-weight: bold;">Tags</td>
                  <td style="padding: 8px; background-color: white;">{', '.join(alert.tags)}</td>
                </tr>
            """

        for key, value in alert.metadata.items():
            html += f"""
                <tr>
                  <td style="padding: 8px; background-color: #e0e0e0; font-weight: bold;">{key.replace('_', ' ').title()}</td>
                  <td style="padding: 8px; background-color: white;">{value}</td>
                </tr>
            """

        html += """
              </table>

              <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ccc; color: #666; font-size: 12px;">
                Plant AI System Analyzer
              </p>
            </div>
          </body>
        </html>
        """

        return html

    def _get_color(self, priority: NotificationPriority) -> str:
        """Get color for priority level."""
        colors = {
            NotificationPriority.LOW: "#2196F3",      # Blue
            NotificationPriority.MEDIUM: "#FF9800",   # Orange
            NotificationPriority.HIGH: "#F44336",     # Red
            NotificationPriority.CRITICAL: "#B71C1C", # Dark Red
        }
        return colors.get(priority, "#757575")

    def _send_email(self, msg: MIMEMultipart) -> None:
        """Send email via SMTP."""
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            if self.use_tls:
                server.starttls()

            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)

            server.send_message(msg)

    def test_connection(self) -> bool:
        """Test email connection."""
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
            return True
        except Exception:
            return False
