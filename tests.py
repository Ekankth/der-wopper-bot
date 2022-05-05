#!/usr/bin/env python3
# Run as: ./tests.py

import bot  # check whether the file parses
import logic
import msg  # check keyset
import unittest


class TestMigration(unittest.TestCase):
    def check_dict(self, d1):
        g1 = logic.OngoingGame.from_dict(d1)
        d2 = g1.to_dict()
        g2 = logic.OngoingGame.from_dict(d2)
        d3 = g2.to_dict()
        self.assertEqual(d2, d3)

    def test_empty_v0(self):
        self.check_dict({
            'joined_users': {
                },
            'last_chooser': None,
            'last_chosen': None,
            'last_wop': 'w',  # This is actually possible!
            'init_datetime': 1234,
            })

    def test_nonempty_v0(self):
        self.check_dict({
            'joined_users': {
                'usna1': 'fina1',
                'usna2': 'fina2',
                'usna3': 'fina3',
                },
            'last_chooser': 'usna1',
            'last_chosen': 'usna2',
            'last_wop': 'p',
            'init_datetime': 1234,
            })

    def test_empty_v1(self):
        self.check_dict({
            'joined_users': {
                },
            'last_chooser': None,
            'last_chosen': None,
            'last_wop': None,
            'init_datetime': 1234,
            'track_overall': { 'g': 1, 'lc': {} },
            'track_individual': {
                }
            })

    def test_nonempty_v1(self):
        self.check_dict({
            'joined_users': {
                'usna1': 'fina1',
                'usna2': 'fina2',
                'usna3': 'fina3',
                },
            'last_chooser': 'usna1',
            'last_chosen': 'usna2',
            'last_wop': 'p',
            'init_datetime': 1234,
            'track_overall': { 'g': 1, 'lc': {'usna1': -2, 'usna2': -2, 'usna3': -2} },
            'track_individual': {
                'usna1': {'g': 1, 'lc': {'usna2': -2, 'usna3': -2}},
                'usna2': {'g': 1, 'lc': {'usna1': -2, 'usna3': -2}},
                'usna3': {'g': 1, 'lc': {'usna1': -2, 'usna2': -2}},
                }
            })


