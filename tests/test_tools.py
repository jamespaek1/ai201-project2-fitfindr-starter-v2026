"""Development checks, not the five-try Unit 4 model evaluation."""
import unittest
from unittest.mock import patch

import tools
from generate import ModelUnavailable
from utils.data_loader import load_listings, get_example_wardrobe, get_empty_wardrobe


class SearchTests(unittest.TestCase):
    def test_real_listing_at_price_ceiling_and_split_size(self):
        found = tools.search_listings('graphic tee', 'm', 18)
        self.assertIn('lst_002', [item['id'] for item in found])
        self.assertTrue(all(item['price'] <= 18 for item in found))
        self.assertNotIn('lst_002', [i['id'] for i in tools.search_listings('graphic tee', 'M', 17.99)])

    def test_size_labels_do_not_match_substrings(self):
        records = load_listings()
        for query, forbidden in [('S', 'US 9'), ('L', 'XL')]:
            with self.subTest(query=query):
                found = tools.search_listings('vintage', query)
                self.assertFalse(any(i['size'].startswith(forbidden) for i in found))
        self.assertTrue(any(i['id'] == 'lst_003' for i in tools.search_listings('flannel', 'XL', 22)))

    def test_shoe_and_waist_sizes(self):
        for item in load_listings():
            if item['size'] in ('US 8.5', 'US 8'):
                self.assertIn(item, tools.search_listings(item['title'], item['size'][3:], item['price']))
        self.assertIn('lst_001', [i['id'] for i in tools.search_listings('jeans', 'W30', 38)])
        self.assertNotIn('lst_001', [i['id'] for i in tools.search_listings('jeans', 'W30 L32', 38)])

    def test_one_size_is_not_an_apparel_wildcard(self):
        self.assertTrue(tools._size_matches('one size', 'One Size (adjustable)'))
        self.assertTrue(tools._size_matches('one size', 'One Size / Oversized'))
        self.assertFalse(tools._size_matches('M', 'One Size'))

    def test_empty_and_impossible_searches(self):
        for description in ['', ' ', 'looking for a', 'xyzzynothing']:
            self.assertEqual(tools.search_listings(description), [])
        self.assertEqual(tools.search_listings('designer ballgown', 'XXS', 5), [])

    def test_nonfinite_and_negative_prices_are_rejected(self):
        for price in [-1, float('nan'), float('inf')]:
            with self.assertRaises(ValueError):
                tools.search_listings('tee', max_price=price)

    def test_repeatable_ranking_and_limit(self):
        with patch.object(tools.config, 'SEARCH_RESULT_LIMIT', 2):
            found = tools.search_listings('vintage')
            self.assertEqual(len(found), 2)
            self.assertEqual(found, tools.search_listings('VINTAGE'))
        self.assertEqual(tools.search_listings('graphic tees'), tools.search_listings('graphic tee'))


class PromptTests(unittest.TestCase):
    def setUp(self):
        self.item = load_listings()[1]  # null brand, S/M tee

    @patch('tools.generate', return_value='  Styling result.  ')
    def test_real_wardrobe_and_null_brand_are_preserved(self, generate):
        self.assertEqual(tools.suggest_outfit(self.item, get_example_wardrobe()), 'Styling result.')
        prompt = generate.call_args.args[0]
        self.assertIn('Baggy straight-leg jeans', prompt)
        self.assertIn('"brand": null', prompt)
        self.assertIn('do not invent owned clothing', prompt)

    @patch('tools.generate', return_value='General styling advice.')
    def test_empty_wardrobe_still_calls_model_for_general_advice(self, generate):
        self.assertEqual(tools.suggest_outfit(self.item, get_empty_wardrobe()), 'General styling advice.')
        self.assertIn('wardrobe is empty', generate.call_args.args[0])
        self.assertIn('do not claim the user owns', generate.call_args.args[0])

    @patch('tools.generate')
    def test_empty_input_guards_do_not_call_model(self, generate):
        self.assertEqual(tools.create_fit_card(' \n', self.item), 'No fit card: add an outfit suggestion first.')
        self.assertIn('select a listing', tools.suggest_outfit({}, get_empty_wardrobe()))
        self.assertIn('select a listing', tools.create_fit_card('jeans', {}))
        generate.assert_not_called()

    @patch('tools.generate', return_value='')
    def test_empty_model_output_is_not_success(self, generate):
        with self.assertRaises(ModelUnavailable):
            tools.create_fit_card('jeans', self.item)

    @patch('tools.generate', return_value='A caption.')
    def test_caption_receives_item_outfit_and_exact_price(self, generate):
        self.assertEqual(tools.create_fit_card('jeans and sneakers', self.item), 'A caption.')
        prompt = generate.call_args.args[0]
        self.assertIn('jeans and sneakers', prompt)
        self.assertIn('$18.00', prompt)
        self.assertIn('lst_002', prompt)
        self.assertIn('2 to 4 sentences', generate.call_args.kwargs['system'])


if __name__ == '__main__':
    unittest.main()
