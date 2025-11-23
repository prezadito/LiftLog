# Club Feature Implementation Guide

**Status**: Backend Complete, Frontend Infrastructure Complete
**Last Updated**: 2025-11-23
**Branch**: `claude/plan-create-club-feature-016UD1cnoqHSPZdut5ngTqqx`

## ✅ Completed

### 1. Backend Implementation (Python FastAPI)

#### Database Models
- ✅ `Club` model with encrypted metadata
- ✅ `ClubMember` model with role-based permissions
- ✅ `ClubEvent` model for club feed items
- ✅ Alembic migration (`001_add_club_tables.py`)

#### API Endpoints (`/v2/club/*`)
- ✅ **CRUD**: create, get, update, delete clubs
- ✅ **Search**: search public clubs, get user's clubs
- ✅ **Membership**: get members, invite, join, leave, remove
- ✅ **Events**: post events, get club feed
- ✅ **Authorization**: Password auth + role-based access control
- ✅ **Error Handling**: Proper exceptions (ForbiddenException added)

#### Protocol Buffers
- ✅ `ClubDao.proto` with all club schemas
- ✅ Updated `UserEvent.proto` for inbox messages
- ✅ Updated `FeedStateDao.proto` for club state
- ✅ Generated TypeScript code

### 2. Frontend Infrastructure

#### Models
- ✅ `club-models.ts`: Club, ClubMember, ClubFeedItem, ClubInvite
- ✅ `club-api-models.ts`: Request/Response types
- ✅ Type-safe models with POJO converters

#### Services
- ✅ `club-api.ts`: ClubApiService with full CRUD, membership, events
- ✅ Base64 encoding/decoding
- ✅ Error handling with ApiResult pattern

---

## 🔄 Remaining Work

### 3. Redux State Management

#### **File**: `app/store/clubs/index.ts`

