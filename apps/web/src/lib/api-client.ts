/**
 * Typed HTTP client for ATIP FastAPI modular monolith backend.
 * Handles standard response envelopes, request IDs, and error envelopes.
 */

export interface ResponseMeta {
  request_id?: string;
  timestamp: string;
}

export interface PaginationMetadata {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface DataResponse<T> {
  data: T;
  meta: ResponseMeta;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: PaginationMetadata;
  meta: ResponseMeta;
}

export interface ApiErrorPayload {
  code: string;
  message: string;
  details?: Array<{ loc?: Array<string | number>; msg: string; type?: string }>;
  request_id?: string;
}

export interface ApiErrorEnvelope {
  error: ApiErrorPayload;
}

export class ApiClientError extends Error {
  code: string;
  status: number;
  details?: Array<{ loc?: Array<string | number>; msg: string; type?: string }>;
  requestId?: string;

  constructor(status: number, payload: ApiErrorPayload) {
    super(payload.message || `API Error: HTTP ${status}`);
    this.name = "ApiClientError";
    this.status = status;
    this.code = payload.code || "API_ERROR";
    this.details = payload.details;
    this.requestId = payload.request_id;
  }
}

export interface RepositoryApiItem {
  id: string;
  name: string;
  full_name: string;
  default_branch: string;
  is_private: boolean;
  clone_url: string;
  language?: string | null;
  last_synced_at?: string | null;
  created_at: string;
}

export interface UserProfileApi {
  id: string;
  email: string;
  name: string;
  avatar_url?: string | null;
  is_active: boolean;
  organizations: Array<{
    id: string;
    slug: string;
    name: string;
    role: string;
  }>;
}

const DEFAULT_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = DEFAULT_API_URL) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = endpoint.startsWith("http") ? endpoint : `${this.baseUrl}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;
    const headers = new Headers(options.headers);

    if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorPayload: ApiErrorPayload;
      try {
        const body: ApiErrorEnvelope = await response.json();
        errorPayload = body.error || { code: "HTTP_ERROR", message: response.statusText };
      } catch {
        errorPayload = { code: "HTTP_ERROR", message: `HTTP ${response.status}: ${response.statusText}` };
      }
      throw new ApiClientError(response.status, errorPayload);
    }

    return response.json();
  }

  // Probe & Health
  async getHealth(): Promise<{ status: string; version: string; environment: string }> {
    const rootUrl = this.baseUrl.replace(/\/api\/v1$/, "");
    const res = await this.request<DataResponse<{ status: string; version: string; environment: string }>>(
      `${rootUrl}/healthz`
    );
    return res.data;
  }

  // Identity
  async getMe(): Promise<UserProfileApi> {
    const res = await this.request<DataResponse<UserProfileApi>>("/me");
    return res.data;
  }

  // Repositories
  async getRepositories(params?: { page?: number; page_size?: number }): Promise<PaginatedResponse<RepositoryApiItem>> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set("page", params.page.toString());
    if (params?.page_size) searchParams.set("page_size", params.page_size.toString());
    const query = searchParams.toString() ? `?${searchParams.toString()}` : "";
    return this.request<PaginatedResponse<RepositoryApiItem>>(`/repositories${query}`);
  }

  async getRepository(id: string): Promise<RepositoryApiItem> {
    const res = await this.request<DataResponse<RepositoryApiItem>>(`/repositories/${id}`);
    return res.data;
  }

  async syncRepository(id: string): Promise<{ repository_id: string; job_id: string; status: string }> {
    const res = await this.request<DataResponse<{ repository_id: string; job_id: string; status: string }>>(
      `/repositories/${id}/sync`,
      { method: "POST" }
    );
    return res.data;
  }
}

export const apiClient = new ApiClient();
