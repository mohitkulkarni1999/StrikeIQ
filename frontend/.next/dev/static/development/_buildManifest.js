self.__BUILD_MANIFEST = {
  "/": [
    "static/chunks/pages/index.js"
  ],
  "/auth": [
    "static/chunks/pages/auth.js"
  ],
  "/auth/success": [
    "static/chunks/pages/auth/success.js"
  ],
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
    "/_app",
    "/_error",
    "/auth",
    "/auth/success"
  ]
};self.__BUILD_MANIFEST_CB && self.__BUILD_MANIFEST_CB()