```typescript
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Club, ClubPOJO, ClubMember, ClubMemberPOJO, ClubFeedItem, ClubFeedItemPOJO, ClubInvite, ClubInvitePOJO } from '@/models/club-models';
import { FeedUser, FeedUserPOJO } from '@/models/feed-models';

export interface ClubsState {
  isHydrated: boolean;
  clubs: Record<string, ClubPOJO>;           // Clubs user is member of, by club ID
  clubMembers: Record<string, Record<string, FeedUserPOJO>>;  // club ID -> user ID -> FeedUser
  clubFeeds: Record<string, ClubFeedItemPOJO[]>;  // club ID -> feed items
  clubInvites: ClubInvitePOJO[];            // Pending invites
  discoveredClubs: ClubPOJO[];               // Search results
  selectedClubId: string | undefined;        // Currently viewing club
  isFetching: boolean;
}

const initialState: ClubsState = {
  isHydrated: false,
  clubs: {},
  clubMembers: {},
  clubFeeds: {},
  clubInvites: [],
  discoveredClubs: [],
  selectedClubId: undefined,
  isFetching: false,
};

const clubsSlice = createSlice({
  name: 'clubs',
  initialState,
  reducers: {
    // Club CRUD
    createClubStarted: (state) => {
      state.isFetching = true;
    },
    createClubCompleted: (state, action: PayloadAction<{ club: ClubPOJO }>) => {
      state.clubs[action.payload.club.id] = action.payload.club;
      state.isFetching = false;
    },
    createClubFailed: (state) => {
      state.isFetching = false;
    },

    // Load user's clubs
    loadMyClubsStarted: (state) => {
      state.isFetching = true;
    },
    loadMyClubsCompleted: (state, action: PayloadAction<{ clubs: ClubPOJO[] }>) => {
      action.payload.clubs.forEach((club) => {
        state.clubs[club.id] = club;
      });
      state.isFetching = false;
      state.isHydrated = true;
    },
    loadMyClubsFailed: (state) => {
      state.isFetching = false;
    },

    // Search/discover clubs
    searchClubsStarted: (state) => {
      state.isFetching = true;
    },
    searchClubsCompleted: (state, action: PayloadAction<{ clubs: ClubPOJO[] }>) => {
      state.discoveredClubs = action.payload.clubs;
      state.isFetching = false;
    },
    searchClubsFailed: (state) => {
      state.isFetching = false;
    },

    // Join club
    joinClubStarted: (state) => {
      state.isFetching = true;
    },
    joinClubCompleted: (state, action: PayloadAction<{ club: ClubPOJO }>) => {
      state.clubs[action.payload.club.id] = action.payload.club;
      state.isFetching = false;
    },
    joinClubFailed: (state) => {
      state.isFetching = false;
    },

    // Leave club
    leaveClubCompleted: (state, action: PayloadAction<{ clubId: string }>) => {
      delete state.clubs[action.payload.clubId];
      delete state.clubMembers[action.payload.clubId];
      delete state.clubFeeds[action.payload.clubId];
    },

    // Club members
    loadClubMembersCompleted: (
      state,
      action: PayloadAction<{ clubId: string; members: Record<string, FeedUserPOJO> }>,
    ) => {
      state.clubMembers[action.payload.clubId] = action.payload.members;
    },

    // Club feed
    loadClubFeedCompleted: (
      state,
      action: PayloadAction<{ clubId: string; items: ClubFeedItemPOJO[] }>,
    ) => {
      state.clubFeeds[action.payload.clubId] = action.payload.items;
    },
    postToClubFeedCompleted: (
      state,
      action: PayloadAction<{ clubId: string; item: ClubFeedItemPOJO }>,
    ) => {
      if (!state.clubFeeds[action.payload.clubId]) {
        state.clubFeeds[action.payload.clubId] = [];
      }
      state.clubFeeds[action.payload.clubId].unshift(action.payload.item);
    },

    // Club invites
    clubInviteReceived: (state, action: PayloadAction<{ invite: ClubInvitePOJO }>) => {
      state.clubInvites.push(action.payload.invite);
    },
    acceptClubInviteCompleted: (
      state,
      action: PayloadAction<{ clubId: string; club: ClubPOJO }>,
    ) => {
      state.clubInvites = state.clubInvites.filter((i) => i.clubId !== action.payload.clubId);
      state.clubs[action.payload.club.id] = action.payload.club;
    },
    declineClubInviteCompleted: (state, action: PayloadAction<{ clubId: string }>) => {
      state.clubInvites = state.clubInvites.filter((i) => i.clubId !== action.payload.clubId);
    },

    // UI state
    selectClub: (state, action: PayloadAction<{ clubId: string | undefined }>) => {
      state.selectedClubId = action.payload.clubId;
    },

    // Hydration
    clubsHydrated: (state, action: PayloadAction<Partial<ClubsState>>) => {
      return { ...state, ...action.payload, isHydrated: true };
    },
  },
});

export const {
  createClubStarted,
  createClubCompleted,
  createClubFailed,
  loadMyClubsStarted,
  loadMyClubsCompleted,
  loadMyClubsFailed,
  searchClubsStarted,
  searchClubsCompleted,
  searchClubsFailed,
  joinClubStarted,
  joinClubCompleted,
  joinClubFailed,
  leaveClubCompleted,
  loadClubMembersCompleted,
  loadClubFeedCompleted,
  postToClubFeedCompleted,
  clubInviteReceived,
  acceptClubInviteCompleted,
  declineClubInviteCompleted,
  selectClub,
  clubsHydrated,
} = clubsSlice.actions;

export default clubsSlice.reducer;
```

#### **File**: `app/store/clubs/effects.ts`

