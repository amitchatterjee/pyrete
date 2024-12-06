from session import Session
from ftypes import Switch

def __find_switch(facts):
    for fact in facts:
        if isinstance(fact, Switch):
            return fact
    return None
        
def execute(repository, facts, global_ctx={}, start_from=None):
    resulting_facts = facts
    for ruleset in repository.rulesets:
        if start_from and ruleset.id != start_from:
            continue
        session = Session(ruleset, resulting_facts, f"{repository.id}:{ruleset.id}", global_ctx)
        resulting_facts = session.execute()
        if switch_to := __find_switch(resulting_facts):
            resulting_facts.remove(switch_to)
            if switch_to.ruleset == '_end':
                break
            return execute(repository, resulting_facts, global_ctx, switch_to.ruleset)
    return resulting_facts