"""
MASTER CHAOS TEST RUNNER
Execute all chaos tests and generate comprehensive report
"""

import asyncio
import subprocess
import sys
import os
import time
from datetime import datetime


class MasterChaosTestRunner:
    def __init__(self):
        self.test_files = [
            # Backend tests
            "backend/tests/chaos/test_auth_chaos.py",
            "backend/tests/chaos/test_server_restart.py", 
            "backend/tests/chaos/test_websocket_chaos.py",
            "backend/tests/chaos/test_ai_engine_chaos.py",
            "backend/tests/chaos/test_memory_safety.py",
            "backend/tests/chaos/test_full_system_chaos.py",
            
            # Frontend tests
            "frontend/tests/chaos/test_network_failure.js",
            "frontend/tests/chaos/test_market_status.js",
            "frontend/tests/chaos/test_ui_crash_protection.js",
            
            # Report generator
            "backend/tests/chaos/generate_chaos_report.py"
        ]
        
        self.test_results = {}
        self.start_time = None
        self.end_time = None
    
    async def run_all_tests(self):
        """Run all chaos tests"""
        print("🔥 STARTING MASTER CHAOS TEST SUITE")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total tests to run: {len(self.test_files)}")
        print("")
        
        self.start_time = time.time()
        
        try:
            # Run each test
            for i, test_file in enumerate(self.test_files, 1):
                print(f"📋 [{i}/{len(self.test_files)}] Running {test_file}")
                print("-" * 50)
                
                success = await self.run_single_test(test_file)
                self.test_results[test_file] = {
                    "success": success,
                    "timestamp": datetime.now().isoformat()
                }
                
                status = "✅ PASSED" if success else "❌ FAILED"
                print(f"{status} {test_file}")
                print("")
            
            self.end_time = time.time()
            total_duration = self.end_time - self.start_time
            
            # Generate final summary
            await self.generate_final_summary(total_duration)
            
            return self.test_results
            
        except Exception as e:
            print(f"❌ Master chaos test runner failed: {str(e)}")
            raise
    
    async def run_single_test(self, test_file: str) -> bool:
        """Run a single test file"""
        try:
            # Determine test type and run accordingly
            if test_file.endswith('.py'):
                return await self.run_python_test(test_file)
            elif test_file.endswith('.js'):
                return await self.run_javascript_test(test_file)
            else:
                print(f"⚠️ Unknown test file type: {test_file}")
                return False
                
        except Exception as e:
            print(f"❌ Error running {test_file}: {str(e)}")
            return False
    
    async def run_python_test(self, test_file: str) -> bool:
        """Run Python test file"""
        try:
            # Change to appropriate directory
            if test_file.startswith('backend/'):
                cwd = 'backend'
                relative_path = test_file[8:]  # Remove 'backend/' prefix
            elif test_file.startswith('frontend/'):
                cwd = 'frontend'
                relative_path = test_file[10:]  # Remove 'frontend/' prefix
            else:
                cwd = '.'
                relative_path = test_file
            
            # Run Python test
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                relative_path,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Print output
            if stdout:
                print(stdout.decode())
            if stderr:
                print("STDERR:", stderr.decode())
            
            return process.returncode == 0
            
        except Exception as e:
            print(f"❌ Python test execution failed: {str(e)}")
            return False
    
    async def run_javascript_test(self, test_file: str) -> bool:
        """Run JavaScript test file"""
        try:
            # Change to frontend directory for JS tests
            if test_file.startswith('frontend/'):
                cwd = 'frontend'
                relative_path = test_file[10:]  # Remove 'frontend/' prefix
            else:
                cwd = '.'
                relative_path = test_file
            
            # Run JavaScript test with Node.js
            process = await asyncio.create_subprocess_exec(
                'node',
                relative_path,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Print output
            if stdout:
                print(stdout.decode())
            if stderr:
                print("STDERR:", stderr.decode())
            
            return process.returncode == 0
            
        except Exception as e:
            print(f"❌ JavaScript test execution failed: {str(e)}")
            return False
    
    async def generate_final_summary(self, total_duration: float):
        """Generate final summary of all tests"""
        print("🏁 CHAOS TEST SUITE COMPLETED")
        print("=" * 50)
        print(f"Ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total duration: {total_duration:.2f} seconds")
        print("")
        
        # Count results
        passed = sum(1 for result in self.test_results.values() if result["success"])
        failed = sum(1 for result in self.test_results.values() if not result["success"])
        total = len(self.test_results)
        
        print("📊 FINAL RESULTS")
        print("-" * 20)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        print("")
        
        # Show individual results
        print("📋 INDIVIDUAL TEST RESULTS")
        print("-" * 30)
        for test_file, result in self.test_results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status} {test_file}")
        print("")
        
        # Check if report was generated
        report_files = [
            "CHAOS_TEST_REPORT.md",
            "chaos_test_report.json"
        ]
        
        print("📄 GENERATED REPORTS")
        print("-" * 25)
        for report_file in report_files:
            if os.path.exists(report_file):
                print(f"✅ {report_file}")
            else:
                print(f"❌ {report_file} (missing)")
        print("")
        
        # Final verdict
        if failed == 0:
            print("🎉 ALL CHAOS TESTS PASSED!")
            print("✅ System is ready for production deployment")
        elif passed > failed:
            print("⚠️ SOME TESTS FAILED")
            print("🔧 Review failed tests and fix issues before deployment")
        else:
            print("❌ MOST TESTS FAILED")
            print("🚨 Critical issues found - system not ready for deployment")
        
        print("")


async def main():
    """Main entry point"""
    runner = MasterChaosTestRunner()
    
    try:
        results = await runner.run_all_tests()
        
        # Return appropriate exit code
        failed_count = sum(1 for result in results.values() if not result["success"])
        if failed_count == 0:
            print("CHAOS TEST SUITE CREATED SUCCESSFULLY")
            return 0
        else:
            print(f"CHAOS TEST SUITE COMPLETED WITH {failed_count} FAILURES")
            return 1
            
    except Exception as e:
        print(f"❌ Master chaos test runner failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
