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

  async post<T>(path: string, body: unknown): Promise<T> {
    const response = await fetch(this.url(path), {
      method: 'POST',
      credentials: this.options.credentials ?? 'include',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': this.csrfToken(),
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      let message = `POST ${path} failed with ${response.status}`;
      try {
        const payload = await response.json();
        message = typeof payload === 'object' && payload !== null ? JSON.stringify(payload) : message;
      } catch {
        // Keep the default status message when the server returns non-JSON.
      }
      throw new Error(message);
    }

    return (await response.json()) as T;
  }

  async postForm<T>(path: string, body: FormData): Promise<T> {
    const response = await fetch(this.url(path), {
      method: 'POST',
      credentials: this.options.credentials ?? 'include',
      headers: {
        Accept: 'application/json',
        'X-CSRFToken': this.csrfToken(),
      },
      body,
    });

    if (!response.ok) {
      let message = `POST ${path} failed with ${response.status}`;
      try {
        const payload = await response.json();
        message = JSON.stringify(payload);
      } catch {
        // Keep the default status message when the server returns non-JSON.
      }
      throw new Error(message);
    }

    return (await response.json()) as T;
  }

  async delete<T>(path: string, body: unknown): Promise<T> {
    const response = await fetch(this.url(path), {
      method: 'DELETE',
      credentials: this.options.credentials ?? 'include',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': this.csrfToken(),
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`DELETE ${path} failed with ${response.status}`);
    }

    return (await response.json()) as T;
  }

  private url(path: string): string {
    const normalizedBase = this.options.baseUrl.replace(/\/$/, '');
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    return `${normalizedBase}${normalizedPath}`;
  }

  private csrfToken(): string {
    const meta = document.querySelector<HTMLMetaElement>('meta[name="csrf-token"]')?.content;
    if (meta) return meta;
    const cookie = document.cookie.split('; ').find((row) => row.startsWith('csrftoken='));
    return cookie ? decodeURIComponent(cookie.split('=')[1]) : '';
  }
}
