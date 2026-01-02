# core/critical_path_analyzer.py

class CriticalPathAnalyzer:
    """
    Identifies mission-critical nodes in the decision tree.
    """
    def is_on_critical_path(self, node_id, execution_graph):
        """
        Determines if a failure at this node stops the entire objective.
        Logic: Checks if the node has the 'critical' attribute set or 
        if it's a mandatory dependency for the leaf nodes.
        """
        # For now, we check if the node data explicitly marks it as critical
        node_data = execution_graph.get(node_id, {})
        return node_data.get('is_critical', False)
