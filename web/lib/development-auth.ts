import { createHmac } from "node:crypto";

function encode(value: string): string {
  return Buffer.from(value).toString("base64url");
}

export function developmentToken(): string | undefined {
  if (process.env.CONSULTANT_DEV_TOKEN) return process.env.CONSULTANT_DEV_TOKEN;
  const secret = process.env.CONSULTANT_DEVELOPMENT_AUTH_SECRET;
  if (!secret) return undefined;
  const payload = encode(JSON.stringify({
    organization_id: process.env.CONSULTANT_DEMO_ORGANIZATION_ID ?? "00000000-0000-4000-8000-000000000001",
    user_id: process.env.CONSULTANT_DEMO_USER_ID ?? "00000000-0000-4000-8000-000000000002",
    display_name: "Local consultant",
  }));
  const signature = createHmac("sha256", secret).update(payload).digest("base64url");
  return `${payload}.${signature}`;
}
