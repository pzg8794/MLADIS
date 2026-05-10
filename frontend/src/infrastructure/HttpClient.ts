export interface HttpClientOptions {
  baseUrl: string;
  credentials?: RequestCredentials;
}

export class HttpClient {
  constructor(private readonly options: HttpClientOptions) {}

  async get<T>(path: string): Promise<T> {
    const response = await fetch(this.url(path), {
      credentials: this.options.credentials ?? 'include',
      headers: { Accept: 'application/json' },
    });

    if (!response.ok) {
      throw new Error(`GET ${path} failed with ${response.status}`);
    }

    return (await response.json()) as T;
  }

  private url(path: string): string {
    const normalizedBase = this.options.baseUrl.replace(/\/$/, '');
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    return `${normalizedBase}${normalizedPath}`;
  }
}
