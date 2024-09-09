import re

def parse_and_analyze(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
    
    results = []  # Store (average, highest) for each 'Twenty' section
    current_real_values = []
    
    def analyze_real_values(values):
        if values:
            avg = sum(values) / len(values)
            highest = max(values)
            return avg, highest
        return None, None
    
    for line in lines:
        line = line.strip()  # Remove extra spaces/newlines
        
        if line.startswith('One'):
            # Calculate average and highest for previous section if applicable
            if current_real_values:
                avg, highest = analyze_real_values(current_real_values)
                results.append((avg, highest))
                current_real_values = []  # Reset for the next section
        
        elif line.startswith('real'):
            # Extract the time in format `0m4,343s` and convert to seconds
            match = re.search(r'real\s+(\d+)m([\d,]+)s', line)
            if match:
                minutes = int(match.group(1))
                seconds = float(match.group(2).replace(',', '.'))  # Handle comma as decimal point
                total_seconds = minutes * 60 + seconds
                current_real_values.append(total_seconds)
    
    # Calculate average and highest for the last section
    if current_real_values:
        avg, highest = analyze_real_values(current_real_values)
        results.append((avg, highest))
    
    return results

# Example usage
filename = 'shell_scripts/times/real_time5.txt'
results = parse_and_analyze(filename)

for i, (avg, highest) in enumerate(results, 1):
    if avg is not None and highest is not None:
        print(f"Section {i} - Average: {avg:.2f} seconds, Highest: {highest:.2f} seconds")


