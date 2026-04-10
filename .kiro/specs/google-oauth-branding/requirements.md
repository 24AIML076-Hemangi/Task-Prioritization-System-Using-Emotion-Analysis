# Requirements Document

## Introduction

This feature covers improving the Google OAuth consent screen branding, fixing Google verification issues, and upgrading the UI for the task prioritization app hosted at https://task-prioritization-system-using-emotion.onrender.com. The goal is to make the app look and feel like a real product — not a college project — so that Google's OAuth verification passes and users trust the consent screen and landing page.

## Glossary

- **App**: The task prioritization web application hosted on Render.
- **Consent_Screen**: The Google OAuth consent screen shown to users before they authorize the app.
- **Privacy_Policy**: The page at `/privacy.html` describing how user data is handled.
- **Terms_Page**: The page at `/terms.html` describing the rules of using the service.
- **Homepage**: The page at `/index.html` — the public-facing landing page.
- **Authorized_Domain**: A domain registered in Google Cloud Console that Google uses to verify app ownership.
- **Branding_Block**: The Google OAuth error state where branding is not shown to users due to missing or unverified configuration.
- **OAuth_Verification**: The Google process of reviewing an app's consent screen, policy pages, and domain before granting full access.

---

## Requirements

### Requirement 1: App Name and Description for OAuth Consent Screen

**User Story:** As a developer, I want a shorter and professional app name and description for the OAuth consent screen, so that users trust the app and Google does not flag it as unverified or academic.

#### Acceptance Criteria

1. THE App SHALL use an app name on the consent screen that is 30 characters or fewer and does not contain academic or student-project language.
2. THE App SHALL display a one-to-two sentence app description on the consent screen that clearly states the app's purpose in plain, product-oriented language.
3. THE App SHALL NOT use the phrase "Using Emotion Analysis" or "AIML Student Project" in any user-facing OAuth consent screen text.
4. WHEN a user views the consent screen, THE Consent_Screen SHALL show the app name, a short description, and a link to the Privacy Policy.

---

### Requirement 2: Privacy Policy Page

**User Story:** As a user, I want to read a clear and trustworthy privacy policy, so that I understand how my data is used before authorizing the app.

#### Acceptance Criteria

1. THE Privacy_Policy SHALL be accessible at the path `/privacy.html` without requiring login.
2. THE Privacy_Policy SHALL include a section explaining that the user's Google email is collected only for account authentication and sending task reminders.
3. THE Privacy_Policy SHALL include a statement that user data is not sold, shared with third parties for advertising, or used for any purpose other than operating the service.
4. THE Privacy_Policy SHALL include a section describing how task reminder emails are sent using the user's authorized Gmail account via the Gmail API.
5. THE Privacy_Policy SHALL NOT contain references to "AIML Student Project", "college project", or any academic framing.
6. THE Privacy_Policy SHALL include a "Last updated" date and a contact email address.
7. WHEN a user visits `/privacy.html`, THE Privacy_Policy SHALL render without requiring JavaScript or authentication.

---

### Requirement 3: Terms of Service Page

**User Story:** As a user, I want to read clear terms of service, so that I know what I am agreeing to when I use the app.

#### Acceptance Criteria

1. THE Terms_Page SHALL be accessible at the path `/terms.html` without requiring login.
2. THE Terms_Page SHALL include a section describing the permitted use of the service (personal task management and productivity).
3. THE Terms_Page SHALL include a statement that the emotion analysis feature is optional, non-medical, and non-diagnostic.
4. THE Terms_Page SHALL include a disclaimer that the service is provided "as is" without warranty.
5. THE Terms_Page SHALL NOT contain references to "AIML Student Project", "college project", or any academic framing.
6. THE Terms_Page SHALL include a "Last updated" date and a contact email address.
7. WHEN a user visits `/terms.html`, THE Terms_Page SHALL render without requiring JavaScript or authentication.

---

### Requirement 4: Google OAuth Verification Fix

**User Story:** As a developer, I want to resolve the "branding not shown to users" error on the Google OAuth consent screen, so that users see the app name and logo during sign-in.

#### Acceptance Criteria

1. THE App SHALL have the domain `task-prioritization-system-using-emotion.onrender.com` registered as an authorized domain in the Google Cloud Console OAuth consent screen settings.
2. THE App SHALL have the Privacy Policy URL set to `https://task-prioritization-system-using-emotion.onrender.com/privacy.html` in the Google Cloud Console OAuth consent screen settings.
3. THE App SHALL have the Terms of Service URL set to `https://task-prioritization-system-using-emotion.onrender.com/terms.html` in the Google Cloud Console OAuth consent screen settings.
4. WHEN the authorized domain is verified and policy URLs are set, THE Consent_Screen SHALL display the app name and logo to users without the "branding not shown" warning.
5. THE App SHALL serve the Google site verification HTML file (already present at `Frontend/googlebcac5a3065294396.html`) at its correct public URL so that Google can verify domain ownership.
6. IF the OAuth app is in "Testing" mode with fewer than 100 users, THEN THE App SHALL remain functional for test users while the developer submits for production verification.

---

### Requirement 5: Homepage UI

**User Story:** As a visitor, I want to see a clean and professional homepage, so that I trust the app before logging in.

#### Acceptance Criteria

1. THE Homepage SHALL display the app name, a short tagline (one sentence), and a "Login with Google" button as the primary call to action.
2. THE Homepage SHALL display the app logo already present at `/logo.png`.
3. WHEN a user clicks the "Login with Google" button, THE Homepage SHALL navigate the user to `/login.html`.
4. THE Homepage SHALL include visible links to `/privacy.html` and `/terms.html` in the footer or below the main call to action.
5. THE Homepage SHALL use a clean, minimal design with no more than two primary colors and readable typography.
6. THE Homepage SHALL be fully responsive and render correctly on both desktop and mobile viewports.
7. WHEN the page loads, THE Homepage SHALL not require JavaScript to display the core content (app name, tagline, login button, policy links).
