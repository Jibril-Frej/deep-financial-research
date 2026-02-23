from graph.blueprint import app

# Simulate a user question
input_state = {"question": "What is the state of NVDA?"}

# Run the graph
output = app.invoke(input_state)

print("\n--- FINAL OUTPUT ---")
print(output["final_response"])
