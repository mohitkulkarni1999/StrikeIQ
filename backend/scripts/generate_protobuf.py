#!/usr/bin/env python3
"""
Generate Python protobuf classes from MarketDataFeedV3.proto
"""

import subprocess
import sys
from pathlib import Path

def generate_protobuf_classes():
    """
    Generate Python classes from proto file using protoc
    """
    try:
        proto_file = Path("app/services/MarketDataFeedV3.proto")
        output_dir = Path("app/services")
        
        if not proto_file.exists():
            print(f"❌ Proto file not found: {proto_file}")
            return False
        
        # Generate Python classes
        cmd = [
            "protoc",
            "--python_out=.",
            str(proto_file)
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print("✅ Protobuf classes generated successfully")
            
            # Check if generated file exists
            generated_file = Path("app/services/MarketDataFeedV3_pb2.py")
            if generated_file.exists():
                print(f"✅ Generated file: {generated_file}")
                return True
            else:
                print(f"❌ Generated file not found: {generated_file}")
                return False
        else:
            print(f"❌ Protoc failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error generating protobuf classes: {e}")
        return False

if __name__ == "__main__":
    success = generate_protobuf_classes()
    sys.exit(0 if success else 1)
