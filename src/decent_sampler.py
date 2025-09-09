"""
DecentSampler Preset Generator

This module provides classes to represent and generate DecentSampler (.dspreset) files.
DecentSampler is a free, cross-platform sampler plugin that can load .dspreset files.
"""

from pathlib import Path
from typing import List, Optional
from lxml import etree


class Sample:
    """
    Represents a single sample within a group in a DecentSampler preset.
    
    Attributes:
        file_path (Path): Path to the sample file
        root_note (int): Root note (MIDI note number, 0-127, default: 60)
        low_note (int): Lowest note this sample responds to (0-127, default: 0)
        high_note (int): Highest note this sample responds to (0-127, default: 127)
        low_velocity (int): Lowest velocity this sample responds to (0-127, default: 0)
        high_velocity (int): Highest velocity this sample responds to (0-127, default: 127)
        seq_mode (str): Round robin mode (default: "always")
        seq_length (int): Length of round robin queue (default: 0)
        seq_position (int): Position in round robin queue (default: 1)
    """
    
    def __init__(self, file_path: Path, root_note: int = 60, low_note: int = 0, 
                 high_note: int = 127, low_velocity: int = 0, high_velocity: int = 127,
                 seq_mode: str = "always", seq_length: int = 0, seq_position: int = 1):
        """
        Initialize a Sample.
        
        Args:
            file_path: Path to the sample file
            root_note: Root note (MIDI note number, 0-127, default: 60)
            low_note: Lowest note this sample responds to (0-127, default: 0)
            high_note: Highest note this sample responds to (0-127, default: 127)
            low_velocity: Lowest velocity this sample responds to (0-127, default: 0)
            high_velocity: Highest velocity this sample responds to (0-127, default: 127)
            seq_mode: Round robin mode (default: "always")
            seq_length: Length of round robin queue (default: 0)
            seq_position: Position in round robin queue (default: 1)
        """
        self.file_path = Path(file_path)
        self.root_note = root_note
        self.low_note = low_note
        self.high_note = high_note
        self.low_velocity = low_velocity
        self.high_velocity = high_velocity
        self.seq_mode = seq_mode
        self.seq_length = seq_length
        self.seq_position = seq_position
        self.selected = False  # For checkbox selection
    
    def to_xml_element(self, samples_path: str = "Samples") -> etree.Element:
        """
        Convert this Sample to an XML element.
        
        Args:
            samples_path: Base path for samples (default: "Samples")
        
        Returns:
            lxml.etree.Element representing this sample
        """
        sample_element = etree.Element("sample")
        # Use samples_path + filename instead of full file path
        file_path = samples_path + "/" + self.file_path.name
        sample_element.set("path", file_path)
        sample_element.set("rootNote", str(self.root_note))
        sample_element.set("loNote", str(self.low_note))
        sample_element.set("hiNote", str(self.high_note))
        sample_element.set("loVel", str(self.low_velocity))
        sample_element.set("hiVel", str(self.high_velocity))
        
        # Add round robin attributes if not default values
        if self.seq_mode != "always":
            sample_element.set("seqMode", self.seq_mode)
        if self.seq_length > 0:
            sample_element.set("seqLength", str(self.seq_length))
        if self.seq_position != 1:
            sample_element.set("seqPosition", str(self.seq_position))
        
        return sample_element


