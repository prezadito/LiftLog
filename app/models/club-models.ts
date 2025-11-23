import { Instant } from '@js-joda/core';
import { AesKey } from '@/models/encryption-models';
import { Session, SessionPOJO } from '@/models/session-models';

export type ClubRole = 'owner' | 'admin' | 'member' | 'viewer';

export interface ClubSettingsPOJO {
  _BRAND: 'CLUB_SETTINGS_POJO';
  membersCanPost: boolean;
  membersCanInvite: boolean;
  maxMembers: number;
}

export class ClubSettings {
  readonly membersCanPost: boolean;
  readonly membersCanInvite: boolean;
  readonly maxMembers: number;

  constructor(membersCanPost: boolean, membersCanInvite: boolean, maxMembers: number) {
    this.membersCanPost = membersCanPost;
    this.membersCanInvite = membersCanInvite;
    this.maxMembers = maxMembers;
  }

  static fromPOJO(pojo: Omit<ClubSettingsPOJO, '_BRAND'>): ClubSettings {
    return new ClubSettings(pojo.membersCanPost, pojo.membersCanInvite, pojo.maxMembers);
  }

  toPOJO(): ClubSettingsPOJO {
    return {
      _BRAND: 'CLUB_SETTINGS_POJO',
      membersCanPost: this.membersCanPost,
      membersCanInvite: this.membersCanInvite,
      maxMembers: this.maxMembers,
    };
  }

  with(other: Partial<ClubSettingsPOJO>): ClubSettings {
    return new ClubSettings(
      other.membersCanPost ?? this.membersCanPost,
      other.membersCanInvite ?? this.membersCanInvite,
      other.maxMembers ?? this.maxMembers,
    );
  }
}

export interface ClubPOJO {
  _BRAND: 'CLUB_POJO';
  id: string;
  ownerUserId: string;
  created: Instant;
  name: string;
  description: string | undefined;
  profilePicture: Uint8Array | undefined;
  aesKey: AesKey;
  isPublic: boolean;
  settings: ClubSettingsPOJO;
  memberCount: number;
}

export class Club {
  readonly id: string;
  readonly ownerUserId: string;
  readonly created: Instant;
  readonly name: string;
  readonly description: string | undefined;
  readonly profilePicture: Uint8Array | undefined;
  readonly aesKey: AesKey;
  readonly isPublic: boolean;
  readonly settings: ClubSettings;
  readonly memberCount: number;

  /**
   * @deprecated please use full constructor. Here only for serialization
   */
  constructor();
  constructor(
    id: string,
    ownerUserId: string,
    created: Instant,
    name: string,
    description: string | undefined,
    profilePicture: Uint8Array | undefined,
    aesKey: AesKey,
    isPublic: boolean,
    settings: ClubSettings,
    memberCount: number,
  );
  constructor(
    id?: string,
    ownerUserId?: string,
    created?: Instant,
    name?: string,
    description?: string,
    profilePicture?: Uint8Array,
    aesKey?: AesKey,
    isPublic?: boolean,
    settings?: ClubSettings,
    memberCount?: number,
  ) {
    this.id = id!;
    this.ownerUserId = ownerUserId!;
    this.created = created!;
    this.name = name!;
    this.description = description;
    this.profilePicture = profilePicture;
    this.aesKey = aesKey!;
    this.isPublic = isPublic!;
    this.settings = settings!;
    this.memberCount = memberCount!;
  }

  static fromPOJO(pojo: Omit<ClubPOJO, '_BRAND'>): Club {
    return new Club(
      pojo.id,
      pojo.ownerUserId,
      pojo.created,
      pojo.name,
      pojo.description,
      pojo.profilePicture,
      pojo.aesKey,
      pojo.isPublic,
      ClubSettings.fromPOJO(pojo.settings),
      pojo.memberCount,
    );
  }

  toPOJO(): ClubPOJO {
    return {
      _BRAND: 'CLUB_POJO',
      id: this.id,
      ownerUserId: this.ownerUserId,
      created: this.created,
      name: this.name,
      description: this.description,
      profilePicture: this.profilePicture,
      aesKey: this.aesKey,
      isPublic: this.isPublic,
      settings: this.settings.toPOJO(),
      memberCount: this.memberCount,
    };
  }

