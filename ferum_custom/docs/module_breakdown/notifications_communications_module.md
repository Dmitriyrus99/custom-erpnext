# Notifications & Communications Module (Cross-cutting)

- (This is not explicitly listed as a separate module, but logically it groups the bot integration, email notifications, and monitoring alerts.)

### Responsibilities

- Provide unified handling of notifications through various channels (Telegram, WhatsApp, Email) and handle user interactions via bots.

### Components

- Telegram Bot (via Aiogram), potentially WhatsApp integration (possibly through a third-party API like Twilio), Email (via ERPNext email or SMTP), and system notifications.

Key Functions:

- The Telegram Bot service runs as part of the custom backend (Aiogram listening for commands).
- It authenticates users, processes commands as described in earlier modules.

### WhatsApp integration might mirror Telegram functionality

- possibly using an official API or a bot that relays messages.
- If implemented, commands might be simple or only notifications (the spec highlights Telegram more).

- Email notifications use either ERPNext’s built-in notification engine (configured via Notification doctype or via hooks) for things like “on new request, email X”.
- Some custom ones like the subcontractor invoice alert might be done via custom code for more flexibility (including Telegram message).

### Ensure that each notification type is used appropriately

- urgent notifications via Telegram (instant), formal ones via email (for record/tracking).

The module also might include templates for messages (like predefined email templates or bot responses).

Integration with Roles:

Administrator receives certain notifications (e.g., new invoice).

Project Manager receives notifications about requests and report submissions in their projects.

Engineer receives assignment and status change notices.

Client receives updates on request status and possibly invoice dispatch.

These rules are implemented through a combination of Notification settings and code logic.

Logging:

- There is likely logging for notifications as well (to ensure, e.g., that a Telegram message was successfully sent or if failed, the system can retry or fall back to SMS/email).

Sentry might catch any errors in the bot (like if Telegram API fails).

- No direct DocType (other than maybe a doctype to store mapping of Telegram user IDs to ERPNext users, which could be a simple custom doctype or even using the Notification Settings doctype in ERPNext to store chat IDs).

### UI

- Not much UI, except maybe a settings page to configure which notifications go to which channel, or to input the Telegram chat IDs.

- In summary, while not a standalone ERP module, this piece ties all modules together by keeping users informed and allowing certain actions via convenient channels, improving responsiveness and reducing the need for users to always log in to the ERP interface.
