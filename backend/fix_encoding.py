# Fix line 385 in websocket_market_feed.py

# Read the file
with open('app/services/websocket_market_feed.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Replace line 385 with correct encoding
lines[384] = '        except Exception as e:\n            logger.error(f"Recv error → reconnecting: {e}")\n            await self._handle_disconnect()\n            break\n'

# Write back to file
with open('app/services/websocket_market_feed.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed line 385 encoding issue")
