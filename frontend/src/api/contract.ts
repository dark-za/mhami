import type { paths } from "./generated-types";

export type BootstrapApiResponse = paths["/api/v1/bootstrap"]["get"]["responses"][200]["content"]["application/json"];

export type LoginRequest = paths["/api/v1/auth/login"]["post"]["requestBody"]["content"]["application/json"];

export type RegisterRequest = paths["/api/v1/auth/register"]["post"]["requestBody"]["content"]["application/json"];
