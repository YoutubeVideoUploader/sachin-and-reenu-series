import unittest
import os
from playwright.sync_api import sync_playwright

class TestAdjustModalUI(unittest.TestCase):
    def test_adjust_modal_standalone_visibility(self):
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
            
            # 1. Initial State: Adjust modal hidden
            adj_display = page.evaluate('() => window.getComputedStyle(document.getElementById("adjustModal")).display')
            self.assertEqual(adj_display, 'none')
            
            # 2. Click Adjust button in header
            page.click('#btnHeaderAdjust')
            
            adj_display_after = page.evaluate('() => window.getComputedStyle(document.getElementById("adjustModal")).display')
            adj_visible = page.is_visible('#adjustModal')
            
            self.assertEqual(adj_display_after, 'flex')
            self.assertTrue(adj_visible, 'Adjust modal must be visible immediately when clicking header Adjust button')
            
            # Check both options exist
            opt1_visible = page.is_visible('#btnAdjustPrompts')
            opt2_visible = page.is_visible('#btnAdjustDialogues')
            self.assertTrue(opt1_visible, 'Option 1 (Tab 2 from Tab 5+4) must be visible')
            self.assertTrue(opt2_visible, 'Option 2 (Improve dialogue & Tab 2) must be visible')

            # 3. Test close button
            page.click('#adjustModal button:has-text("Close")')
            adj_display_closed = page.evaluate('() => window.getComputedStyle(document.getElementById("adjustModal")).display')
            self.assertEqual(adj_display_closed, 'none')
            
            # 4. Switch to Outline Tab and test Outline Adjust button
            page.click('button[onclick*="shotOutlineTab"]')
            page.click('#btnAdjustEpisode')
            adj_visible_outline = page.is_visible('#adjustModal')
            self.assertTrue(adj_visible_outline, 'Outline Adjust button must open adjust modal immediately')

            browser.close()

if __name__ == '__main__':
    unittest.main()