```typescript
import { startAppListening } from '@/store/store';
import {
  createClubStarted,
  createClubCompleted,
  createClubFailed,
  loadMyClubsStarted,
  loadMyClubsCompleted,
  loadMyClubsFailed,
  // ... other actions
} from './index';
import { Club } from '@/models/club-models';
import { EncryptionService } from '@/services/encryption-service';

// Create club effect
startAppListening({
  actionCreator: createClubStarted,
  effect: async (action, listenerApi) => {
    const { extra, getState, dispatch } = listenerApi;
    const state = getState();
    const identity = state.feed.identity;

    if (!identity) {
      dispatch(createClubFailed());
      return;
    }

    try {
      // Generate club AES key
      const clubAesKey = await EncryptionService.generateAesKeyAsync();

      // Encrypt club name, description
      const encryptedName = await extra.encryptionService.encryptAesCbcAsync(
        new TextEncoder().encode(action.payload.name),
        clubAesKey,
      );

      const encryptedDescription = action.payload.description
        ? await extra.encryptionService.encryptAesCbcAsync(
            new TextEncoder().encode(action.payload.description),
            clubAesKey,
          )
        : undefined;

      // Encrypt AES key with owner's RSA public key
      const encryptedAesKey = await extra.encryptionService.encryptRsaOaepSha256Async(
        clubAesKey,
        identity.publicKey,
      );

      // Call API
      const result = await extra.clubApi.createClubAsync({
        userId: identity.id,
        password: identity.password,
        encryptedName: encryptedName.encryptedPayload,
        encryptedDescription: encryptedDescription?.encryptedPayload,
        encryptionIv: encryptedName.iv.value,
        isPublic: action.payload.isPublic,
        membersCanPost: action.payload.membersCanPost,
        membersCanInvite: action.payload.membersCanInvite,
        maxMembers: action.payload.maxMembers,
      });

      if (result.isError) {
        dispatch(createClubFailed());
        return;
      }

      // Create club object
      const club = new Club(
        result.data.clubId,
        identity.id,
        Instant.parse(result.data.created),
        action.payload.name,
        action.payload.description,
        undefined,
        clubAesKey,
        action.payload.isPublic,
        action.payload.settings,
        1, // Owner is first member
      );

      dispatch(createClubCompleted({ club: club.toPOJO() }));
    } catch (error) {
      console.error('Error creating club:', error);
      dispatch(createClubFailed());
    }
  },
});

// Load my clubs effect
startAppListening({
  actionCreator: loadMyClubsStarted,
  effect: async (action, listenerApi) => {
    const { extra, getState, dispatch } = listenerApi;
    const state = getState();
    const identity = state.feed.identity;

    if (!identity) {
      dispatch(loadMyClubsFailed());
      return;
    }

    try {
      const result = await extra.clubApi.getMyClubsAsync({
        userId: identity.id,
        password: identity.password,
      });

      if (result.isError) {
        dispatch(loadMyClubsFailed());
        return;
      }

      // Decrypt club names and create Club objects
      const clubs = await Promise.all(
        result.data.clubs.map(async (clubResponse) => {
          // Fetch member to get encrypted AES key
          const membersResult = await extra.clubApi.getClubMembersAsync({
            clubId: clubResponse.id,
            userId: identity.id,
            password: identity.password,
          });

          if (membersResult.isError) {
            return null;
          }

          const myMembership = membersResult.data.members.find(
            (m) => m.userId === identity.id,
          );

          if (!myMembership) {
            return null;
          }

          // Decrypt AES key
          const clubAesKey = await extra.encryptionService.decryptRsaOaepSha256Async(
            myMembership.encryptedAesKey,
            identity.privateKey,
          );

          // Decrypt club name
          const decryptedName = await extra.encryptionService.decryptAesCbcAsync(
            {
              encryptedPayload: clubResponse.encryptedName,
              iv: { value: clubResponse.encryptionIv },
            },
            clubAesKey,
          );

          const name = new TextDecoder().decode(decryptedName);

          // Decrypt description if present
          let description: string | undefined;
          if (clubResponse.encryptedDescription) {
            const decryptedDesc = await extra.encryptionService.decryptAesCbcAsync(
              {
                encryptedPayload: clubResponse.encryptedDescription,
                iv: { value: clubResponse.encryptionIv },
              },
              clubAesKey,
            );
            description = new TextDecoder().decode(decryptedDesc);
          }

          return new Club(
            clubResponse.id,
            clubResponse.ownerUserId,
            Instant.parse(clubResponse.created),
            name,
            description,
            clubResponse.encryptedProfilePicture,
            clubAesKey,
            clubResponse.isPublic,
            new ClubSettings(
              clubResponse.membersCanPost,
              clubResponse.membersCanInvite,
              clubResponse.maxMembers,
            ),
            clubResponse.memberCount,
          );
        }),
      );

      const validClubs = clubs.filter((c) => c !== null) as Club[];

      dispatch(
        loadMyClubsCompleted({ clubs: validClubs.map((c) => c.toPOJO()) }),
      );
    } catch (error) {
      console.error('Error loading clubs:', error);
      dispatch(loadMyClubsFailed());
    }
  },
});

// Similar effects for:
// - searchClubs
// - joinClub
// - leaveClub
// - postToClubFeed
// - loadClubFeed
// - inviteToClub
// - acceptClubInvite
```

