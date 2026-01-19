interface ApiResponse<T> {
  data: T | null;
  error: string | null;
}

class ApiClient {
  private csrfToken: string | null = null;

  private getCookie(name: string): string | null {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      return parts.pop()?.split(";").shift() || null;
    }
    return null;
  }

  async fetchCsrfToken(): Promise<void> {
    const response = await fetch("/api/accounts/csrf/");
    if (response.ok) {
      const data = await response.json();
      this.csrfToken = data.csrf_token;
    }
  }

  private async request<T>(
    method: string,
    url: string,
    body?: unknown
  ): Promise<ApiResponse<T>> {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };

    // Add CSRF token for non-GET requests
    if (method !== "GET") {
      const token = this.csrfToken || this.getCookie("csrftoken");
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

    const response = await fetch(url, options);

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
  }

  get<T>(url: string): Promise<ApiResponse<T>> {
    return this.request<T>("GET", url);
  }

  post<T>(url: string, body?: unknown): Promise<ApiResponse<T>> {
    return this.request<T>("POST", url, body);
  }
}

export const api = new ApiClient();
