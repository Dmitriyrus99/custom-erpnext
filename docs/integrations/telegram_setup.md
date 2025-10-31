# Telegram Integration Setup

Ferum Custom can send operational alerts and expose lightweight workflows over Telegram. This guide covers creating the bot, locking it down, and validating the new healthcheck tooling.

## 1. Create the Telegram bot

1. Start a chat with [@BotFather](https://t.me/BotFather).
2. Run `/newbot` and follow the prompts to choose a name and username.
3. BotFather returns an HTTPS API token (`123456:ABC-DEF...`). Keep it secret.
4. Optional: configure the bot’s profile photo and description for your team.

## 2. Decide chat topology

- **Broadcasts**: choose a private group chat for system notifications (obtain its numeric `chat_id` using @RawDataBot or by calling the Ferum API once configured).
- **1:1 commands**: staff can interact from direct messages; set up `telegram_allowed_chat_ids` and `telegram_admin_usernames` to restrict access.

## 3. Configure Ferum Custom Settings

Open Desk → **Ferum Custom Settings** and configure the Telegram section:

| Field | Description |
| --- | --- |
| Enable Telegram Notifications | Master switch guarding webhook + outbound messages. |
| Telegram Bot Token | Token issued by BotFather. Stored as Password. |
| Default Chat ID | chat_id used for broadcast alerts (e.g., SLA breach). |
| Allowed Chat IDs | One chat_id per line. When set, any update from outside this list is ignored. |
| Admin Telegram Usernames | Comma/newline separated Telegram usernames permitted to run admin commands (`/analytics`, `/close`, `/ping`). |
| Telegram Webhook Secret | Shared secret appended to the webhook URL (`...?secret=...`). |

Save the record. Use the new **Check Telegram** button to run an API connectivity test (`getMe`)—success will display the bot username.

### Environment overrides

All fields can be controlled via environment variables. The app now auto-loads keys from `config/.env.integrations` (and `config/.env.local.integrations` for local overrides). Examples:

```bash
export FERUM_ENABLE_TELEGRAM_NOTIFICATIONS=1
export FERUM_TELEGRAM_BOT_TOKEN=123456:ABC...
export FERUM_TELEGRAM_ALLOWED_CHAT_IDS="-1001234567890,987654321"
export FERUM_TELEGRAM_ADMIN_USERNAMES="ops_lead,cto"
export FERUM_TELEGRAM_WEBHOOK_SECRET=super-secret
```

Or put the same lines into `config/.env.integrations` and restart Bench.

## 4. Wire the webhook

1. Deploy Ferum Custom (`bench start` + workers) and expose the site over HTTPS.
2. Construct the webhook URL (no secrets in the URL):

```
https://<site>/api/method/ferum_custom.api.telegram_bot.handle_update
```

3. Register it with Telegram (recommended: secret header):

```bash
curl "https://api.telegram.org/bot$FERUM_TELEGRAM_BOT_TOKEN/setWebhook" \
  -d "url=https://erp.example.com/api/method/ferum_custom.api.telegram_bot.handle_update" \
  -d "secret_token=$FERUM_TELEGRAM_WEBHOOK_SECRET"
```

   Fallback (supported): pass `?secret=...` in the URL if you cannot set `secret_token`:

```bash
curl "https://api.telegram.org/bot$FERUM_TELEGRAM_BOT_TOKEN/setWebhook" \
  -d "url=https://erp.example.com/api/method/ferum_custom.api.telegram_bot.handle_update?secret=$FERUM_TELEGRAM_WEBHOOK_SECRET"
```

4. Confirm with `getWebhookInfo`:

```bash
curl "https://api.telegram.org/bot$FERUM_TELEGRAM_BOT_TOKEN/getWebhookInfo"
```

## 5. Validate end-to-end

1. From an **allowed chat**, send `/ping`. The bot replies with the healthcheck summary and works only for configured admin usernames.
2. Create a test Service Request; you should receive a broadcast in the default chat.
3. Trigger an SLA breach (or manually call `/analytics`) to ensure admin-only commands are enforced.
4. Attempt to message from a non-allowed chat: the webhook ignores the update and logs "chat not in allowlist".

## 6. Security checklist

- Keep the Bot token and webhook secret outside source control (environment variables or password manager).
- Restrict chats via `telegram_allowed_chat_ids`. When empty, Ferum accepts any chat.
- Maintain the admin username list; admin commands bypass some UI checks.
- Enable HTTPS and verify that only Telegram IPs can reach the webhook (optional, but recommended).
- Rotate tokens on staff changes—use BotFather `/revoke` and update settings.
- Monitor the `/ping` command from the operations runbook to confirm connectivity after deploys.

## 7. Troubleshooting

| Issue | Resolution |
| --- | --- |
| `/ping` → “Telegram not ready: error” | Check the healthcheck message; missing token or network issue. Retry with curl. |
| No notifications sent | Ensure feature flag enabled, bot token valid, and worker queue `short` is running. Check `frappe.log_error` for exceptions. |
| “chat not in allowlist” in logs | Add the chat ID to **Allowed Chat IDs** or remove the allowlist to permit all. |
| Admin denial | Verify the Telegram username (`@username`) matches the entry in **Admin Telegram Usernames** (case-insensitive). |

The integration is now hardened: command access is scoped, outbound messages respect allowlists, and the `/ping`/healthcheck provide quick diagnostics.
