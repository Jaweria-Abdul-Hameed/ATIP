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

export interface GitHubUserProfileApi {
  login: string;
  name?: string | null;
  avatar_url?: string | null;
  html_url?: string | null;
  public_repos: number;
  total_private_repos: number;
}

export interface GitHubRepoItemApi {
  id: number;
  name: string;
  full_name: string;
  owner_login: string;
  default_branch: string;
  is_private: boolean;
  clone_url: string;
  html_url: string;
  language?: string | null;
  description?: string | null;
  updated_at?: string | null;
  is_connected: boolean;
}

export interface GitHubTokenConnectResponseApi {
  user: GitHubUserProfileApi;
  repositories: GitHubRepoItemApi[];
  installation_id: string;
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

export interface RiskFactorApiItem {
  factor_key: string;
  name: string;
  raw_value: any;
  normalized_score: number;
  weight: number;
  weighted_score: number;
  impact: "low" | "medium" | "high" | "critical";
  description: string;
  confidence: number;
  is_missing: boolean;
  missing_reason?: string | null;
}

export interface ChangeImpactNodeApiItem {
  file_path: string;
  depth: number;
  impact_score: number;
  is_direct: boolean;
  imported_by: string[];
  propagation_reason: string;
}

export interface FileRiskAssessmentApiItem {
  file_path: string;
  risk_score: number;
  risk_tier: "low" | "medium" | "high" | "critical";
  confidence: number;
  has_missing_data: boolean;
  missing_reasons: string[];
  factors: RiskFactorApiItem[];
  direct_dependents_count: number;
  transitive_dependents_count: number;
  churn_count: number;
  lines_changed: number;
  cyclomatic_complexity?: number | null;
  maintainability_index?: number | null;
  coverage_pct?: number | null;
  has_test_file: boolean;
  defect_commit_count: number;
  associated_tests: string[];
}

export interface RiskAssessmentSummaryApiItem {
  id: string;
  repository_id: string;
  commit_sha: string;
  branch: string;
  model_version: string;
  model_type: string;
  overall_score: number;
  risk_tier: "low" | "medium" | "high" | "critical";
  confidence: number;
  has_missing_data: boolean;
  feature_weights: Record<string, number>;
  summary_stats: {
    files_analyzed?: number;
    high_risk_count?: number;
    critical_risk_count?: number;
    missing_data_count?: number;
    avg_score?: number;
    top_risk_file?: string;
    top_risk_score?: number;
  };
  evaluated_at: string;
  files: FileRiskAssessmentApiItem[];
  impacted_nodes?: ChangeImpactNodeApiItem[];
}

export interface SelectedRegressionTestApiItem {
  test_file: string;
  test_identifier: string;
  priority: "critical" | "high" | "medium" | "low";
  selection_reason: string;
  target_file: string;
  depth: number;
  is_flaky_candidate: boolean;
  flakiness_score: number;
  flakiness_reasons: string[];
}

export interface TestGapApiItem {
  file_path: string;
  risk_score: number;
  severity: string;
  gap_type: string;
  impacted_dependents_count: number;
  recommendation: string;
}

export interface TestSelectionResultApiItem {
  repository_id: string;
  commit_sha: string;
  total_existing_tests_count: number;
  selected_tests_count: number;
  selected_tests: SelectedRegressionTestApiItem[];
  test_gaps_count: number;
  test_gaps: TestGapApiItem[];
  flaky_tests_count: number;
  flaky_tests: SelectedRegressionTestApiItem[];
  selection_ratio_pct: number;
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
    if (!headers.has("X-Reviewer-Fallback")) {
      headers.set("X-Reviewer-Fallback", "true");
    }

    const response = await fetch(url, {
      ...options,
      credentials: options.credentials || "include",
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
    github_installation_id?: string | null;
  }): Promise<RepositoryApiItem> {
    const res = await this.request<DataResponse<RepositoryApiItem>>("/repositories/connect", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return res.data;
  }

  async connectPublicRepository(payload: {
    url: string;
    branch?: string;
  }): Promise<RepositoryApiItem> {
    const res = await this.request<DataResponse<RepositoryApiItem>>("/repositories/connect-public-url", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return res.data;
  }

  async loginWithGitHubToken(token: string): Promise<GitHubTokenConnectResponseApi> {
    const res = await this.request<DataResponse<GitHubTokenConnectResponseApi>>("/github/token-login", {
      method: "POST",
      body: JSON.stringify({ token }),
    });
    return res.data;
  }

  async getGitHubUserRepos(installationId?: string): Promise<GitHubRepoItemApi[]> {
    const q = installationId ? `?installation_id=${installationId}` : "";
    const res = await this.request<DataResponse<GitHubRepoItemApi[]>>(`/github/user-repos${q}`);
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

  async getRepositoryRisks(
    repoId: string,
    params?: { commitSha?: string; branch?: string; forceRecompute?: boolean }
  ): Promise<RiskAssessmentSummaryApiItem> {
    const sp = new URLSearchParams();
    if (params?.commitSha) sp.set("commit_sha", params.commitSha);
    if (params?.branch) sp.set("branch", params.branch);
    if (params?.forceRecompute) sp.set("force_recompute", "true");
    const q = sp.toString() ? `?${sp.toString()}` : "";
    const res = await this.request<DataResponse<RiskAssessmentSummaryApiItem>>(
      `/repositories/${repoId}/risks${q}`
    );
    return res.data;
  }

  async evaluateRepositoryRisks(
    repoId: string,
    payload: { commit_sha?: string; branch?: string; force_recompute?: boolean }
  ): Promise<RiskAssessmentSummaryApiItem> {
    const res = await this.request<DataResponse<RiskAssessmentSummaryApiItem>>(
      `/repositories/${repoId}/risks/evaluate`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
    return res.data;
  }

  async getFileRiskDetail(
    repoId: string,
    filePath: string,
    commitSha?: string
  ): Promise<FileRiskAssessmentApiItem> {
    const q = commitSha ? `?commit_sha=${encodeURIComponent(commitSha)}` : "";
    const res = await this.request<DataResponse<FileRiskAssessmentApiItem>>(
      `/repositories/${repoId}/risks/files/${encodeURIComponent(filePath)}${q}`
    );
    return res.data;
  }

  async getChangeImpactPropagation(
    repoId: string,
    params?: { commitSha?: string; branch?: string }
  ): Promise<ChangeImpactNodeApiItem[]> {
    const sp = new URLSearchParams();
    if (params?.commitSha) sp.set("commit_sha", params.commitSha);
    if (params?.branch) sp.set("branch", params.branch);
    const q = sp.toString() ? `?${sp.toString()}` : "";
    const res = await this.request<DataResponse<ChangeImpactNodeApiItem[]>>(
      `/repositories/${repoId}/risks/impact${q}`
    );
    return res.data;
  }

  async getImpactedTestSelection(
    repoId: string,
    commitSha?: string
  ): Promise<TestSelectionResultApiItem> {
    const q = commitSha ? `?commit_sha=${encodeURIComponent(commitSha)}` : "";
    const res = await this.request<DataResponse<TestSelectionResultApiItem>>(
      `/repositories/${repoId}/risks/test-selection${q}`
    );
    return res.data;
  }
}

export const apiClient = new ApiClient();
