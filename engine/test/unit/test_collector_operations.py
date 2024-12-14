from rule import Rule,Condition
from ruleset import Ruleset
from repository import Repository
from helper import assign
from controls import insert, delete, update
from service import execute

from ftypes import Collector

from test_helpers.test_util import find_result_of_type
from test_helpers.test_facts import C1, R1

def test_collector_in_input_facts():
    rule_1 = Rule(id='r1',
                when=Condition(of_type=Collector, id='sum_of_c1s', matches_exp=lambda ctx, this: this.sum() > 10 and assign(ctx, sum=this.sum(), size=len(this.collection))),
                then=lambda ctx: insert(ctx, R1(ctx.sum, ctx.size)))
    facts = [C1(10), C1(10), Collector(of_type=C1, id='sum_of_c1s', nvalue=lambda obj: obj.val)]
    result_facts = execute(Repository('repo1', [Ruleset('rs1', [rule_1])]), facts)
    matching = find_result_of_type(R1, result_facts)
    assert 1 == len(matching)
    assert 20 == matching[0].vals[0]
    assert 2 == matching[0].vals[1]

def test_collector_filter():
    rule_1 = Rule(id='r1',
                when=Condition(of_type=Collector, id='sum_of_c1s', matches_exp=lambda ctx, this: this.sum() > 10 and assign(ctx, sum=this.sum(), size=len(this.collection))),
                then=lambda ctx: insert(ctx, R1(ctx.sum, ctx.size)))
    facts = [C1(10), C1(10), Collector(of_type=C1, id='sum_of_c1s', filter=lambda obj: obj.val > 10, nvalue=lambda obj: obj.val)]
    result_facts = execute(Repository('repo1', [Ruleset('rs1', [rule_1])]), facts)
    matching = find_result_of_type(R1, result_facts)
    assert 0 == len(matching)
 
def test_collector_changes_on_fact_insertion():
    rule_1 = Rule(id='r1',
                  when=Condition(of_type=C1, matches_exp=lambda ctx, this: this.val > 10),
                  then=lambda ctx: insert(ctx, C1(1)))
    rule_2 = Rule(id='r2', order=1,
                when=Condition(of_type=Collector, id='sum_of_c1s', matches_exp=lambda ctx, this: this.sum() > 10 and assign(ctx, sum=this.sum(), size=len(this.collection))),
                then=lambda ctx: insert(ctx, R1(ctx.sum, ctx.size)))
    facts = [C1(10), C1(20), Collector(of_type=C1, id='sum_of_c1s', nvalue=lambda obj: obj.val)]
    result_facts = execute(Repository('repo1', [Ruleset('rs1', [rule_1, rule_2])]), facts)
    matching = find_result_of_type(R1, result_facts)
    assert 1 == len(matching)
    assert 31 == matching[0].vals[0]
    assert 3 == matching[0].vals[1]

    # Change the order and this time, it should produce two results as rule 2 should run twice
    rule_1 = Rule(id='r1', order=1,
                  when=Condition(of_type=C1, matches_exp=lambda ctx, this: this.val > 10),
                  then=lambda ctx: insert(ctx, C1(1)))
    rule_2 = Rule(id='r2',
                when=Condition(of_type=Collector, id='sum_of_c1s', matches_exp=lambda ctx, this: this.sum() > 10 and assign(ctx, sum=this.sum(), size=len(this.collection))),
                then=lambda ctx: insert(ctx, R1(ctx.sum, ctx.size)))
    facts = [C1(10), C1(20), Collector(of_type=C1, id='sum_of_c1s', nvalue=lambda obj: obj.val)]
    result_facts = execute(Repository('repo1', [Ruleset('rs1', [rule_1, rule_2])]), facts)
    matching = find_result_of_type(R1, result_facts)
    assert 2 == len(matching)
    matching.sort(key=lambda o: o.vals[1])
    assert 30 == matching[0].vals[0]
    assert 2 == matching[0].vals[1]
    assert 31 == matching[1].vals[0]
    assert 3 == matching[1].vals[1]

