import unittest
from llm_router import LLMRouter
from processor_with_router import NewsProcessorWithRouter
from scraper import ImageFetcher

class TestDailyTokenUnits(unittest.TestCase):
    
    def test_router_pick_model(self):
        router = LLMRouter()
        model = router.pick_model()
        self.assertIsNotNone(model)
        self.assertIn(model.provider, ["huggingface", "openrouter"])

    def test_image_fetcher_candidates(self):
        # Use a reliable URL for testing
        url = "https://openai.com/news/introducing-openai-o1-preview/"
        candidates = ImageFetcher.get_candidate_images(url)
        self.assertIsInstance(candidates, list)
        # Even if 0 found, it should be a list. 
        # But usually OpenAI has og:image
        
    def test_processor_parsing(self):
        # Mocking or using a very simple test for parsing logic
        processor = NewsProcessorWithRouter()
        
        # Test headline cleaning
        raw = "HEADLINE: \"AI Breakthrough\"\nSUMMARY: This is a test.\nSELECTED_IMAGE_URL: https://example.com/img.jpg\nSIGNIFICANCE_SCORE: 90\nIMAGE_LAYOUT: WIDE"
        # We manually test the regex parts if possible or just the full flow with a mock
        
    def test_relevance_keywords(self):
        from scraper import NewsAggregator
        agg = NewsAggregator()
        stories = [
            {'title': 'New LLM from OpenAI', 'url': 'https://openai.com'},
            {'title': 'How to bake a cake', 'url': 'https://food.com'}
        ]
        filtered = agg.filter_ai_stories(stories)
        self.assertEqual(len(filtered), 1)
        self.assertIn('LLM', filtered[0]['title'])

if __name__ == '__main__':
    unittest.main()

