// PATH: varex_frontend/__tests__/auth.test.ts

import { login, logout } from "@/lib/auth";

global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

beforeEach(() => {
  mockFetch.mockClear();
  sessionStorage.clear();
});

describe("login()", () => {
  it("returns user on success", async () => {
    mockFetch.mockResolvedValueOnce({
      ok:   true,
      json: async () => ({ id: "123", name: "Test", email: "t@v.in", role: "free_user" }),
    } as Response);

    const user = await login("t@v.in", "Pass123!");
    expect(user.role).toBe("free_user");
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/auth/login"),
      expect.objectContaining({ method: "POST", credentials: "include" })
    );
  });

  it("throws on 401", async () => {
    mockFetch.mockResolvedValueOnce({
      ok:   false,
      json: async () => ({ detail: "Incorrect email or password" }),
    } as Response);

    await expect(login("wrong@v.in", "wrong")).rejects.toThrow("Incorrect email or password");
  });
});

describe("logout()", () => {
  it("calls logout endpoint and clears sessionStorage", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) } as Response);
    sessionStorage.setItem("varex_user", JSON.stringify({ id: "1" }));

    await logout();

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/auth/logout"),
      expect.objectContaining({ method: "POST", credentials: "include" })
    );
    expect(sessionStorage.getItem("varex_user")).toBeNull();
  });
});
