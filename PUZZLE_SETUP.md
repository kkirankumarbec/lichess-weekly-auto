# Weekly Chess Puzzle - setup

The puzzle page itself is already live and working (chessboard, instant
right/wrong feedback, auto weekly puzzle). The only piece left is wiring up
where solved scores get saved, which needs two small one-time steps in
Google Forms/Sheets (using your existing Google account - nothing new to
sign up for).

## Step 1 - Create the Google Form

1. Go to [forms.google.com](https://forms.google.com) and create a new blank form.
2. Add exactly **two** questions, in this order, both set to **"Short answer"**:
   1. Title it `Name`
   2. Title it `Week`
3. Click the gear icon (Settings) -> **Responses** tab -> make sure
   **"Collect email addresses" is OFF**. (Keeps kids' emails out of the
   leaderboard data.)
4. Click **Send** (top right) -> click the link icon -> copy the form's
   normal URL, but don't send that one to kids. Instead:
   - Click the **three-dot menu (⋮)** in the top right of the form editor
     -> **"Get pre-filled link"**.
   - Type anything in both fields (e.g. `TestName` and `TestWeek`) and
     click **"Get link"** at the bottom.
   - Copy the long URL it gives you - it looks like:
     `https://docs.google.com/forms/d/e/1FAIpQLSc.../viewform?usp=pp_url&entry.123456789=TestName&entry.987654321=TestWeek`
5. **Send me that whole URL.** I'll pull the `entry.xxxxx` IDs out of it
   myself and wire up `docs/config.js`.

## Step 2 - Publish the response Sheet as CSV

1. In the Form editor, click the **Responses** tab -> the green Sheets icon
   -> **"Create a new spreadsheet"** (if you haven't already linked one).
2. Open that Sheet. **File -> Share -> Publish to web**.
3. In the dropdown, pick the specific sheet/tab with the form responses
   (not "Entire document"), and set the format to **CSV**.
4. Click **Publish**, confirm, and copy the link it gives you.
5. **Send me that link too.** I'll drop it into `config.json` as `csv_url`.

Once I have both, I'll wire everything up and the page will go from
"solve the puzzle" to "solve the puzzle -> save your name -> show up on
the leaderboard" end to end.

## Notes

- Anyone with the Sheet's published CSV link can read it (that's what
  "publish to web" means) - it'll only ever contain name + week, never
  email addresses, as long as Step 1.3 stays off.
- You can re-roll this week's puzzle any time from the repo's **Actions**
  tab -> **Weekly Chess Puzzle** -> **Run workflow** (optionally picking a
  harder/easier difficulty or a theme like `mateIn1`, `fork`, `endgame`).
- The leaderboard refreshes automatically every 4 hours, or on demand from
  **Actions** -> **Refresh Puzzle Leaderboard** -> **Run workflow**.
