#!/usr/bin/env python3
"""
Test script to verify hash pattern (#) round robin detection
"""

import sys
import os
import re
from pathlib import Path

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def extract_base_name(filename):
    """Extract base name from filename by removing round robin patterns."""
    # Remove common round robin patterns
    patterns = [
        r'_rr\d+$',      # _rr1, _rr2, etc.
        r'_\d+$',        # _1, _2, etc.
        r'_round\d+$',   # _round1, _round2, etc.
        r'_alt\d+$',     # _alt1, _alt2, etc.
        r'_var\d+$',     # _var1, _var2, etc.
        r'#\d+$',        # #1, #2, etc.
    ]
    
    for pattern in patterns:
        filename = re.sub(pattern, '', filename, flags=re.IGNORECASE)
    
    return filename

def extract_round_robin_position(filename):
    """Extract round robin position from filename patterns."""
    # Check for # pattern first (e.g., C4#1, C4#2)
    hash_match = re.search(r'#(\d+)$', filename)
    if hash_match:
        return int(hash_match.group(1))
    
    # Check for other patterns
    patterns = [
        (r'_rr(\d+)$', 1),      # _rr1, _rr2, etc.
        (r'_(\d+)$', 1),        # _1, _2, etc.
        (r'_round(\d+)$', 1),   # _round1, _round2, etc.
        (r'_alt(\d+)$', 1),     # _alt1, _alt2, etc.
        (r'_var(\d+)$', 1),     # _var1, _var2, etc.
    ]
    
    for pattern, group_num in patterns:
        match = re.search(pattern, filename, flags=re.IGNORECASE)
        if match:
            return int(match.group(group_num))
    
    return 1  # Default position

def test_hash_pattern_detection():
    """Test the hash pattern detection functionality."""
    
    # Test base name extraction
    print("Testing base name extraction:")
    test_filenames = ["C4#1", "C4#2", "C4#3", "D4#1", "D4#2", "E4", "C4_rr1", "C4_1", "C4_round1"]
    for filename in test_filenames:
        base_name = extract_base_name(filename)
        print(f"  {filename} -> {base_name}")
    
    print("\nTesting position extraction:")
    for filename in test_filenames:
        position = extract_round_robin_position(filename)
        print(f"  {filename} -> position {position}")
    
    # Test grouping logic
    print("\nTesting grouping logic:")
    samples_by_base = {}
    test_samples = [
        "C4#1.wav", "C4#2.wav", "C4#3.wav",
        "D4#1.wav", "D4#2.wav", 
        "E4.wav",  # Single sample, no round robin
        "F4_rr1.wav", "F4_rr2.wav"
    ]
    
    for sample_name in test_samples:
        base_name = extract_base_name(sample_name.replace('.wav', ''))
        if base_name not in samples_by_base:
            samples_by_base[base_name] = []
        samples_by_base[base_name].append(sample_name)
    
    print("Grouped samples:")
    for base_name, samples in samples_by_base.items():
        if len(samples) > 1:
            print(f"  {base_name}: {samples} (Round Robin Group)")
            # Show positions
            for sample in samples:
                position = extract_round_robin_position(sample.replace('.wav', ''))
                print(f"    {sample} -> position {position}")
        else:
            print(f"  {base_name}: {samples} (Single sample)")

if __name__ == "__main__":
    test_hash_pattern_detection()
