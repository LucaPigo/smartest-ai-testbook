import type { HealthApi, TestCreationApi, ExecutionApi, ReportingApi, TestSuite } from './generated';

export type Api = { health: HealthApi; tests: TestCreationApi; execution: ExecutionApi; reporting: ReportingApi };
export type AppContext = { api: Api; suites: TestSuite[]; loaded: boolean; refreshSuites: () => Promise<void> };
