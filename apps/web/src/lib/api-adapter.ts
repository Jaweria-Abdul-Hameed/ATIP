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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const USE_FIXTURES = process.env.NEXT_PUBLIC_ENABLE_DEMO_FIXTURES !== "false";

export const api = {
  getUser: async (): Promise<User> => {
    if (USE_FIXTURES) return DEMO_USER;
    const res = await fetch(`${API_BASE_URL}/me`);
    if (!res.ok) throw new Error("Failed to fetch user");
    return res.json();
  },

  getRepositories: async (): Promise<Repository[]> => {
    if (USE_FIXTURES) return DEMO_REPOSITORIES;
    const res = await fetch(`${API_BASE_URL}/repositories`);
    if (!res.ok) throw new Error("Failed to fetch repositories");
    return res.json();
  },

  getRepository: async (id: string): Promise<Repository | undefined> => {
    if (USE_FIXTURES) {
      return DEMO_REPOSITORIES.find((r) => r.id === id) || DEMO_REPOSITORIES[0];
    }
    const res = await fetch(`${API_BASE_URL}/repositories/${id}`);
    if (!res.ok) throw new Error("Failed to fetch repository");
    return res.json();
  },

  getCommits: async (_repoId?: string): Promise<CommitItem[]> => {
    if (USE_FIXTURES) return DEMO_COMMITS;
    return DEMO_COMMITS;
  },

  getRiskyFiles: async (_repoId?: string): Promise<RiskyFile[]> => {
    if (USE_FIXTURES) return DEMO_RISK_FILES;
    return DEMO_RISK_FILES;
  },

  getWhiteBoxMatrix: async (_repoId?: string): Promise<WhiteBoxMatrixRow[]> => {
    if (USE_FIXTURES) return DEMO_WHITE_BOX_MATRIX;
    return DEMO_WHITE_BOX_MATRIX;
  },

  getMCDCProof: async (): Promise<MCDCPairProof> => {
    if (USE_FIXTURES) return DEMO_MCDC_PROOF;
    return DEMO_MCDC_PROOF;
  },

  getTestPlans: async (_repoId?: string): Promise<TestPlanItem[]> => {
    if (USE_FIXTURES) return DEMO_TEST_PLANS;
    return DEMO_TEST_PLANS;
  },

  getTestRuns: async (_repoId?: string): Promise<TestRunItem[]> => {
    if (USE_FIXTURES) return DEMO_TEST_RUNS;
    return DEMO_TEST_RUNS;
  },

  getTestRun: async (id: string): Promise<TestRunItem | undefined> => {
    if (USE_FIXTURES) {
      return DEMO_TEST_RUNS.find((r) => r.id === id) || DEMO_TEST_RUNS[0];
    }
    const res = await fetch(`${API_BASE_URL}/test-runs/${id}`);
    if (!res.ok) throw new Error("Failed to fetch test run");
    return res.json();
  },

  getAIInvestigation: async (): Promise<AIAnalysisInvestigation> => {
    if (USE_FIXTURES) return DEMO_AI_INVESTIGATION;
    return DEMO_AI_INVESTIGATION;
  },
};