class SampleGroup:
    """
    Represents a group of samples with common properties in a DecentSampler preset.
    
    Attributes:
        name (str): Name of the group (default: based on root note)
        enabled (bool): Whether the group is enabled (default: True)
        volume (str): Volume setting (linear 0.0-1.0 or dB like "3dB", default: "1.0")
        amp_vel_track (float): Velocity tracking (0.0-1.0, default: 0.0)
        group_tuning (float): Group tuning in semitones (default: 0.0)
        seq_mode (str): Round robin mode for the group (default: "always")
        seq_length (int): Length of round robin queue for the group (default: 0)
        samples (List[Sample]): List of samples in this group
    """
    
    def __init__(self, name: str = "", enabled: bool = True, volume: str = "1.0", 
                 amp_vel_track: float = 0.0, group_tuning: float = 0.0, 
                 seq_mode: str = "always", seq_length: int = 0, samples: List[Sample] = None):
        """
        Initialize a SampleGroup.
        
        Args:
            name: Name of the group
            enabled: Whether the group is enabled
            volume: Volume setting (linear or dB)
            amp_vel_track: Velocity tracking amount
            group_tuning: Group tuning in semitones
            seq_mode: Round robin mode for the group
            seq_length: Length of round robin queue for the group
            samples: List of samples in this group
        """
        self.name = name
        self.enabled = enabled
        self.volume = volume
        self.amp_vel_track = amp_vel_track
        self.group_tuning = group_tuning
        self.seq_mode = seq_mode
        self.seq_length = seq_length
        self.samples = samples or []
        self.selected = False  # For checkbox selection
    
    def add_sample(self, sample: Sample) -> None:
        """
        Add a sample to this group.
        
        Args:
            sample: Sample to add
        """
        self.samples.append(sample)
    
    def remove_sample(self, sample: Sample) -> None:
        """
        Remove a sample from this group.
        
        Args:
            sample: Sample to remove
        """
        if sample in self.samples:
            self.samples.remove(sample)
    
    def to_xml_element(self, samples_path: str = "Samples") -> etree.Element:
        """
        Convert this SampleGroup to an XML element.
        
        Args:
            samples_path: Base path for samples (default: "Samples")
        
        Returns:
            lxml.etree.Element representing this sample group
        """
        group_element = etree.Element("group")
        
        # Add group attributes
        group_element.set("enabled", str(self.enabled).lower())
        group_element.set("volume", self.volume)
        group_element.set("ampVelTrack", str(self.amp_vel_track))
        group_element.set("groupTuning", str(self.group_tuning))
        
        # Add round robin attributes if not default values
        if self.seq_mode != "always":
            group_element.set("seqMode", self.seq_mode)
        if self.seq_length > 0:
            group_element.set("seqLength", str(self.seq_length))
        
        # Add all samples in this group
        for sample in self.samples:
            group_element.append(sample.to_xml_element(samples_path))
        
        return group_element


