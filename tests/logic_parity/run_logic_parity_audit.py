"""
Logic Parity Audit Runner
Orchestrates the complete logic consistency audit between backend and frontend
"""

import sys
import os
import subprocess
import json
from datetime import datetime
from typing import Dict, Any, List

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

class LogicParityAuditor:
    """Orchestrates complete logic parity audit"""
    
    def __init__(self):
        self.backend_api_results = None
        self.frontend_results = None
        self.final_comparisons = []
        self.audit_start_time = datetime.now()
    
    def run_backend_api_parity(self):
        """Run backend-API parity tests"""
        print("🔧 Step 1: Running Backend-API Parity Tests")
        print("=" * 60)
        
        try:
            # Import and run backend-API parity test
            from test_backend_api_parity import run_backend_api_parity_tests
            
            test_data, comparison_table = run_backend_api_parity_tests()
            
            self.backend_api_results = {
                test_data: test_data,
                comparison_table: comparison_table,
                timestamp: datetime.now().isoformat()
            }
            
            print("✅ Backend-API parity tests completed")
            return True
            
        except Exception as e:
            print(f"❌ Backend-API parity test failed: {e}")
            return False
    
    def run_frontend_parity(self):
        """Run frontend parity tests"""
        print("\n🔧 Step 2: Running Frontend Parity Tests")
        print("=" * 60)
        
        try:
            # Run frontend parity test using Node.js
            result = subprocess.run(
                ['node', 'test_frontend_parity.js'],
                cwd=os.path.dirname(__file__),
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                # Parse the comparison table from output
                output_lines = result.stdout.split('\n')
                comparison_start = False
                comparison_lines = []
                
                for line in output_lines:
                    if '| Field | Backend | API | Frontend | Status |' in line:
                        comparison_start = True
                    elif comparison_start and line.startswith('|'):
                        comparison_lines.append(line)
                    elif comparison_start and not line.strip():
                        break
                
                comparison_table = '\n'.join(comparison_lines) if comparison_lines else "No comparison data available"
                
                self.frontend_results = {
                    comparison_table: comparison_table,
                    stdout: result.stdout,
                    stderr: result.stderr,
                    timestamp: datetime.now().isoformat()
                }
                
                print("✅ Frontend parity tests completed")
                return True
            else:
                print(f"❌ Frontend parity test failed with return code: {result.returncode}")
                print(f"Stderr: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Frontend parity test timed out")
            return False
        except Exception as e:
            print(f"❌ Frontend parity test error: {e}")
            return False
    
    def load_test_data(self):
        """Load test data for final comparison"""
        try:
            # Load backend-API test data
            with open('backend_api_parity_data.json', 'r') as f:
                backend_data = json.load(f)
            
            # Load frontend test data
            with open('frontend_parity_results.json', 'r') as f:
                frontend_data = json.load(f)
            
            return backend_data, frontend_data
            
        except Exception as e:
            print(f"❌ Failed to load test data: {e}")
            return None, None
    
    def create_final_comparison_table(self):
        """Create final comparison table with all three layers"""
        backend_data, frontend_data = self.load_test_data()
        
        if not backend_data or not frontend_data:
            return "| Error: Could not load test data for final comparison |"
        
        table_lines = []
        table_lines.append("| Field | Backend | API | Frontend | Status |")
        table_lines.append("| ----- | ------- | --- | -------- | ------ |")
        
        # Process each test scenario
        for test_scenario in backend_data['test_data']:
            test_id = test_scenario['test_id']
            
            # Get values from each layer
            backend_fields = test_scenario['backend_fields']
            api_fields = test_scenario['api_fields']
            frontend_values = frontend_data['captured_values'].get(test_id, {})
            
            # Compare each field
            for field in ['pcr', 'net_gamma', 'support', 'resistance', 'signal', 'confidence']:
                backend_val = backend_fields.get(field)
                api_val = api_fields.get(field)
                frontend_val = frontend_values.get(field)
                
                # Determine if all values match
                match = self.compare_all_values(backend_val, api_val, frontend_val)
                status = "PASS" if match else "FAIL"
                
                # Format values for display
                backend_display = str(backend_val) if backend_val is not None else "N/A"
                api_display = str(api_val) if api_val is not None else "N/A"
                frontend_display = str(frontend_val) if frontend_val is not None else "N/A"
                
                table_lines.append(f"| {field} | {backend_display} | {api_display} | {frontend_display} | {status} |")
                
                # Store comparison result
                self.final_comparisons.append({
                    'test_id': test_id,
                    'field': field,
                    'backend_value': backend_val,
                    'api_value': api_val,
                    'frontend_value': frontend_val,
                    'match': match
                })
        
        return '\n'.join(table_lines)
    
    def compare_all_values(self, backend_val, api_val, frontend_val):
        """Compare values across all three layers"""
        # Helper function to normalize numeric values
        def normalize(val):
            if val is None:
                return None
            if isinstance(val, str):
                # Remove formatting characters and convert to float
                clean_val = val.replace(',', '').replace('%', '').strip()
                try:
                    return float(clean_val)
                except:
                    return val
            return val
        
        backend_norm = normalize(backend_val)
        api_norm = normalize(api_val)
        frontend_norm = normalize(frontend_val)
        
        # If all are None, consider as match
        if backend_norm is None and api_norm is None and frontend_norm is None:
            return True
        
        # If any is None while others are not, no match
        if None in [backend_norm, api_norm, frontend_norm]:
            return False
        
        # For numeric values, use tolerance
        if all(isinstance(v, (int, float)) for v in [backend_norm, api_norm, frontend_norm]):
            tolerance = 0.01
            return (abs(backend_norm - api_norm) <= tolerance and 
                   abs(api_norm - frontend_norm) <= tolerance and
                   abs(backend_norm - frontend_norm) <= tolerance)
        
        # For string values, exact match after stripping
        if all(isinstance(v, str) for v in [backend_norm, api_norm, frontend_norm]):
            return (backend_norm.strip() == api_norm.strip() == frontend_norm.strip())
        
        # Direct comparison for other types
        return backend_norm == api_norm == frontend_norm
    
    def generate_summary_statistics(self):
        """Generate summary statistics for the audit"""
        if not self.final_comparisons:
            return "No comparison data available"
        
        total_comparisons = len(self.final_comparisons)
        passed_comparisons = sum(1 for comp in self.final_comparisons if comp['match'])
        failed_comparisons = total_comparisons - passed_comparisons
        success_rate = (passed_comparisons / total_comparisons * 100) if total_comparisons > 0 else 0
        
        # Field-specific statistics
        field_stats = {}
        for field in ['pcr', 'net_gamma', 'support', 'resistance', 'signal', 'confidence']:
            field_comparisons = [comp for comp in self.final_comparisons if comp['field'] == field]
            if field_comparisons:
                field_passed = sum(1 for comp in field_comparisons if comp['match'])
                field_total = len(field_comparisons)
                field_stats[field] = {
                    'passed': field_passed,
                    'total': field_total,
                    'success_rate': (field_passed / field_total * 100)
                }
        
        summary = f"""
## 📊 AUDIT SUMMARY STATISTICS

### Overall Results
- **Total Comparisons**: {total_comparisons}
- **Passed**: {passed_comparisons}
- **Failed**: {failed_comparisons}
- **Success Rate**: {success_rate:.1f}%

### Field-Specific Results
"""
        
        for field, stats in field_stats.items():
            status = "✅ PASS" if stats['success_rate'] == 100 else "❌ FAIL"
            summary += f"""
- **{field}**: {stats['passed']}/{stats['total']} ({stats['success_rate']:.1f}%) {status}"""
        
        # Test scenario statistics
        test_scenarios = set(comp['test_id'] for comp in self.final_comparisons)
        perfect_scenarios = 0
        
        for scenario in test_scenarios:
            scenario_comparisons = [comp for comp in self.final_comparisons if comp['test_id'] == scenario]
            if all(comp['match'] for comp in scenario_comparisons):
                perfect_scenarios += 1
        
        summary += f"""

### Test Scenario Results
- **Total Scenarios**: {len(test_scenarios)}
- **Perfect Scenarios**: {perfect_scenarios}
- **Scenario Success Rate**: {(perfect_scenarios / len(test_scenarios) * 100):.1f}%
"""
        
        return summary
    
    def generate_mismatch_report(self):
        """Generate detailed report of mismatches"""
        mismatches = [comp for comp in self.final_comparisons if not comp['match']]
        
        if not mismatches:
            return "## 🎉 NO MISMATCHES FOUND\n\nAll fields match perfectly across backend, API, and frontend!"
        
        report = "## ❌ MISMATCH DETAILS\n\n"
        
        # Group by test scenario
        scenarios = {}
        for mismatch in mismatches:
            test_id = mismatch['test_id']
            if test_id not in scenarios:
                scenarios[test_id] = []
            scenarios[test_id].append(mismatch)
        
        for test_id, scenario_mismatches in scenarios.items():
            report += f"### Test Scenario: {test_id}\n\n"
            
            for mismatch in scenario_mismatches:
                field = mismatch['field']
                backend_val = mismatch['backend_value']
                api_val = mismatch['api_value']
                frontend_val = mismatch['frontend_value']
                
                report += f"**{field}**:\n"
                report += f"- Backend: `{backend_val}`\n"
                report += f"- API: `{api_val}`\n"
                report += f"- Frontend: `{frontend_val}`\n"
                report += f"- Status: ❌ MISMATCH\n\n"
        
        return report
    
    def generate_final_report(self):
        """Generate the final logic parity report"""
        print("\n🔧 Step 3: Generating Final Logic Parity Report")
        print("=" * 60)
        
        # Create final comparison table
        comparison_table = self.create_final_comparison_table()
        
        # Generate summary statistics
        summary_stats = self.generate_summary_statistics()
        
        # Generate mismatch report
        mismatch_report = self.generate_mismatch_report()
        
        # Calculate audit duration
        audit_duration = datetime.now() - self.audit_start_time
        
        # Create final report
        report = f"""# StrikeIQ Logic Parity Audit Report

**Date**: {datetime.now().strftime('%B %d, %Y')}
**Audit Type**: Complete Logic Consistency Validation
**Duration**: {audit_duration}
**Status**: {'✅ PASSED' if all(comp['match'] for comp in self.final_comparisons) else '❌ FAILED'}

---

## 📋 EXECUTIVE SUMMARY

This audit validates logic consistency between backend AI engines, API responses, and frontend UI components for the StrikeIQ trading analytics platform.

**Objective**: Ensure that critical fields (pcr, net_gamma, support, resistance, signal, confidence) have identical values across all system layers.

---

## 🔍 AUDIT METHODOLOGY

### Step 1: Backend-API Parity Testing
- Captured AI engine outputs using simulated LiveMetrics
- Called API endpoints (/metrics, /signals)
- Compared engine outputs with API responses

### Step 2: Frontend Parity Testing
- Launched frontend using Puppeteer
- Captured displayed values from UI components
- Compared UI values with API responses

### Step 3: End-to-End Validation
- Cross-referenced all three layers
- Validated field consistency
- Generated comprehensive comparison report

---

## 📊 COMPARISON RESULTS

{comparison_table}

{summary_stats}

{mismatch_report}

---

## 🎯 VALIDATION CRITERIA

All fields must match exactly (within tolerance for numeric values):

- ✅ **PCR**: Put-Call Ratio consistency
- ✅ **Net Gamma**: Gamma exposure consistency  
- ✅ **Support**: Support level consistency
- ✅ **Resistance**: Resistance level consistency
- ✅ **Signal**: Trading signal consistency
- ✅ **Confidence**: Signal confidence consistency

---

## 🏁 FINAL AUDIT VERDICT

**Audit Status**: {'✅ PASSED' if all(comp['match'] for comp in self.final_comparisons) else '❌ FAILED'}

**System Consistency**: {'EXCELLENT' if all(comp['match'] for comp in self.final_comparisons) else 'NEEDS ATTENTION'}

**Production Readiness**: {'✅ READY' if all(comp['match'] for comp in self.final_comparisons) else '⚠️ REQUIRES FIXES'}

---

## 📈 RECOMMENDATIONS

{'All system layers are perfectly consistent. No action required.' if all(comp['match'] for comp in self.final_comparisons) else 'Address the mismatches identified in the report above to ensure system consistency.'}

---

*Report generated by StrikeIQ Logic Parity Auditor*
*Timestamp: {datetime.now().isoformat()}*
"""
        
        # Save report
        report_filename = 'LOGIC_PARITY_REPORT.md'
        with open(report_filename, 'w') as f:
            f.write(report)
        
        print(f"✅ Final report saved to {report_filename}")
        
        # Also save raw comparison data
        raw_data = {
            'audit_metadata': {
                'start_time': self.audit_start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration': str(audit_duration),
                'total_comparisons': len(self.final_comparisons),
                'passed_comparisons': sum(1 for comp in self.final_comparisons if comp['match']),
                'success_rate': (sum(1 for comp in self.final_comparisons if comp['match']) / len(self.final_comparisons) * 100) if self.final_comparisons else 0
            },
            'comparisons': self.final_comparisons,
            'backend_api_results': self.backend_api_results,
            'frontend_results': self.frontend_results
        }
        
        raw_filename = 'logic_parity_raw_data.json'
        with open(raw_filename, 'w') as f:
            json.dump(raw_data, f, indent=2)
        
        print(f"✅ Raw data saved to {raw_filename}")
        
        return report
    
    def run_complete_audit(self):
        """Run the complete logic parity audit"""
        print("🚀 Starting StrikeIQ Logic Parity Audit")
        print("=" * 80)
        print("Validating logic consistency between backend, API, and frontend")
        print("=" * 80)
        
        # Step 1: Run backend-API parity tests
        if not self.run_backend_api_parity():
            print("❌ Backend-API parity tests failed. Aborting audit.")
            return False
        
        # Step 2: Run frontend parity tests
        if not self.run_frontend_parity():
            print("❌ Frontend parity tests failed. Aborting audit.")
            return False
        
        # Step 3: Generate final report
        report = self.generate_final_report()
        
        print("\n" + "=" * 80)
        print("🎉 Logic Parity Audit Complete")
        print("=" * 80)
        print(report)
        
        return True

def main():
    """Main entry point"""
    auditor = LogicParityAuditor()
    success = auditor.run_complete_audit()
    
    if success:
        print("\n✅ Audit completed successfully")
        return 0
    else:
        print("\n❌ Audit failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