def test_collector_changes_on_fact_deletion():
    rule_1 = Rule(id='r1',
                  when=Condition(of_type=C1, matches_exp=lambda ctx, this: this.val > 10 and assign(ctx, obj=this)),
                  then=lambda ctx: delete(ctx, ctx.obj))
    rule_2 = Rule(id='r2', order=1,
                when=Condition(of_type=Collector, id='sum_of_c1s', matches_exp=lambda ctx, this:  assign(ctx, sum=this.sum(), size=len(this.collection))),
                then=lambda ctx: insert(ctx, R1(ctx.sum, ctx.size)))
    facts = [C1(10), C1(20), Collector(of_type=C1, id='sum_of_c1s', nvalue=lambda obj: obj.val)]
    result_facts = execute(Repository('repo1', [Ruleset('rs1', [rule_1, rule_2])]), facts)
    matching = find_result_of_type(R1, result_facts)
    assert 1 == len(matching)
    assert 10 == matching[0].vals[0]
    assert 1 == matching[0].vals[1]

    rule_1 = Rule(id='r1', order=1,
                  when=Condition(of_type=C1, matches_exp=lambda ctx, this: this.val > 10 and assign(ctx, obj=this)),
                  then=lambda ctx: delete(ctx, ctx.obj))
    rule_2 = Rule(id='r2',
                when=Condition(of_type=Collector, id='sum_of_c1s', matches_exp=lambda ctx, this:  assign(ctx, sum=this.sum(), size=len(this.collection))),
                then=lambda ctx: insert(ctx, R1(ctx.sum, ctx.size)))
    facts = [C1(10), C1(20), Collector(of_type=C1, id='sum_of_c1s', nvalue=lambda obj: obj.val)]
    result_facts = execute(Repository('repo1', [Ruleset('rs1', [rule_1, rule_2])]), facts)
    matching = find_result_of_type(R1, result_facts)
    assert 2 == len(matching)
    matching.sort(key=lambda o: o.vals[1])
    assert 10 == matching[0].vals[0]
    assert 1 == matching[0].vals[1]
    assert 30 == matching[1].vals[0]
    assert 2 == matching[1].vals[1]

def test_collector_changes_on_fact_updates():
    def divide_by_2(ctx):
        ctx.obj.val = ctx.obj.val // 2
        update(ctx, ctx.obj)
    rule_1 = Rule(id='r1', retrigger_on_update=False,
                  when=Condition(of_type=C1, matches_exp=lambda ctx, this: assign(ctx, obj=this)),
                  then=divide_by_2)
    rule_2 = Rule(id='r2', order=1,
                when=Condition(of_type=Collector, id='sum_of_c1s', matches_exp=lambda ctx, this:  assign(ctx, sum=this.sum(), size=len(this.collection))),
                then=lambda ctx: insert(ctx, R1(ctx.sum, ctx.size)))
    facts = [C1(50), C1(10), Collector(of_type=C1, id='sum_of_c1s', nvalue=lambda obj: obj.val)]
    result_facts = execute(Repository('repo1', [Ruleset('rs1', [rule_1, rule_2])]), facts)
    matching = find_result_of_type(R1, result_facts)
    assert 1 == len(matching)
    assert 30 == matching[0].vals[0]
    assert 2 == matching[0].vals[1]

    def divide_by_2(ctx):
        ctx.obj.val = ctx.obj.val // 2
        update(ctx, ctx.obj)
    rule_1 = Rule(id='r1', retrigger_on_update=False, order=1,
                  when=Condition(of_type=C1, matches_exp=lambda ctx, this: assign(ctx, obj=this)),
                  then=divide_by_2)
    rule_2 = Rule(id='r2', 
                when=Condition(of_type=Collector, id='sum_of_c1s', matches_exp=lambda ctx, this:  assign(ctx, sum=this.sum(), size=len(this.collection))),
                then=lambda ctx: insert(ctx, R1(ctx.sum, ctx.size)))
    facts = [C1(50), C1(10), Collector(of_type=C1, id='sum_of_c1s', nvalue=lambda obj: obj.val)]
    result_facts = execute(Repository('repo1', [Ruleset('rs1', [rule_1, rule_2])]), facts)
    matching = find_result_of_type(R1, result_facts)
    assert 3 == len(matching)
    matching.sort(key=lambda o: o.vals[0], reverse=True)
    print(matching)
    # The first element (after sorting) is always 50+10
    assert 50+10 == matching[0].vals[0]
    # Depending on whether r1 was triggered by C1 or C2, we will get different outcomes. If C1 triggered first, then the value is 25+10. If C2 was triggered first, then the value is 50+5
    assert matching[1].vals[0] in [25+10,50+5]
    # The last iteration will always be 30
    assert 30 == matching[2].vals[0]