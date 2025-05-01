import pytest
from unittest.mock import patch, MagicMock
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging 
from app.utils.smtp_connection import SMTPClient

TEST_SERVER = "smtp.testserver.com"
TEST_PORT = 587
TEST_USERNAME = "test_user@test.com"
TEST_PASSWORD = "testpassword"
TEST_RECIPIENT = "recipient@test.com"
TEST_SUBJECT = "Test Email Subject"
TEST_HTML_CONTENT = "<p>This is a test email.</p>"


@pytest.fixture
def smtp_client_instance():
    """Provides an instance of the SMTPClient for tests."""
    return SMTPClient(TEST_SERVER, TEST_PORT, TEST_USERNAME, TEST_PASSWORD)

@patch('app.utils.smtp_connection.smtplib.SMTP')
@patch('app.utils.smtp_connection.logging')
def test_send_email_success(mock_logging, mock_smtp_class, smtp_client_instance):
    """
    Test that send_email successfully sends an email and logs info.
    Mocks smtplib.SMTP and logging.
    """
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value.__enter__.return_value = mock_smtp_instance

    smtp_client_instance.send_email(
        TEST_SUBJECT,
        TEST_HTML_CONTENT,
        TEST_RECIPIENT
    )

    mock_smtp_class.assert_called_once_with(TEST_SERVER, TEST_PORT)

    mock_smtp_instance.starttls.assert_called_once()

    mock_smtp_instance.login.assert_called_once_with(TEST_USERNAME, TEST_PASSWORD)

    mock_smtp_instance.sendmail.assert_called_once()
    sent_from, sent_to, sent_message_string = mock_smtp_instance.sendmail.call_args[0]

    assert sent_from == TEST_USERNAME
    assert sent_to == TEST_RECIPIENT

    from email.parser import Parser
    parser = Parser()
    sent_message = parser.parsestr(sent_message_string)

    assert sent_message['Subject'] == TEST_SUBJECT
    assert sent_message['From'] == TEST_USERNAME
    assert sent_message['To'] == TEST_RECIPIENT

    html_part_found = False
    for part in sent_message.walk():
        if part.get_content_type() == 'text/html':
            assert part.get_payload(decode=True).decode(part.get_content_charset()) == TEST_HTML_CONTENT
            html_part_found = True
            break

    assert html_part_found, "HTML content part not found in the sent message"

    mock_logging.info.assert_called_once_with(f"Email sent to {TEST_RECIPIENT}")


@patch('app.utils.smtp_connection.smtplib.SMTP')
@patch('app.utils.smtp_connection.logging')
def test_send_email_logs_error_and_raises(mock_logging, mock_smtp_class, smtp_client_instance):
    """
    Test that send_email logs an error and re-raises the exception if sending fails.
    Mocks smtplib.SMTP to raise an exception and mocks logging.
    """
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value.__enter__.return_value = mock_smtp_instance

    mock_smtp_instance.starttls.side_effect = smtplib.SMTPException("Simulated SMTP error")

    with pytest.raises(smtplib.SMTPException) as excinfo:
        smtp_client_instance.send_email(
            TEST_SUBJECT,
            TEST_HTML_CONTENT,
            TEST_RECIPIENT
        )

    mock_smtp_class.assert_called_once_with(TEST_SERVER, TEST_PORT)

    assert "Simulated SMTP error" in str(excinfo.value)

    mock_logging.error.assert_called_once()
    error_message = mock_logging.error.call_args[0][0]
    assert "Failed to send email: Simulated SMTP error" in error_message

    mock_smtp_instance.sendmail.assert_not_called()

    mock_smtp_class.return_value.__enter__.assert_called_once()
    mock_smtp_class.return_value.__exit__.assert_called_once()
