2FA Administration – Recovery and Policy
=======================================

Scope: How to reset a user’s 2FA, enable email fallback, generate backup codes, and enforce 2FA for roles.

Reset a user’s 2FA (lost authenticator)
- From Desk (System Manager):
  - In the JS console or via API: frappe.call('ferum_custom.ferum_custom.security.twofa.reset_user_2fa', {user: 'user@example.com'})
  - Or bench console:
    - from ferum_custom.ferum_custom.security import twofa
    - twofa.reset_user_2fa('user@example.com')
- Effect: Clears the user’s TOTP secret and setup flag. On next login with method = “OTP App”, user receives an email with QR instructions to re‑enroll (built‑in Frappe flow).

Email OTP fallback
- System Settings → Email → Two-Factor Authentication:
  - Enable Two Factor Authentication = ON
  - Two Factor Authentication method = “OTP App” (preferred) or “Email” (temporary fallback if needed)
- With method “OTP App”: when the user is not set up (fresh or after reset), Frappe sends an email with QR and one‑time code to finish setup. This acts as the fallback channel.

Backup recovery codes (admin issued)
- Generate codes (System Manager only):
  - frappe.call('ferum_custom.ferum_custom.security.twofa.generate_backup_codes', {user: 'user@example.com', count: 10})
  - Returns plaintext codes. Store securely and deliver to the user out‑of‑band.
- Use a backup code (admin‑assisted recovery):
  - User provides a backup code to the admin.
  - Admin runs: frappe.call('ferum_custom.ferum_custom.security.twofa.consume_backup_code', {user: 'user@example.com', code: 'AAAA-BBBB'})
  - If valid and unused, the code is consumed and the user’s 2FA is reset; user logs in and re‑enrolls via email flow.
- View status (hashed tails only):
  - frappe.call('ferum_custom.ferum_custom.security.twofa.list_backup_codes', {user: 'user@example.com'})

Enforce 2FA for specific roles
- System Settings:
  - Enable Two Factor Authentication = ON; Method = “OTP App”
- Mark roles as 2FA‑enforced:
  - bench console:
    - from frappe.twofactor import toggle_two_factor_auth
    - toggle_two_factor_auth(True, roles=["System Manager", "Project Manager", "Office Manager"])
  - Or API:
    - frappe.call('ferum_custom.ferum_custom.security.twofa.configure_two_factor', {
        method: 'OTP App',
        enforce_roles: ["System Manager", "Project Manager", "Office Manager"]
      })

Command‑line snippets (bench console)
- Reset one user:
  - from ferum_custom.ferum_custom.security import twofa
  - twofa.reset_user_2fa('user@example.com')
- Bulk reset for a role (dangerous – confirm users first):
  - users = frappe.get_all('Has Role', filters={'role': 'Service Engineer'}, pluck='parent')
  - for u in set(users): twofa.reset_user_2fa(u)

Operational best practices
- Keep 2FA enabled for all System Users; consider leaving Website Users excluded.
- Encourage users to add a secondary email for account recovery.
- Rotate backup codes after each use; store only hashes (done automatically by the helper).

