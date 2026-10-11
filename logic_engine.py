"""Practical 07: a propositional knowledge base with forward chaining."""


class KnowledgeBase:
    def __init__(self):
        self.facts = set()
        self.rules = []

    def tell_fact(self, fact_string):
        self.facts.add(fact_string)

    def tell_rule(self, premise_list, conclusion_string):
        # Copy the premises so later changes to the input do not change the rule.
        self.rules.append((list(premise_list), conclusion_string))

    def clear_facts(self):
        # Rules persist; percepts and their deductions belong to one tile only.
        self.facts.clear()

    def forward_chain(self):
        """Apply rules until a full pass adds no new facts (a fixed point)."""
        new_facts_added = True
        while new_facts_added:
            new_facts_added = False
            for premises, conclusion in self.rules:
                if conclusion not in self.facts:
                    if all(premise in self.facts for premise in premises):
                        self.facts.add(conclusion)
                        new_facts_added = True