class DecentPreset:
    """
    Represents a complete DecentSampler preset with metadata and sample groups.
    
    Attributes:
        preset_name (str): Name of the preset
        author (str): Author of the preset
        description (str): Description of the preset
        category (str): Category of the preset
        sample_groups (List[SampleGroup]): List of sample groups in this preset
    """
    
    def __init__(self, preset_name: str, author: str = "", description: str = "", 
                 category: str = "", sample_groups: List[SampleGroup] = None, 
                 samples_path: str = "Samples"):
        """
        Initialize a DecentPreset.
        
        Args:
            preset_name: Name of the preset
            author: Author of the preset (default: empty string)
            description: Description of the preset (default: empty string)
            category: Category of the preset (default: empty string)
            sample_groups: List of sample groups (default: empty list)
            samples_path: Base path for samples (default: "Samples")
        """
        self.preset_name = preset_name
        self.author = author
        self.description = description
        self.category = category
        self.sample_groups = sample_groups or []
        self.samples_path = samples_path
    
    def add_sample_group(self, sample_group: SampleGroup) -> None:
        """
        Add a sample group to this preset.
        
        Args:
            sample_group: SampleGroup to add
        """
        self.sample_groups.append(sample_group)
    
    def to_xml(self, global_volume: str = "1.0", global_tuning: str = "0.0", 
               glide_time: str = "0.0", glide_mode: str = "legato",
               global_seq_mode: str = "always", global_seq_length: str = "0",
               min_version: str = "0", preset_name: str = "", author: str = "",
               category: str = "", description: str = "") -> etree.ElementTree:
        """
        Convert this preset to a DecentSampler XML structure.
        
        Args:
            global_volume: Global volume for groups (default: "1.0")
            global_tuning: Global tuning in semitones (default: "0.0")
            glide_time: Glide time (default: "0.0")
            glide_mode: Glide mode - "legato", "always", or "off" (default: "legato")
            global_seq_mode: Global round robin mode (default: "always")
            global_seq_length: Global round robin length (default: "0")
            min_version: Minimum version required (default: "0", omit if 0 or empty)
            preset_name: Name of the preset (added as XML comment)
            author: Author of the preset (added as XML comment)
            category: Category of the preset (added as XML comment)
            description: Description of the preset (added as XML comment)
        
        Returns:
            lxml.etree.ElementTree representing the complete DecentSampler preset
        """
        # Create root element
        root = etree.Element("DecentSampler")
        
        # Add minVersion only if it's not 0 or empty
        if min_version and min_version != "0":
            root.set("minVersion", min_version)
        
        # Add preset information as XML comments
        if preset_name:
            comment = etree.Comment(f" Preset Name: {preset_name} ")
            root.append(comment)
        if author:
            comment = etree.Comment(f" Author: {author} ")
            root.append(comment)
        if category:
            comment = etree.Comment(f" Category: {category} ")
            root.append(comment)
        if description:
            comment = etree.Comment(f" Description: {description} ")
            root.append(comment)
        
        # Add metadata (removed - now using comments instead)
        
        # Only create groups container if there are sample groups
        if self.sample_groups:
            # Create groups container with global attributes
            groups = etree.SubElement(root, "groups")
            groups.set("volume", global_volume)
            groups.set("globalTuning", global_tuning)
            groups.set("glideTime", glide_time)
            groups.set("glideMode", glide_mode)
            
            # Add global round robin attributes if not default values
            if global_seq_mode != "always":
                groups.set("seqMode", global_seq_mode)
            if global_seq_length != "0":
                groups.set("seqLength", global_seq_length)
            
            # Add each sample group as a group element
            for sample_group in self.sample_groups:
                groups.append(sample_group.to_xml_element(self.samples_path))
        else:
            # If no sample groups, add a comment indicating empty preset
            comment = etree.Comment(" No sample groups defined ")
            root.append(comment)
        
        # Create and return ElementTree
        return etree.ElementTree(root)
    
    def save_to_file(self, file_path: Path) -> None:
        """
        Save this preset to a .dspreset file.
        
        Args:
            file_path: Path where to save the preset file
        """
        tree = self.to_xml()
        tree.write(str(file_path), encoding='utf-8', xml_declaration=True, pretty_print=True)
    
    def to_string(self, preset_name: str = "", author: str = "", category: str = "", description: str = "", min_version: str = "0") -> str:
        """
        Convert this preset to a formatted XML string with improved formatting.
        
        Args:
            preset_name: Name of the preset (added as XML comment)
            author: Author of the preset (added as XML comment)
            category: Category of the preset (added as XML comment)
            description: Description of the preset (added as XML comment)
            min_version: Minimum version required (default: "0", omit if 0 or empty)
        
        Returns:
            Formatted XML string representation
        """
        tree = self.to_xml(preset_name=preset_name, author=author, category=category, description=description, min_version=min_version)
        # Use custom formatting for better readability
        xml_string = etree.tostring(tree, encoding='unicode', pretty_print=True)
        
        # Add XML declaration header
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
        
        # Additional formatting improvements
        lines = xml_string.split('\n')
        formatted_lines = [xml_declaration]  # Start with XML declaration
        
        for line in lines:
            # Add extra spacing around sample elements
            if '<sample' in line:
                formatted_lines.append('')  # Empty line before sample
                formatted_lines.append(line)
                formatted_lines.append('')  # Empty line after sample
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)


if __name__ == "__main__":
    # Example usage
    print("Creating DecentSampler preset example...")
    
    # Create a sample group
    sample_group = SampleGroup(
        file_path=Path("samples/piano_c4.wav"),
        root_note=60,  # C4
        low_note=48,   # C3
        high_note=72,  # C5
        low_velocity=0,
        high_velocity=127
    )
    
    # Create a preset
    preset = DecentPreset(
        preset_name="Piano C4 Sample",
        author="Decent Converter",
        description="A simple piano sample preset",
        category="Piano"
    )
    
    # Add the sample group
    preset.add_sample_group(sample_group)
    
    # Generate and display XML
    xml_string = preset.to_string()
    print("\nGenerated DecentSampler XML:")
    print("=" * 50)
    print(xml_string)
    
    # Save to file (optional)
    output_path = Path("example_preset.dspreset")
    preset.save_to_file(output_path)
    print(f"\nPreset saved to: {output_path}")
