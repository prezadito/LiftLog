import { ClubRole } from './club-models';

// Club CRUD
export interface CreateClubRequest {
  userId: string;
  password: string;
  encryptedName: Uint8Array;
  encryptedDescription?: Uint8Array;
  encryptedProfilePicture?: Uint8Array;
  encryptionIv: Uint8Array;
  isPublic: boolean;
  membersCanPost: boolean;
  membersCanInvite: boolean;
  maxMembers: number;
}

export interface CreateClubResponse {
  clubId: string;
  created: string;
}

export interface GetClubResponse {
  id: string;
  ownerUserId: string;
  created: string;
  encryptedName: Uint8Array;
  encryptedDescription?: Uint8Array;
  encryptedProfilePicture?: Uint8Array;
  encryptionIv: Uint8Array;
  isPublic: boolean;
  membersCanPost: boolean;
  membersCanInvite: boolean;
  maxMembers: number;
  memberCount: number;
}

export interface UpdateClubRequest {
  clubId: string;
  userId: string;
  password: string;
  encryptedName?: Uint8Array;
  encryptedDescription?: Uint8Array;
  encryptedProfilePicture?: Uint8Array;
  encryptionIv?: Uint8Array;
  isPublic?: boolean;
  membersCanPost?: boolean;
  membersCanInvite?: boolean;
  maxMembers?: number;
}

export interface DeleteClubRequest {
  clubId: string;
  userId: string;
  password: string;
}

export interface SearchClubsRequest {
  query?: string;
  limit?: number;
  offset?: number;
}

export interface SearchClubsResponse {
  clubs: GetClubResponse[];
  total: number;
}

export interface GetMyClubsRequest {
  userId: string;
  password: string;
}

export interface GetMyClubsResponse {
  clubs: GetClubResponse[];
}

// Club Membership
export interface ClubMemberResponse {
  id: string;
  clubId: string;
  userId: string;
  joined: string;
  role: ClubRole;
  encryptedAesKey: Uint8Array;
}

export interface GetClubMembersRequest {
  clubId: string;
  userId: string;
  password: string;
}

export interface GetClubMembersResponse {
  members: ClubMemberResponse[];
}

export interface InviteToClubRequest {
  clubId: string;
  inviterUserId: string;
  inviterPassword: string;
  inviteeUserId: string;
  encryptedClubName: Uint8Array;
  encryptedClubDescription: Uint8Array;
  encryptedProfilePicture?: Uint8Array;
  encryptedAesKey: Uint8Array;
  offeredRole: ClubRole;
}

export interface JoinPublicClubRequest {
  clubId: string;
  userId: string;
  password: string;
}

export interface AcceptClubInviteRequest {
  clubId: string;
  userId: string;
  password: string;
  encryptedAesKey: Uint8Array;
}

export interface LeaveClubRequest {
  clubId: string;
  userId: string;
  password: string;
}

export interface RemoveClubMemberRequest {
  clubId: string;
  adminUserId: string;
  adminPassword: string;
  memberUserId: string;
}

export interface UpdateMemberRoleRequest {
  clubId: string;
  adminUserId: string;
  adminPassword: string;
  memberUserId: string;
  newRole: ClubRole;
}

// Club Events
export interface ClubEventResponse {
  id: string;
  clubId: string;
  userId: string;
  timestamp: string;
  expiry: string;
  encryptedEvent: Uint8Array;
  encryptionIv: Uint8Array;
}

export interface PostClubEventRequest {
  clubId: string;
  userId: string;
  password: string;
  eventId: string;
  encryptedEvent: Uint8Array;
  encryptionIv: Uint8Array;
  expiry: string;
}

export interface GetClubEventsRequest {
  clubId: string;
  userId: string;
  password: string;
  since?: string;
  limit?: number;
}

export interface GetClubEventsResponse {
  events: ClubEventResponse[];
}
