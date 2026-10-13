interface ApiResponse<T> {
  data: T | null;
  error: string | null;
}

const NETWORK_ERROR = "Couldn't reach the server. Check your connection.";

class ApiClient {
  private csrfRequest: Promise<string | null> | null = null;

  private getCookie(name: string): string | null {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      return parts.pop()?.split(";").shift() || null;
    }
    return null;
  }

  // Asks the server for a token, which also sets the cookie. Writes that land together share one request.
  private fetchCsrfToken(): Promise<string | null> {
    this.csrfRequest ??= fetch("/api/accounts/csrf/", { credentials: "same-origin" })
      .then(async (response) => (response.ok ? ((await response.json()).csrf_token as string) : null))
      .finally(() => {
        this.csrfRequest = null;
      });
    return this.csrfRequest;
  }

  // Django keeps the cookie current, rotating it on login, so it's read fresh
  // for every write rather than remembered here.
  private async csrfToken(refresh: boolean): Promise<string | null> {
    return (!refresh && this.getCookie("csrftoken")) || this.fetchCsrfToken();
  }

  private async send(method: string, url: string, body: unknown, refreshCsrf: boolean): Promise<Response> {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };

    // Add CSRF token for non-GET requests
    if (method !== "GET") {
      const token = await this.csrfToken(refreshCsrf);
      if (token) {
        headers["X-CSRFToken"] = token;
      }
    }

    const options: RequestInit = {
      method,
      headers,
      credentials: "same-origin",
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    return fetch(url, options);
  }

  private async request<T>(
    method: string,
    url: string,
    body?: unknown
  ): Promise<ApiResponse<T>> {
    try {
      let response = await this.send(method, url, body, false);

      // A bad token is refused before the endpoint runs, so sending again
      // with a new one can't apply the write twice.
      if (response.status === 403 && method !== "GET") {
        response = await this.send(method, url, body, true);
      }

      if (response.ok) {
        const data = await response.json();
        return { data, error: null };
      }

      // Handle errors
      if (response.status === 401) {
        return { data: null, error: "Unauthorized" };
      }

      const errorData = await response.json().catch(() => ({}));
      return { data: null, error: errorData.message || "Request failed" };
    } catch {
      // Offline, or the connection dropped partway.
      return { data: null, error: NETWORK_ERROR };
    }
  }

  get<T>(url: string): Promise<ApiResponse<T>> {
    return this.request<T>("GET", url);
  }

  post<T>(url: string, body?: unknown): Promise<ApiResponse<T>> {
    return this.request<T>("POST", url, body);
  }

  put<T>(url: string, body?: unknown): Promise<ApiResponse<T>> {
    return this.request<T>("PUT", url, body);
  }

  delete<T>(url: string): Promise<ApiResponse<T>> {
    return this.request<T>("DELETE", url);
  }
}

export const api = new ApiClient();
