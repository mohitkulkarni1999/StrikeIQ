self.__BUILD_MANIFEST = {
  "__rewrites": {
    "afterFiles": [
      {
        "source": "/api/:path*"
      }
    ],
    "beforeFiles": [],
    "fallback": []
  },
  "sortedPages": [
    "/",
    "/IntelligenceDashboard",
    "/IntelligenceDashboardFinal",
    "/_app",
    "/_error",
    "/auth",
    "/auth/error",
    "/auth/success"
  ]
};self.__BUILD_MANIFEST_CB && self.__BUILD_MANIFEST_CB()