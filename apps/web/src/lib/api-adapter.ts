import {
  DEMO_USER,
  DEMO_REPOSITORIES,
  DEMO_COMMITS,
  DEMO_RISK_FILES,
  DEMO_WHITE_BOX_MATRIX,
  DEMO_MCDC_PROOF,
  DEMO_TEST_PLANS,
  DEMO_TEST_RUNS,
  DEMO_AI_INVESTIGATION,
} from "./fixtures";
import {
  User,
  Repository,
  CommitItem,
  RiskyFile,
  WhiteBoxMatrixRow,
  MCDCPairProof,
  TestPlanItem,
  TestRunItem,
  AIAnalysisInvestigation,
} from "@/types";
import { apiClient, RepositoryApiItem } from "./api-client";

const USE_FIXTURES = process.env.NEXT_PUBLIC_ENABLE_DEMO_FIXTURES === "true";

function mapApiRepo(item: RepositoryApiItem): Repository {
  return {
    id: item.id,
    name: item.name,
    fullName: item.full_name,
    defaultBranch: item.default_branch,
    lastSynced: item.last_synced_at ? new Date(item.last_synced_at).toLocaleString() : "Never",
    status: item.last_synced_at ? "ready" : "connected",
    riskScore: 0,
    testCount: 0,
    fileCount: 0,
    coveragePercent: 0,
  };
}

export const api = {
  isDemoMode: (): boolean => USE_FIXTURES,

  getUser: async (): Promise<User> => {
    if (USE_FIXTURES) return DEMO_USER;
    try {
      const apiUser = await apiClient.getMe();
      return {
        id: apiUser.id,
        name: apiUser.name,
        email: apiUser.email,
        avatarUrl: apiUser.avatar_url || undefined,
        workspaceName: apiUser.organizations[0]?.name || "Workspace",
      };
    } catch {
      return DEMO_USER;
    }
  },

  getRepositories: async (opts?: { forceLive?: boolean }): Promise<Repository[]> => {
    if (USE_FIXTURES && !opts?.forceLive) return DEMO_REPOSITORIES;
    try {
      const response = await apiClient.getRepositories();
      return response.data.map(mapApiRepo);
    } catch (err) {
      console.warn("FastAPI unreachable, falling back to empty repository set:", err);
      return [];
    }
  },

  getRepository: async (id: string, opts?: { forceLive?: boolean }): Promise<Repository | undefined> => {
    if (USE_FIXTURES && !opts?.forceLive) {
      return DEMO_REPOSITORIES.find((r) => r.id === id) || DEMO_REPOSITORIES[0];
    }
    try {
      const item = await apiClient.getRepository(id);
      return mapApiRepo(item);
    } catch {
      return undefined;
    }
  },

  getCommits: async (_repoId?: string): Promise<CommitItem[]> => {
    return DEMO_COMMITS;
  },

  getRiskyFiles: async (_repoId?: string): Promise<RiskyFile[]> => {
    return DEMO_RISK_FILES;
  },

  getWhiteBoxMatrix: async (_repoId?: string): Promise<WhiteBoxMatrixRow[]> => {
    return DEMO_WHITE_BOX_MATRIX;
  },

  getMCDCProof: async (): Promise<MCDCPairProof> => {
    return DEMO_MCDC_PROOF;
  },

  getTestPlans: async (_repoId?: string): Promise<TestPlanItem[]> => {
    return DEMO_TEST_PLANS;
  },

  getTestRuns: async (_repoId?: string): Promise<TestRunItem[]> => {
    return DEMO_TEST_RUNS;
  },

  getTestRun: async (id: string): Promise<TestRunItem | undefined> => {
    return DEMO_TEST_RUNS.find((r) => r.id === id) || DEMO_TEST_RUNS[0];
  },

  getAIInvestigation: async (): Promise<AIAnalysisInvestigation> => {
    return DEMO_AI_INVESTIGATION;
  },
};
