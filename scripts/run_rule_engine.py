from src.graph_construction.graph_loader import load_graph
from src.graph_construction.converter import dataframe_to_schema
from src.detection.rule_engine import default_rule_engine

DATASET = "1r"

print("Loading graph...")

df_graph = load_graph(DATASET)

print("Converting graph...")

graph = dataframe_to_schema(df_graph)

print(f"Nodes : {len(graph.nodes):,}")
print(f"Edges : {len(graph.edges):,}")

engine = default_rule_engine()

results = engine.run(graph)

print("\nRule Engine Report")
print("=" * 60)

total = 0

for result in results:

    print(result.rule)

    if result.passed:
        print("  PASS")
    else:
        print(f"  FAIL ({len(result.violations)})")
        total += len(result.violations)

print("\nTotal Violations:", total)
