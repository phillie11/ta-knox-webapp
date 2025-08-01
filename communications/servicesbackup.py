# communications/services.py
import os
import msal
import requests
from bs4 import BeautifulSoup
import mimetypes
import base64
import logging
import json
import uuid
import re
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import List, Dict, Optional
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.core.mail import send_mail
from django.core.signing import Signer
from django.core.cache import cache

logger = logging.getLogger(__name__)

# communications/services.py - MERGED version with working signature + SharePoint links

import os
import msal
import requests
from bs4 import BeautifulSoup
import mimetypes
import base64
import logging
from django.conf import settings
from django.core.signing import Signer

logger = logging.getLogger(__name__)

class OutlookEmailService:
    def __init__(self):
        # Print what's being loaded from settings for debugging
        print("LOADED FROM SETTINGS:")
        print(f"Client ID: {settings.MS_GRAPH_CLIENT_ID}")
        print(f"Tenant ID: {settings.MS_GRAPH_TENANT_ID}")
        print(f"User Email: {settings.MS_GRAPH_USER_EMAIL}")
        print(f"Client Secret (first 5 chars): {settings.MS_GRAPH_CLIENT_SECRET[:5] if settings.MS_GRAPH_CLIENT_SECRET else 'None'}")

        self.client_id = settings.MS_GRAPH_CLIENT_ID
        self.client_secret = settings.MS_GRAPH_CLIENT_SECRET
        self.tenant_id = settings.MS_GRAPH_TENANT_ID
        self.user_email = settings.MS_GRAPH_USER_EMAIL

        # ENHANCED: Load signature with detailed debugging
        print("\n🔍 SIGNATURE LOADING DEBUG:")
        self.email_signature = self._load_signature()
        print(f"📝 Final signature length: {len(self.email_signature) if self.email_signature else 0} characters")
        if self.email_signature:
            # Show first 200 characters to verify content
            preview = self.email_signature[:200].replace('\n', ' ').replace('\r', ' ')
            print(f"📝 Signature preview: {preview}...")
        print("🔍 SIGNATURE LOADING COMPLETE\n")

        self.scope = ['https://graph.microsoft.com/.default']
        self.token = self._get_access_token()

    def _load_signature(self):
        """Load the Outlook signature from static directory or Windows signatures"""
        try:
            # OPTION 1: Try Django static directory first (your uploaded signature)
            from django.conf import settings
            import os

            static_signature_path = os.path.join(settings.BASE_DIR, 'static', 'signatures', 'estimating.htm')
            print(f"🔍 Trying static signature path: {static_signature_path}")

            if os.path.exists(static_signature_path):
                print(f"✅ Found signature in static directory!")

                with open(static_signature_path, 'r', encoding='utf-8') as file:
                    signature_html = file.read()

                print(f"📄 Static signature loaded, length: {len(signature_html)} characters")

                # Process the signature to handle images
                soup = BeautifulSoup(signature_html, 'lxml')
                images = soup.find_all('img')

                print(f"🖼️ Found {len(images)} images in static signature")

                for i, img in enumerate(images):
                    src = img.get('src')
                    print(f"   Image {i+1}: {src}")

                    if src and not src.startswith('http') and not src.startswith('data:'):
                        # Try to find the image in static/signatures_files/
                        static_image_path = os.path.join(settings.BASE_DIR, 'static', 'signatures_files', os.path.basename(src))
                        print(f"   🔍 Looking for image at: {static_image_path}")

                        if os.path.exists(static_image_path):
                            try:
                                mime_type, _ = mimetypes.guess_type(static_image_path)
                                with open(static_image_path, 'rb') as image_file:
                                    encoded = base64.b64encode(image_file.read()).decode('utf-8')
                                    img['src'] = f"data:{mime_type};base64,{encoded}"
                                print(f"   ✅ Static image embedded: {os.path.basename(static_image_path)}")
                            except Exception as img_error:
                                print(f"   ❌ Error embedding static image: {img_error}")
                        else:
                            print(f"   ⚠️ Static image not found, keeping original src")

                final_signature = str(soup)
                print(f"✅ Static signature processed successfully, final length: {len(final_signature)} characters")
                return final_signature

            # OPTION 2: Fall back to Windows Signatures directory
            print(f"ℹ️ Static signature not found, trying Windows directory")

            username = os.environ.get("USERNAME")
            print(f"🔍 Windows USERNAME detected: '{username}'")

            if not username:
                print(f"⚠️ USERNAME environment variable not set")
                return self._get_fallback_signature()

            # Try the exact signature path from your working version
            signature_path = f"C:\\Users\\{username}\\AppData\\Roaming\\Microsoft\\Signatures\\Estimating (Estimating@ta-knox.co.uk).htm"
            print(f"🔍 Primary signature path: {signature_path}")

            if not os.path.exists(signature_path):
                print(f"❌ Primary signature file not found")

                # List all signature files in the directory to see what's available
                signatures_dir = f"C:\\Users\\{username}\\AppData\\Roaming\\Microsoft\\Signatures"
                print(f"🔍 Checking signatures directory: {signatures_dir}")

                if os.path.exists(signatures_dir):
                    print(f"📁 Signatures directory exists, listing all .htm files:")
                    for file in os.listdir(signatures_dir):
                        if file.endswith('.htm'):
                            full_path = os.path.join(signatures_dir, file)
                            size = os.path.getsize(full_path)
                            print(f"   📄 {file} ({size} bytes)")
                else:
                    print(f"❌ Signatures directory does not exist: {signatures_dir}")

                # Try alternative signature paths with exact names you might have
                alt_paths = [
                    f"C:\\Users\\{username}\\AppData\\Roaming\\Microsoft\\Signatures\\Estimating.htm",
                    f"C:\\Users\\{username}\\AppData\\Roaming\\Microsoft\\Signatures\\Default.htm",
                    f"C:\\Users\\{username}\\AppData\\Roaming\\Microsoft\\Signatures\\estimating@ta-knox.co.uk.htm",
                    f"C:\\Users\\{username}\\AppData\\Roaming\\Microsoft\\Signatures\\estimating.htm"
                ]

                for alt_path in alt_paths:
                    print(f"🔍 Trying alternative: {os.path.basename(alt_path)}")
                    if os.path.exists(alt_path):
                        signature_path = alt_path
                        print(f"✅ Found signature at: {alt_path}")
                        break
                else:
                    print(f"❌ No Windows signature files found, using fallback")
                    return self._get_fallback_signature()

            print(f"📖 Reading Windows signature file: {signature_path}")
            with open(signature_path, 'r', encoding='utf-8') as file:
                signature_html = file.read()

            print(f"✅ Windows signature file read successfully")
            print(f"📄 Original signature length: {len(signature_html)} characters")

            soup = BeautifulSoup(signature_html, 'lxml')
            images = soup.find_all('img')

            print(f"🖼️ Found {len(images)} images in Windows signature")

            for i, img in enumerate(images):
                src = img.get('src')
                print(f"   Image {i+1}: {src}")

                if src and not src.startswith('http') and not src.startswith('data:'):
                    # Build full path to image
                    signature_folder = signature_path.replace('.htm', '_files')
                    image_path = os.path.join(signature_folder, os.path.basename(src))

                    print(f"   🔍 Looking for Windows image at: {image_path}")

                    if os.path.exists(image_path):
                        try:
                            mime_type, _ = mimetypes.guess_type(image_path)
                            with open(image_path, 'rb') as image_file:
                                encoded = base64.b64encode(image_file.read()).decode('utf-8')
                                img['src'] = f"data:{mime_type};base64,{encoded}"
                            print(f"   ✅ Windows image embedded: {os.path.basename(image_path)} ({mime_type})")
                        except Exception as img_error:
                            print(f"   ❌ Error embedding Windows image: {img_error}")
                    else:
                        print(f"   ❌ Windows image file not found: {image_path}")

            final_signature = str(soup)
            print(f"✅ Windows signature processed successfully")
            print(f"📄 Final signature length: {len(final_signature)} characters")
            return final_signature

        except Exception as e:
            print(f"💥 Error loading signature: {str(e)}")
            import traceback
            print(f"📋 Full traceback: {traceback.format_exc()}")
            return self._get_fallback_signature()

    def _get_fallback_signature(self):
        """Fallback signature if Outlook signature cannot be loaded"""
        fallback = """
        <div style="margin-top: 30px; padding-top: 20px; border-top: 2px solid #007bff; font-size: 14px; color: #333;">
            <table style="width: 100%; font-family: Arial, sans-serif;">
                <tr>
                    <td style="padding-right: 20px; vertical-align: top;">
                        <img src="https://www.taknox.co.uk/wp-content/uploads/2020/09/taknox-logo.png"
                             alt="TA Knox Ltd" height="60" style="display: block;">
                    </td>
                    <td style="vertical-align: top;">
                        <div style="line-height: 1.4;">
                            <strong style="color: #007bff; font-size: 16px;">TA Knox Ltd</strong><br>
                            <span style="color: #666;">Estimating Department</span><br>
                            <span style="color: #666;">📧 estimating@taknox.co.uk</span><br>
                            <span style="color: #666;">🌐 www.taknox.co.uk</span><br>
                            <span style="color: #666;">📞 01234 567890</span>
                        </div>
                    </td>
                </tr>
            </table>
        </div>
        """
        print("⚠️ Using fallback signature")
        return fallback

    def _get_access_token(self):
        # Print out the values being used for authentication (for debugging)
        print(f"Tenant ID: {self.tenant_id}")
        print(f"Client ID: {self.client_id}")
        print(f"Client Secret length: {len(self.client_secret)}")

        # Construct the authority URL with explicit protocol and tenant
        authority_url = f"https://login.microsoftonline.com/{self.tenant_id}"
        print(f"Authority URL: {authority_url}")

        # Create the confidential client application
        app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=authority_url
        )

        # Specify the scope for Microsoft Graph API
        scopes = ["https://graph.microsoft.com/.default"]
        print(f"Requesting scopes: {scopes}")

        # Acquire token for client (application)
        result = app.acquire_token_for_client(scopes=scopes)

        # Check for errors in the result
        if "error" in result:
            print(f"Error acquiring token: {result.get('error')}")
            print(f"Error description: {result.get('error_description')}")

        if "access_token" in result:
            token_preview = result["access_token"][:10] + "..." if result["access_token"] else "None"
            print(f"Successfully acquired token: {token_preview}")
            return result["access_token"]
        else:
            error_message = f"Could not acquire token: {result.get('error')}, Description: {result.get('error_description', '')}"
            logger.error(error_message)
            raise Exception(error_message)

    def _generate_simple_tracking_buttons(self, invitation_id):
        """Generate simple tracking buttons that update database directly"""
        signer = Signer()
        token = signer.sign(str(invitation_id))

        # Use simple tracking URLs that don't redirect to external pages
        from django.conf import settings
        base_url = getattr(settings, 'BASE_URL', 'https://taknox.pythonanywhere.com')

        yes_url = f"{base_url}/tenders/track-response/{token}/?response=yes"
        no_url = f"{base_url}/tenders/track-response/{token}/?response=no"

        return f"""
        <div style="text-align: center; margin: 30px 0; padding: 20px; background-color: #f8f9fa; border-radius: 8px;">
            <div style="margin-bottom: 15px;">
                <h3 style="font-size: 18px; font-weight: bold; color: #333; margin: 0;">
                    Please let us know if you will be tendering:
                </h3>
            </div>
            <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin: 0 auto; max-width: 400px;">
                <tr>
                    <td style="text-align: center; padding: 0 10px;">
                        <table border="0" cellspacing="0" cellpadding="0">
                            <tr>
                                <td bgcolor="#00CC00" style="padding: 15px 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0, 204, 0, 0.4); border: 2px solid #00AA00;">
                                    <a href="{yes_url}" target="_blank" style="color: #ffffff; text-decoration: none; display: inline-block; font-weight: bold; font-size: 16px; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">
                                        ✓ Yes, I will tender
                                    </a>
                                </td>
                            </tr>
                        </table>
                    </td>
                    <td style="text-align: center; padding: 0 10px;">
                        <table border="0" cellspacing="0" cellpadding="0">
                            <tr>
                                <td bgcolor="#FF0000" style="padding: 15px 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(255, 0, 0, 0.4); border: 2px solid #CC0000;">
                                    <a href="{no_url}" target="_blank" style="color: #ffffff; text-decoration: none; display: inline-block; font-weight: bold; font-size: 16px; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">
                                        ✗ No, I won't tender
                                    </a>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
            <div style="margin-top: 15px;">
                <p style="font-size: 12px; color: #666; margin: 0;">
                    Click a button above to record your response automatically.
                </p>
            </div>
        </div>
        """

    def _generate_sharepoint_section_with_tracking(self, sharepoint_links, invitation_id):
        """Generate SharePoint section with download tracking"""
        if not sharepoint_links:
            logger.warning("No SharePoint links provided to _generate_sharepoint_section_with_tracking")
            return ""

        signer = Signer()
        token = signer.sign(str(invitation_id))

        from django.conf import settings
        base_url = getattr(settings, 'BASE_URL', 'https://taknox.pythonanywhere.com')

        sharepoint_section = """
        <div style="margin: 20px 0; padding: 20px; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border: 1px solid #dee2e6; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <table width="100%" border="0" cellspacing="0" cellpadding="0">
                <tr>
                    <td>
                        <table border="0" cellspacing="0" cellpadding="0">
                            <tr>
                                <td style="background: #007bff; color: white; width: 40px; height: 40px; border-radius: 50%; text-align: center; vertical-align: middle; font-size: 18px; margin-right: 15px;">
                                    📁
                                </td>
                                <td style="padding-left: 15px;">
                                    <h3 style="color: #007bff; margin: 0; font-size: 18px;">Tender Documents</h3>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        """

        for link in sharepoint_links:
            # Add tracking to SharePoint links
            tracking_url = f"{base_url}/tenders/track-download/{token}/?url={requests.utils.quote(link['url'], safe='')}"

            sharepoint_section += f"""
            <div style="margin: 15px 0; padding: 12px; background: white; border-radius: 6px; border-left: 4px solid #007bff;">
                <table width="100%" border="0" cellspacing="0" cellpadding="0">
                    <tr>
                        <td>
                            <a href="{tracking_url}" target="_blank" style="color: #007bff; text-decoration: none; font-weight: bold; font-size: 16px;">
                                🔗 {link['title']}
                            </a>
                            <br>
                            <span style="font-size: 12px; color: #666;">
                                Click to access documents (SharePoint login may be required)
                            </span>
                        </td>
                    </tr>
                </table>
            </div>
            """

        sharepoint_section += """
            <div style="margin-top: 15px; padding: 10px; background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px;">
                <p style="margin: 0; font-size: 12px; color: #856404;">
                    <strong>Note:</strong> Document access is tracked for tendering purposes.
                </p>
            </div>
        </div>
        """

        logger.info(f"Generated SharePoint section with {len(sharepoint_links)} links")
        return sharepoint_section

    def send_email(self, to_email, subject, body, cc=None, attachments=None, reply_url=None, sharepoint_links=None, invitation_id=None, **kwargs):
        """
        ENHANCED: Send email with SharePoint links and tracking
        """
        try:
            logger.info(f"📧 Sending email to: {to_email}")
            logger.info(f"📧 Subject: {subject}")
            logger.info(f"📧 SharePoint links: {sharepoint_links}")
            logger.info(f"📧 Invitation ID: {invitation_id}")

            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }

            # ENHANCED: Build SharePoint section with tracking
            sharepoint_section = ""
            if sharepoint_links and invitation_id:
                sharepoint_section = self._generate_sharepoint_section_with_tracking(sharepoint_links, invitation_id)
                logger.info("✅ SharePoint section generated with tracking")
            elif sharepoint_links:
                logger.warning("⚠️ SharePoint links provided but no invitation_id for tracking")
            else:
                logger.info("ℹ️ No SharePoint links to include")

            # ENHANCED: Build action buttons with simple tracking
            action_buttons = ""
            if invitation_id:
                action_buttons = self._generate_simple_tracking_buttons(invitation_id)
                logger.info("✅ Action buttons generated with simple tracking")
            elif reply_url:
                # Fallback to old-style buttons if no invitation_id
                action_buttons = self._generate_action_buttons(reply_url)
                logger.info("✅ Fallback action buttons generated")

            # ENHANCED: Build complete email HTML
            html_content = f"""
            <html>
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <!-- Email Body -->
                <div style="margin-bottom: 20px;">
                    {body}
                </div>

                <!-- SharePoint Documents Section -->
                {sharepoint_section}

                <!-- Action Buttons -->
                <div style="margin: 20px 0;">
                    {action_buttons}
                </div>

                <!-- Signature -->
                <div style="margin-top: 20px;">
                    {self.email_signature}
                </div>
            </body>
            </html>
            """

            # DEBUG: Log signature status
            if self.email_signature and len(self.email_signature.strip()) > 10:
                logger.info(f"✅ Email signature included (length: {len(self.email_signature)} characters)")
            else:
                logger.warning(f"⚠️ Email signature missing or empty (length: {len(self.email_signature) if self.email_signature else 0})")

            # Build email message
            email_message = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML",
                        "content": html_content
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": to_email
                            }
                        }
                    ],
                },
                "saveToSentItems": "true"
            }

            # Add CC if provided
            if cc:
                email_message["message"]["ccRecipients"] = [
                    {"emailAddress": {"address": cc_email}} for cc_email in cc
                ]

            # Add attachments if provided
            if attachments:
                email_message["message"]["attachments"] = []
                for attachment in attachments:
                    with open(attachment["path"], "rb") as file:
                        content = base64.b64encode(file.read()).decode('utf-8')

                    attachment_data = {
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": attachment["name"],
                        "contentType": attachment["content_type"],
                        "contentBytes": content
                    }
                    email_message["message"]["attachments"].append(attachment_data)

            # Send the email
            response = requests.post(
                f'https://graph.microsoft.com/v1.0/users/{self.user_email}/sendMail',
                headers=headers,
                json=email_message
            )

            logger.info(f"📧 Email API response: {response.status_code}")

            if response.status_code == 202:
                logger.info(f"✅ Email sent successfully to: {to_email}")
                logger.info(f"✅ Signature included: {bool(self.email_signature)}")
                logger.info(f"✅ SharePoint links included: {len(sharepoint_links) if sharepoint_links else 0}")
                logger.info(f"✅ Action buttons included: {bool(action_buttons)}")
                return True
            else:
                error_message = f"❌ Failed to send email: {response.status_code} - {response.text}"
                logger.error(error_message)
                return False

        except Exception as e:
            logger.exception(f"💥 Error sending email: {str(e)}")
            return False

    def _generate_action_buttons(self, reply_url):
        """Generate HTML for Yes/No action buttons (FALLBACK - old style)"""
        return f"""
        <table width="100%" border="0" cellspacing="0" cellpadding="0">
            <tr>
                <td style="text-align: center; padding: 0 10px;">
                    <table border="0" cellspacing="0" cellpadding="0">
                        <tr>
                            <td bgcolor="#00CC00" style="padding: 12px 18px; border-radius: 3px; border: 2px solid #00AA00;">
                                <a href="{reply_url}?response=yes" target="_blank" style="color: #ffffff; text-decoration: none; display: inline-block; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">Yes, I will tender</a>
                            </td>
                        </tr>
                    </table>
                </td>
                <td width="20">&nbsp;</td>
                <td style="text-align: center; padding: 0 10px;">
                    <table border="0" cellspacing="0" cellpadding="0">
                        <tr>
                            <td bgcolor="#FF0000" style="padding: 12px 18px; border-radius: 3px; border: 2px solid #CC0000;">
                                <a href="{reply_url}?response=no" target="_blank" style="color: #ffffff; text-decoration: none; display: inline-block; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">No, I will not tender</a>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        """

    def send_tender_invitation(self, invitation, tracking_url=None):
        """
        FIXED: Send tender invitation - use custom message from form, no duplicates
        """
        try:
            project = invitation.project
            subcontractor = invitation.subcontractor

            logger.info(f"📧 Sending tender invitation to {subcontractor.email} for project {project.name}")

            # Build subject
            subject = f"Tender Invitation - {project.name}"

            # FIXED: Only use subcontractor deadline (sc_deadline)
            if project.sc_deadline:
                deadline_str = project.sc_deadline.strftime('%d/%m/%Y')
                deadline_description = "subcontractor deadline"
            else:
                deadline_str = "TBC"
                deadline_description = "deadline"

            # FIXED: Use ONLY the custom message from the form, no default text
            if hasattr(invitation, 'custom_message') and invitation.custom_message.strip():
                # Use the custom message exactly as entered in the form
                body = f"""
                <div style="margin-bottom: 20px;">
                    <p>Dear {subcontractor.first_name or 'Sir/Madam'},</p>
                    {invitation.custom_message}
                </div>
                """
                logger.info("✅ Using custom message from form")
            else:
                # Only use fallback if no custom message provided
                body = f"""
                <div style="margin-bottom: 20px;">
                    <p>Dear {subcontractor.first_name or 'Sir/Madam'},</p>

                    <p>We would like to invite you to tender for <strong>{project.name}</strong>.</p>

                    {f'<p><strong>Location:</strong> {project.location}</p>' if project.location else ''}

                    <p>Please find the tender documents accessible via the SharePoint link below.</p>

                    <p>The {deadline_description} is <strong>{deadline_str}</strong>.</p>

                    <p>Please let us know if you will be submitting a tender by clicking one of the buttons below.</p>
                </div>
                """
                logger.info("✅ Using default message (no custom message provided)")

            # Add tracking pixel if tracking_url provided (keep for email open tracking)
            if tracking_url:
                body += f'<img src="{tracking_url}" width="1" height="1" style="display:none;" />'

            # CRITICAL: Check for FORM SharePoint link FIRST (ignore project fields completely)
            sharepoint_links = []

            # 1. PRIORITY: Check if form SharePoint link was passed via invitation object
            if hasattr(invitation, '_form_sharepoint_link') and invitation._form_sharepoint_link:
                sharepoint_url = invitation._form_sharepoint_link
                link_title = getattr(invitation, '_form_sharepoint_description', 'ITT Documents')
                logger.info(f"✅ Using SharePoint link from FORM: {sharepoint_url}")

                sharepoint_links.append({
                    'url': sharepoint_url.strip(),
                    'title': link_title
                })

            # 2. DO NOT use project SharePoint fields at all for tender invitations
            # This ensures only the form's SharePoint link is used

            if sharepoint_links:
                logger.info(f"📎 Using {len(sharepoint_links)} SharePoint links from FORM")
                for i, link in enumerate(sharepoint_links):
                    logger.info(f"   📎 Link {i+1}: {link['title']} -> {link['url']}")
            else:
                logger.warning(f"❌ NO SharePoint link provided in form for {project.name}")

            # Send the email with invitation ID for tracking
            result = self.send_email(
                to_email=subcontractor.email,
                subject=subject,
                body=body,
                sharepoint_links=sharepoint_links,  # Will be empty if no form link provided
                invitation_id=invitation.id
            )

            logger.info(f"📧 Tender invitation send result: {result} for {subcontractor.email}")

            if not result:
                logger.error(f"❌ Email service returned failure for {subcontractor.email}")
            elif not sharepoint_links:
                logger.warning(f"⚠️ Email sent but NO SharePoint links included (none provided in form) for {subcontractor.email}")
            else:
                logger.info(f"✅ Email sent successfully with FORM SharePoint links to {subcontractor.email}")

            return result

        except Exception as e:
            logger.error(f"💥 Error sending tender invitation: {str(e)}")
            logger.exception("Full traceback:")
            return False

    def send_tender_reminder(self, invitation):
        """
        FIXED: Send tender reminder - only use subcontractor deadline
        """
        try:
            project = invitation.project
            subcontractor = invitation.subcontractor

            logger.info(f"📧 Sending tender reminder to {subcontractor.email} for project {project.name}")

            # Build subject
            subject = f"REMINDER: Tender for {project.name}"

            # FIXED: Only use subcontractor deadline (sc_deadline)
            if project.sc_deadline:
                deadline_str = project.sc_deadline.strftime('%d/%m/%Y')
                deadline_description = "subcontractor deadline"
            else:
                deadline_str = "TBC"
                deadline_description = "deadline"

            # Build email body
            body = f"""
            <div style="margin-bottom: 20px;">
                <p>Dear {subcontractor.first_name or 'Sir/Madam'},</p>

                <p>This is a friendly reminder about the tender invitation for <strong>{project.name}</strong>.</p>

                <p>The {deadline_description} is <strong>{deadline_str}</strong>.</p>

                <p>Please find the tender documents accessible via the SharePoint link below.</p>

                <p>Please let us know if you will be submitting a tender by clicking one of the buttons below.</p>
            </div>
            """

            # Build SharePoint links (reminders don't use form links, so check project fields)
            sharepoint_links = []
            sharepoint_url = None

            if hasattr(project, 'sharepoint_folder_url') and project.sharepoint_folder_url:
                sharepoint_url = project.sharepoint_folder_url
            elif hasattr(project, 'sharepoint_documents_link') and project.sharepoint_documents_link:
                sharepoint_url = project.sharepoint_documents_link
            elif hasattr(project, 'sharepoint_link') and project.sharepoint_link:
                sharepoint_url = project.sharepoint_link

            if sharepoint_url:
                link_title = getattr(project, 'sharepoint_link_description', None) or 'ITT Documents'
                sharepoint_links.append({
                    'url': sharepoint_url,
                    'title': link_title
                })

            # Send the email with invitation ID for tracking
            result = self.send_email(
                to_email=subcontractor.email,
                subject=subject,
                body=body,
                sharepoint_links=sharepoint_links,
                invitation_id=invitation.id
            )

            logger.info(f"📧 Tender reminder send result: {result} for {subcontractor.email}")
            return result

        except Exception as e:
            logger.error(f"💥 Error sending tender reminder: {str(e)}")
            logger.exception("Full traceback:")
            return False

    def send_tender_addendum(self, invitation, addendum):
        """
        Send a tender addendum email to a subcontractor
        Uses the existing send_email method
        """
        try:
            project = invitation.project
            subcontractor = invitation.subcontractor

            logger.info(f"Sending tender addendum to {subcontractor.email} for project {project.name}")

            # Build subject - add error handling for addendum attributes
            try:
                addendum_title = getattr(addendum, 'title', 'Addendum')
                subject = f"ADDENDUM: {addendum_title} - {project.name}"
            except Exception as e:
                logger.error(f"Error accessing addendum title: {str(e)}")
                subject = f"ADDENDUM: Tender Update - {project.name}"

            # Build email body - add error handling for addendum description
            try:
                addendum_description = getattr(addendum, 'description', 'Please see the attached addendum.')
                body = f"""
                <p>Dear {subcontractor.first_name or 'Sir/Madam'},</p>

                <p>Please find attached an addendum to the tender for <strong>{project.name}</strong>.</p>

                <div style="margin: 20px 0; padding: 15px; border-left: 4px solid #0078d4; background-color: #f8f9fa;">
                    {addendum_description}
                </div>

                <p>Please review the updated documents via the SharePoint link below.</p>

                <p>If you have any questions regarding this addendum, please don't hesitate to contact us.</p>
                """
            except Exception as e:
                logger.error(f"Error accessing addendum description: {str(e)}")
                body = f"""
                <p>Dear {subcontractor.first_name or 'Sir/Madam'},</p>

                <p>Please find attached an addendum to the tender for <strong>{project.name}</strong>.</p>

                <p>Please review the updated documents via the SharePoint link below.</p>

                <p>If you have any questions regarding this addendum, please don't hesitate to contact us.</p>
                """

            # Build SharePoint links for updated documents
            sharepoint_links = []

            # Check both possible field names for SharePoint links
            sharepoint_url = None
            if hasattr(project, 'sharepoint_folder_url') and project.sharepoint_folder_url:
                sharepoint_url = project.sharepoint_folder_url
            elif hasattr(project, 'sharepoint_documents_link') and project.sharepoint_documents_link:
                sharepoint_url = project.sharepoint_documents_link

            if sharepoint_url:
                sharepoint_links.append({
                    'url': sharepoint_url,
                    'title': getattr(project, 'sharepoint_link_description', None) or 'Updated ITT Documents'
                })

            # Send the email using existing send_email method
            result = self.send_email(
                to_email=subcontractor.email,
                subject=subject,
                body=body,
                sharepoint_links=sharepoint_links
            )

            logger.info(f"Tender addendum send result: {result} for {subcontractor.email}")
            return result

        except Exception as e:
            logger.error(f"Error sending tender addendum: {str(e)}")
            logger.exception("Full traceback:")
            return False



    def get_folders_for_dropdown(self):
        """Get mail folders for the dropdown selector"""
        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }

            # Get top-level folders
            response = requests.get(
                f'https://graph.microsoft.com/v1.0/users/{self.user_email}/mailFolders',
                headers=headers
            )

            if response.status_code != 200:
                logger.error(f"Failed to get folders: {response.status_code}")
                return []

            folders = response.json().get('value', [])
            processed_folders = []

            for folder in folders:
                folder_id = folder.get('id')
                display_name = folder.get('displayName')

                processed_folders.append({
                    'id': folder_id,
                    'name': display_name,
                    'full_path': display_name
                })

                # Get child folders (one level deep)
                try:
                    child_response = requests.get(
                        f'https://graph.microsoft.com/v1.0/users/{self.user_email}/mailFolders/{folder_id}/childFolders',
                        headers=headers
                    )

                    if child_response.status_code == 200:
                        child_folders = child_response.json().get('value', [])
                        for child in child_folders:
                            child_id = child.get('id')
                            child_name = child.get('displayName')
                            processed_folders.append({
                                'id': child_id,
                                'name': child_name,
                                'full_path': f"{display_name}/{child_name}"
                            })
                except:
                    # Skip child folders if there's an error
                    pass

            return processed_folders

        except Exception as e:
            logger.exception(f"Error getting folders: {str(e)}")
            return []

    def check_project_folder_simple(self, config):
        """
        Simplified email checking - just match domains and mark as returned
        Returns: (emails_processed, tenders_matched)
        """
        from tenders.models import TenderInvitation

        logger.info(f"Checking emails for project: {config.project.name}")

        # Get emails from the last 7 days (or since last check)
        if config.last_check_time:
            start_time = config.last_check_time
        else:
            start_time = timezone.now() - timedelta(days=7)

        start_time_utc = start_time.astimezone(dt_timezone.utc)
        filter_query = f"receivedDateTime ge {start_time_utc.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}"

        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }

            # Get emails from the configured folder
            endpoint = f'https://graph.microsoft.com/v1.0/users/{self.user_email}/mailFolders/{config.folder_id}/messages'
            params = {
                '$filter': filter_query,
                '$orderby': 'receivedDateTime desc',
                '$top': 50,  # Check last 50 emails
                '$select': 'id,subject,from,receivedDateTime,hasAttachments'
            }

            response = requests.get(endpoint, headers=headers, params=params)

            if response.status_code != 200:
                logger.error(f"Failed to get emails: {response.status_code} - {response.text}")
                return 0, 0

            emails = response.json().get('value', [])
            logger.info(f"Found {len(emails)} emails to check")

            # Get all invitations for this project with their domains
            invitations = TenderInvitation.objects.filter(
                project=config.project
            ).select_related('subcontractor')

            # Create a simple domain lookup
            domain_to_invitation = {}
            for invitation in invitations:
                if invitation.subcontractor.email and '@' in invitation.subcontractor.email:
                    domain = invitation.subcontractor.email.split('@')[1].lower()
                    domain_to_invitation[domain] = invitation

            logger.info(f"Checking against {len(domain_to_invitation)} domains")

            emails_processed = 0
            tenders_matched = 0

            # Check each email
            for email in emails:
                emails_processed += 1

                # Get sender email
                sender_info = email.get('from', {})
                if not sender_info or not sender_info.get('emailAddress'):
                    continue

                sender_email = sender_info['emailAddress'].get('address', '').lower()
                if not sender_email or '@' not in sender_email:
                    continue

                # Extract domain
                sender_domain = sender_email.split('@')[1]

                # Check if this domain matches any of our subcontractors
                if sender_domain in domain_to_invitation:
                    invitation = domain_to_invitation[sender_domain]

                    # Skip if already marked as returned
                    if invitation.tender_returned:
                        logger.info(f"Tender already returned for {invitation.subcontractor.company}")
                        continue

                    # Mark as returned
                    invitation.tender_returned = True
                    invitation.tender_returned_at = timezone.now()
                    invitation.tender_attachments = {
                        'sender': sender_email,
                        'subject': email.get('subject', ''),
                        'received_date': email.get('receivedDateTime', ''),
                        'has_attachments': email.get('hasAttachments', False),
                        'matched_by': 'domain_match',
                        'domain': sender_domain,
                        'processed_at': timezone.now().isoformat()
                    }
                    invitation.save()

                    tenders_matched += 1
                    logger.info(f"✅ Marked tender as returned for {invitation.subcontractor.company} (domain: {sender_domain})")

            # Update last check time
            config.last_check_time = timezone.now()
            config.save()

            logger.info(f"Email check complete: {emails_processed} emails processed, {tenders_matched} tenders matched")
            return emails_processed, tenders_matched

        except Exception as e:
            logger.exception(f"Error checking emails: {str(e)}")
            return 0, 0