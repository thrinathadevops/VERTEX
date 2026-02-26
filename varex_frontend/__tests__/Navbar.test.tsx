// PATH: varex_frontend/__tests__/Navbar.test.tsx

import { render, screen } from "@testing-library/react";
import Navbar from "@/components/Navbar";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter:   () => ({ push: jest.fn() }),
  usePathname: () => "/",
}));

describe("Navbar", () => {
  it("renders the VAREX logo", () => {
    render(<Navbar />);
    expect(screen.getByAltText(/varex/i)).toBeInTheDocument();
  });

  it("renders navigation links", () => {
    render(<Navbar />);
    expect(screen.getByRole("link", { name: /services/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /portfolio/i })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /dashboard/i })).not.toBeInTheDocument();
  });
});
