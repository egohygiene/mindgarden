import "@fontsource-variable/fraunces";
import "@fontsource-variable/manrope";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createRoot } from "react-dom/client";
import { captureGardenAccess, createGardenClient } from "./api";
import { Studio } from "./Studio";
import "./studio.css";

const client = createGardenClient(captureGardenAccess());
const queries = new QueryClient({
  defaultOptions: {
    queries: {
      gcTime: 0,
      staleTime: 0,
      networkMode: "always",
      retry: false,
      refetchOnWindowFocus: false,
      refetchOnReconnect: false,
    },
  },
});

const container = document.getElementById("studio");
if (!container) throw new Error("The Mindgarden Studio root element is missing");

createRoot(container).render(
  <QueryClientProvider client={queries}>
    <Studio client={client} />
  </QueryClientProvider>,
);
