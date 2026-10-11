"""Run with: python -m unittest test_logic -v, or python test_logic.py."""

import contextlib
import io
import unittest

from agent import SearchAgent
from logic_engine import KnowledgeBase
from visual_grid_game import VisualGridHuntGame


def test_forward_chaining():
    """The two assert-based validation cases supplied in the worksheet."""
    kb = KnowledgeBase()
    kb.tell_rule(['TargetVisible', 'HasDust'], 'SafeToEngage')
    kb.tell_rule(['SafeToEngage', 'BloodseekerMissing'], 'Retreat')

    kb.clear_facts()
    kb.tell_fact('TargetVisible')
    kb.tell_fact('HasDust')
    kb.forward_chain()
    assert 'SafeToEngage' in kb.facts, 'Test 1 Failed: Should deduce SafeToEngage'
    assert 'Retreat' not in kb.facts, 'Test 1 Failed: Should NOT deduce Retreat'

    kb.clear_facts()
    kb.tell_fact('TargetVisible')
    kb.tell_fact('HasDust')
    kb.tell_fact('BloodseekerMissing')
    kb.forward_chain()
    assert 'Retreat' in kb.facts, 'Test 2 Failed: Should deduce Retreat'
    print('All Logic Engine Test Cases Passed!')


class TestKnowledgeBase(unittest.TestCase):
    def test_worksheet_cases(self):
        test_forward_chaining()

    def test_multiple_passes_and_rule_order(self):
        kb = KnowledgeBase()
        # The last deduction appears first: one pass alone cannot derive C.
        kb.tell_rule(['B'], 'C')
        kb.tell_rule(['A'], 'B')
        kb.tell_fact('A')
        kb.forward_chain()
        self.assertEqual(kb.facts, {'A', 'B', 'C'})

    def test_missing_premise_does_not_fire(self):
        kb = KnowledgeBase()
        kb.tell_rule(['TargetVisible', 'HasDust'], 'SafeToEngage')
        kb.tell_fact('TargetVisible')
        kb.forward_chain()
        self.assertNotIn('SafeToEngage', kb.facts)

    def test_clear_facts_preserves_rules(self):
        kb = KnowledgeBase()
        kb.tell_rule(['A'], 'B')
        kb.tell_fact('A')
        kb.forward_chain()
        kb.clear_facts()
        self.assertEqual(kb.facts, set())
        self.assertEqual(len(kb.rules), 1)
        kb.forward_chain()
        self.assertNotIn('B', kb.facts)

    def test_cycles_and_duplicate_facts_terminate(self):
        kb = KnowledgeBase()
        kb.tell_rule(['A'], 'B')
        kb.tell_rule(['B'], 'A')
        kb.tell_fact('A')
        kb.tell_fact('A')
        kb.forward_chain()
        kb.forward_chain()
        self.assertEqual(kb.facts, {'A', 'B'})


class TestLogicConstrainedAStar(unittest.TestCase):
    def setUp(self):
        self.agent = SearchAgent()
        self.tile_facts = {
            (1, 0): ['TargetVisible', 'HasDust', 'BloodseekerMissing'],
            (0, 1): ['TargetVisible', 'HasDust'],
        }

    def test_no_facts_preserves_original_astar(self):
        self.assertEqual(
            self.agent.astar_search((0, 0), (2, 0), [], (3, 3)),
            ['Right', 'Right']
        )

    def test_both_heuristics_find_shortest_feasible_detour(self):
        for heuristic in ['manhattan', 'euclidean']:
            with self.subTest(heuristic=heuristic):
                path = self.agent.astar_search(
                    (0, 0), (2, 0), [], (3, 3),
                    heuristic_type=heuristic, tile_facts=self.tile_facts
                )
                self.assertIsNotNone(path)
                self.assertEqual(len(path), 4)
                self.assertEqual(path[0], 'Up')
                x, y = 0, 0
                moves = {'Up': (0, 1), 'Down': (0, -1),
                         'Left': (-1, 0), 'Right': (1, 0)}
                for action in path:
                    dx, dy = moves[action]
                    x, y = x + dx, y + dy
                    self.assertNotEqual((x, y), (1, 0))
                self.assertEqual((x, y), (2, 0))

    def test_forbidden_goal_returns_failure(self):
        self.assertIsNone(self.agent.astar_search(
            (0, 0), (1, 0), [], (3, 3), tile_facts=self.tile_facts
        ))

    def test_safe_neighbor_after_unsafe_neighbor_has_fresh_facts(self):
        # Up is considered before Right. Retreat from Up must not block Right.
        path = self.agent.astar_search(
            (0, 0), (1, 0), [], (2, 2),
            tile_facts={(0, 1): ['TargetVisible', 'HasDust', 'BloodseekerMissing']}
        )
        self.assertEqual(path, ['Right'])

    def test_walls_and_logic_can_block_all_routes(self):
        self.assertIsNone(self.agent.astar_search(
            (0, 0), (2, 0), [(0, 1)], (3, 3), tile_facts=self.tile_facts
        ))

    def test_unreachable_nearest_food_does_not_block_other_food(self):
        with contextlib.redirect_stdout(io.StringIO()):
            action = self.agent.sense_and_act({
                'food_here': False, 'grid_size': (3, 3), 'walls': [],
                'all_food': [(1, 0), (0, 2)]
            })
        self.assertEqual(action, 'Up')

    def test_real_grid_action_loop_avoids_forbidden_tile(self):
        # Exercise the actual game percept/action loop without opening Tkinter.
        env = VisualGridHuntGame(
            width=4, height=4, num_food=0, num_opponents=0, custom_walls=[]
        )
        env.toxic_traps.clear()
        env.food_positions = {(2, 0)}
        with contextlib.redirect_stdout(io.StringIO()):
            for _ in range(10):
                if env.is_done():
                    break
                action = self.agent.sense_and_act(env.get_percept())
                env.execute_action(action)
                self.assertNotEqual(tuple(env.agent_pos), (1, 0))
                self.assertEqual(self.agent.current_pos, tuple(env.agent_pos))
        self.assertEqual(env.food_positions, set())
        self.assertEqual(env.score, 20)


if __name__ == '__main__':
    unittest.main(verbosity=2)
