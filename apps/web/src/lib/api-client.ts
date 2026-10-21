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

export interface OrganizationApiItem {
  id: string;
  slug: string;
  name: string;
  billing_tier: string;
  role?: string | null;
  created_at: string;
}

export interface MemberApiItem {
  id: string;
  user_id: string;
  email: string;
  name: string;
  avatar_url?: string | null;
  role: string;
  created_at: string;
}

export interface GitHubInstallationApiItem {
  id: string;
  organization_id: string;
  installation_id: number;
  account_login: string;
  account_id: number;
  target_type: string;
  repository_selection: string;
  is_active: boolean;
  created_at: string;
}

export interface DiscoveredRepositoryApiItem {
  github_repo_id: number;
  name: string;
  full_name: string;
  default_branch: string;
  is_private: boolean;
  clone_url: string;
  language?: string | null;
  is_connected: boolean;
}

export interface BranchApiItem {
  name: string;
  commit_sha: string;
  is_default: boolean;
}

export interface PullRequestApiItem {
  number: number;
  title: string;
  state: string;
  head_branch: string;
  head_sha: string;
  base_branch: string;
  author: string;
  created_at: string;
  updated_at: string;
}

export interface CommitApiItem {
  id: string;
  repository_id: string;
  organization_id: string;
  commit_sha: string;
  tree_sha?: string | null;
  parent_shas?: string[] | null;
  author_name?: string | null;
  author_email?: string | null;
  committer_name?: string | null;
  committer_email?: string | null;
  committed_at?: string | null;
  summary?: string | null;
  message: string;
  insertions: number;
  deletions: number;
  files_changed_count: number;
}

export interface SnapshotTreeApiItem {
  path: string;
  type: string;
  size_bytes: number;
  sha: string;
}

export interface DependencyNodeApiItem {
  id: string;
  file_path: string;
  fan_in: number;
  fan_out: number;
  dependencies: string[];
  dependents: string[];
}

export interface DependencyEdgeApiItem {
  source: string;
  target: string;
  target_module: string;
  target_file?: string | null;
  is_external: boolean;
  import_type: string;
  line: number;
}

export interface DependencyGraphApiItem {
  commit_sha: string;
  total_nodes: number;
  total_edges: number;
  internal_edges_count: number;
  external_edges_count: number;
  circular_cycles: string[][];
  nodes: DependencyNodeApiItem[];
  edges: DependencyEdgeApiItem[];
}

export interface CoverageFileApiDetail {
  file_path: string;
  statements_total: number;
  statements_covered: number;
  coverage_pct: number;
  covered_lines: number[];
  uncovered_lines: number[];
}

export interface CoverageSummaryApiItem {
  format_type: string;
  statements_total: number;
  statements_covered: number;
  statement_coverage_pct: number;
  branches_total: number;
  branches_covered: number;
  branch_coverage_pct: number;
  files_count: number;
  files: Record<string, CoverageFileApiDetail>;
}

export interface FileComplexityApiItem {
  file_path: string;
  language: string;
  lines_total: number;
  lines_code: number;
  lines_comments: number;
  lines_blank: number;
  cyclomatic_complexity: number;
  average_function_complexity: number;
  max_function_complexity: number;
  maintainability_index: number;
  functions: Array<{
    name: string;
    line_start: number;
    line_end: number;
    complexity: number;
    arg_count: number;
  }>;
}

