export type AgentScope = {
  value: string;
  status: string;
};

export type AgentGrant = {
  id: string;
  company: string;
  user: string;
  client_name: string;
  client_fingerprint: string;
  scopes: string[];
  status: string;
  active: boolean;
  expires_at: string;
  revoked_at: string | null;
  created_at: string;
  updated_at: string;
};

export type AgentActionLog = {
  id: string;
  grant: string;
  company: string;
  request_id: string;
  tool_name: string;
  required_scope: string;
  idempotency_key: string;
  arguments_hash: string;
  status: string;
  result: Record<string, unknown>;
  error_code: string;
  created_at: string;
  updated_at: string;
};

export type CompanyMemberOption = {
  id: string;
  label: string;
  detail: string;
};
