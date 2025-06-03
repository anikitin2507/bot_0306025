# Telegram Location Facts Bot — Product Requirements Document (PRD)

## 1. Overview / Problem
Travelers, commuters, and the merely curious often pass by places with hidden stories. Opening a maps app and searching manually is slow.  
**Goal:** Build a Telegram bot that instantly replies with an unusual fact about something near a user-shared location, using GPT-4o-mini. The first release (v 1.0) handles one-off location pins; v 1.1 adds live-location support that pushes a new fact every 10 minutes.

---

## 2. Key User Flows
| Step | v 1.0 (Pin) | v 1.1 (Live location) |
|------|-------------|-----------------------|
| 1 | User opens chat and taps 📎 → Location → “Send my current location”. | User taps 📎 → Location → “Share Live Location” (e.g., 30 min). |
| 2 | Telegram sends an **Update** containing `message.location` (`latitude`, `longitude`). | Telegram sends the same initial Update plus `live_period`; every ~5 s it sends `edited_message.location` updates. |
| 3 | Bot POSTs {lat,lon} to GPT-4o-mini with a crafted prompt. | Bot stores chat + message_id, sets a 10-minute timer. |
| 4 | GPT response → bot replies with a short fun fact. | On every timer tick, bot uses the latest coordinates to fetch a new fact and replies. |
| 5 | — | Live updates stop automatically when `edited_message.location` ends or user stops sharing. |

---

## 3. Functional Requirements
1. **Telegram Intake**  
   - Parse `Update.message.location` object:  
     ```json
     { "latitude": float, "longitude": float, "horizontal_accuracy": float? }
     ```  
   - For live locations, handle `edited_message.location` until `message.live_period` expires.
2. **OpenAI Integration**  
   - Use GPT-4o-mini completion endpoint.  
   - Prompt template includes reverse-geocoded place name + request for a “little-known fact within 1 km”.
3. **Response Formatting**  
   - ≤ 3 sentences, max 280 chars, emoji-friendly.  
   - Graceful fallback if no fact found.
4. **Scheduling (v 1.1)**  
   - In-memory job that triggers every 10 min per live location session.  
   - Cancels on `stop_live_location` or bot restart.
5. **Dev & Ops**  
   - **Cursor** for coding.  
   - GitHub repo with Railway deploy (Dockerfile + `railway.json`).  
   - Config via env vars: `OPENAI_API_KEY`, `TELEGRAM_TOKEN`.  
   - Minimal logging; Sentry optional.
6. **Security / Abuse**  
   - Rate-limit per chat (e.g., 5 req/min).  
   - Ignore non-location messages except `/start`.

---

## 4. Non-Goals
- Multi-language support (answer will be in the chat language only).  
- Detailed POI databases or offline cache.  
- Web UI, payments, user accounts, analytics dashboard.  
- Facts guaranteed to be 100 % accurate scholarly references.

---

## 5. Milestones & Release Plan
| Date | Milestone | Scope |
|------|-----------|-------|
| **Day 0 (Tonight)** | M0 – Repo & boilerplate | Set up bot webhook, health check. |
| **+2 h** | M1 – v 1.0 Feature complete | Location → GPT → reply; error handling; deploy to Railway. |
| **+0.5 h** | QA smoke test | Test pins in iOS & Android; doc README. |
| **Release v 1.0** | Promote to friends. |
| **+1.5 h** | M2 – Live-location engine | Timer service, update handling, stop conditions. |
| **+0.5 h** | QA live location | Walk outside, validate 10-min cadence. |
| **Release v 1.1** | Public announcement, collect feedback. |