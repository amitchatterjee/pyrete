import logging
import uuid
from collections import deque

from perm import combinations
from node import Node
from factset import Factset
from graph import Graph

class Session:
    def __init__(self, ruleset, facts, id=uuid.uuid1(), global_ctx={}):
        self.id = id
        self.ruleset = ruleset
        self.rules = ruleset.rules
        self.global_ctx = global_ctx
        self.factset = Factset()
        self.graph = Graph(self.__comparator)
        self.__add_facts(facts)

    def __str__(self):
        return f"Session({self.id}, ruleset: {self.ruleset}, facts:{self.factset})"
    
    def __repr__(self):
        return self.__str__()

    def execute(self):
        self.__execute_graph()
        return self.factset.facts

    def __comparator(self, obj, other):
        # TODO only rule.order based ordering is implemented for now
        return obj.rule.order - other.rule.order


    def __execute_graph(self):
        logging.debug(f"Executing rules on graph: {self.graph}")
        #print(f"Graph content: {self.graph.to_element_list()}")
        self.graph.new_cursor()
        while True:
            element = self.graph.next_element()
            if element is None:
                # Reached the end of the graph
                break
            node = element.obj
            # Execute the rule on the node
            result = node.execute(self.factset)
            count = 0
            leftmost = element
            if result:
                # If all conditions were satisfied and the thens were executed
                if len(result['insert']):
                    new_facts = result['insert']
                    leftmost, chg_count = self.__add_facts(new_facts, leftmost)
                    count = count + chg_count
                    logging.debug(f"Inserted facts: {new_facts}")
            
                if len(result['update']):
                    updated_facts = result['update']
                    leftmost, chg_count  = self.__update_facts(updated_facts, leftmost)
                    count = count + chg_count
                    logging.debug(f"Updated facts: {updated_facts}")

                if len(result['delete']):
                   deleted_facts = result['delete']
                   leftmost, chg_count =  self.__delete_facts(deleted_facts, leftmost)
                   count = count + chg_count
                   logging.debug(f"Deleted facts: {deleted_facts}")

                logging.debug(f"After all merges were completed: change count: {count}, leftmost element with change: {leftmost}, current element: {element}, cursor needs to adjust: {self.graph.cursor_is_right_of(leftmost)}")
                self.graph.new_cursor(node=leftmost)
    
    def __delete_facts(self, deleted_facts, current_leftmost):
        cursor_name = 'delete'
        self.graph.new_cursor(cursor_name=cursor_name)
        deduped_deletes = set(deleted_facts)
        new_leftmost = current_leftmost
        count = 0
        while True:
            element = self.graph.next_element(cursor_name)
            if element is None:
                break

            if len([value for value in element.obj.when_objs if value in deduped_deletes]):
                next_element = self.graph.delete_element(element)
                if element.obj == new_leftmost.obj:
                    # If the leftmost object is being deleted
                    new_leftmost = next_element
                else:
                    new_leftmost = self.__minimum(new_leftmost, element)
                count = count+1
        logging.debug(f"Deleted from graph: {self.graph}, count: {count}, new leftmost: {new_leftmost}")
        return new_leftmost, count

    def __update_facts(self, updated_facts, current_leftmost):
        cursor_name = 'update'
        self.graph.new_cursor(cursor_name=cursor_name)
        deduped_updates = set(updated_facts)
        new_leftmost = current_leftmost
        count = 0
        while True:
            element = self.graph.next_element(cursor_name)
            if element is None:
                break
            if element.obj.invalidate_leaves(deduped_updates):
                new_leftmost = self.__minimum(new_leftmost, element)
                count = count+1
        logging.debug(f"Updated graph: {self.graph}, count: {count}, new leftmost: {new_leftmost}")
        return new_leftmost, count

    def __add_facts(self, new_facts, current_leftmost=None):
        # The new_facts variable contains a (deduped) set
        new_facts = self.factset.add_facts(new_facts)

        new_leftmost = current_leftmost
        count = 0
        logging.debug(f"Adding to graph: all facts: {self.factset.facts}, new: {new_facts}")
        for rule in self.rules:
            satisfies = True
            when_objs = []
            # For each class associated with the when clause, look if object(s) of that type exists. If objects exist for all of the when clauses, then this rule satisfies the need and is ready to be put in the graph
            for when in rule.whens:
                objs = self.factset.facts_of_type(when.of_type)
                if not objs:
                    satisfies = False
                    break
                when_objs.append(objs)

            if satisfies:
                # Get all the permutations associated with the objects
                perms = combinations(when_objs, new_facts)                
                logging.debug(f"{rule}, object permutation: {perms}")
                # insert to the graph
                for each in perms:
                    node_id = f"{self.id}:{rule.id}:{each}"
                    node = Node(node_id, rule, self.rules, self.global_ctx, each)
                    element = self.graph.add(node)
                    logging.debug(f"Added node: {element}")
                    new_leftmost = self.__minimum(new_leftmost, element)
                    count = count+1
                    
        logging.debug(f"Inserted into graph: {self.graph}, count: {count}, new leftmost: {new_leftmost}")
        return new_leftmost, count
    
    def __minimum(self, element1, element2):
        if not element1:
            # print(f"Minimum: min = {element2} e1:{element1}, e2: {element2}")
            return element2
        min = element2 if self.graph.compare(element1, element2) >= 0 else element1
        # print(f"Minimum: min = {min} e1:{element1}, e2: {element2}")
        return min
