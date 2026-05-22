# Shared Notes Display - Visual Architecture

## High-Level Data Flow

```
User logs in with JWT token
                ↓
        [Frontend Dashboard]
                ↓
    GET /api/notes/  (Django REST)
                ↓
    ┌─────────────────────────────────────────────────────────┐
    │  Backend Returns ALL Accessible Notes:                  │
    │  - User's own private notes                            │
    │  - Notes where user is collaborator                    │
    │  - Notes with pending invitations                      │
    └─────────────────────────────────────────────────────────┘
                ↓
    ┌─────────────────────────────────────────────────────────┐
    │  Each Note Enriched with Metadata:                      │
    │  {                                                      │
    │    "id": 1,                                            │
    │    "title": "Project Plan",                            │
    │    "share_state": "shared",                            │
    │    "viewer_access": "view",                            │
    │    "collaborators": [...],                             │
    │    "is_archived": false,                               │
    │    "is_deleted": false,                                │
    │    "is_pinned": false                                  │
    │  }                                                      │
    └─────────────────────────────────────────────────────────┘
                ↓
    ┌─────────────────────────────────────────────────────────┐
    │  Frontend NotesList Component:                          │
    │  Categorizes based on currentView                       │
    └─────────────────────────────────────────────────────────┘
                ↓
    ┌──────────────────┬──────────────┬──────────────┬─────────┐
    ↓                  ↓              ↓              ↓         ↓
  [Notes]         [Archive]      [Shared]       [Trash]    [Labels]
  ├─ Pinned       ├─ Archived    ├─ My Shared   ├─ Deleted
  └─ Others       │  non-delete   ├─ Collabor.
                  │              │  Notes
                  │              └─ By others
```

## Note State Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  NOTE CREATION (Owner creates note)                         │
│  ├─ viewer_access: "owner"                                 │
│  ├─ share_state: "private"                                 │
│  └─ collaborators: []                                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ POST /api/notes/{note_id}/collaborators/
                       │ (Owner adds collaborator)
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  INVITATION CREATED                                         │
│  ├─ NoteCollaboratorInvite created (STATUS_PENDING)        │
│  ├─ note.share_state: "private" (still, no active collab.) │
│  ├─ Invited user's viewer_access: "pending"                │
│  └─ Email sent to invited user                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
            ┌──────────┴──────────┐
            │                     │
            ↓                     ↓
    ┌───────────────┐     ┌───────────────┐
    │   ACCEPT      │     │   DECLINE     │
    │  Invitation   │     │  Invitation   │
    └───────┬───────┘     └───────┬───────┘
            │                     │
            ↓                     ↓
┌──────────────────────┐  ┌──────────────────────┐
│ NoteCollaborator     │  │ Invite Status:       │
│ created (STATUS_     │  │ DECLINED             │
│ ACTIVE)              │  │ responded_at set     │
│                      │  │ No access granted    │
│ share_state:         │  └──────────────────────┘
│ "shared" (now has    │
│ active collab.)      │
│                      │
│ Invited user can     │
│ now view/edit note   │
└──────────────────────┘

```

## Frontend View Categorization

```
┌──────────────────────────────────────────────────────────────────────┐
│ currentView === 'notes'  (My Notes)                                  │
│ Filter: viewer_access === 'owner' AND                               │
│         share_state === 'private' AND                               │
│         is_archived === false AND                                   │
│         is_deleted === false                                        │
│                                                                       │
│ Shows: Only user's own private notes (no collaborators)             │
│        Further divided into:                                         │
│        - Pinned (is_pinned === true)                                │
│        - Others (is_pinned === false)                               │
└──────────────────────────────────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────────┐
│ currentView === 'shared'  (Shared Notes)                             │
│ Filter: share_state !== 'private' AND                               │
│         is_archived === false AND                                   │
│         is_deleted === false                                        │
│                                                                       │
│ Shows: All notes where user is NOT owner but HAS access             │
│        - Notes owned by others but user is collaborator             │
│        - Notes where user is pending invite (share_state:pending)   │
│        - Anything with collaborators                                │
└──────────────────────────────────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────────┐
│ currentView === 'archive'  (Archived)                                │
│ Filter: is_archived === true AND                                    │
│         is_deleted === false                                        │
│                                                                       │
│ Shows: All archived notes (both own and shared)                      │
└──────────────────────────────────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────────┐
│ currentView === 'trash'  (Trash)                                     │
│ Filter: is_deleted === true                                         │
│                                                                       │
│ Shows: All soft-deleted notes                                        │
└──────────────────────────────────────────────────────────────────────┘
```

## Shared Notes Example Scenario

```
┌──────────────────────────────────────────────────────────────┐
│ SCENARIO: User A shares "Budget Q4" with Users B & C         │
└──────────────────────────────────────────────────────────────┘

STEP 1: User A creates note "Budget Q4"
┌─────────────────────────────────────────────────────────────┐
│ Note (id=1)                                                 │
│ ├─ title: "Budget Q4"                                       │
│ ├─ user: User A (owner)                                     │
│ ├─ share_state: "private"                                   │
│ └─ collaborators: []                                         │
│                                                              │
│ User A's Dashboard → "Notes" tab:                           │
│ ├─ Pinned: [empty]                                          │
│ └─ Others: [Budget Q4] ← Appears here                       │
└─────────────────────────────────────────────────────────────┘

STEP 2: User A adds collaborators
POST /api/notes/1/collaborators/
├─ Invite User B with access_level="view"
└─ Invite User C with access_level="edit"

