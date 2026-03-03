export default function RouteGuard({ children }: { children: React.ReactNode }) {
  // PASSIVE WRAPPER - No authentication logic
  // Auth validation is now handled by axios interceptor
  return <>{children}</>
}