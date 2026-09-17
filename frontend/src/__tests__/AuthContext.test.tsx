import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";

import { AuthProvider, useAuth } from "@/context/AuthContext";

function wrapper({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}

const mockUser = {
  id: "u_installer_1",
  name: "Jordan Reyes",
  email: "jordan.reyes@installer.qcells.com",
  role: "installer" as const,
  region: "Southwest Region",
};

describe("AuthContext", () => {
  beforeEach(() => {
    localStorage.clear();
    jest.restoreAllMocks();
  });

  it("starts logged out with isLoading resolving to false", async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.user).toBeNull();
    expect(result.current.token).toBeNull();
  });

  it("logs in successfully and persists the session", async () => {
    jest.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ token: "token_u_installer_1", user: mockUser }),
    } as Response);

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.login("jordan.reyes@installer.qcells.com", "installer123");
    });

    expect(result.current.user?.name).toBe("Jordan Reyes");
    expect(result.current.token).toBe("token_u_installer_1");
    expect(localStorage.getItem("qcells_l1_token")).toBe("token_u_installer_1");
  });

  it("surfaces an error message on failed login", async () => {
    jest.spyOn(global, "fetch").mockResolvedValue({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
      json: async () => ({ detail: "Invalid email or password" }),
    } as Response);

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await expect(result.current.login("wrong@qcells.com", "bad")).rejects.toThrow();
    });

    expect(result.current.error).toBe("Invalid email or password");
    expect(result.current.user).toBeNull();
  });

  it("clears the session on logout", async () => {
    jest.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ token: "token_u_installer_1", user: mockUser }),
    } as Response);

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    await act(async () => {
      await result.current.login("jordan.reyes@installer.qcells.com", "installer123");
    });

    act(() => result.current.logout());

    expect(result.current.user).toBeNull();
    expect(localStorage.getItem("qcells_l1_token")).toBeNull();
  });
});
