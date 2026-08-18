import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";

export default function AppLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit" showDevConsole={false} enableInspector={false}>
      {children}
    </CopilotKit>
  );
}
