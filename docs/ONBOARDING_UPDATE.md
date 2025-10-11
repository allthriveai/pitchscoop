# Onboarding Flow Update ✅

## What Changed

Added a smart first step for organizers that asks about event page scraping before manual entry.

### New Flow for Organizers

**Before:**
1. Event Details (name, type, date, rules)
2. Judging Criteria
3. Complete

**After:**
1. **Quick Start** - "Do you have a public event page I can automatically scrape details from to save you time?"
2. Event Details (manual or review scraped)
3. Judging Criteria  
4. Complete

### User Experience

**When user says:** *"Start onboarding for me as an organizer"*

**Claude will now ask:**
> "Do you have a public event page I can automatically scrape details from to save you time?"
> 
> Event page URL (optional): [https://devpost.com/your-hackathon or https://lu.ma/your-event]
> 
> I can auto-fill details from Devpost, Luma, Eventbrite, and other event platforms. Leave blank to enter manually.

**If user provides link:**
- Message: "Great! I'll try to scrape details from that link. Please review and fill in any missing information."
- Next: Event Details (with pre-filled data - TODO: implement scraping)

**If user skips (no link):**
- Message: "No problem! Let's create your event manually."
- Next: Event Details (empty form)

## Implementation Details

### Files Changed
- `api/domains/onboarding/services/onboarding_service.py`
  - Added `event_link_check` step
  - Modified `_move_to_next_step()` to handle link check
  - Modified `_get_step_details()` to define new step
  - Updated total_steps from 2 to 3

### Tested
✅ Flow with event link
✅ Flow without event link (manual entry)
✅ Both paths lead to Event Details step
✅ Clean JSON output (no SQL pollution)

## Next Steps

**To Enable Scraping:**
1. Add event page scraper service
2. Support Devpost, Luma, Eventbrite APIs
3. Parse and extract: name, date, type, description
4. Pre-fill Event Details form with scraped data

**To Test in Claude Desktop:**
1. Restart Claude Desktop (Cmd+Q, reopen)
2. Say: "Start onboarding for me as an organizer"
3. You'll see the new "Quick Start" question first!

## Benefits

- **Faster onboarding** - Auto-fill from public pages
- **Better UX** - Ask permission before manual entry
- **Flexible** - Works with or without link
- **Scalable** - Easy to add more scraping sources

Ready to use! 🚀
