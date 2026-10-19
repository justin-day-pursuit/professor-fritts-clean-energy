import { Suspense } from "react";
import PlanMockup from "./plan-mockup/page";

export default function Page() {
  return (
    <Suspense>
      <PlanMockup />
    </Suspense>
  );
}

