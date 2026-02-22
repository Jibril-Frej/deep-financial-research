from graph.blueprint import app

# Simulate a user question
input_state = {"question": "What are the risk factors for NVDA?"}

# Run the graph
output = app.invoke(input_state)

print("\n--- FINAL OUTPUT ---")
print(output["final_response"])