┌─────────────────────────────────────────────────────────────┐
│ NoteCollaboratorInvite (id=1)                              │
│ ├─ note: 1 (Budget Q4)                                      │
│ ├─ invited_user: User B                                     │
│ ├─ status: PENDING                                          │
│ ├─ access_level: "view"                                     │
│ └─ token: (auto-generated)                                  │
│                                                              │
│ Emails sent:                                                │
│ - "You have been invited to view 'Budget Q4'"              │
│ - No accept/decline links (user logs in to accept)         │
└─────────────────────────────────────────────────────────────┘

Note state (backend):
├─ Note.share_state: STILL "private" (no active collab. yet)
└─ User B's viewer_access: "pending" (not yet accepted)

User B's Dashboard (pending invitations):
└─ Bell icon shows "1" new invitation
   └─ Click to open modal → Lists pending notes

STEP 3: User B accepts invitation
POST /api/invitations/
{
  "invite_id": 1,
  "action": "accept"
}

┌─────────────────────────────────────────────────────────────┐
│ ACTION RESULT:                                               │
│                                                              │
│ 1. NoteCollaborator created:                               │
│    ├─ note: 1 (Budget Q4)                                   │
│    ├─ user: User B                                          │
│    └─ access_level: "view"                                  │
│                                                              │
│ 2. NoteCollaboratorInvite updated:                          │
│    ├─ status: ACCEPTED                                      │
│    ├─ responded_at: (current timestamp)                     │
│    └─ User B can now view the note                          │
│                                                              │
│ 3. Cache cleared for this note                              │
└─────────────────────────────────────────────────────────────┘

STEP 4: Now note is shared (has active collaborators)
GET /api/notes/ (called by both User A and B)

┌─────────────────────────────────────────────────────────────┐
│ Note (id=1) - WITH FULL CONTEXT                            │
│ ├─ title: "Budget Q4"                                       │
│ ├─ owner: {id: A, name: "User A", email: "a@example.com"} │
│ ├─ share_state: "shared" ← NOW CHANGED                     │
│ ├─ viewer_access: [Depends on user]                        │
│ │  ├─ User A: "owner"                                      │
│ │  └─ User B: "view"                                       │
│ ├─ collaborators: [                                         │
│ │  └─ User A (owner)                                       │
│ │                                                            │
│ │  Note: User B not in list yet if viewing from A's account│
│ │  because B is active collaborator, shown separately      │
│ │]                                                           │
│ ├─ is_archived: false                                       │
│ ├─ is_deleted: false                                        │
│ └─ created_at: (timestamp)                                  │
└─────────────────────────────────────────────────────────────┘

STEP 5: Frontend filtering for "Shared" view

User A's Dashboard → "Shared" tab:
├─ currentView === 'shared'
├─ Filter: share_state !== 'private'
├─ Result: ✓ "Budget Q4" appears
│          (because share_state="shared")
└─ Shows: Budget Q4
   └─ Collaborators: [User B, User C pending]

User B's Dashboard → "Shared" tab:
├─ currentView === 'shared'
├─ Filter: share_state !== 'private'
├─ Result: ✓ "Budget Q4" appears
│          (because share_state="shared")
└─ Shows: Budget Q4
   └─ Owner: User A

User C's Dashboard → "Shared" tab:
├─ currentView === 'shared'
├─ Filter: share_state !== 'private'
├─ Status: "Pending" in invitations
│          (not yet accepted, not in Shared tab)
└─ Only appears in Shared tab AFTER accepting invite
```

## Database State Summary

```
NOTES TABLE:
┌─────┬──────────────┬──────────┬───────┬────────┐
│ id  │ title        │ user_id  │ color │ ...    │
├─────┼──────────────┼──────────┼───────┼────────┤
│ 1   │ Budget Q4    │ A        │ blue  │ ...    │
└─────┴──────────────┴──────────┴───────┴────────┘

NOTE_COLLABORATOR_INVITE TABLE:
┌─────┬─────────┬───────────────┬──────────────┬─────────┬────────────┐
│ id  │ note_id │ invited_user  │ status       │ access  │ responded  │
├─────┼─────────┼───────────────┼──────────────┼─────────┼────────────┤
│ 1   │ 1       │ B             │ ACCEPTED     │ view    │ 2024-05-18 │
│ 2   │ 1       │ C             │ PENDING      │ edit    │ NULL       │
└─────┴─────────┴───────────────┴──────────────┴─────────┴────────────┘

NOTE_COLLABORATOR TABLE (Only ACCEPTED):
┌─────┬─────────┬──────────┬──────────┐
│ id  │ note_id │ user_id  │ access   │
├─────┼─────────┼──────────┼──────────┤
│ 1   │ 1       │ B        │ view     │
└─────┴─────────┴──────────┴──────────┘

NOTE: User C does NOT have NoteCollaborator entry yet
      (still in NoteCollaboratorInvite with PENDING status)
```

## Key Takeaway

```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️ IMPORTANT                                                │
│                                                              │
│ Shared notes are DISPLAYED based on FRONTEND FILTERING      │
│ of the complete notes list, NOT via a dedicated API.        │
│                                                              │
│ The Backend provides:                                        │
│ • One GET /api/notes/ endpoint returning ALL notes          │
│ • Each note has share_state & viewer_access fields          │
│                                                              │
│ The Frontend does:                                           │
│ • Filter by currentView                                     │
│ • Categorize into Shared/Private/Archive/Trash/Labels       │
│                                                              │
│ This design allows flexible UI categorization without       │
│ requiring multiple API calls.                               │
└─────────────────────────────────────────────────────────────┘
```
