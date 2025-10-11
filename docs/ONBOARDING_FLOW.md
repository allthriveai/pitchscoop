# PitchScoop Onboarding Flow

## Initial User Decision Point

**Question:** "What would you like to do?"

### Path A: Create an Event
**Help Text:** You can be an event organizer or set up a one-off practice. Events can be practice, a hackathon, investor pitch, or job interview.

#### Event Creation Flow:
1. **Event Details**
   - Name of event
   - Date of event
   - Event Type (dropdown, Hackathon, VC Pitch, Interview, Practice, Other)
   - Add a link to event to scrape for event details (optional)
   - Rules for judging

2. **Judging Criteria Setup** (Event Organizer Controls)
   
   **Idea Category** (Weight: adjustable by organizer)
   - Wow Factor: Innovative, Unique
   - Feasible: Can be built and marketed
   - Competitive: Doesn't have a lot of competition
   
   **Technical Implementation** (Weight: adjustable by organizer)
   - Did you build the code today?
   - Does the code work?
   - Does the code make sense?
   - Is the code innovative and inspiring?
   
   **Tool Use** (Weight: adjustable by organizer)
   - Did you use the hackathon sponsor tools?
   - Did you use the hackathon sponsor tools in an innovative and comprehensive manner?
   
   **Presentation** (Weight: adjustable by organizer)
   - Dynamic and passionate: Engaged the audience
   - Clear and comprehensible: Didn't speak too fast or too slow
   - Flow has beginning, middle and end, highlighting problem solved in a clear manner and explaining how solution works clearly

   **Other** (Weight: adjustable by organizer)
   - Custom category name: [Event organizer types in custom category]
   - Custom criteria description: [Event organizer defines what this measures]

### Path B: Join an Event
**Help Text:** Join an event as practice or submit to the event to be part of the leaderboard.

#### Participant Onboarding Flow:
1. **Create Profile**
   - User name
   - Team name
   - Project name
   - Project description
   - GitHub repo (optional)

2. **Event Participation Options**
   - Join an existing event
   - Upload video or take a video
   - See past events
   - Record and practice

## User Actions Available After Onboarding

### For Event Organizers:
- Manage event settings
- Adjust judging criteria weights
- Add/edit custom judging categories
- View participant submissions
- Access event analytics

### For Participants:
- Submit to active events
- Practice with recordings
- View leaderboards
- Access past event history
- Record and review pitches

## Content Structure for Implementation

### Welcome Messages
- **New Event Organizer:** "Ready to create your amazing event?"
- **New Participant:** "Find the perfect event to showcase your skills!"
- **Returning User:** "Welcome back! Continue where you left off."

### Help Text Library
- Event type explanations
- Judging criteria definitions
- Custom category creation guidelines
- Video submission guidelines
- Profile setup assistance
- Project description best practices

### Progressive Disclosure
- Start with simple path selection
- Reveal complexity based on user choice
- Provide contextual help at each step
- Allow users to save progress and return later