  with(other: Partial<ClubPOJO>): Club {
    return new Club(
      other.id ?? this.id,
      other.ownerUserId ?? this.ownerUserId,
      other.created ?? this.created,
      other.name ?? this.name,
      other.description ?? this.description,
      other.profilePicture ?? this.profilePicture,
      other.aesKey ?? this.aesKey,
      other.isPublic ?? this.isPublic,
      other.settings ? ClubSettings.fromPOJO(other.settings) : this.settings,
      other.memberCount ?? this.memberCount,
    );
  }
}

export interface ClubMemberPOJO {
  _BRAND: 'CLUB_MEMBER_POJO';
  clubId: string;
  userId: string;
  role: ClubRole;
  joined: Instant;
}

export class ClubMember {
  readonly clubId: string;
  readonly userId: string;
  readonly role: ClubRole;
  readonly joined: Instant;

  constructor(clubId: string, userId: string, role: ClubRole, joined: Instant) {
    this.clubId = clubId;
    this.userId = userId;
    this.role = role;
    this.joined = joined;
  }

  static fromPOJO(pojo: Omit<ClubMemberPOJO, '_BRAND'>): ClubMember {
    return new ClubMember(pojo.clubId, pojo.userId, pojo.role, pojo.joined);
  }

  toPOJO(): ClubMemberPOJO {
    return {
      _BRAND: 'CLUB_MEMBER_POJO',
      clubId: this.clubId,
      userId: this.userId,
      role: this.role,
      joined: this.joined,
    };
  }

  with(other: Partial<ClubMemberPOJO>): ClubMember {
    return new ClubMember(
      other.clubId ?? this.clubId,
      other.userId ?? this.userId,
      other.role ?? this.role,
      other.joined ?? this.joined,
    );
  }
}

export interface ClubFeedItemPOJO {
  _BRAND: 'CLUB_SESSION_FEED_ITEM_POJO' | 'CLUB_ANNOUNCEMENT_FEED_ITEM_POJO';
  clubId: string;
  userId: string;
  eventId: string;
  timestamp: Instant;
  expiry: Instant;
}

export abstract class ClubFeedItem {
  readonly clubId: string;
  readonly userId: string;
  readonly eventId: string;
  readonly timestamp: Instant;
  readonly expiry: Instant;

  constructor(
    clubId: string,
    userId: string,
    eventId: string,
    timestamp: Instant,
    expiry: Instant,
  ) {
    this.clubId = clubId;
    this.userId = userId;
    this.eventId = eventId;
    this.timestamp = timestamp;
    this.expiry = expiry;
  }

  abstract toPOJO(): ClubFeedItemPOJO;
  abstract withSession(session: Session | undefined): ClubFeedItem;
  abstract withAnnouncement(announcement: string | undefined): ClubFeedItem;
}

export interface ClubSessionFeedItemPOJO extends ClubFeedItemPOJO {
  _BRAND: 'CLUB_SESSION_FEED_ITEM_POJO';
  session: SessionPOJO;
}

export class ClubSessionFeedItem extends ClubFeedItem {
  readonly session: Session;

  constructor(
    clubId: string,
    userId: string,
    eventId: string,
    timestamp: Instant,
    expiry: Instant,
    session: Session,
  ) {
    super(clubId, userId, eventId, timestamp, expiry);
    this.session = session;
  }

  static fromPOJO(pojo: Omit<ClubSessionFeedItemPOJO, '_BRAND'>): ClubSessionFeedItem {
    return new ClubSessionFeedItem(
      pojo.clubId,
      pojo.userId,
      pojo.eventId,
      pojo.timestamp,
      pojo.expiry,
      Session.fromPOJO(pojo.session),
    );
  }

  toPOJO(): ClubSessionFeedItemPOJO {
    return {
      _BRAND: 'CLUB_SESSION_FEED_ITEM_POJO',
      clubId: this.clubId,
      userId: this.userId,
      eventId: this.eventId,
      timestamp: this.timestamp,
      expiry: this.expiry,
      session: this.session.toPOJO(),
    };
  }