#### Register in Store
Update `app/store/store.ts`:
```typescript
import clubsReducer from './clubs';

export const store = configureStore({
  reducer: {
    // ... existing reducers
    clubs: clubsReducer,
  },
  // ... existing middleware
});
```

---

### 4. UI Components

#### Tab Navigation
**File**: `app/app/(tabs)/_layout.tsx`

Add new tab between Feed and History:
```tsx
<Tabs.Screen
  name="clubs"
  options={{
    title: t('clubs.title'),
    tabBarIcon: ({ color }) => <GroupIcon size={24} color={color} />,
  }}
/>
```

#### Club Routes

Create directory structure:
```
app/app/(tabs)/clubs/
├── index.tsx              # Club list (user's clubs)
├── discover.tsx           # Browse/search public clubs
├── create.tsx             # Create new club
├── [clubId]/
│   ├── index.tsx          # Club detail & feed
│   ├── members.tsx        # Member management
│   └── settings.tsx       # Club settings (admin only)
```

#### **Example**: Club List (`index.tsx`)

```typescript
import { useAppSelector, useAppDispatch } from '@/store';
import { useEffect } from 'react';
import { loadMyClubsStarted, selectClub } from '@/store/clubs';
import { FlatList } from 'react-native';
import { ClubCard } from '@/components/presentation/ClubCard';

export default function ClubsScreen() {
  const dispatch = useAppDispatch();
  const clubs = useAppSelector((state) =>
    Object.values(state.clubs.clubs).map(Club.fromPOJO)
  );
  const isHydrated = useAppSelector((state) => state.clubs.isHydrated);

  useEffect(() => {
    if (!isHydrated) {
      dispatch(loadMyClubsStarted());
    }
  }, [isHydrated]);

  return (
    <FlatList
      data={clubs}
      renderItem={({ item }) => (
        <ClubCard
          club={item}
          onPress={() => {
            dispatch(selectClub({ clubId: item.id }));
            router.push(`/clubs/${item.id}`);
          }}
        />
      )}
      keyExtractor={(item) => item.id}
    />
  );
}
```

#### Presentation Components

**File**: `app/components/presentation/ClubCard.tsx`
```tsx
import { Card, Text, Avatar, Badge } from 'react-native-paper';
import { Club } from '@/models/club-models';

export interface ClubCardProps {
  club: Club;
  onPress: () => void;
}

export const ClubCard: React.FC<ClubCardProps> = ({ club, onPress }) => {
  return (
    <Card onPress={onPress}>
      <Card.Title
        title={club.name}
        subtitle={`${club.memberCount} members`}
        left={(props) => (
          <Avatar.Image
            {...props}
            source={
              club.profilePicture
                ? { uri: `data:image/png;base64,${btoa(...)}` }
                : require('@/assets/default-club.png')
            }
          />
        )}
        right={(props) => (
          club.isPublic ? <Badge {...props}>Public</Badge> : null
        )}
      />
      {club.description && <Card.Content><Text>{club.description}</Text></Card.Content>}
    </Card>
  );
};
```

