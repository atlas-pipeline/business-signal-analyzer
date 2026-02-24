#!/usr/bin/env python3
"""
Phase 1: Automated Link and Route Audit
Crawls all routes and API endpoints, reports failures.
"""
import requests
import json
import sys
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Set, Tuple
import re

class AppAuditor:
    def __init__(self, base_url: str = "https://business-signal-analyzer.onrender.com"):
        self.base_url = base_url.rstrip('/')
        self.frontend_routes = [
            '/', '/topics.html', '/ideas.html', '/evidence.html'
        ]
        self.api_endpoints = [
            ('GET', '/api/health'),
            ('GET', '/api/conversations'),
            ('POST', '/api/conversations'),
            ('GET', '/api/topics'),
            ('POST', '/api/topics'),
            ('GET', '/api/ideas'),
            ('POST', '/api/ideas'),
            ('POST', '/api/demand/collect'),
            ('POST', '/api/ideas/{id}/score'),
            ('GET', '/api/scoring/weights'),
            ('GET', '/api/evidence/idea/{id}'),
        ]
        self.findings: List[Dict] = []
    
    def audit_frontend_routes(self) -> List[Dict]:
        """Check all frontend routes return valid HTML."""
        print("🔍 Auditing frontend routes...")
        results = []
        
        for route in self.frontend_routes:
            url = f"{self.base_url}{route}"
            try:
                resp = requests.get(url, timeout=30)
                
                # Check for valid HTML response
                is_html = 'text/html' in resp.headers.get('content-type', '')
                has_body = '<body>' in resp.text.lower() or '<!doctype' in resp.text.lower()
                is_blank = len(resp.text.strip()) < 100
                
                if resp.status_code == 200 and is_html and has_body and not is_blank:
                    results.append({
                        'route': route,
                        'status': 'PASS',
                        'code': resp.status_code,
                        'size': len(resp.text)
                    })
                else:
                    results.append({
                        'route': route,
                        'status': 'FAIL',
                        'code': resp.status_code,
                        'html': is_html,
                        'has_body': has_body,
                        'is_blank': is_blank,
                        'size': len(resp.text)
                    })
                    self.findings.append({
                        'severity': 'HIGH' if route == '/' else 'MEDIUM',
                        'type': 'frontend_route',
                        'route': route,
                        'issue': f"Status {resp.status_code}, HTML: {is_html}, Has body: {has_body}, Blank: {is_blank}"
                    })
            except Exception as e:
                results.append({
                    'route': route,
                    'status': 'ERROR',
                    'error': str(e)
                })
                self.findings.append({
                    'severity': 'CRITICAL',
                    'type': 'frontend_route',
                    'route': route,
                    'issue': f"Exception: {str(e)}"
                })
        
        return results
    
    def audit_api_endpoints(self) -> List[Dict]:
        """Check all API endpoints respond correctly."""
        print("🔍 Auditing API endpoints...")
        results = []
        
        # Health check
        try:
            resp = requests.get(f"{self.base_url}/api/health", timeout=10)
            if resp.status_code == 200 and 'healthy' in resp.text:
                results.append({'endpoint': '/api/health', 'status': 'PASS', 'code': 200})
            else:
                results.append({'endpoint': '/api/health', 'status': 'FAIL', 'code': resp.status_code})
                self.findings.append({
                    'severity': 'CRITICAL',
                    'type': 'api',
                    'endpoint': '/api/health',
                    'issue': f"Health check failed: {resp.status_code}"
                })
        except Exception as e:
            results.append({'endpoint': '/api/health', 'status': 'ERROR', 'error': str(e)})
            self.findings.append({
                'severity': 'CRITICAL',
                'type': 'api',
                'endpoint': '/api/health',
                'issue': f"Health check exception: {str(e)}"
            })
        
        # Test GET endpoints that don't require params
        get_endpoints = [
            '/api/conversations',
            '/api/topics',
            '/api/ideas',
            '/api/scoring/weights',
        ]
        
        for endpoint in get_endpoints:
            try:
                resp = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                if resp.status_code in [200, 422]:  # 422 is OK (validation error for missing params)
                    results.append({'endpoint': endpoint, 'status': 'PASS', 'code': resp.status_code})
                else:
                    results.append({'endpoint': endpoint, 'status': 'WARN', 'code': resp.status_code})
                    self.findings.append({
                        'severity': 'MEDIUM',
                        'type': 'api',
                        'endpoint': endpoint,
                        'issue': f"Unexpected status: {resp.status_code}"
                    })
            except Exception as e:
                results.append({'endpoint': endpoint, 'status': 'ERROR', 'error': str(e)})
                self.findings.append({
                    'severity': 'HIGH',
                    'type': 'api',
                    'endpoint': endpoint,
                    'issue': f"Exception: {str(e)}"
                })
        
        return results
    
    def check_navigation_links(self) -> List[Dict]:
        """Check all nav links in HTML point to valid routes."""
        print("🔍 Checking navigation links...")
        results = []
        
        try:
            resp = requests.get(f"{self.base_url}/", timeout=10)
            html = resp.text
            
            # Find all href links
            links = re.findall(r'href=["\']([^"\']+)["\']', html)
            internal_links = [l for l in links if not l.startswith('http') and not l.startswith('#')]
            
            for link in set(internal_links):
                if link.startswith('/'):
                    full_url = f"{self.base_url}{link}"
                else:
                    full_url = f"{self.base_url}/{link}"
                
                try:
                    link_resp = requests.head(full_url, timeout=5, allow_redirects=True)
                    if link_resp.status_code < 400:
                        results.append({'link': link, 'status': 'PASS', 'code': link_resp.status_code})
                    else:
                        results.append({'link': link, 'status': 'FAIL', 'code': link_resp.status_code})
                        self.findings.append({
                            'severity': 'MEDIUM',
                            'type': 'navigation',
                            'link': link,
                            'issue': f"Broken link, status: {link_resp.status_code}"
                        })
                except Exception as e:
                    results.append({'link': link, 'status': 'ERROR', 'error': str(e)})
        except Exception as e:
            results.append({'error': str(e)})
        
        return results
    
    def run_full_audit(self) -> Dict:
        """Run complete audit and return report."""
        print("=" * 60)
        print("BUSINESS SIGNAL ANALYZER - FULL AUDIT")
        print("=" * 60)
        print(f"Target: {self.base_url}")
        print()
        
        frontend = self.audit_frontend_routes()
        api = self.audit_api_endpoints()
        nav = self.check_navigation_links()
        
        report = {
            'timestamp': str(datetime.now()),
            'base_url': self.base_url,
            'summary': {
                'frontend_routes_checked': len(frontend),
                'api_endpoints_checked': len(api),
                'nav_links_checked': len(nav),
                'total_findings': len(self.findings),
                'critical': len([f for f in self.findings if f['severity'] == 'CRITICAL']),
                'high': len([f for f in self.findings if f['severity'] == 'HIGH']),
                'medium': len([f for f in self.findings if f['severity'] == 'MEDIUM']),
            },
            'frontend_results': frontend,
            'api_results': api,
            'navigation_results': nav,
            'findings': sorted(self.findings, key=lambda x: {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}[x['severity']])
        }
        
        self.print_report(report)
        return report
    
    def print_report(self, report: Dict):
        """Print formatted audit report."""
        print("\n" + "=" * 60)
        print("AUDIT RESULTS")
        print("=" * 60)
        
        print(f"\n📊 Summary:")
        for key, val in report['summary'].items():
            print(f"  {key}: {val}")
        
        print(f"\n🌐 Frontend Routes:")
        for r in report['frontend_results']:
            icon = '✅' if r['status'] == 'PASS' else '❌' if r['status'] == 'FAIL' else '⚠️'
            print(f"  {icon} {r['route']}: {r['status']} (code: {r.get('code', 'N/A')})")
        
        print(f"\n🔌 API Endpoints:")
        for r in report['api_results']:
            icon = '✅' if r['status'] == 'PASS' else '❌' if r['status'] == 'FAIL' else '⚠️'
            print(f"  {icon} {r['endpoint']}: {r['status']}")
        
        if report['findings']:
            print(f"\n🐛 Findings (sorted by severity):")
            for f in report['findings'][:10]:  # Show top 10
                icon = '🔴' if f['severity'] == 'CRITICAL' else '🟠' if f['severity'] == 'HIGH' else '🟡'
                print(f"  {icon} [{f['severity']}] {f.get('route', f.get('endpoint', f.get('link', 'unknown')))}")
                print(f"     Issue: {f['issue'][:80]}...")
        else:
            print("\n✨ No findings - all checks passed!")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    from datetime import datetime
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://business-signal-analyzer.onrender.com"
    auditor = AppAuditor(base_url)
    report = auditor.run_full_audit()
    
    # Exit with error code if critical findings
    critical_count = len([f for f in report['findings'] if f['severity'] == 'CRITICAL'])
    sys.exit(1 if critical_count > 0 else 0)