  withSession(session: Session | undefined): ClubFeedItem {
    if (!session) return this;
    return new ClubSessionFeedItem(
      this.clubId,
      this.userId,
      this.eventId,
      this.timestamp,
      this.expiry,
      session,
    );
  }

  withAnnouncement(_announcement: string | undefined): ClubFeedItem {
    return this;
  }
}

export interface ClubAnnouncementFeedItemPOJO extends ClubFeedItemPOJO {
  _BRAND: 'CLUB_ANNOUNCEMENT_FEED_ITEM_POJO';
  announcement: string;
}

export class ClubAnnouncementFeedItem extends ClubFeedItem {
  readonly announcement: string;

  constructor(
    clubId: string,
    userId: string,
    eventId: string,
    timestamp: Instant,
    expiry: Instant,
    announcement: string,
  ) {
    super(clubId, userId, eventId, timestamp, expiry);
    this.announcement = announcement;
  }

  static fromPOJO(pojo: Omit<ClubAnnouncementFeedItemPOJO, '_BRAND'>): ClubAnnouncementFeedItem {
    return new ClubAnnouncementFeedItem(
      pojo.clubId,
      pojo.userId,
      pojo.eventId,
      pojo.timestamp,
      pojo.expiry,
      pojo.announcement,
    );
  }

  toPOJO(): ClubAnnouncementFeedItemPOJO {
    return {
      _BRAND: 'CLUB_ANNOUNCEMENT_FEED_ITEM_POJO',
      clubId: this.clubId,
      userId: this.userId,
      eventId: this.eventId,
      timestamp: this.timestamp,
      expiry: this.expiry,
      announcement: this.announcement,
    };
  }

  withSession(_session: Session | undefined): ClubFeedItem {
    return this;
  }

  withAnnouncement(announcement: string | undefined): ClubFeedItem {
    if (!announcement) return this;
    return new ClubAnnouncementFeedItem(
      this.clubId,
      this.userId,
      this.eventId,
      this.timestamp,
      this.expiry,
      announcement,
    );
  }
}

export interface ClubInvitePOJO {
  _BRAND: 'CLUB_INVITE_POJO';
  clubId: string;
  clubName: string;
  clubDescription: string | undefined;
  clubProfilePicture: Uint8Array | undefined;
  clubAesKey: AesKey;
  offeredRole: ClubRole;
  fromUserId: string;
  fromUserName: string | undefined;
}

export class ClubInvite {
  readonly clubId: string;
  readonly clubName: string;
  readonly clubDescription: string | undefined;
  readonly clubProfilePicture: Uint8Array | undefined;
  readonly clubAesKey: AesKey;
  readonly offeredRole: ClubRole;
  readonly fromUserId: string;
  readonly fromUserName: string | undefined;

  constructor(
    clubId: string,
    clubName: string,
    clubDescription: string | undefined,
    clubProfilePicture: Uint8Array | undefined,
    clubAesKey: AesKey,
    offeredRole: ClubRole,
    fromUserId: string,
    fromUserName: string | undefined,
  ) {
    this.clubId = clubId;
    this.clubName = clubName;
    this.clubDescription = clubDescription;
    this.clubProfilePicture = clubProfilePicture;
    this.clubAesKey = clubAesKey;
    this.offeredRole = offeredRole;
    this.fromUserId = fromUserId;
    this.fromUserName = fromUserName;
  }

  static fromPOJO(pojo: Omit<ClubInvitePOJO, '_BRAND'>): ClubInvite {
    return new ClubInvite(
      pojo.clubId,
      pojo.clubName,
      pojo.clubDescription,
      pojo.clubProfilePicture,
      pojo.clubAesKey,
      pojo.offeredRole,
      pojo.fromUserId,
      pojo.fromUserName,
    );
  }

  toPOJO(): ClubInvitePOJO {
    return {
      _BRAND: 'CLUB_INVITE_POJO',
      clubId: this.clubId,
      clubName: this.clubName,
      clubDescription: this.clubDescription,
      clubProfilePicture: this.clubProfilePicture,
      clubAesKey: this.clubAesKey,
      offeredRole: this.offeredRole,
      fromUserId: this.fromUserId,
      fromUserName: this.fromUserName,
    };
  }
}
