# Round Robin Support for DecentSampler Library Creator

This document describes the round robin functionality implemented in the DecentSampler Library Creator application.

## Overview

Round robin support allows multiple samples to be played for the same note, creating more natural variations in sound. This is particularly useful for instruments like drums, strings, or any sampled instrument where you want to avoid the "machine gun" effect of repeated identical samples.

## Features Implemented

### 1. Round Robin Dialog (`RoundRobinDialog`)

A comprehensive dialog for configuring round robin settings with the following attributes:

- **seqMode**: Round robin behavior mode
  - `always` (default): No round robin, always play the same sample
  - `random`: Random selection from available samples
  - `true_random`: Completely random selection
  - `round_robin`: Sequential selection through samples

- **seqLength**: Length of the round robin queue
  - Set to 0 for auto-detection
  - Can be set at sample, group, or global level

- **seqPosition**: Position of this sample in the round robin queue
  - Automatically assigned (1, 2, 3, ...) or manually configured
  - Can be set at sample or group level

### 2. Round Robin Manager (`RoundRobinManager`)

A dedicated widget for managing round robin groups with:

- **Tree view** showing all round robin groups
- **Add/Edit/Remove** group functionality
- **Auto-detection** of round robin patterns from filenames
- **Preview** functionality to test round robin effects
- **Visual indicators** for different round robin modes

### 3. Enhanced Sample Mapping Interface

The sample mapping interface includes:

- **Visual highlighting** of round robin samples in the table
- **Round Robin button** to configure selected samples

### 4. Visual Keyboard Indicators

The piano keyboard shows:

- **Orange keys** for round robin samples
- **Light green keys** for selected round robin samples
- **Different colors** for different round robin modes
- **Visual feedback** when clicking on round robin keys

### 5. Automatic Pattern Detection

The system automatically detects common round robin filename patterns:

- `_rr1.wav`, `_rr2.wav`, `_rr3.wav` (round robin)
- `_1.wav`, `_2.wav`, `_3.wav` (numbered)
- `_round1.wav`, `_round2.wav` (round)
- `_alt1.wav`, `_alt2.wav` (alternate)
- `_var1.wav`, `_var2.wav` (variation)

### 6. XML Generation

The XML output includes proper round robin attributes:

```xml
<sample path="Samples/C4_rr1.wav" 
        rootNote="60" 
        loNote="60" 
        hiNote="60" 
        loVel="0" 
        hiVel="127"
        seqMode="round_robin"
        seqLength="3"
        seqPosition="1" />
```

## Usage Instructions

### Setting Up Round Robin

1. **Add samples** to your project using the Sample Mapping tab
2. **Select samples** that should be part of a round robin group
3. **Click the Round Robin button** to open the configuration dialog
4. **Choose the round robin mode** and configure other settings
5. **Use the Round Robin tab** to manage multiple round robin groups

### Auto-Detection

1. **Add samples** with round robin naming patterns
2. **Go to the Round Robin tab**
3. **Click Auto-Detect** to automatically group samples
4. **Review and adjust** the detected groups as needed

### Visual Feedback

- **Orange keys** on the keyboard indicate round robin samples
- **Highlighted rows** in the table show round robin information
- **Different colors** help distinguish between different round robin modes

## Technical Implementation

### File Structure

- `sample_mapping.py`: Contains all round robin UI components and logic
- `decent_sampler.py`: Updated to support round robin attributes in XML generation
- `decent_sampler_gui.py`: Main GUI with new Round Robin tab

### Key Classes

- `RoundRobinDialog`: Configuration dialog for round robin settings
- `RoundRobinManager`: Widget for managing round robin groups
- `RoundRobinModeDelegate`: Table delegate for round robin mode selection
- `VisualKeyboard`: Updated with round robin visual indicators

### Data Flow

1. **Sample Creation**: Samples are created with default round robin attributes
2. **Pattern Detection**: Automatic detection of round robin patterns in filenames
3. **User Configuration**: Users can modify round robin settings via dialogs
4. **Visual Updates**: UI updates to show round robin information
5. **XML Generation**: Round robin attributes are included in the final XML output

## Testing

Use the `test_round_robin.py` script to test the round robin functionality:

```bash
python test_round_robin.py
```

This will create a test window with sample round robin files and demonstrate all the features.


## Troubleshooting

### Common Issues

1. **Samples not detected**: Ensure filenames follow the supported patterns
2. **Visual indicators not showing**: Check that samples have proper round robin attributes
3. **XML not generating**: Verify that round robin attributes are properly set

### Debug Tips

- Use the Round Robin tab to inspect current round robin groups
- Check the table view for round robin column values
- Verify XML output includes the expected round robin attributes