class TestSequences(unittest.TestCase):
    def check_sequence(self, sequence):
        game = logic.OngoingGame('Static seed for reproducible randomness, do not change')
        for i, (query, expected_response) in enumerate(sequence):
            with self.subTest(step=i):
                actual_response = logic.handle(game, *query)
                self.assertEqual(expected_response, actual_response)
                self.assertIn(expected_response[0], msg.MESSAGES.keys())
                if expected_response == actual_response and expected_response[0] in msg.MESSAGES.keys():
                    # Check that all templates all work:
                    for template in msg.MESSAGES[expected_response[0]]:
                        self.assertTrue(template.format(*expected_response[1:]))
        d = game.to_dict()
        g2 = logic.OngoingGame.from_dict(d)
        d2 = g2.to_dict()
        self.assertEqual(d, d2)

    def test_empty(self):
        self.check_sequence([])

    def test_start(self):
        self.check_sequence([
            (('start', '', 'fina', 'usna'), ('unknown_command', 'fina')),
        ])

    def test_join(self):
        self.check_sequence([
            (('join', '', 'fina', 'usna'), ('welcome', 'fina')),
            (('join', '', 'fina', 'usna'), ('already_in', 'fina')),
        ])

    def test_join_no_username(self):
        self.check_sequence([
            (('join', '', 'fina', ''), ('welcome_no_username', 'fina')),
            (('join', '', 'fina', None), ('welcome_no_username', 'fina')),
        ])

    def test_leave(self):
        self.check_sequence([
            (('leave', '', 'fina', 'usna'), ('already_left', 'fina')),
        ])

    def test_join_leave(self):
        self.check_sequence([
            (('join', '', 'fina', 'usna'), ('welcome', 'fina')),
            (('leave', '', 'fina', 'usna'), ('leave', 'fina')),
            (('leave', '', 'fina', 'usna'), ('already_left', 'fina')),
            (('join', '', 'fina', 'usna'), ('welcome', 'fina')),
            (('leave', '', 'fina', 'usna'), ('leave', 'fina')),
            (('leave', '', 'fina', 'usna'), ('already_left', 'fina')),
        ])

    def test_random_nonplayer(self):
        self.check_sequence([
            (('random', '', 'fina', 'usna'), ('nonplayer', 'fina')),
        ])

    def test_random_nonplayer_nonempty(self):
        self.check_sequence([
            (('join', '', 'a', 'a'), ('welcome', 'a')),
            (('join', '', 'b', 'b'), ('welcome', 'b')),
            (('random', '', 'fina', 'usna'), ('nonplayer', 'fina')),
        ])

    def test_random_singleplayer(self):
        self.check_sequence([
            (('join', '', 'fina', 'usna'), ('welcome', 'fina')),
            (('random', '', 'fina', 'usna'), ('random_singleplayer', 'fina')),
            (('random', '', 'fina', 'usna'), ('random_singleplayer', 'fina')),
        ])

    def test_random_twoplayer(self):
        self.check_sequence([
            (('join', '', 'fina', 'usna'), ('welcome', 'fina')),
            (('join', '', 'ofina', 'ousna'), ('welcome', 'ofina')),
            (('random', '', 'fina', 'usna'), ('random_chosen', 'ousna')),
            (('random', '', 'ofina', 'ousna'), ('random_chosen', 'usna')),
            (('random', '', 'fina', 'usna'), ('random_chosen', 'ousna')),
            (('random', '', 'ofina', 'ousna'), ('random_chosen', 'usna')),
        ])

    def test_true_random_twoplayer(self):
        self.check_sequence([
            (('join', '', 'fina', 'usna'), ('welcome', 'fina')),
            (('join', '', 'ofina', 'ousna'), ('welcome', 'ofina')),
            (('true_random', '', 'fina', 'usna'), ('random_chosen', 'ousna')),
            (('true_random', '', 'ofina', 'ousna'), ('random_chosen', 'usna')),
            (('true_random', '', 'fina', 'usna'), ('random_chosen', 'ousna')),
            (('true_random', '', 'ofina', 'ousna'), ('random_chosen', 'usna')),
        ])

    def test_random_chosen_left(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('leave', '', 'fina2', 'usna2'), ('leave', 'fina2')),  # ← 'chosen' leaves!
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna3')),  # chooser tries again
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('leave', '', 'fina2', 'usna2'), ('leave', 'fina2')),  # ← 'chosen' leaves!
            (('random', '', 'fina3', 'usna3'), ('random_chosen', 'usna1')),  # someone else tries again
        ])

    def test_true_random_chosen_left(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('true_random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('leave', '', 'fina2', 'usna2'), ('leave', 'fina2')),  # ← 'chosen' leaves!
            (('true_random', '', 'fina1', 'usna1'), ('random_chosen', 'usna3')),  # chooser tries again
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('true_random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('leave', '', 'fina2', 'usna2'), ('leave', 'fina2')),  # ← 'chosen' leaves!
            (('true_random', '', 'fina3', 'usna3'), ('random_chosen', 'usna1')),  # someone else tries again
        ])

    def test_random_chooser_left(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('leave', '', 'fina1', 'usna1'), ('leave', 'fina1')),  # ← 'chooser' leaves!
            (('random', '', 'fina2', 'usna2'), ('random_chosen', 'usna3')),  # chosen continues game
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('leave', '', 'fina1', 'usna1'), ('leave', 'fina1')),  # ← 'chooser' leaves!
            (('random', '', 'fina3', 'usna3'), ('random_chosen', 'usna2')),  # someone else tries again
        ])

    def test_true_random_chooser_left(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('true_random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('leave', '', 'fina1', 'usna1'), ('leave', 'fina1')),  # ← 'chooser' leaves!
            (('true_random', '', 'fina2', 'usna2'), ('random_chosen', 'usna3')),  # chosen continues game
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('true_random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('leave', '', 'fina1', 'usna1'), ('leave', 'fina1')),  # ← 'chooser' leaves!
            (('true_random', '', 'fina3', 'usna3'), ('random_chosen', 'usna2')),  # someone else tries again
        ])

    def test_random_wrong(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('random', '', 'fina3', 'usna3'), ('random_not_involved', 'fina3', 'fina1', 'usna2')),  # Not your turn!
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('random', '', 'fina1', 'usna1'), ('random_already_chosen', 'fina1', 'usna2')),  # Already chosen!
        ])

    def test_random_several(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),  # Relies on seeded RNG
            (('random', '', 'fina2', 'usna2'), ('random_chosen', 'usna1')),  # Relies on seeded RNG
        ])

    def test_show_random_several(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 18), ('usna3', 18)]")),
            (('show_random', 'usna1', 'fina1', 'usna1'), ('debug1', "[('usna2', 18), ('usna3', 18)]")),
            (('show_random', 'usna2', 'fina1', 'usna1'), ('debug1', "[('usna1', 18), ('usna3', 18)]")),
            (('show_random', 'usna3', 'fina1', 'usna1'), ('debug1', "[('usna1', 18), ('usna2', 18)]")),
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 18), ('usna2', 18)]")),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),  # Relies on seeded RNG
            (('whytho', '', 'fina1', 'usna1'), ('debug1', "random[('usna2', 18), ('usna3', 18)]")),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 0), ('usna3', 32)]")),
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 25), ('usna3', 25)]")),  # <- The important one
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 25), ('usna2', 9)]")),
            (('random', '', 'fina2', 'usna2'), ('random_chosen', 'usna1')),  # Relies on seeded RNG
            (('whytho', '', 'fina2', 'usna2'), ('debug1', "random[('usna1', 25), ('usna3', 25)]")),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 1), ('usna3', 41)]")),  # <- The important one
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 0), ('usna3', 41)]")),
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 9), ('usna2', 10)]")),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna3')),  # Relies on seeded RNG
            (('whytho', '', 'fina1', 'usna1'), ('debug1', "random[('usna2', 1), ('usna3', 41)]")),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 5), ('usna3', 0)]")),
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 1), ('usna3', 16)]")),
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 10), ('usna2', 13)]")),  # <- The important one
            (('random', '', 'fina3', 'usna3'), ('random_chosen', 'usna1')),  # Relies on seeded RNG
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 10), ('usna3', 1)]")),  # <- The important one
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 0), ('usna3', 17)]")),
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 0), ('usna2', 25)]")),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),  # Relies on seeded RNG
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 0), ('usna3', 5)]")),
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 1), ('usna3', 20)]")),  # <- The important one
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 1), ('usna2', 16)]")),
            (('random', '', 'fina2', 'usna2'), ('random_chosen', 'usna3')),  # Relies on seeded RNG
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 1), ('usna3', 1)]")),
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 5), ('usna3', 0)]")),
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 4), ('usna2', 17)]")),  # <- The important one
        ])

    @unittest.skip('Not an actual test, just generates test data, must be sanity-checked by human')
    def test_make_reference(self):
        game = logic.OngoingGame('Static seed for reproducible randomness, do not change')
        def observe(*tuple_in):
            tuple_out = logic.handle(game, *tuple_in)
            print((tuple_in, tuple_out))
            return tuple_out
        num_players = 5
        num_turns = 20
        for i in range(1, num_players + 1):
            observe('join', '', f'fina{i}', f'usna{i}')
        current_player = 'usna1'
        for step in range(num_turns):
            for i in range(1, num_players + 1):
                observe('show_random', '', f'fina{i}', f'usna{i}')
            tuple_out = observe('random', '', current_player.replace('usna', 'fina'), current_player)
            assert tuple_out[0] == 'random_chosen'
            current_player = tuple_out[1]

    def test_show_random_many(self):
        # Use test_make_reference to generate, then sanity-check by hand!
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('join', '', 'fina4', 'usna4'), ('welcome', 'fina4')),
            (('join', '', 'fina5', 'usna5'), ('welcome', 'fina5')),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 18), ('usna3', 18), ('usna4', 18), ('usna5', 18)]")),
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 18), ('usna3', 18), ('usna4', 18), ('usna5', 18)]")),
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 18), ('usna2', 18), ('usna4', 18), ('usna5', 18)]")),
            (('show_random', '', 'fina4', 'usna4'), ('debug1', "[('usna1', 18), ('usna2', 18), ('usna3', 18), ('usna5', 18)]")),
            (('show_random', '', 'fina5', 'usna5'), ('debug1', "[('usna1', 18), ('usna2', 18), ('usna3', 18), ('usna4', 18)]")),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna3')),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 32), ('usna3', 0), ('usna4', 32), ('usna5', 32)]")),
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 25), ('usna3', 9), ('usna4', 25), ('usna5', 25)]")),
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 25), ('usna2', 25), ('usna4', 25), ('usna5', 25)]")),  # <- The important one
            (('show_random', '', 'fina4', 'usna4'), ('debug1', "[('usna1', 25), ('usna2', 25), ('usna3', 9), ('usna5', 25)]")),
            (('show_random', '', 'fina5', 'usna5'), ('debug1', "[('usna1', 25), ('usna2', 25), ('usna3', 9), ('usna4', 25)]")),
            (('random', '', 'fina3', 'usna3'), ('random_chosen', 'usna2')),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 16), ('usna3', 1), ('usna4', 41), ('usna5', 41)]")),
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 34), ('usna3', 10), ('usna4', 34), ('usna5', 34)]")),  # <- The important one
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 41), ('usna2', 0), ('usna4', 41), ('usna5', 41)]")),
            (('show_random', '', 'fina4', 'usna4'), ('debug1', "[('usna1', 34), ('usna2', 9), ('usna3', 10), ('usna5', 34)]")),
            (('show_random', '', 'fina5', 'usna5'), ('debug1', "[('usna1', 34), ('usna2', 9), ('usna3', 10), ('usna4', 34)]")),
            (('random', '', 'fina2', 'usna2'), ('random_chosen', 'usna4')),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 17), ('usna3', 4), ('usna4', 16), ('usna5', 52)]")),
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 52), ('usna3', 20), ('usna4', 0), ('usna5', 52)]")),
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 52), ('usna2', 1), ('usna4', 16), ('usna5', 52)]")),
            (('show_random', '', 'fina4', 'usna4'), ('debug1', "[('usna1', 45), ('usna2', 10), ('usna3', 13), ('usna5', 45)]")),  # <- The important one
            (('show_random', '', 'fina5', 'usna5'), ('debug1', "[('usna1', 45), ('usna2', 10), ('usna3', 13), ('usna4', 9)]")),
            (('random', '', 'fina4', 'usna4'), ('random_chosen', 'usna2')),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 16), ('usna3', 9), ('usna4', 17), ('usna5', 65)]")),
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 65), ('usna3', 25), ('usna4', 1), ('usna5', 65)]")),  # <- The important one
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 65), ('usna2', 0), ('usna4', 17), ('usna5', 65)]")),
            (('show_random', '', 'fina4', 'usna4'), ('debug1', "[('usna1', 65), ('usna2', 0), ('usna3', 25), ('usna5', 65)]")),
            (('show_random', '', 'fina5', 'usna5'), ('debug1', "[('usna1', 58), ('usna2', 9), ('usna3', 18), ('usna4', 10)]")),
            (('random', '', 'fina2', 'usna2'), ('random_chosen', 'usna5')),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 17), ('usna3', 16), ('usna4', 20), ('usna5', 16)]")),
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 89), ('usna3', 41), ('usna4', 5), ('usna5', 0)]")),
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 80), ('usna2', 1), ('usna4', 20), ('usna5', 16)]")),
            (('show_random', '', 'fina4', 'usna4'), ('debug1', "[('usna1', 80), ('usna2', 1), ('usna3', 32), ('usna5', 16)]")),
            (('show_random', '', 'fina5', 'usna5'), ('debug1', "[('usna1', 73), ('usna2', 10), ('usna3', 25), ('usna4', 13)]")),  # <- The important one
            (('random', '', 'fina5', 'usna5'), ('random_chosen', 'usna2')),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 16), ('usna3', 25), ('usna4', 25), ('usna5', 17)]")),
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 106), ('usna3', 50), ('usna4', 10), ('usna5', 1)]")),  # <- The important one
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 97), ('usna2', 0), ('usna4', 25), ('usna5', 17)]")),
            (('show_random', '', 'fina4', 'usna4'), ('debug1', "[('usna1', 97), ('usna2', 0), ('usna3', 41), ('usna5', 17)]")),
            (('show_random', '', 'fina5', 'usna5'), ('debug1', "[('usna1', 97), ('usna2', 0), ('usna3', 41), ('usna4', 25)]")),
            (('random', '', 'fina2', 'usna2'), ('random_chosen', 'usna1')),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 17), ('usna3', 36), ('usna4', 32), ('usna5', 20)]")),  # <- The important one
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 0), ('usna3', 72), ('usna4', 20), ('usna5', 5)]")),
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 16), ('usna2', 1), ('usna4', 32), ('usna5', 20)]")),
            (('show_random', '', 'fina4', 'usna4'), ('debug1', "[('usna1', 16), ('usna2', 1), ('usna3', 52), ('usna5', 20)]")),
            (('show_random', '', 'fina5', 'usna5'), ('debug1', "[('usna1', 16), ('usna2', 1), ('usna3', 52), ('usna4', 32)]")),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna5')),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 29), ('usna3', 50), ('usna4', 50), ('usna5', 0)]")),
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 1), ('usna3', 85), ('usna4', 29), ('usna5', 1)]")),
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 17), ('usna2', 4), ('usna4', 41), ('usna5', 16)]")),
            (('show_random', '', 'fina4', 'usna4'), ('debug1', "[('usna1', 17), ('usna2', 4), ('usna3', 65), ('usna5', 16)]")),
            (('show_random', '', 'fina5', 'usna5'), ('debug1', "[('usna1', 17), ('usna2', 4), ('usna3', 65), ('usna4', 41)]")),  # <- The important one
            (('random', '', 'fina5', 'usna5'), ('random_chosen', 'usna3')),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 34), ('usna3', 1), ('usna4', 61), ('usna5', 1)]")),
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 4), ('usna3', 36), ('usna4', 40), ('usna5', 2)]")),
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 20), ('usna2', 9), ('usna4', 52), ('usna5', 17)]")),  # <- The important one
            (('show_random', '', 'fina4', 'usna4'), ('debug1', "[('usna1', 20), ('usna2', 9), ('usna3', 16), ('usna5', 17)]")),
            (('show_random', '', 'fina5', 'usna5'), ('debug1', "[('usna1', 29), ('usna2', 10), ('usna3', 0), ('usna4', 61)]")),
            (('random', '', 'fina3', 'usna3'), ('random_chosen', 'usna4')),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 41), ('usna3', 2), ('usna4', 25), ('usna5', 4)]")),
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 9), ('usna3', 37), ('usna4', 4), ('usna5', 5)]")),
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 34), ('usna2', 17), ('usna4', 0), ('usna5', 29)]")),
            (('show_random', '', 'fina4', 'usna4'), ('debug1', "[('usna1', 25), ('usna2', 16), ('usna3', 17), ('usna5', 20)]")),  # <- The important one
            (('show_random', '', 'fina5', 'usna5'), ('debug1', "[('usna1', 34), ('usna2', 17), ('usna3', 1), ('usna4', 25)]")),
            (('random', '', 'fina4', 'usna4'), ('random_chosen', 'usna1')),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 50), ('usna3', 5), ('usna4', 26), ('usna5', 9)]")),  # <- The important one
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 0), ('usna3', 40), ('usna4', 5), ('usna5', 10)]")),
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 25), ('usna2', 26), ('usna4', 1), ('usna5', 34)]")),
            (('show_random', '', 'fina4', 'usna4'), ('debug1', "[('usna1', 0), ('usna2', 26), ('usna3', 29), ('usna5', 34)]")),
            (('show_random', '', 'fina5', 'usna5'), ('debug1', "[('usna1', 25), ('usna2', 26), ('usna3', 4), ('usna4', 26)]")),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 0), ('usna3', 13), ('usna4', 40), ('usna5', 17)]")),
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 1), ('usna3', 45), ('usna4', 8), ('usna5', 17)]")),  # <- The important one
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 26), ('usna2', 1), ('usna4', 4), ('usna5', 41)]")),
            (('show_random', '', 'fina4', 'usna4'), ('debug1', "[('usna1', 1), ('usna2', 1), ('usna3', 34), ('usna5', 41)]")),
            (('show_random', '', 'fina5', 'usna5'), ('debug1', "[('usna1', 26), ('usna2', 1), ('usna3', 9), ('usna4', 29)]")),
            (('random', '', 'fina2', 'usna2'), ('random_chosen', 'usna4')),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 1), ('usna3', 20), ('usna4', 36), ('usna5', 26)]")),
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 5), ('usna3', 65), ('usna4', 0), ('usna5', 29)]")),
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 29), ('usna2', 2), ('usna4', 0), ('usna5', 50)]")),
            (('show_random', '', 'fina4', 'usna4'), ('debug1', "[('usna1', 4), ('usna2', 2), ('usna3', 41), ('usna5', 50)]")),  # <- The important one
            (('show_random', '', 'fina5', 'usna5'), ('debug1', "[('usna1', 29), ('usna2', 2), ('usna3', 16), ('usna4', 25)]")),
            (('random', '', 'fina4', 'usna4'), ('random_chosen', 'usna5')),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 4), ('usna3', 29), ('usna4', 37), ('usna5', 1)]")),
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 10), ('usna3', 74), ('usna4', 1), ('usna5', 4)]")),
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 34), ('usna2', 5), ('usna4', 1), ('usna5', 25)]")),
            (('show_random', '', 'fina4', 'usna4'), ('debug1', "[('usna1', 10), ('usna2', 8), ('usna3', 61), ('usna5', 0)]")),
            (('show_random', '', 'fina5', 'usna5'), ('debug1', "[('usna1', 34), ('usna2', 5), ('usna3', 25), ('usna4', 26)]")),  # <- The important one
            (('random', '', 'fina5', 'usna5'), ('random_chosen', 'usna1')),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 9), ('usna3', 40), ('usna4', 40), ('usna5', 2)]")),  # <- The important one
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 1), ('usna3', 85), ('usna4', 4), ('usna5', 5)]")),
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 25), ('usna2', 10), ('usna4', 4), ('usna5', 26)]")),
            (('show_random', '', 'fina4', 'usna4'), ('debug1', "[('usna1', 1), ('usna2', 13), ('usna3', 72), ('usna5', 1)]")),
            (('show_random', '', 'fina5', 'usna5'), ('debug1', "[('usna1', 0), ('usna2', 13), ('usna3', 37), ('usna4', 40)]")),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna4')),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 17), ('usna3', 58), ('usna4', 0), ('usna5', 8)]")),
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 2), ('usna3', 98), ('usna4', 0), ('usna5', 8)]")),
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 26), ('usna2', 17), ('usna4', 0), ('usna5', 29)]")),
            (('show_random', '', 'fina4', 'usna4'), ('debug1', "[('usna1', 2), ('usna2', 20), ('usna3', 85), ('usna5', 4)]")),  # <- The important one
            (('show_random', '', 'fina5', 'usna5'), ('debug1', "[('usna1', 1), ('usna2', 20), ('usna3', 50), ('usna4', 36)]")),
            (('random', '', 'fina4', 'usna4'), ('random_chosen', 'usna1')),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 26), ('usna3', 73), ('usna4', 1), ('usna5', 13)]")),  # <- The important one
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 1), ('usna3', 113), ('usna4', 1), ('usna5', 13)]")),
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 25), ('usna2', 26), ('usna4', 1), ('usna5', 34)]")),
            (('show_random', '', 'fina4', 'usna4'), ('debug1', "[('usna1', 0), ('usna2', 34), ('usna3', 113), ('usna5', 10)]")),
            (('show_random', '', 'fina5', 'usna5'), ('debug1', "[('usna1', 0), ('usna2', 29), ('usna3', 65), ('usna4', 37)]")),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna5')),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 40), ('usna3', 97), ('usna4', 5), ('usna5', 0)]")),
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 2), ('usna3', 130), ('usna4', 4), ('usna5', 4)]")),
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 26), ('usna2', 37), ('usna4', 4), ('usna5', 25)]")),
            (('show_random', '', 'fina4', 'usna4'), ('debug1', "[('usna1', 1), ('usna2', 45), ('usna3', 130), ('usna5', 1)]")),
            (('show_random', '', 'fina5', 'usna5'), ('debug1', "[('usna1', 1), ('usna2', 40), ('usna3', 82), ('usna4', 40)]")),  # <- The important one
            (('random', '', 'fina5', 'usna5'), ('random_chosen', 'usna2')),
            (('show_random', '', 'fina1', 'usna1'), ('debug1', "[('usna2', 4), ('usna3', 116), ('usna4', 10), ('usna5', 1)]")),
            (('show_random', '', 'fina2', 'usna2'), ('debug1', "[('usna1', 5), ('usna3', 149), ('usna4', 9), ('usna5', 5)]")),  # <- The important one
            (('show_random', '', 'fina3', 'usna3'), ('debug1', "[('usna1', 29), ('usna2', 1), ('usna4', 9), ('usna5', 26)]")),
            (('show_random', '', 'fina4', 'usna4'), ('debug1', "[('usna1', 4), ('usna2', 9), ('usna3', 149), ('usna5', 2)]")),
            (('show_random', '', 'fina5', 'usna5'), ('debug1', "[('usna1', 5), ('usna2', 0), ('usna3', 104), ('usna4', 58)]")),
            (('random', '', 'fina2', 'usna2'), ('random_chosen', 'usna3')),
            # usna3 had to wait for quite a long time (10 turns), but the probabilities were high to be chosen at any point.
            # I'll attribute this as being a "medium-bad run", which shouldn't have happened, but oh well.
        ])

    def test_true_random_several(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('true_random', '', 'fina1', 'usna1'), ('random_chosen', 'usna3')),  # Relies on seeded RNG
            (('true_random', '', 'fina3', 'usna3'), ('random_chosen', 'usna2')),  # Relies on seeded RNG
        ])

    def test_whytho(self):
        self.check_sequence([
            (('whytho', '', 'fina1', 'usna1'), ('debug1', "dunno")),
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('whytho', '', 'fina1', 'usna1'), ('debug1', "dunno")),
            (('whytho', '', 'fina2', 'usna2'), ('debug1', "dunno")),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('whytho', '', 'fina1', 'usna1'), ('debug1', "random[('usna2', 18)]")),
            (('true_random', '', 'fina2', 'usna2'), ('random_chosen', 'usna1')),
            (('whytho', '', 'fina1', 'usna1'), ('debug1', "true_random['fina1']")),
            (('choose', 'usna2', 'fina1', 'usna1'), ('chosen_chosen', 'usna2', 'fina1')),
            (('whytho', '', 'fina1', 'usna1'), ('debug1', "choose")),
        ])

    def test_wop_nonplayer(self):
        self.check_sequence([
            (('wop', '', 'fina', 'usna'), ('nonplayer', 'fina')),
        ])

    def test_wop_nobodychosen(self):
        self.check_sequence([
            (('join', '', 'fina', 'usna'), ('welcome', 'fina')),
            (('wop', '', 'fina', 'usna'), ('wop_nobodychosen', 'fina', 'Pflicht')),  # Relies on seeded RNG
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('leave', '', 'fina2', 'usna2'), ('leave', 'fina2')),
            (('wop', '', 'fina1', 'usna1'), ('wop_nobodychosen', 'fina1', 'Pflicht')),  # Relies on seeded RNG
        ])

    def test_wop_nonchosen(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('wop', '', 'fina1', 'usna1'), ('wop_nonchosen', 'fina1', 'usna2')),
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('leave', '', 'fina1', 'usna1'), ('leave', 'fina1')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('wop', '', 'fina3', 'usna3'), ('wop_nonchosen', 'fina3', 'usna2')),
        ])

    def test_wop_regular(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('wop', '', 'fina2', 'usna2'), ('wop_result_p', 'fina2', 'usna1')),  # Relies on seeded RNG
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('leave', '', 'fina1', 'usna1'), ('leave', 'fina1')),
            (('wop', '', 'fina2', 'usna2'), ('wop_result_p', 'fina2', '???')),  # Relies on seeded RNG
        ])

    def test_wop_again(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('wop', '', 'fina2', 'usna2'), ('wop_result_p', 'fina2', 'usna1')),  # Relies on seeded RNG
            (('wop', '', 'fina2', 'usna2'), ('wop_again', 'fina2', 'Pflicht', 'usna1')),  # Must be the same result
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('wop', '', 'fina2', 'usna2'), ('wop_result_p', 'fina2', 'usna1')),  # Relies on seeded RNG
            (('leave', '', 'fina1', 'usna1'), ('leave', 'fina1')),
            (('wop', '', 'fina2', 'usna2'), ('wop_again', 'fina2', 'Pflicht', '???')),  # Must be the same result
        ])

    def test_who_error(self):
        self.check_sequence([
            (('who', '', 'qfina', 'qusna'), ('who_nobody', 'qfina')),
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('leave', '', 'fina1', 'usna1'), ('leave', 'fina1')),
            (('who', '', 'qfina', 'qusna'), ('who_no_chooser', 'qfina', 'usna2')),
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('leave', '', 'fina2', 'usna2'), ('leave', 'fina2')),
            (('who', '', 'qfina', 'qusna'), ('who_no_chosen', 'usna1')),
        ])

    def test_who_regular(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('who', '', 'qfina', 'qusna'), ('who_no_wop', 'usna1', 'usna2')),
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('wop', '', 'fina2', 'usna2'), ('wop_result_p', 'fina2', 'usna1')),  # Relies on seeded RNG
            (('who', '', 'qfina', 'qusna'), ('who_wop_p', 'fina1', 'usna2')),
        ])

    def test_players_zero(self):
        self.check_sequence([
            (('players', '', 'fina1', 'usna1'), ('players_nobody', 'fina1')),
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('leave', '', 'fina1', 'usna1'), ('leave', 'fina1')),
            (('players', '', 'qfina', 'qusna'), ('players_nobody', 'qfina')),
        ])

    def test_players_one(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('players', '', 'fina1', 'usna1'), ('players_one_self', 'fina1', 'fina1')),
            (('players', '', 'fina2', 'usna2'), ('players_one_other', 'fina2', 'fina1')),
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('leave', '', 'fina2', 'usna2'), ('leave', 'fina2')),
            (('players', '', 'fina1', 'usna1'), ('players_one_self', 'fina1', 'fina1')),
            (('players', '', 'fina2', 'usna2'), ('players_one_other', 'fina2', 'fina1')),
        ])

    def test_players_few(self):
        self.check_sequence([
            (('join', '', 'a', 'ua'), ('welcome', 'a')),
            (('join', '', 'b', 'ub'), ('welcome', 'b')),
            (('players', '', 'a', 'ua'), ('players_few_self', 'a', 'a und b')),
            (('players', '', 'xx', 'uxx'), ('players_few_other', 'xx', 'a und b')),
            (('join', '', 'c', 'uc'), ('welcome', 'c')),
            (('players', '', 'a', 'ua'), ('players_few_self', 'a', 'a, b und c')),
            (('players', '', 'xx', 'uxx'), ('players_few_other', 'xx', 'a, b und c')),
            (('join', '', 'd', 'ud'), ('welcome', 'd')),
            (('players', '', 'a', 'ua'), ('players_few_self', 'a', 'a, b, c und d')),
            (('players', '', 'xx', 'uxx'), ('players_few_other', 'xx', 'a, b, c und d')),
        ])

    def test_players_many(self):
        self.check_sequence([
            (('join', '', 'e', 'ue'), ('welcome', 'e')),
            (('join', '', 'd', 'ud'), ('welcome', 'd')),
            (('join', '', 'c', 'uc'), ('welcome', 'c')),
            (('join', '', 'b', 'ub'), ('welcome', 'b')),
            (('join', '', 'a', 'ua'), ('welcome', 'a')),
            (('players', '', 'a', 'ua'), ('players_many_self', 'a', 'a, b, c, d und e')),
            (('players', '', 'xx', 'uxx'), ('players_many_other', 'xx', 'a, b, c, d und e')),
            (('join', '', 'f', 'uf'), ('welcome', 'f')),
            (('players', '', 'a', 'ua'), ('players_many_self', 'a', 'a, b, c, d, e und f')),
            (('players', '', 'xx', 'uxx'), ('players_many_other', 'xx', 'a, b, c, d, e und f')),
        ])

    def test_kick_nonplayer(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('kick', '', 'qfina', 'qusna'), ('kick_nonplayer', 'qfina')),
        ])
        self.check_sequence([
            (('kick', '', 'qfina', 'qusna'), ('kick_nonplayer', 'qfina')),
        ])

    def test_kick_no_chosen(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('kick', '', 'fina1', 'usna1'), ('kick_no_chosen', 'fina1')),
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('leave', '', 'fina2', 'usna2'), ('leave', 'fina2')),
            (('kick', '', 'fina1', 'usna1'), ('kick_no_chosen', 'fina1')),
        ])

    def test_kick_regular(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('kick', '', 'fina1', 'usna1'), ('kick', 'fina1', 'usna2')),
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('kick', '', 'fina2', 'usna2'), ('kick', 'fina2', 'usna2')),  # Self-kick is okay I guess?
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('kick', '', 'fina3', 'usna3'), ('kick', 'fina3', 'usna2')),  # join-kick is okay I guess?
        ])

    def test_kick_regular_function(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('kick', '', 'fina1', 'usna1'), ('kick', 'fina1', 'usna2')),
            (('leave', '', 'fina2', 'usna2'), ('already_left', 'fina2')),
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('kick', '', 'fina2', 'usna2'), ('kick', 'fina2', 'usna2')),  # Self-kick is okay I guess?
            (('leave', '', 'fina2', 'usna2'), ('already_left', 'fina2')),
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('kick', '', 'fina3', 'usna3'), ('kick', 'fina3', 'usna2')),  # join-kick is okay I guess?
            (('leave', '', 'fina2', 'usna2'), ('already_left', 'fina2')),
        ])

    def test_choose_nonplayer(self):
        self.check_sequence([
            (('choose', 'asdf', 'fina', 'usna'), ('nonplayer', 'fina')),
            (('choose', '', 'fina', 'usna'), ('nonplayer', 'fina')),
            (('choose', 'usna', 'fina', 'usna'), ('nonplayer', 'fina')),
        ])

    def test_choose_nonplayer_nonempty(self):
        self.check_sequence([
            (('join', '', 'a', 'a'), ('welcome', 'a')),
            (('join', '', 'b', 'b'), ('welcome', 'b')),
            (('choose', 'asdf', 'fina', 'usna'), ('nonplayer', 'fina')),
            (('choose', '', 'fina', 'usna'), ('nonplayer', 'fina')),
            (('choose', 'usna', 'fina', 'usna'), ('nonplayer', 'fina')),
        ])

    def test_choose_singleplayer(self):
        self.check_sequence([
            (('join', '', 'fina', 'usna'), ('welcome', 'fina')),
            (('choose', 'asdf', 'fina', 'usna'), ('random_singleplayer', 'fina')),
            (('choose', 'asdf', 'fina', 'usna'), ('random_singleplayer', 'fina')),
            (('choose', '', 'fina', 'usna'), ('random_singleplayer', 'fina')),
            (('choose', 'usna', 'fina', 'usna'), ('random_singleplayer', 'fina')),
        ])

    def test_choose_twoplayer(self):
        self.check_sequence([
            (('join', '', 'fina', 'usna'), ('welcome', 'fina')),
            (('join', '', 'ofina', 'ousna'), ('welcome', 'ofina')),
            (('choose', 'ousna', 'fina', 'usna'), ('chosen_chosen', 'ousna', 'fina')),
            (('choose', 'usna', 'ofina', 'ousna'), ('chosen_chosen', 'usna', 'ofina')),
            (('choose', 'ousna', 'fina', 'usna'), ('chosen_chosen', 'ousna', 'fina')),
            (('choose', 'usna', 'ofina', 'ousna'), ('chosen_chosen', 'usna', 'ofina')),
        ])

    def test_choose_form_at(self):
        self.check_sequence([
            (('join', '', 'fina', 'usna'), ('welcome', 'fina')),
            (('join', '', 'ofina', 'ousna'), ('welcome', 'ofina')),
            (('choose', '@ousna', 'fina', 'usna'), ('chosen_chosen', 'ousna', 'fina')),
        ])

    def test_choose_form_fina(self):
        self.check_sequence([
            (('join', '', 'fina', 'usna'), ('welcome', 'fina')),
            (('join', '', 'ofina', 'ousna'), ('welcome', 'ofina')),
            (('choose', 'ofina', 'fina', 'usna'), ('chosen_chosen', 'ousna', 'fina')),
        ])

    def test_choose_emptyarg(self):
        self.check_sequence([
            (('join', '', 'fina', 'usna'), ('welcome', 'fina')),
            (('join', '', 'ofina', 'ousna'), ('welcome', 'ofina')),
            (('choose', '', 'fina', 'usna'), ('chosen_empty', 'fina', 'usna')),
        ])

    def test_choose_self(self):
        self.check_sequence([
            (('join', '', 'fina', 'usna'), ('welcome', 'fina')),
            (('join', '', 'ofina', 'ousna'), ('welcome', 'ofina')),
            (('choose', 'usna', 'fina', 'usna'), ('chosen_self', 'fina')),
        ])

    def test_choose_chosen_left(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('choose', 'usna2', 'fina1', 'usna1'), ('chosen_chosen', 'usna2', 'fina1')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('leave', '', 'fina2', 'usna2'), ('leave', 'fina2')),  # ← 'chosen' leaves!
            (('choose', 'usna3', 'fina1', 'usna1'), ('chosen_chosen', 'usna3', 'fina1')),  # chooser tries again
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('choose', 'usna2', 'fina1', 'usna1'), ('chosen_chosen', 'usna2', 'fina1')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('leave', '', 'fina2', 'usna2'), ('leave', 'fina2')),  # ← 'chosen' leaves!
            (('choose', 'usna1', 'fina3', 'usna3'), ('chosen_chosen', 'usna1', 'fina3')),  # someone else tries again
        ])

    def test_choose_chooser_left(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('choose', 'usna2', 'fina1', 'usna1'), ('chosen_chosen', 'usna2', 'fina1')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('leave', '', 'fina1', 'usna1'), ('leave', 'fina1')),  # ← 'chooser' leaves!
            (('choose', 'usna3', 'fina2', 'usna2'), ('chosen_chosen', 'usna3', 'fina2')),  # chosen continues game
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('choose', 'usna2', 'fina1', 'usna1'), ('chosen_chosen', 'usna2', 'fina1')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('leave', '', 'fina1', 'usna1'), ('leave', 'fina1')),  # ← 'chooser' leaves!
            (('choose', 'usna2', 'fina3', 'usna3'), ('chosen_chosen', 'usna2', 'fina3')),  # someone else tries again
        ])

    def test_choose_wrong(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('choose', 'usna2', 'fina1', 'usna1'), ('chosen_chosen', 'usna2', 'fina1')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('choose', 'usna1', 'fina3', 'usna3'), ('random_not_involved', 'fina3', 'fina1', 'usna2')),  # Not your turn!
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('choose', 'usna2', 'fina1', 'usna1'), ('chosen_chosen', 'usna2', 'fina1')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('choose', 'usna3', 'fina1', 'usna1'), ('random_already_chosen', 'fina1', 'usna2')),  # Already chosen!
        ])

    def test_choose_several(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('choose', 'usna3', 'fina1', 'usna1'), ('chosen_chosen', 'usna3', 'fina1')),
            (('choose', 'usna2', 'fina3', 'usna3'), ('chosen_chosen', 'usna2', 'fina3')),
        ])

    def test_dox_nonplayer(self):
        self.check_sequence([
            (('do_w', '', 'fina', 'usna'), ('nonplayer', 'fina')),
            (('do_p', '', 'fina', 'usna'), ('nonplayer', 'fina')),
        ])

    def test_dox_nonplayer_nonempty(self):
        self.check_sequence([
            (('join', '', 'a', 'a'), ('welcome', 'a')),
            (('join', '', 'b', 'b'), ('welcome', 'b')),
            (('do_w', '', 'fina', 'usna'), ('nonplayer', 'fina')),
            (('do_p', '', 'fina', 'usna'), ('nonplayer', 'fina')),
        ])

    def test_dox_nobody(self):
        self.check_sequence([
            (('join', '', 'fina', 'usna'), ('welcome', 'fina')),
            (('do_w', '', 'fina', 'usna'), ('dox_choose_first', 'fina')),
            (('do_p', '', 'fina', 'usna'), ('dox_choose_first', 'fina')),
        ])

    def test_dox_nochosen(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('leave', '', 'fina2', 'usna2'), ('leave', 'fina2')),
            (('do_w', '', 'fina1', 'usna1'), ('dox_choose_first', 'fina1')),
            (('do_p', '', 'fina1', 'usna1'), ('dox_choose_first', 'fina1')),
        ])

    def test_dox_nochooser(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('random', '', 'fina1', 'usna1'), ('random_chosen', 'usna2')),
            (('leave', '', 'fina1', 'usna1'), ('leave', 'fina1')),
            (('do_w', '', 'fina2', 'usna2'), ('dox_choose_first', 'fina2')),
            (('do_p', '', 'fina2', 'usna2'), ('dox_choose_first', 'fina2')),
        ])

    def test_dox_twoplayer(self):
        self.check_sequence([
            (('join', '', 'fina', 'usna'), ('welcome', 'fina')),
            (('join', '', 'ofina', 'ousna'), ('welcome', 'ofina')),
            (('choose', 'ousna', 'fina', 'usna'), ('chosen_chosen', 'ousna', 'fina')),
            (('do_w', '', 'ofina', 'ousna'), ('dox_w', 'ofina', 'usna')),
            (('choose', 'usna', 'ofina', 'ousna'), ('chosen_chosen', 'usna', 'ofina')),
            (('do_p', '', 'fina', 'usna'), ('dox_p', 'fina', 'ousna')),
        ])

    def test_dox_not_involved(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('join', '', 'fina3', 'usna3'), ('welcome', 'fina3')),
            (('choose', 'usna2', 'fina1', 'usna1'), ('chosen_chosen', 'usna2', 'fina1')),
            (('do_w', '', 'fina3', 'usna3'), ('dox_not_involved', 'fina3', 'usna2', 'fina1')),
            (('do_p', '', 'fina3', 'usna3'), ('dox_not_involved', 'fina3', 'usna2', 'fina1')),
        ])

    def test_dox_wrong_side(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('choose', 'usna2', 'fina1', 'usna1'), ('chosen_chosen', 'usna2', 'fina1')),
            (('do_w', '', 'fina1', 'usna1'), ('dox_wrong_side', 'fina1', 'usna2')),
            (('do_p', '', 'fina1', 'usna1'), ('dox_wrong_side', 'fina1', 'usna2')),
        ])

    def test_dox_again(self):
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('choose', 'usna2', 'fina1', 'usna1'), ('chosen_chosen', 'usna2', 'fina1')),
            (('do_w', '', 'fina2', 'usna2'), ('dox_w', 'fina2', 'usna1')),
            (('do_w', '', 'fina2', 'usna2'), ('dox_already_w', 'fina2', 'usna1')),
            (('do_p', '', 'fina2', 'usna2'), ('dox_already_w', 'fina2', 'usna1')),
            (('wop', '', 'fina2', 'usna2'), ('wop_again', 'fina2', 'Wahrheit', 'usna1')),
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('choose', 'usna2', 'fina1', 'usna1'), ('chosen_chosen', 'usna2', 'fina1')),
            (('do_p', '', 'fina2', 'usna2'), ('dox_p', 'fina2', 'usna1')),
            (('do_p', '', 'fina2', 'usna2'), ('dox_already_p', 'fina2', 'usna1')),
            (('do_w', '', 'fina2', 'usna2'), ('dox_already_p', 'fina2', 'usna1')),
            (('wop', '', 'fina2', 'usna2'), ('wop_again', 'fina2', 'Pflicht', 'usna1')),
        ])
        self.check_sequence([
            (('join', '', 'fina1', 'usna1'), ('welcome', 'fina1')),
            (('join', '', 'fina2', 'usna2'), ('welcome', 'fina2')),
            (('choose', 'usna2', 'fina1', 'usna1'), ('chosen_chosen', 'usna2', 'fina1')),
            (('wop', '', 'fina2', 'usna2'), ('wop_result_p', 'fina2', 'usna1')),  # Relies on seeded RNG
            (('do_p', '', 'fina2', 'usna2'), ('dox_already_p', 'fina2', 'usna1')),
            (('do_w', '', 'fina2', 'usna2'), ('dox_already_p', 'fina2', 'usna1')),
        ])


if __name__ == '__main__':
    unittest.main()
