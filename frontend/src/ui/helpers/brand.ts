import fallbackLogoUrl from '../../assets/mladis-connected-intelligence.png';

export function getConfiguredLogoUrl() {
  if (typeof document === 'undefined') {
    return fallbackLogoUrl;
  }

  const configuredUrl = document.querySelector<HTMLMetaElement>('meta[name="mladis-logo-url"]')?.content.trim();
  return configuredUrl || fallbackLogoUrl;
}

export { fallbackLogoUrl };
