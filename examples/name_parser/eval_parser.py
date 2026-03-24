import time
from parser import parse_names

def run_benchmark():
    # A tiny dataset of tricky sentences
    dataset = [
        ("My name is John Doe and my friend is Alice.", {"John", "Doe", "Alice"}),
        ("We live in New York, which is cool.", set()),
        ("Dr. Gregory House works at Princeton-Plainsboro Teaching Hospital.", {"Gregory", "House"}),
        ("The CEO of Apple, Tim Cook, announced a new iPhone on Tuesday.", {"Tim", "Cook"}),
    ]
    
    total_expected = 0
    total_correct = 0
    total_false_positives = 0
    
    start_time = time.time()
    
    for text, expected in dataset:
        extracted = set(parse_names(text))
        total_expected += len(expected)
        
        correct = len(extracted.intersection(expected))
        false_positives = len(extracted - expected)
        
        total_correct += correct
        total_false_positives += false_positives
        
    duration = time.time() - start_time
    
    # Calculate a score: 1.0 is perfect. We penalize false positives.
    if total_expected == 0:
        precision = 1.0 if total_false_positives == 0 else 0.0
        recall = 1.0
    else:
        precision = total_correct / (total_correct + total_false_positives) if (total_correct + total_false_positives) > 0 else 0.0
        recall = total_correct / total_expected
        
    f1_score = 0.0
    if precision + recall > 0:
        f1_score = 2 * (precision * recall) / (precision + recall)
        
    print(f"Extraction F1-Score: {f1_score:.2f}")
    print(f"Time Taken: {duration:.4f}s")
    
if __name__ == "__main__":
    run_benchmark()
