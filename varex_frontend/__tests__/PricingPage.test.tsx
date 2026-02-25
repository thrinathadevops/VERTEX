// PATH: varex_frontend/__tests__/PricingPage.test.tsx

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import PricingPage from "@/app/pricing/page";

jest.mock("next/navigation", () => ({ useRouter: () => ({ push: jest.fn(), replace: jest.fn() }) }));
jest.mock("@/lib/api",       () => ({ getMe: jest.fn().mockResolvedValue(null) }));
jest.mock("@/lib/razorpay",  () => ({ initiatePayment: jest.fn() }));

describe("PricingPage", () => {
  it("renders all three plan cards", async () => {
    render(<PricingPage />);
    await waitFor(() => {
      expect(screen.getByText("Free")).toBeInTheDocument();
      expect(screen.getByText("Monthly")).toBeInTheDocument();
      expect(screen.getByText("Quarterly")).toBeInTheDocument();
    });
  });

  it("shows Subscribe buttons for non-logged-in users", async () => {
    render(<PricingPage />);
    await waitFor(() => {
      const buttons = screen.getAllByText("Subscribe");
      expect(buttons.length).toBeGreaterThan(0);
    });
  });
});
