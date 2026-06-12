export const GITHUB_REPO_URL = 'https://github.com/qq00qq00/fh6-virtual_tcu_evolution'

export function githubReleaseUrl(version: string): string {
  const tag = version.startsWith('v') ? version : `v${version}`
  return `${GITHUB_REPO_URL}/releases/tag/${tag}`
}