export interface AnalysisJobApiItem {
  id: string;
  repository_id: string;
  status: string;
  progress_pct: number;
  current_step: string;
  commit_sha: string;
  error_message?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface AnalysisRunApiItem {
  id: string;
  repository_id: string;
  commit_sha: string;
  branch: string;
  job_id?: string | null;
  status: string;
  total_files: number;
  total_lines: number;
  languages_json?: Record<string, { files: number; lines: number }> | null;
  complexity_summary?: {
    analyzed_files_count: number;
    average_cyclomatic_complexity: number;
    average_maintainability_index: number;
    highest_complexity_files?: any[];
  } | null;
  test_inventory?: Array<{
    file_path: string;
    suite_name: string;
    test_name: string;
    line_number: number;
    framework: string;
    language: string;
  }> | null;
  coverage_summary?: CoverageSummaryApiItem | null;
  dependency_count: number;
  completed_at?: string | null;
  created_at: string;
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

  async discoverRepositories(query?: string): Promise<PaginatedResponse<DiscoveredRepositoryApiItem>> {
    const searchParams = new URLSearchParams();
    if (query) searchParams.set("query", query);
    const q = searchParams.toString() ? `?${searchParams.toString()}` : "";
    return this.request<PaginatedResponse<DiscoveredRepositoryApiItem>>(`/repositories/discover${q}`);
  }

  async connectRepository(payload: {
    github_repo_id: number;
    name: string;
    full_name: string;
    default_branch: string;
    is_private: boolean;
    clone_url: string;
    language?: string | null;
  }): Promise<RepositoryApiItem> {
    const res = await this.request<DataResponse<RepositoryApiItem>>("/repositories/connect", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return res.data;
  }

  async getRepositoryBranches(id: string): Promise<BranchApiItem[]> {
    const res = await this.request<DataResponse<BranchApiItem[]>>(`/repositories/${id}/branches`);
    return res.data;
  }

  async getRepositoryPullRequests(id: string): Promise<PullRequestApiItem[]> {
    const res = await this.request<DataResponse<PullRequestApiItem[]>>(`/repositories/${id}/pull-requests`);
    return res.data;
  }

  // Organizations & RBAC
  async getOrganizations(): Promise<PaginatedResponse<OrganizationApiItem>> {
    return this.request<PaginatedResponse<OrganizationApiItem>>("/organizations");
  }

  async getOrganization(id: string): Promise<OrganizationApiItem> {
    const res = await this.request<DataResponse<OrganizationApiItem>>(`/organizations/${id}`);
    return res.data;
  }

  async getOrganizationMembers(orgId: string): Promise<MemberApiItem[]> {
    const res = await this.request<DataResponse<MemberApiItem[]>>(`/organizations/${orgId}/members`);
    return res.data;
  }

  async inviteMember(orgId: string, email: string, role: string): Promise<MemberApiItem> {
    const res = await this.request<DataResponse<MemberApiItem>>(`/organizations/${orgId}/invitations`, {
      method: "POST",
      body: JSON.stringify({ email, role }),
    });
    return res.data;
  }

  async updateMemberRole(orgId: string, userId: string, role: string): Promise<MemberApiItem> {
    const res = await this.request<DataResponse<MemberApiItem>>(`/organizations/${orgId}/members/${userId}`, {
      method: "PATCH",
      body: JSON.stringify({ role }),
    });
    return res.data;
  }

  async removeMember(orgId: string, userId: string): Promise<{ message: string }> {
    const res = await this.request<DataResponse<{ message: string }>>(`/organizations/${orgId}/members/${userId}`, {
      method: "DELETE",
    });
    return res.data;
  }

  // GitHub App
  async getGitHubInstallations(): Promise<GitHubInstallationApiItem[]> {
    const res = await this.request<DataResponse<GitHubInstallationApiItem[]>>("/github/installations");
    return res.data;
  }

  async getGitHubInstallUrl(): Promise<string> {
    const res = await this.request<DataResponse<{ install_url: string }>>("/github/install-url");
    return res.data.install_url;
  }

  // Mining & Analysis endpoints
  async getRepositoryCommits(
    repoId: string,
    params?: { branch?: string; page?: number; page_size?: number }
  ): Promise<PaginatedResponse<CommitApiItem>> {
    const sp = new URLSearchParams();
    if (params?.branch) sp.set("branch", params.branch);
    if (params?.page) sp.set("page", params.page.toString());
    if (params?.page_size) sp.set("page_size", params.page_size.toString());
    const q = sp.toString() ? `?${sp.toString()}` : "";
    return this.request<PaginatedResponse<CommitApiItem>>(`/repositories/${repoId}/commits${q}`);
  }

  async getRepositorySnapshotTree(repoId: string, commitSha: string): Promise<SnapshotTreeApiItem[]> {
    const res = await this.request<DataResponse<SnapshotTreeApiItem[]>>(
      `/repositories/${repoId}/snapshots/${commitSha}/tree`
    );
    return res.data;
  }

  async getRepositorySnapshotFile(
    repoId: string,
    commitSha: string,
    path: string
  ): Promise<{ content: string; is_binary: boolean }> {
    const res = await this.request<DataResponse<{ content: string; is_binary: boolean }>>(
      `/repositories/${repoId}/snapshots/${commitSha}/files/${path}`
    );
    return res.data;
  }

  async getRepositoryDependencies(repoId: string, commitSha?: string): Promise<DependencyGraphApiItem> {
    const q = commitSha ? `?commit_sha=${encodeURIComponent(commitSha)}` : "";
    const res = await this.request<DataResponse<DependencyGraphApiItem>>(
      `/repositories/${repoId}/dependencies${q}`
    );
    return res.data;
  }

  async getRepositoryCoverage(repoId: string, commitSha?: string): Promise<CoverageSummaryApiItem | null> {
    const q = commitSha ? `?commit_sha=${encodeURIComponent(commitSha)}` : "";
    const res = await this.request<DataResponse<CoverageSummaryApiItem | null>>(
      `/repositories/${repoId}/coverage${q}`
    );
    return res.data;
  }

  async getRepositoryComplexity(
    repoId: string,
    commitSha?: string,
    filePath?: string
  ): Promise<FileComplexityApiItem[]> {
    const sp = new URLSearchParams();
    if (commitSha) sp.set("commit_sha", commitSha);
    if (filePath) sp.set("file_path", filePath);
    const q = sp.toString() ? `?${sp.toString()}` : "";
    const res = await this.request<DataResponse<FileComplexityApiItem[]>>(
      `/repositories/${repoId}/complexity${q}`
    );
    return res.data;
  }

  async triggerRepositoryAnalysis(
    repoId: string,
    payload: { commit_sha?: string; branch?: string; force_rerun?: boolean }
  ): Promise<AnalysisJobApiItem> {
    const res = await this.request<DataResponse<AnalysisJobApiItem>>(`/repositories/${repoId}/analyses`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return res.data;
  }

  async getAnalysisJob(id: string): Promise<AnalysisJobApiItem> {
    const res = await this.request<DataResponse<AnalysisJobApiItem>>(`/analyses/${id}`);
    return res.data;
  }

  async getRepositoryAnalyses(
    repoId: string,
    params?: { page?: number; page_size?: number }
  ): Promise<PaginatedResponse<AnalysisRunApiItem>> {
    const sp = new URLSearchParams();
    if (params?.page) sp.set("page", params.page.toString());
    if (params?.page_size) sp.set("page_size", params.page_size.toString());
    const q = sp.toString() ? `?${sp.toString()}` : "";
    return this.request<PaginatedResponse<AnalysisRunApiItem>>(`/repositories/${repoId}/analyses${q}`);
  }
}

export const apiClient = new ApiClient();
