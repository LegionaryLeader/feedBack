import { test, expect } from '@playwright/test';

test('capability inspector renders runtime snapshot', async ({ page }) => {
  await page.goto('/');
  // Plugins load asynchronously after the initial HTML, so `.screen.active`
  // (already satisfied by the home screen) is not a sufficient signal. Wait
  // until showScreen exists AND the bundled inspector plugin's screen has been
  // injected before navigating, otherwise showScreen() targets a missing id
  // and the test races.
  await page.waitForFunction(() => {
    const appWindow = window as any;
    return typeof appWindow.showScreen === 'function'
      && document.getElementById('plugin-capability_inspector') !== null;
  }, { timeout: 30000 });
  // showScreen is async; await it so navigation completes before we assert.
  await page.evaluate(async () => {
    await (window as any).showScreen('plugin-capability_inspector');
  });
  await page.waitForSelector('#capability-inspector-content', { timeout: 10000 });
  await expect(page.locator('#capability-inspector-summary')).toContainText('domains', { timeout: 10000 });
  await expect(page.locator('#capability-inspector-content')).toContainText('playback', { timeout: 10000 });
});
