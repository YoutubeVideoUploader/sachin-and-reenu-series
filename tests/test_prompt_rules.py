import unittest
import os
import json
from playwright.sync_api import sync_playwright

class TestPromptRules(unittest.TestCase):
    def test_shot1_prompt_rules_compliance(self):
        html_path = os.path.abspath('portal.html')
        file_url = 'file:///' + html_path.replace('\\', '/')

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(channel="chrome", headless=True)
            except Exception:
                browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.route('**/*fonts.googleapis.com*', lambda r: r.abort())
            page.route('**/*fonts.gstatic.com*', lambda r: r.abort())
            page.goto(file_url, wait_until='domcontentloaded')

            shot1 = {
                'shot_number': 1,
                'speaker': 'Third-Person Narrator',
                'action': 'Dense grey fog swirls violently across the winding Munnar hillside road as Amal slowly drives forward with headlights piercing the mist.',
                'dialogue_malayalam': 'യാത്ര മുന്നോട്ട് പോകുന്തോറും മൂടൽമഞ്ഞ് കനത്തുവന്നു.',
                'location': 'Munnar Mountain Road',
                'persistent_props': ['Car'],
                'camera_hint': 'Wide tracking shot pulling back slowly in front of the crawling car.'
            }

            res = page.evaluate('''(s) => compileDeterministicGoogleFlowPrompt(s, characterRegistryData)''', shot1)
            jp = res['json_prompt']

            # 1. Characters Present check
            char_names = [c['name'] for c in jp['characters_present']]
            self.assertIn('Amal', char_names, f"Amal must be in characters_present since he is driving in action. Got: {char_names}")
            self.assertIn('Sachin', char_names, "Sachin must be in characters_present")
            self.assertIn('Reenu', char_names, "Reenu must be in characters_present")

            # 2. Tab 4 locked attire check
            amal = next(c for c in jp['characters_present'] if c['name'] == 'Amal')
            self.assertIn('Terracotta Rust-Orange', amal['locked_attire'], "Amal must wear Terracotta Rust-Orange solid T-shirt from Tab 4")

            sachin = next(c for c in jp['characters_present'] if c['name'] == 'Sachin')
            self.assertIn('Navy Blue', sachin['locked_attire'], "Sachin must wear Navy Blue solid crewneck T-shirt from Tab 4")

            reenu = next(c for c in jp['characters_present'] if c['name'] == 'Reenu')
            self.assertIn('Lavender', reenu['locked_attire'], "Reenu must wear Pastel Lavender floral T-shirt from Tab 4")

            # 3. Third-Person Narrator voice check (MALE)
            self.assertIn('Male', jp['audio_spec']['voice_persona'])
            self.assertNotIn('Female', jp['audio_spec']['voice_persona'])
            self.assertIn('EXTERNAL MALE VOICEOVER ONLY', jp['audio_spec']['audio_directive'])
            self.assertNotIn('FEMALE', jp['audio_spec']['audio_directive'])

            # 4. Closed lips rule check
            self.assertIn('strictly closed lips', jp['action'])
            self.assertIn('strictly closed lips', jp['audio_sync'])

            # 5. Visual DNA Teenager & Negative Prompt Boundaries check
            self.assertIn('18-19 year old', sachin['visual_dna'])
            self.assertNotIn('24-year-old', sachin['visual_dna'])
            self.assertIn('ZERO FACIAL HAIR', sachin['visual_dna'])
            self.assertIn('PROHIBIT REALISTIC HUMAN SKIN PORES', sachin['visual_dna'])

            self.assertIn('18-19 year old', reenu['visual_dna'])
            self.assertNotIn('22-year-old', reenu['visual_dna'])
            self.assertIn('PROHIBIT REALISTIC HUMAN SKIN PORES', reenu['visual_dna'])

            self.assertIn('18-19 year old', amal['visual_dna'])
            self.assertIn('ZERO BEARD', amal['visual_dna'])
            self.assertIn('PROHIBIT REALISTIC HUMAN SKIN PORES', amal['visual_dna'])

            # 6. Camera check
            self.assertEqual(jp['camera'], 'Wide tracking shot pulling back slowly in front of the crawling car.')

            # 7. Audio spec BGM check
            self.assertEqual(jp['audio_spec']['background_music'], 'Strictly NO background music, zero score, clean dialogue only.')

            browser.close()

if __name__ == '__main__':
    unittest.main()