Similar components needed:
- `ClubFeedItem.tsx` - Display club feed items
- `ClubMemberListItem.tsx` - Member with role badge
- `ClubInviteCard.tsx` - Pending invite card
- `ClubSearchBar.tsx` - Search/filter clubs

#### Smart Components

**File**: `app/components/smart/ClubFeed.tsx`
```tsx
// Redux-connected feed component
// Loads club feed items, handles infinite scroll
// Decrypts and displays sessions/announcements
```

---

### 5. Internationalization

**File**: `app/i18n/en.json`

Add keys:
```json
{
  "clubs": {
    "title": "Clubs",
    "my_clubs": "My Clubs",
    "discover": "Discover Clubs",
    "create": "Create Club",
    "create_club": "Create Club",
    "edit_club": "Edit Club",
    "delete_club": "Delete Club",
    "club_name": "Club Name",
    "club_description": "Description",
    "public_club": "Public Club",
    "private_club": "Private Club",
    "members": "Members",
    "member_count": "{count, plural, =1 {1 member} other {# members}}",
    "settings": "Settings",
    "invite_member": "Invite Member",
    "join_club": "Join Club",
    "leave_club": "Leave Club",
    "remove_member": "Remove Member",
    "make_admin": "Make Admin",
    "make_member": "Make Member",
    "posted_in": "Posted in {clubName}",
    "members_can_post": "Members can post",
    "members_can_invite": "Members can invite",
    "max_members": "Max members",
    "unlimited": "Unlimited",
    "role_owner": "Owner",
    "role_admin": "Admin",
    "role_member": "Member",
    "role_viewer": "Viewer",
    "invites": "Club Invites",
    "invited_by": "Invited by {userName}",
    "accept_invite": "Accept",
    "decline_invite": "Decline",
    "no_clubs": "You're not in any clubs yet",
    "no_invites": "No pending invites",
    "search_clubs": "Search clubs...",
    "errors": {
      "create_failed": "Failed to create club",
      "load_failed": "Failed to load clubs",
      "join_failed": "Failed to join club",
      "leave_failed": "Failed to leave club",
      "club_full": "Club has reached maximum members",
      "not_authorized": "You don't have permission for this action"
    }
  }
}
```

Run: `npm run pull-translations` to sync with Tolgee

---

### 6. Testing

#### Backend Tests
**File**: `backend-python/tests/test_clubs.py`

```python
import pytest
from app.models.database import Club, ClubMember, ClubEvent

@pytest.mark.asyncio
async def test_create_club(client, test_user):
    response = await client.post("/v2/club/create", json={
        "userId": str(test_user.id),
        "password": "test_password",
        "encryptedName": "dGVzdCBjbHVi",  # base64 "test club"
        "encryptionIv": "MTIzNDU2Nzg=",
        "isPublic": True,
        "membersCanPost": True,
        "membersCanInvite": False,
        "maxMembers": 50,
    })
    assert response.status_code == 200
    data = response.json()
    assert "clubId" in data

# Similar tests for all endpoints
```

#### Frontend Tests
**File**: `app/store/clubs/index.spec.ts`

```typescript
import reducer, { createClubCompleted, loadMyClubsCompleted } from './index';
import { ClubPOJO } from '@/models/club-models';

describe('clubs reducer', () => {
  it('should handle createClubCompleted', () => {
    const club: ClubPOJO = { /* ... */ };
    const state = reducer(undefined, createClubCompleted({ club }));
    expect(state.clubs[club.id]).toEqual(club);
  });

  // More tests...
});
```

#### E2E Tests
**File**: `tests/cypress-tests/e2e/clubs.cy.ts`

```typescript
describe('Club Feature', () => {
  it('should create a club', () => {
    cy.visit('/clubs');
    cy.get('[data-testid="create-club-button"]').click();
    cy.get('[data-testid="club-name-input"]').type('Test Club');
    cy.get('[data-testid="submit-button"]').click();
    cy.contains('Test Club').should('exist');
  });

  // More tests...
});
```

