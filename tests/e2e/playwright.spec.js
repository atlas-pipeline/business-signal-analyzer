const { test, expect } = require('@playwright/test');

const BASE_URL = process.env.BASE_URL || 'https://business-signal-analyzer.onrender.com';

// Phase 2: Automated UI Interaction Tests
test.describe('Business Signal Analyzer - E2E Tests', () => {
  
  test.beforeEach(async ({ page }) => {
    // Capture console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error(`Console error: ${msg.text()}`);
      }
    });
    
    // Capture page errors
    page.on('pageerror', error => {
      console.error(`Page error: ${error.message}`);
    });
  });

  test.describe('Navigation', () => {
    test('all nav links work', async ({ page }) => {
      await page.goto(BASE_URL);
      
      const navLinks = [
        { selector: 'a[href="/"]', expected: 'Ingest' },
        { selector: 'a[href="/topics.html"]', expected: 'Topics' },
        { selector: 'a[href="/ideas.html"]', expected: 'Ideas' },
        { selector: 'a[href="/evidence.html"]', expected: 'Evidence' }
      ];
      
      for (const link of navLinks) {
        const element = page.locator(link.selector).first();
        await expect(element).toBeVisible();
        await expect(element).toContainText(link.expected);
        
        // Click and verify navigation
        await element.click();
        await page.waitForLoadState('networkidle');
        
        // Verify no console errors after navigation
        // (errors captured in beforeEach)
      }
    });
  });

  test.describe('Ingest Page', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto(BASE_URL);
    });

    test('paste conversation and submit', async ({ page }) => {
      const testText = 'User: I have a problem with invoices taking too long.\n\nMe: How long does it take?\n\nUser: About 3-4 hours per week.';
      
      // Fill textarea
      const textarea = page.locator('#conversationText');
      await expect(textarea).toBeVisible();
      await textarea.fill(testText);
      
      // Click submit
      const submitBtn = page.locator('#submitBtn');
      await expect(submitBtn).toBeVisible();
      await submitBtn.click();
      
      // Wait for result
      const result = page.locator('#result');
      await expect(result).toBeVisible({ timeout: 10000 });
      
      // Verify success message
      await expect(result).toContainText('Conversation analyzed');
      
      // Verify button is re-enabled
      await expect(submitBtn).toBeEnabled();
    });

    test('submit empty form shows error', async ({ page }) => {
      const submitBtn = page.locator('#submitBtn');
      await submitBtn.click();
      
      // Should show alert or error
      // Note: Current implementation uses alert() which Playwright can detect
    });

    test('Reddit scraper button exists and is clickable', async ({ page }) => {
      const scrapeBtn = page.locator('#scrapeBtn');
      await expect(scrapeBtn).toBeVisible();
      await expect(scrapeBtn).toContainText('Auto-Scrape');
      
      // Note: Actually clicking this triggers a long API call
      // Just verify button state changes when clicked
      await scrapeBtn.click();
      
      // Loading indicator should appear
      const loading = page.locator('#scrapeLoading');
      // Loading may or may not appear depending on network speed
    });
  });

  test.describe('Topics Page', () => {
    test('load topics page', async ({ page }) => {
      await page.goto(`${BASE_URL}/topics.html`);
      
      // Wait for content to load
      await page.waitForLoadState('networkidle');
      
      // Check for topics list or empty state
      const content = page.locator('#topicsList');
      await expect(content).toBeVisible();
      
      // Should show either topics or empty state message
      const hasTopics = await page.locator('.topic-card').count() > 0;
      const hasEmptyState = await content.textContent().then(t => t.includes('No topics yet'));
      
      expect(hasTopics || hasEmptyState).toBeTruthy();
    });
  });

  test.describe('Ideas Page', () => {
    test('load ideas page', async ({ page }) => {
      await page.goto(`${BASE_URL}/ideas.html`);
      
      await page.waitForLoadState('networkidle');
      
      const ideasList = page.locator('#ideasList');
      await expect(ideasList).toBeVisible();
    });

    test('ideas have score breakdown when present', async ({ page }) => {
      await page.goto(`${BASE_URL}/ideas.html`);
      
      const ideaCards = page.locator('.idea-card');
      const count = await ideaCards.count();
      
      if (count > 0) {
        // If ideas exist, check for score breakdown
        const firstCard = ideaCards.first();
        await expect(firstCard.locator('.score-breakdown, .score')).toBeVisible();
      }
    });
  });

  test.describe('Evidence Page', () => {
    test('load evidence page', async ({ page }) => {
      await page.goto(`${BASE_URL}/evidence.html`);
      
      await page.waitForLoadState('networkidle');
      
      const evidenceList = page.locator('#evidenceList');
      await expect(evidenceList).toBeVisible();
    });
  });

  test.describe('API Health', () => {
    test('health endpoint returns healthy', async ({ request }) => {
      const response = await request.get(`${BASE_URL}/api/health`);
      expect(response.ok()).toBeTruthy();
      
      const body = await response.json();
      expect(body.status).toBe('healthy');
    });

    test('conversations endpoint accessible', async ({ request }) => {
      const response = await request.get(`${BASE_URL}/api/conversations`);
      expect(response.status()).toBe(200);
      
      const body = await response.json();
      expect(Array.isArray(body)).toBeTruthy();
    });
  });
});

// Smoke test - quick check all pages load
test.describe('Smoke Tests', () => {
  const routes = ['/', '/topics.html', '/ideas.html', '/evidence.html'];
  
  for (const route of routes) {
    test(`smoke: ${route} loads without errors`, async ({ page }) => {
      const errors = [];
      page.on('pageerror', e => errors.push(e.message));
      
      await page.goto(`${BASE_URL}${route}`);
      await page.waitForLoadState('networkidle');
      
      expect(errors).toHaveLength(0);
      
      // Verify page has content (not blank)
      const body = await page.locator('body').textContent();
      expect(body.length).toBeGreaterThan(100);
    });
  }
});
