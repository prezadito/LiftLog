import {
  CreateClubRequest,
  CreateClubResponse,
  GetClubResponse,
  UpdateClubRequest,
  DeleteClubRequest,
  SearchClubsRequest,
  SearchClubsResponse,
  GetMyClubsRequest,
  GetMyClubsResponse,
  GetClubMembersRequest,
  GetClubMembersResponse,
  InviteToClubRequest,
  JoinPublicClubRequest,
  AcceptClubInviteRequest,
  LeaveClubRequest,
  RemoveClubMemberRequest,
  UpdateMemberRoleRequest,
  ClubEventResponse,
  PostClubEventRequest,
  GetClubEventsRequest,
  GetClubEventsResponse,
} from '@/models/club-api-models';
import { ApiErrorType, ApiResult, ResponseError } from '@/services/api-error';
import type { FetchResponse } from 'expo/build/winter/fetch/FetchResponse';
import { fetch } from 'expo/fetch';
import { Platform } from 'react-native';

type Base64Response<T> = T extends Uint8Array
  ? string
  : T extends Uint8Array | undefined
    ? string | undefined
    : T extends (infer U)[]
      ? Base64Response<U>[]
      : T extends object
        ? { [K in keyof T]: Base64Response<T[K]> }
        : T;

export class ClubApiService {
  private readonly baseUrl: string;

  constructor() {
    if (__DEV__) {
      this.baseUrl =
        Platform.OS === 'android'
          ? 'http://10.0.2.2:5264/v2/'
          : 'http://127.0.0.1:5264/v2/';
    } else {
      this.baseUrl = 'https://api.liftlog.online/v2/';
    }
  }

  // Club CRUD operations

  async createClubAsync(
    request: CreateClubRequest,
  ): Promise<ApiResult<CreateClubResponse>> {
    return this.getApiResultAsync(async () => {
      const response = await fetch(`${this.baseUrl}club/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: stringify(request),
      });
      this.ensureSuccessStatusCode(response);
      return (await response.json()) as Base64Response<CreateClubResponse>;
    });
  }

  async getClubAsync(clubId: string): Promise<ApiResult<GetClubResponse>> {
    return this.getApiResultAsync(async () => {
      const response = await fetch(`${this.baseUrl}club/${clubId}`);
      this.ensureSuccessStatusCode(response);
      const base64Response =
        (await response.json()) as Base64Response<GetClubResponse>;
      return {
        id: base64Response.id,
        ownerUserId: base64Response.ownerUserId,
        created: base64Response.created,
        encryptedName: base64ToUint8Array(base64Response.encryptedName),
        encryptedDescription: base64Response.encryptedDescription
          ? base64ToUint8Array(base64Response.encryptedDescription)
          : undefined,
        encryptedProfilePicture: base64Response.encryptedProfilePicture
          ? base64ToUint8Array(base64Response.encryptedProfilePicture)
          : undefined,
        encryptionIv: base64ToUint8Array(base64Response.encryptionIv),
        isPublic: base64Response.isPublic,
        membersCanPost: base64Response.membersCanPost,
        membersCanInvite: base64Response.membersCanInvite,
        maxMembers: base64Response.maxMembers,
        memberCount: base64Response.memberCount,
      };
    });
  }

  async updateClubAsync(request: UpdateClubRequest): Promise<ApiResult<void>> {
    return this.getApiResultAsync(async () => {
      const response = await fetch(`${this.baseUrl}club/${request.clubId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: stringify(request),
      });
      this.ensureSuccessStatusCode(response);
    });
  }

