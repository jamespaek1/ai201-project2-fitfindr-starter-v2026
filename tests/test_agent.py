import unittest
from copy import deepcopy
from unittest.mock import patch, Mock

import agent
from generate import ModelUnavailable
from utils.data_loader import get_example_wardrobe, load_listings


def named_mock(name, **kwargs):
    tool = Mock(**kwargs)
    tool.__name__ = name
    return tool


class ParsingTests(unittest.TestCase):
    def test_price_and_size_are_separate_from_description(self):
        self.assertEqual(agent.parse_query('vintage graphic tee under $30, size M'),
                         {'description': 'vintage graphic tee', 'size': 'M', 'max_price': 30.0})
        self.assertEqual(agent.parse_query('shoes size US 8.5 up to $25.50')['size'], 'US 8.5')
        self.assertEqual(agent.parse_query('jeans size W30 L30 max 40')['size'], 'W30 L30')
        self.assertEqual(agent.parse_query('hat size one size')['size'], 'ONE SIZE')

    def test_optional_filters_are_none(self):
        self.assertEqual(agent.parse_query('denim jacket'),
                         {'description': 'denim jacket', 'size': None, 'max_price': None})
        self.assertEqual(agent.parse_query('tee below 0')['max_price'], 0)
        self.assertEqual(agent.parse_query('tee at most $18')['max_price'], 18)

    def test_malformed_constraints_do_not_broaden_the_search(self):
        for query in ['', 'tee under $', 'tee under thirty', 'tee size',
                      'tee under $-1', 'tee under $20 under $30', 'tee size M size L',
                      'size M under $20', 'tee $20']:
            with self.subTest(query=query), self.assertRaises(ValueError):
                agent.parse_query(query)


class LoopTests(unittest.TestCase):
    def setUp(self):
        self.item = load_listings()[1]
        self.wardrobe = get_example_wardrobe()

    def test_happy_path_preserves_actual_inputs_and_call_order(self):
        search = named_mock('search_listings', return_value=[deepcopy(self.item)])
        outfit = named_mock('suggest_outfit', return_value='jeans and sneakers')
        card = named_mock('create_fit_card', return_value='A finished caption.')
        with patch.multiple(agent, search_listings=search, suggest_outfit=outfit, create_fit_card=card):
            session = agent.run_agent('graphic tee under $18, size M', self.wardrobe)
        self.assertIsNone(session['error'])
        self.assertEqual(session['iterations'], 3)
        self.assertEqual([c['tool'] for c in session['tool_calls']],
                         ['search_listings', 'suggest_outfit', 'create_fit_card'])
        self.assertEqual(session['selected_item'], self.item)
        # Assertions use observed mock calls, not merely a self-reported session log.
        self.assertIs(outfit.call_args.kwargs['new_item'], session['selected_item'])
        self.assertIs(card.call_args.kwargs['new_item'], session['selected_item'])
        self.assertEqual(card.call_args.kwargs['outfit'], session['outfit_suggestion'])
        self.assertEqual(session['tool_calls'][1]['inputs']['new_item'], outfit.call_args.kwargs['new_item'])
        self.assertEqual(session['tool_calls'][2]['inputs']['new_item'], card.call_args.kwargs['new_item'])
        self.assertEqual(session['fit_card'], 'A finished caption.')

    def test_real_empty_search_does_not_call_later_tools(self):
        outfit = named_mock('suggest_outfit')
        card = named_mock('create_fit_card')
        with patch.multiple(agent, suggest_outfit=outfit, create_fit_card=card):
            session = agent.run_agent('designer ballgown size XXS under $5', self.wardrobe)
        self.assertEqual([c['tool'] for c in session['tool_calls']], ['search_listings'])
        outfit.assert_not_called()
        card.assert_not_called()
        for field in ['selected_item', 'outfit_suggestion', 'fit_card']:
            self.assertIsNone(session[field])
        self.assertIn('broader keywords', session['error'])
        self.assertIn('another size', session['error'])
        self.assertIn('higher budget', session['error'])

    def test_provider_failure_preserves_search_and_stops(self):
        outfit = named_mock('suggest_outfit', side_effect=ModelUnavailable('Model unavailable. Try again.'))
        card = named_mock('create_fit_card')
        with patch.multiple(agent, suggest_outfit=outfit, create_fit_card=card):
            session = agent.run_agent('graphic tee size M under $18', self.wardrobe)
        self.assertEqual(session['selected_item']['id'], 'lst_002')
        self.assertIsNone(session['fit_card'])
        self.assertEqual(session['error'], 'Model unavailable. Try again.')
        card.assert_not_called()

    def test_iteration_guard_stops_before_second_call(self):
        with patch.object(agent.trace.config, 'MAX_ITERATIONS', 1):
            with self.assertRaisesRegex(RuntimeError, 'MAX_ITERATIONS'):
                agent.run_agent('graphic tee size M under $18', self.wardrobe)

    def test_sessions_do_not_share_user_mutable_state(self):
        one = agent.new_session('tee', self.wardrobe)
        two = agent.new_session('jeans', self.wardrobe)
        one['wardrobe']['items'].clear()
        one['tool_calls'].append({'tool': 'example'})
        self.assertEqual(len(two['wardrobe']['items']), 10)
        self.assertEqual(len(self.wardrobe['items']), 10)
        self.assertEqual(two['tool_calls'], [])

    def test_invalid_query_never_calls_search(self):
        with patch.object(agent, 'search_listings') as search:
            result = agent.run_agent('tee under $', self.wardrobe)
        search.assert_not_called()
        self.assertIsNotNone(result['error'])


if __name__ == '__main__':
    unittest.main()
