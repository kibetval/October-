
# Digit Pulse — Deriv Even/Odd Analysis Bot

GitHub Pages dashboard plus GitHub Actions scheduled Telegram signals. This is a signal-only tool and does not place trades.

## Files

- `index.html`: live dashboard, market selector, tick history, EVEN/ODD/WAIT signals and performance table.
- `signal_bot.py`: scheduled historical-data scanner and Telegram alerts.
- `requirements.txt`: Python dependency.
- `.github/workflows/telegram-signals.yml`: scheduled and manual scans.

## Important behaviour

- The dashboard must stay open in your browser for live streaming.
- The dashboard Stop button stops the dashboard stream only. It does not stop scheduled Telegram scans.
- Dashboard win/loss counts reset when the page reloads.
- GitHub Actions runs on a schedule, not continuously. Scheduled runs can be delayed.
- The analysis score is a heuristic, not a calibrated probability or proof of a profitable strategy.
- WAIT is normal when the signal filter is not met.

## 1. Set the Deriv App ID

In `index.html`, replace `YOUR_APP_ID` with your real Deriv App ID.

In GitHub, add a repository Actions secret named `DERIV_APP_ID` with the same value.

Do not put a Telegram bot token in `index.html`.

## 2. Telegram setup

1. Open `@BotFather` in Telegram.
2. Send `/newbot` and follow the instructions.
3. Save the bot token privately.
4. Open your new bot and send `/start`.
5. Get your Telegram chat ID using Telegram's `getUpdates` API after sending the bot a message.
6. Add these repository secrets in **Settings → Secrets and variables → Actions**:
   - `DERIV_APP_ID`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

Never share or publish your Telegram bot token.

## 3. Upload the project from Android

Upload these root files:
- `index.html`
- `signal_bot.py`
- `requirements.txt`
- `README.md`

Then create this file path through GitHub's **Add file → Create new file** option:

`.github/workflows/telegram-signals.yml`

Paste the workflow code into it and commit the file.

## 4. Enable GitHub Pages

1. Open repository **Settings → Pages**.
2. Choose **Deploy from a branch**.
3. Select branch `main` and folder `/(root)`.
4. Save and wait for the Pages deployment.
5. Open the published page and tap **Start analysis**.

## 5. Test Telegram alerts

1. Open the repository's **Actions** tab.
2. Select **Deriv Even Odd Telegram Signals**.
3. Tap **Run workflow**.
4. Open the run and inspect its logs.

A run can finish successfully without sending a Telegram message if no market passes the signal filter.

## Troubleshooting

- **Add your App ID first:** replace `YOUR_APP_ID` in `index.html`.
- **Missing secret:** check the exact spelling of each secret name.
- **No Telegram message:** inspect the Actions logs and confirm you sent `/start` to your bot.
- **No signal:** WAIT is expected when the filter is not met.
- **No markets:** inspect the `active_symbols` response; market labels can change.
