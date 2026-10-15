import unittest
import os
from playwright.sync_api import sync_playwright

class TestHarmonizeModalUI(unittest.TestCase):
    def test_harmonize_modal_standalone_visibility(self):
        html_path = os.path.abspath('portal.html')
        file_url = f'file:///{html_path.replace(os.sep, "/")}'

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(channel="chrome", headless=True)
            except Exception:
                browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.route('**/*fonts.googleapis.com*', lambda r: r.abort())
            page.route('**/*fonts.gstatic.com*', lambda r: r.abort())
            page.goto(file_url, wait_until='domcontentloaded')
            
            # 1. Initial State: both modals hidden
            harm_display = page.evaluate('() => window.getComputedStyle(document.getElementById("harmonizeFlowModal")).display')
            bf_display = page.evaluate('() => window.getComputedStyle(document.getElementById("butterflyEditorModal")).display')
            self.assertEqual(harm_display, 'none')
            self.assertEqual(bf_display, 'none')
            
            # 2. Click Harmonize Flow button directly (without touching butterfly modal)
            page.click('#btnHeaderHarmonizeFlow')
            
            harm_display_after = page.evaluate('() => window.getComputedStyle(document.getElementById("harmonizeFlowModal")).display')
            bf_display_after = page.evaluate('() => window.getComputedStyle(document.getElementById("butterflyEditorModal")).display')
            harm_visible = page.is_visible('#harmonizeFlowModal')
            
            self.assertEqual(harm_display_after, 'flex')
            self.assertEqual(bf_display_after, 'none')
            self.assertTrue(harm_visible, 'Harmonize modal must be visible immediately without touching butterfly modal')
            
            # 3. Test close button
            page.click('#harmonizeFlowModal button:has-text("Close")')
            harm_display_closed = page.evaluate('() => window.getComputedStyle(document.getElementById("harmonizeFlowModal")).display')
            self.assertEqual(harm_display_closed, 'none')
            
            # 4. Switch to Tab 7 and test Tab 7 Harmonize button
            page.click('button[onclick*="shotOutlineTab"]')
            page.click('#btnHarmonizeFlow')
            harm_visible_tab7 = page.is_visible('#harmonizeFlowModal')
            self.assertTrue(harm_visible_tab7, 'Tab 7 Harmonize button must open modal immediately')

            browser.close()

if __name__ == '__main__':
    unittest.main()
