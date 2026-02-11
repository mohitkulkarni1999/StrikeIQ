import gzip
import json
import sys
import urllib.request

# Download and parse NSE instruments
print("Downloading NSE instruments...")
response = urllib.request.urlopen("https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz")
data = gzip.decompress(response.read())
instruments = json.loads(data.decode('utf-8'))

print(f"Total instruments: {len(instruments)}")

# Find NIFTY instruments
nifty_instruments = []
for inst in instruments:
    if 'NIFTY' in inst.get('name', '').upper():
        nifty_instruments.append(inst)

print(f"\nFound {len(nifty_instruments)} NIFTY instruments:")
for i, inst in enumerate(nifty_instruments[:20]):
    print(f"{i+1}. {inst['instrument_key']} - {inst['name']} - {inst['instrument_type']}")

# Look for index instruments specifically
nifty_indices = [inst for inst in nifty_instruments if 'INDEX' in inst.get('instrument_type', '').upper()]
print(f"\nNIFTY Index instruments ({len(nifty_indices)}):")
for i, inst in enumerate(nifty_indices):
    print(f"{i+1}. {inst['instrument_key']} - {inst['name']} - {inst['instrument_type']}")

# Look for EQ instruments that might be NIFTY
nifty_eq = [inst for inst in nifty_instruments if 'EQ' in inst.get('instrument_type', '').upper()]
print(f"\nNIFTY EQ instruments ({len(nifty_eq)}):")
for i, inst in enumerate(nifty_eq[:10]):
    print(f"{i+1}. {inst['instrument_key']} - {inst['name']} - {inst['instrument_type']}")
