export const GITHUB_REPO_URL = 'https://github.com/Forza-Love/fh6-virtual_tcu'

export function githubReleaseUrl(version: string): string {
  const tag = version.startsWith('v') ? version : `v${version}`
  return `${GITHUB_REPO_URL}/releases/tag/${tag}`
}
