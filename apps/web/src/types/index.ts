export type SeverityLevel = "low" | "medium" | "high" | "critical";

export interface User {
  id: string;
  name: string;
  email: string;
  avatarUrl?: string;
  workspaceName: string;
}

export interface Repository {
  id: string;
  name: string;
  fullName: string;
  defaultBranch: string;
  lastSynced: string;
  status: "connected" | "syncing" | "ready" | "review";
  riskScore: number;
  testCount: number;
  fileCount: number;
  coveragePercent: number;
}

export interface CommitItem {
  hash: string;
  shortHash: string;
  message: string;
  author: string;
  timestamp: string;
  branch: string;
}

export interface RiskyFile {
  id: string;
  filePath: string;
  riskScore: number;
  severity: SeverityLevel;
  riskFactors: string;
  lastChanged: string;
  coveragePercent: number;
  changeFrequency: "Low" | "Medium" | "High";
  reasons: string[];
}

export type WhiteBoxTechniqueKind =
  | "statement"
  | "branch"
  | "condition"
  | "mcdc"
  | "basis_path"
  | "loop"
  | "def_use"
  | "exception"
  | "boundary"
  | "mutation"
  | "regression";

export type ObjectiveStatus =
  | "covered"
  | "partial"
  | "uncovered"
  | "unknown"
  | "unsupported"
  | "proven_infeasible";

export interface WhiteBoxMatrixRow {
  technique: string;
  kind: WhiteBoxTechniqueKind;
  totalObjectives: number;
  coveredCount: number | string;
  status: "Covered" | "Partial" | "Unverified" | "Unknown" | "Unsupported";
  statusVariant: "success" | "warning" | "error" | "neutral";
  details?: string;
}

export interface MCDCPairProof {
  decisionExpr: string;
  sourceSpan: string;
  atomicCondition: string;
  conditionVectorT1: string;
  outcomeT1: string;
  conditionVectorT2: string;
  outcomeT2: string;
  test1Id: string;
  test2Id: string;
  method: "unique_cause" | "masking";
  verified: boolean;
}

export interface TestCaseItem {
  id: string;
  title: string;
  priority: "Low" | "Medium" | "High";
  type: "Unit" | "Integration" | "E2E" | "Property";
  targetComponent: string;
  selected?: boolean;
}

export interface TestPlanItem {
  id: string;
  title: string;
  repoName: string;
  selectedTestsCount: number;
  proposedTestsCount: number;
  createdAt: string;
  status: "draft" | "awaiting_review" | "approved" | "rejected";
  testCases: TestCaseItem[];
}

export interface TestRunItem {
  id: string;
  runNumber: string;
  repoName: string;
  branch: string;
  totalTests: number;
  passedCount: number;
  failedCount: number;
  skippedCount: number;
  duration: string;
  status: "Passed" | "Failed" | "Running" | "Queued" | "Cancelled";
  timestamp: string;
  testResults: {
    id: string;
    fileName: string;
    testCount: number;
    duration: string;
    passed: boolean;
  }[];
}

export interface AIAnalysisInvestigation {
  id: string;
  title: string;
  runId: string;
  status: "completed" | "in_progress";
  messages: {
    sender: "user" | "atip";
    text: string;
    isHypothesis?: boolean;
    citations?: string[];
  }[];
}
