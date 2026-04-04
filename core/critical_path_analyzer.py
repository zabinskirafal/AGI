class CriticalPathAnalyzer:
    """
    Analyzes the decision execution graph to identify mission-critical nodes.
    A node is on the critical path if its failure prevents the main objective.
    """

    def is_on_critical_path(self, node_id, execution_graph):
        """
        Determines if a specific node is essential for successful completion.
        
        Args:
            node_id (str): The identifier of the action/decision node.
            execution_graph (dict): The current decision tree or execution flow.
            
        Returns:
            bool: True if the node is critical, False otherwise.
        """
        if not execution_graph or node_id not in execution_graph:
            return False

        node_data = execution_graph.get(node_id, {})

        # 1. Direct Check: Explicitly marked as critical by the orchestrator
        if node_data.get('is_critical') is True:
            return True

        # 2. Dependency Check: Is this node a mandatory parent for a goal node?
        # (This can be expanded with a graph traversal algorithm like DFS/BFS)
        if node_data.get('impact_level') == 'high' or node_data.get('is_bottleneck') is True:
            return True

        return False

    def get_critical_nodes(self, execution_graph):
        """
        Returns a list of all node IDs currently on the critical path.
        """
        return [node_id for node_id in execution_graph if self.is_on_critical_path(node_id, execution_graph)]
