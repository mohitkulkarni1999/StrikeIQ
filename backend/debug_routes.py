from main import app

print("🔍 Debugging routes...")
print(f"App type: {type(app)}")

routes = []
for route in app.routes:
    route_info = {
        'path': getattr(route, 'path', 'N/A'),
        'methods': getattr(route, 'methods', 'N/A'),
        'type': type(route).__name__
    }
    routes.append(route_info)

print(f"\n📋 Total routes: {len(routes)}")
for i, route in enumerate(routes, 1):
    print(f"{i:2d}. {route['path']:<30} {str(route['methods']):<20} {route['type']}")

# Check for WebSocket routes specifically
ws_routes = [r for r in routes if 'WebSocket' in r['type']]
print(f"\n🔌 WebSocket routes: {len(ws_routes)}")
for ws_route in ws_routes:
    print(f"   - {ws_route['path']} ({ws_route['type']})")
