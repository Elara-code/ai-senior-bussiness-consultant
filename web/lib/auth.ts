export function hasDevelopmentIdentity(): boolean {
  return Boolean(process.env.CONSULTANT_DEV_TOKEN);
}
