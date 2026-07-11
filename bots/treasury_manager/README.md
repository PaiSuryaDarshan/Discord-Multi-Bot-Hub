# Treasury Manager

<p align="center">
  <img src="../../assets/banner_treasuryManager.png" alt="Discord Identity Card Bot Banner" width="100%">
</p>

> **Note:** The production implementation of this bot is intentionally NOT included. Much of its functionality interacts with private community workflows, financial requests, and member-specific information that canNOT be publicly shared or meaningfully documented. This currently ONLY SHOWS the dummy workflow.

## Commands and Usage

### `/request_transaction`

Opens a form for submitting a dummy transaction request to the moderator review queue.

**Who can use it:** Members with the `Treasury Member` role or server administrators.

**How to use it:**

1. Enter `/request_transaction` in a server channel and select the command.
2. Complete all five fields in the form:
   - Amount and currency, such as `250 USDC`
   - Market or trading pair, such as `BTC/USDT`
   - Proposed action, such as `Long`, `Short`, `Buy`, or `Sell`
   - Confidence and holding period, such as `8/10, 2–5 days`
   - Trade thesis and risk limit
3. Submit the form.
4. The bot posts the request in `#treasury-requests` and confirms the submission privately.

The server must contain a channel named `treasury-requests`, and the bot must be able to send messages and embeds there.

### Moderator Review Controls

Members with the `Treasury Approver` role and server administrators can use the buttons attached to requests in `#treasury-requests`.

| Control | Result |
|---------|--------|
| `✅ Approve` | Marks the request as approved and generates a dummy authorisation reference. |
| `⏳ Await` | Places the request on hold while awaiting further information. No authorisation reference is generated. |
| `❌ Reject` | Marks the request as rejected. No authorisation reference is generated. |

Each request can be processed only once. After a moderator selects a decision, all review buttons are disabled.

> **Important:** This is a demonstration workflow. Approval does not transfer funds or execute a real transaction.

## Project Structure

```text
bot.py       Registers slash commands and coordinates the overall approval workflow.

modals.py    Defines the interactive transaction request forms presented to users.

views.py     Implements the approval interface, including Approve, Await, and Reject buttons.

embeds.py    Builds and updates the Discord embeds displayed throughout the request lifecycle.

utils.py     Shared helper functions, including generation of unique transaction authorization keys.

README.md    Documentation for this bot.
```
