import Constants from "expo-constants";

import type { AccessCheck, AccessCheckCreate, CommunityReport } from "../types/contracts";

const configuredApiUrl =
  process.env.EXPO_PUBLIC_BUDDY_API_URL ||
  (Constants.expoConfig?.extra?.apiUrl as string | undefined) ||
  "";
const apiBaseUrl = configuredApiUrl ? trimSlash(configuredApiUrl) : "";

function trimSlash(value: string): string {
  return value.replace(/\/+$/, "");
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Buddy API returned ${response.status}`);
  }

  return (await response.json()) as T;
}

export const buddyApi = {
  hasLiveApi: true,

  async createCheck(payload: AccessCheckCreate): Promise<AccessCheck> {
    const draft = await requestJson<AccessCheck>("/checks/draft", {
      method: "POST",
      body: JSON.stringify(payload)
    });
    await requestJson<AccessCheck>(`/checks/${draft.id}/collect`, { method: "POST" });
    await requestJson(`/checks/${draft.id}/analyze`, { method: "POST" });
    return requestJson<AccessCheck>(`/checks/${draft.id}/finalize`, { method: "POST" });
  },

  async createDraft(payload: AccessCheckCreate): Promise<AccessCheck> {
    return requestJson<AccessCheck>("/checks/draft", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  async listChecks(): Promise<AccessCheck[]> {
    return requestJson<AccessCheck[]>("/checks");
  },

  async listCommunityReports(): Promise<CommunityReport[]> {
    return requestJson<CommunityReport[]>("/community-reports");
  }
};