  async deleteClubAsync(request: DeleteClubRequest): Promise<ApiResult<void>> {
    return this.getApiResultAsync(async () => {
      const response = await fetch(`${this.baseUrl}club/${request.clubId}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: stringify(request),
      });
      this.ensureSuccessStatusCode(response);
    });
  }

  async searchClubsAsync(
    request: SearchClubsRequest,
  ): Promise<ApiResult<SearchClubsResponse>> {
    return this.getApiResultAsync(async () => {
      const response = await fetch(`${this.baseUrl}club/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: stringify(request),
      });
      this.ensureSuccessStatusCode(response);
      const base64Response =
        (await response.json()) as Base64Response<SearchClubsResponse>;
      return {
        clubs: base64Response.clubs.map((club) => ({
          id: club.id,
          ownerUserId: club.ownerUserId,
          created: club.created,
          encryptedName: base64ToUint8Array(club.encryptedName),
          encryptedDescription: club.encryptedDescription
            ? base64ToUint8Array(club.encryptedDescription)
            : undefined,
          encryptedProfilePicture: club.encryptedProfilePicture
            ? base64ToUint8Array(club.encryptedProfilePicture)
            : undefined,
          encryptionIv: base64ToUint8Array(club.encryptionIv),
          isPublic: club.isPublic,
          membersCanPost: club.membersCanPost,
          membersCanInvite: club.membersCanInvite,
          maxMembers: club.maxMembers,
          memberCount: club.memberCount,
        })),
        total: base64Response.total,
      };
    });
  }

  async getMyClubsAsync(
    request: GetMyClubsRequest,
  ): Promise<ApiResult<GetMyClubsResponse>> {
    return this.getApiResultAsync(async () => {
      const response = await fetch(`${this.baseUrl}club/my-clubs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: stringify(request),
      });
      this.ensureSuccessStatusCode(response);
      const base64Response =
        (await response.json()) as Base64Response<GetMyClubsResponse>;
      return {
        clubs: base64Response.clubs.map((club) => ({
          id: club.id,
          ownerUserId: club.ownerUserId,
          created: club.created,
          encryptedName: base64ToUint8Array(club.encryptedName),
          encryptedDescription: club.encryptedDescription
            ? base64ToUint8Array(club.encryptedDescription)
            : undefined,
          encryptedProfilePicture: club.encryptedProfilePicture
            ? base64ToUint8Array(club.encryptedProfilePicture)
            : undefined,
          encryptionIv: base64ToUint8Array(club.encryptionIv),
          isPublic: club.isPublic,
          membersCanPost: club.membersCanPost,
          membersCanInvite: club.membersCanInvite,
          maxMembers: club.maxMembers,
          memberCount: club.memberCount,
        })),
      };
    });
  }

  // Membership operations

  async getClubMembersAsync(
    request: GetClubMembersRequest,
  ): Promise<ApiResult<GetClubMembersResponse>> {
    return this.getApiResultAsync(async () => {
      const response = await fetch(
        `${this.baseUrl}club/${request.clubId}/members`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: stringify(request),
        },
      );
      this.ensureSuccessStatusCode(response);
      const base64Response =
        (await response.json()) as Base64Response<GetClubMembersResponse>;
      return {
        members: base64Response.members.map((member) => ({
          id: member.id,
          clubId: member.clubId,
          userId: member.userId,
          joined: member.joined,
          role: member.role,
          encryptedAesKey: base64ToUint8Array(member.encryptedAesKey),
        })),
      };
    });
  }

  async inviteToClubAsync(request: InviteToClubRequest): Promise<ApiResult<void>> {
    return this.getApiResultAsync(async () => {
      const response = await fetch(
        `${this.baseUrl}club/${request.clubId}/invite`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: stringify(request),
        },
      );
      this.ensureSuccessStatusCode(response);
    });
  }

  async joinPublicClubAsync(
    request: JoinPublicClubRequest,
  ): Promise<ApiResult<void>> {
    return this.getApiResultAsync(async () => {
      const response = await fetch(`${this.baseUrl}club/${request.clubId}/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: stringify(request),
      });
      this.ensureSuccessStatusCode(response);
    });
  }

  async acceptClubInviteAsync(
    request: AcceptClubInviteRequest,
  ): Promise<ApiResult<void>> {
    return this.getApiResultAsync(async () => {
      // This would typically be handled through the inbox system
      // For now, this is a placeholder
      throw new Error('Not implemented - use inbox system');
    });
  }

  async leaveClubAsync(request: LeaveClubRequest): Promise<ApiResult<void>> {
    return this.getApiResultAsync(async () => {
      const response = await fetch(
        `${this.baseUrl}club/${request.clubId}/leave`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: stringify(request),
        },
      );
      this.ensureSuccessStatusCode(response);
    });
  }

  async removeClubMemberAsync(
    request: RemoveClubMemberRequest,
  ): Promise<ApiResult<void>> {
    return this.getApiResultAsync(async () => {
      const response = await fetch(
        `${this.baseUrl}club/${request.clubId}/member/${request.memberUserId}`,
        {
          method: 'DELETE',
          headers: { 'Content-Type': 'application/json' },
          body: stringify(request),
        },
      );
      this.ensureSuccessStatusCode(response);
    });
  }

  async updateMemberRoleAsync(
    request: UpdateMemberRoleRequest,
  ): Promise<ApiResult<void>> {
    return this.getApiResultAsync(async () => {
      const response = await fetch(
        `${this.baseUrl}club/${request.clubId}/member/${request.memberUserId}/role`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: stringify(request),
        },
      );
      this.ensureSuccessStatusCode(response);
    });
  }

  // Event/Feed operations

  async postClubEventAsync(request: PostClubEventRequest): Promise<ApiResult<void>> {
    return this.getApiResultAsync(async () => {
      const response = await fetch(
        `${this.baseUrl}club/${request.clubId}/event`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: stringify(request),
        },
      );
      this.ensureSuccessStatusCode(response);
    });
  }

  async getClubEventsAsync(
    request: GetClubEventsRequest,
  ): Promise<ApiResult<GetClubEventsResponse>> {
    return this.getApiResultAsync(async () => {
      const response = await fetch(
        `${this.baseUrl}club/${request.clubId}/events`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: stringify(request),
        },
      );
      this.ensureSuccessStatusCode(response);
      const base64Response =
        (await response.json()) as Base64Response<GetClubEventsResponse>;
      return {
        events: base64Response.events.map((event) => ({
          id: event.id,
          clubId: event.clubId,
          userId: event.userId,
          timestamp: event.timestamp,
          expiry: event.expiry,
          encryptedEvent: base64ToUint8Array(event.encryptedEvent),
          encryptionIv: base64ToUint8Array(event.encryptionIv),
        })),
      };
    });
  }

  // Private helper methods

  private async getApiResultAsync<T>(
    action: () => Promise<T>,
  ): Promise<ApiResult<T>> {
    try {
      const data = await action();
      return new ApiResult<T>(data);
    } catch (error) {
      if (error instanceof ResponseError) {
        const response = error.response;
        console.debug('Error response', response, await response.text());
        const status = response.status;

        if (status === 404) {
          return ApiResult.fromError({
            type: ApiErrorType.NotFound,
            message: response.statusText,
            exception: error,
          });
        } else if (status === 401) {
          return ApiResult.fromError({
            type: ApiErrorType.Unauthorized,
            message: response.statusText,
            exception: error,
          });
        } else if (status === 403) {
          return ApiResult.fromError({
            type: ApiErrorType.Unauthorized,
            message: 'Forbidden: Insufficient permissions',
            exception: error,
          });
        } else if (status === 429) {
          return ApiResult.fromError({
            type: ApiErrorType.RateLimited,
            message: response.statusText,
            exception: error,
          });
        }
      }

      return ApiResult.fromError({
        type: ApiErrorType.Unknown,
        message:
          (error as { message: string })?.message ||
          'An unknown error occurred',
        exception: error,
      });
    }
  }

  private ensureSuccessStatusCode(response: FetchResponse): void {
    if (!response.ok) {
      throw new ResponseError(response);
    }
  }
}

function stringify(value: unknown): string {
  return JSON.stringify(value, (key, val: unknown) => {
    if (val instanceof Uint8Array) {
      return uint8ArrayToBase64(val);
    }
    return val;
  });
}

function uint8ArrayToBase64(value: Uint8Array): string {
  return btoa(String.fromCharCode(...value));
}

function base64ToUint8Array(value: string): Uint8Array {
  return Uint8Array.from(atob(value), (c) => c.charCodeAt(0));
}
