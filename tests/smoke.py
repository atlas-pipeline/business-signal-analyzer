#!/usr/bin/env python3
"""
Phase 2 Alternative: Python-based UI Smoke Tests
Uses requests + BeautifulSoup to verify UI structure without browser automation.
"""
import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict

class UISmokeTester:
    def __init__(self, base_url: str = "https://business-signal-analyzer.onrender.com"):
        self.base_url = base_url.rstrip('/')
        self.results: List[Dict] = []
    
    def test_page_structure(self, route: str, expected_elements: List[Dict]) -> Dict:
        """Test a page loads and has expected elements."""
        url = f"{self.base_url}{route}"
        
        try:
            resp = requests.get(url, timeout=30)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            findings = []
            all_pass = True
            
            for element in expected_elements:
                selector = element.get('selector')
                text_contains = element.get('text_contains')
                required = element.get('required', True)
                
                if selector.startswith('#'):
                    found = soup.find(id=selector[1:])
                elif selector.startswith('.'):
                    found = soup.find(class_=selector[1:])
                else:
                    found = soup.find(selector)
                
                if found:
                    text_match = True
                    if text_contains:
                        found_text = found.get_text()
                        text_match = text_contains.lower() in found_text.lower()
                    
                    if text_match:
                        findings.append({
                            'element': selector,
                            'status': 'PASS',
                            'found': True
                        })
                    else:
                        findings.append({
                            'element': selector,
                            'status': 'FAIL',
                            'found': True,
                            'text_mismatch': True,
                            'expected': text_contains
                        })
                        if required:
                            all_pass = False
                else:
                    findings.append({
                        'element': selector,
                        'status': 'FAIL' if required else 'SKIP',
                        'found': False
                    })
                    if required:
                        all_pass = False
            
            # Check for JS console errors (we can't really do this without a browser,
            # but we can check for common issues)
            has_js = '<script>' in resp.text
            
            return {
                'route': route,
                'status': 'PASS' if all_pass else 'FAIL',
                'http_code': resp.status_code,
                'elements_tested': len(expected_elements),
                'findings': findings,
                'has_javascript': has_js
            }
            
        except Exception as e:
            return {
                'route': route,
                'status': 'ERROR',
                'error': str(e)
            }
    
    def run_all_smoke_tests(self) -> List[Dict]:
        """Run smoke tests on all pages."""
        print("🔥 Running UI Smoke Tests...")
        
        tests = [
            {
                'route': '/',
                'elements': [
                    {'selector': 'h1', 'text_contains': 'Business Signal Analyzer'},
                    {'selector': '#conversationText', 'required': True},
                    {'selector': '#submitBtn', 'text_contains': 'Analyze'},
                    {'selector': '#scrapeBtn', 'text_contains': 'Scrape'},
                    {'selector': '.nav', 'required': True},
                ]
            },
            {
                'route': '/topics.html',
                'elements': [
                    {'selector': 'h2', 'text_contains': 'Topics'},
                    {'selector': '#topicsList', 'required': True},
                ]
            },
            {
                'route': '/ideas.html',
                'elements': [
                    {'selector': 'h2', 'text_contains': 'Ideas'},
                    {'selector': '#ideasList', 'required': True},
                ]
            },
            {
                'route': '/evidence.html',
                'elements': [
                    {'selector': 'h2', 'text_contains': 'Evidence'},
                    {'selector': '#evidenceList', 'required': True},
                ]
            }
        ]
        
        for test in tests:
            result = self.test_page_structure(test['route'], test['elements'])
            self.results.append(result)
            icon = '✅' if result['status'] == 'PASS' else '❌'
            print(f"  {icon} {test['route']}: {result['status']}")
        
        return self.results
    
    def test_api_flow(self) -> Dict:
        """Test the complete API flow: ingest -> topics -> ideas."""
        print("\n🔄 Testing API Flow...")
        
        # Step 1: Create conversation
        conversation_text = """User: I spend hours every week chasing invoices.
Me: How do you currently track them?
User: Just spreadsheets. It's a mess."""
        
        try:
            resp = requests.post(
                f"{self.base_url}/api/conversations",
                json={'text': conversation_text, 'source_type': 'test'},
                timeout=10
            )
            
            if resp.status_code != 200:
                return {'status': 'FAIL', 'step': 'create_conversation', 'error': resp.text}
            
            conv_data = resp.json()
            conv_id = conv_data.get('id')
            
            print(f"  ✅ Created conversation #{conv_id}")
            
            # Step 2: Get topics
            resp = requests.get(f"{self.base_url}/api/topics?conversation_id={conv_id}", timeout=10)
            if resp.status_code != 200:
                return {'status': 'FAIL', 'step': 'get_topics', 'error': resp.text}
            
            print(f"  ✅ Retrieved topics")
            
            # Step 3: Get ideas
            resp = requests.get(f"{self.base_url}/api/ideas", timeout=10)
            if resp.status_code != 200:
                return {'status': 'FAIL', 'step': 'get_ideas', 'error': resp.text}
            
            ideas = resp.json()
            print(f"  ✅ Retrieved {len(ideas)} ideas")
            
            return {
                'status': 'PASS',
                'conversation_id': conv_id,
                'ideas_count': len(ideas)
            }
            
        except Exception as e:
            return {'status': 'ERROR', 'error': str(e)}
    
    def print_report(self):
        """Print formatted report."""
        print("\n" + "=" * 60)
        print("UI SMOKE TEST REPORT")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        
        print(f"\nResults: {passed} passed, {failed} failed")
        
        for r in self.results:
            if r['status'] != 'PASS':
                print(f"\n❌ {r['route']}:")
                for f in r.get('findings', []):
                    if f['status'] != 'PASS':
                        print(f"   - {f['element']}: {f['status']}")

if __name__ == "__main__":
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://business-signal-analyzer.onrender.com"
    tester = UISmokeTester(base_url)
    
    # Run smoke tests
    tester.run_all_smoke_tests()
    
    # Run API flow test
    flow_result = tester.test_api_flow()
    
    # Print report
    tester.print_report()
    
    print(f"\nAPI Flow: {flow_result['status']}")
    
    # Exit code
    failed = sum(1 for r in tester.results if r['status'] != 'PASS')
    sys.exit(1 if failed > 0 else 0)