---

## 📋 Implementation Checklist

### Redux (Priority 1)
- [ ] Create `app/store/clubs/index.ts` with reducer and actions
- [ ] Create `app/store/clubs/effects.ts` with async effects
- [ ] Register club reducer in store
- [ ] Add persistence for clubs state

### UI - Core (Priority 2)
- [ ] Add clubs tab to navigation
- [ ] Create `clubs/index.tsx` - list user's clubs
- [ ] Create `clubs/discover.tsx` - search/browse
- [ ] Create `clubs/create.tsx` - create new club
- [ ] Create `clubs/[clubId]/index.tsx` - club detail & feed

### UI - Advanced (Priority 3)
- [ ] Create `clubs/[clubId]/members.tsx` - member management
- [ ] Create `clubs/[clubId]/settings.tsx` - club settings
- [ ] Create `ClubCard` component
- [ ] Create `ClubFeedItem` component
- [ ] Create `ClubMemberListItem` component
- [ ] Create `ClubInviteCard` component

### Features (Priority 4)
- [ ] Implement club invite flow (via inbox)
- [ ] Implement join public club flow
- [ ] Implement post to club feed
- [ ] Implement leave club
- [ ] Implement member removal
- [ ] Implement role management

### Polish (Priority 5)
- [ ] Add all i18n strings
- [ ] Add loading states
- [ ] Add error handling
- [ ] Add empty states
- [ ] Add confirmation dialogs
- [ ] Add toast notifications

### Testing (Priority 6)
- [ ] Backend unit tests
- [ ] Frontend unit tests
- [ ] E2E tests
- [ ] Manual testing

---

## 🚀 Deployment

### Database Migration
```bash
cd backend-python
uv run alembic upgrade head
```

### Environment Variables
No new variables needed - uses existing authentication.

### Feature Flag (Optional)
Could gate behind RevenueCat premium subscription:
```typescript
const isPremium = useAppSelector((state) => state.settings.isPremiumUser);
if (!isPremium) {
  // Show upgrade prompt
}
```

---

## 📊 Progress Summary

| Component | Status | Lines of Code | Completion |
|-----------|--------|---------------|------------|
| Protocol Buffers | ✅ Complete | ~200 | 100% |
| Backend Models | ✅ Complete | ~150 | 100% |
| Backend Migration | ✅ Complete | ~100 | 100% |
| Backend API | ✅ Complete | ~1100 | 100% |
| Frontend Models | ✅ Complete | ~500 | 100% |
| Frontend API Service | ✅ Complete | ~500 | 100% |
| Redux State | ⏳ Template Provided | ~300 | 0% |
| Redux Effects | ⏳ Template Provided | ~600 | 0% |
| UI Components | ⏳ Template Provided | ~1500 | 0% |
| i18n | ⏳ Template Provided | ~50 | 0% |
| Tests | ⏳ Template Provided | ~500 | 0% |
| **TOTAL** | **~3500 LOC** | **~50%** |

**Estimated Remaining Work**: 2-3 days for experienced React Native developer

---

## 💡 Next Steps

1. **Immediate**: Implement Redux state and effects (highest priority)
2. **Week 1**: Build core UI (list, discover, create, detail)
3. **Week 2**: Add advanced features (invites, member management)
4. **Week 3**: Testing, i18n, polish

**Quick Start**:
```bash
# Backend already deployed - just run migration
cd backend-python && uv run alembic upgrade head

# Frontend - start with Redux
# Copy templates from this doc into app/store/clubs/
# Then build UI components incrementally
```

---

## 📚 Resources

- **Existing Patterns**: Study `app/store/feed/` for Redux patterns
- **UI Patterns**: Study `app/components/` for component structure
- **API Patterns**: All backend endpoints documented in `ClubApiService`
- **Encryption**: See `/docs/FeedProcess.md` for encryption details
- **Testing**: See existing test files for patterns

---

**Questions?** Check existing feed implementation - clubs follow identical patterns!
