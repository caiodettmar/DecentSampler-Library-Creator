"""
Project Management for DecentSampler Library Creator

This module provides project file functionality including:
- Project serialization and deserialization
- Version management and backward compatibility
- Relative path handling for portability
- Extensible structure for future features
"""

import json
import pickle
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import tempfile
import shutil

from decent_sampler import DecentPreset, SampleGroup, Sample


class ProjectVersion:
    """Project version information and migration utilities."""
    
    CURRENT_VERSION = "1.0.0"
    MIN_SUPPORTED_VERSION = "1.0.0"
    
    # Version history for migration
    VERSION_HISTORY = {
        "1.0.0": "Initial version with basic project management",
        "1.1.0": "Added round robin groups support",
        "1.2.0": "Added autosave functionality",
        "1.3.0": "Added visual indicators and enhanced UI"
    }
    
    @staticmethod
    def is_compatible(version: str) -> bool:
        """Check if a project version is compatible with current version."""
        try:
            current_parts = ProjectVersion.CURRENT_VERSION.split('.')
            version_parts = version.split('.')
            
            # Compare major and minor versions
            if len(current_parts) >= 2 and len(version_parts) >= 2:
                return (current_parts[0] == version_parts[0] and 
                       int(current_parts[1]) >= int(version_parts[1]))
            return False
        except (ValueError, IndexError):
            return False
    
    @staticmethod
    def is_supported(version: str) -> bool:
        """Check if a project version is supported (can be migrated)."""
        try:
            current_parts = ProjectVersion.CURRENT_VERSION.split('.')
            version_parts = version.split('.')
            
            # Check if version is not too old
            if len(current_parts) >= 2 and len(version_parts) >= 2:
                current_major = int(current_parts[0])
                current_minor = int(current_parts[1])
                version_major = int(version_parts[0])
                version_minor = int(version_parts[1])
                
                # Support versions that are not more than 3 minor versions behind
                if version_major == current_major:
                    return current_minor - version_minor <= 3
                elif version_major == current_major - 1:
                    return True  # Support previous major version
                else:
                    return False
            return False
        except (ValueError, IndexError):
            return False
    
    @staticmethod
    def get_version_info(version: str) -> str:
        """Get information about a specific version."""
        return ProjectVersion.VERSION_HISTORY.get(version, "Unknown version")
    
    @staticmethod
    def migrate_project(project_data: Dict[str, Any], from_version: str) -> Dict[str, Any]:
        """Migrate project data from older version to current version."""
        if from_version == ProjectVersion.CURRENT_VERSION:
            return project_data
        
        # Apply migrations in sequence
        migrated_data = project_data.copy()
        
        # Migration from 1.0.0 to 1.1.0: Add round robin groups support
        if from_version == "1.0.0":
            migrated_data = ProjectVersion._migrate_1_0_0_to_1_1_0(migrated_data)
            from_version = "1.1.0"
        
        # Migration from 1.1.0 to 1.2.0: Add autosave settings
        if from_version == "1.1.0":
            migrated_data = ProjectVersion._migrate_1_1_0_to_1_2_0(migrated_data)
            from_version = "1.2.0"
        
        # Migration from 1.2.0 to 1.3.0: Add enhanced UI state
        if from_version == "1.2.0":
            migrated_data = ProjectVersion._migrate_1_2_0_to_1_3_0(migrated_data)
            from_version = "1.3.0"
        
        # Update version to current
        migrated_data['version'] = ProjectVersion.CURRENT_VERSION
        
        return migrated_data
    
    @staticmethod
    def _migrate_1_0_0_to_1_1_0(data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from version 1.0.0 to 1.1.0."""
        # Add round robin groups support
        if 'round_robin_groups' not in data:
            data['round_robin_groups'] = {}
        
        return data
    
    @staticmethod
    def _migrate_1_1_0_to_1_2_0(data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from version 1.1.0 to 1.2.0."""
        # Add autosave settings to settings
        if 'settings' in data:
            settings = data['settings']
            if 'autosave_enabled' not in settings:
                settings['autosave_enabled'] = True
            if 'autosave_interval' not in settings:
                settings['autosave_interval'] = 5
        
        return data
    
    @staticmethod
    def _migrate_1_2_0_to_1_3_0(data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from version 1.2.0 to 1.3.0."""
        # Add enhanced UI state
        if 'ui_state' in data:
            ui_state = data['ui_state']
            if 'xml_wrap_enabled' not in ui_state:
                ui_state['xml_wrap_enabled'] = True
            if 'global_round_robin_enabled' not in ui_state:
                ui_state['global_round_robin_enabled'] = False
        
        return data


class ProjectSettings:
    """Application settings that persist across projects."""
    
    def __init__(self):
        self.recent_projects: List[str] = []
        self.max_recent_projects = 10
        self.autosave_enabled = True
        self.autosave_interval = 5  # minutes
        self.temp_directory = Path(tempfile.gettempdir()) / "DecentConverter"
        self.window_geometry: Optional[Dict[str, int]] = None
        self.last_samples_directory: Optional[str] = None
        self.last_export_directory: Optional[str] = None
    
    def add_recent_project(self, project_path: str):
        """Add a project to recent projects list."""
        # Normalize the path to handle different path formats
        normalized_path = str(Path(project_path).resolve())
        
        # Remove if already exists (check both original and normalized)
        if project_path in self.recent_projects:
            self.recent_projects.remove(project_path)
        if normalized_path in self.recent_projects:
            self.recent_projects.remove(normalized_path)
        
        # Add normalized path to beginning
        self.recent_projects.insert(0, normalized_path)
        
        # Limit to max_recent_projects
        self.recent_projects = self.recent_projects[:self.max_recent_projects]
    
    def remove_recent_project(self, project_path: str):
        """Remove a project from recent projects list."""
        if project_path in self.recent_projects:
            self.recent_projects.remove(project_path)
    
    def cleanup_recent_projects(self):
        """Remove non-existent projects from recent list."""
        self.recent_projects = [p for p in self.recent_projects if Path(p).exists()]
    
    def save_to_file(self, file_path: Path):
        """Save settings to a file."""
        try:
            settings_data = self.to_dict()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    @classmethod
    def load_from_file(cls, file_path: Path) -> 'ProjectSettings':
        """Load settings from a file."""
        try:
            if not file_path.exists():
                return cls()
            
            with open(file_path, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)
            
            return cls.from_dict(settings_data)
        except Exception as e:
            print(f"Error loading settings: {e}")
            return cls()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for serialization."""
        return {
            'recent_projects': self.recent_projects,
            'max_recent_projects': self.max_recent_projects,
            'autosave_enabled': self.autosave_enabled,
            'autosave_interval': self.autosave_interval,
            'temp_directory': str(self.temp_directory),
            'window_geometry': self.window_geometry,
            'last_samples_directory': self.last_samples_directory,
            'last_export_directory': self.last_export_directory
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectSettings':
        """Create settings from dictionary."""
        settings = cls()
        settings.recent_projects = data.get('recent_projects', [])
        settings.max_recent_projects = data.get('max_recent_projects', 10)
        settings.autosave_enabled = data.get('autosave_enabled', True)
        settings.autosave_interval = data.get('autosave_interval', 5)
        settings.temp_directory = Path(data.get('temp_directory', tempfile.gettempdir()))
        settings.window_geometry = data.get('window_geometry')
        settings.last_samples_directory = data.get('last_samples_directory')
        settings.last_export_directory = data.get('last_export_directory')
        return settings


class Project:
    """
    Represents a complete DecentSampler project with all application state.
    
    This class handles serialization and deserialization of:
    - DecentPreset object with all sample groups and metadata
    - Application settings and recent file paths
    - UI state and preferences
    - Future extensible features
    """
    
    def __init__(self, project_path: Optional[Path] = None):
        """
        Initialize a new project.
        
        Args:
            project_path: Path to the project file (None for new project)
        """
        self.project_path = project_path
        self.version = ProjectVersion.CURRENT_VERSION
        self.created_date = datetime.now()
        self.modified_date = datetime.now()
        self.is_modified = False
        
        # Core application data
        self.decent_preset: Optional[DecentPreset] = None
        self.settings = ProjectSettings()
        
        # UI state
        self.ui_state: Dict[str, Any] = {
            'current_tab': 0,
            'xml_wrap_enabled': True,
            'global_round_robin_enabled': False,
            'preset_name': '',
            'author': '',
            'category': '',
            'description': '',
            'samples_path': 'Samples',
            'min_version': '0',
            'volume': '1.0',
            'global_tuning': '0.0',
            'glide_time': '0.0',
            'glide_mode': 'legato',
            'global_seq_mode': 'always',
            'global_seq_length': '0'
        }
        
        # Round robin groups
        self.round_robin_groups: Dict[str, Any] = {}
        
        # Future extensible features (reserved for future implementation)
        self.future_features: Dict[str, Any] = {
            'ui_layout': {},  # UI layout, window geometry, panel states
            'effects': {},  # Effects chains, processing, audio effects
            'midi_settings': {},  # MIDI controllers, CC mappings, MIDI learn
            'modulators': {},  # LFOs, envelopes, modulators, automation
            'note_sequences': {},  # Arpeggiators, sequencers, patterns
            'tags': [],  # Project tags, categories, search metadata
            'buses': {},  # Audio buses, routing, send/return
            'feature_flags': {},  # Feature enable/disable flags
            'custom_data': {},  # Custom data for plugins/extensions
            'metadata': {  # Additional metadata
                'created_by': 'DecentSampler Library Creator',
                'created_version': ProjectVersion.CURRENT_VERSION,
                'last_modified_by': 'DecentSampler Library Creator',
                'last_modified_version': ProjectVersion.CURRENT_VERSION
            }
        }
        
        # Autosave and recovery
        self.autosave_path: Optional[Path] = None
        self.last_autosave: Optional[datetime] = None
    
    def set_decent_preset(self, preset: DecentPreset):
        """Set the DecentPreset object and mark as modified."""
        self.decent_preset = preset
        self.mark_modified()
    
    def mark_modified(self):
        """Mark the project as modified."""
        self.is_modified = True
        self.modified_date = datetime.now()
    
    def mark_saved(self):
        """Mark the project as saved."""
        self.is_modified = False
    
    def get_relative_sample_paths(self, base_path: Path) -> Dict[str, str]:
        """
        Convert absolute sample paths to relative paths for portability.
        
        Args:
            base_path: Base path to make sample paths relative to
            
        Returns:
            Dictionary mapping original paths to relative paths
        """
        if not self.decent_preset:
            return {}
        
        relative_paths = {}
        
        for group in self.decent_preset.sample_groups:
            for sample in group.samples:
                original_path = str(sample.file_path)
                try:
                    # Make path relative to project directory
                    rel_path = os.path.relpath(original_path, base_path)
                    relative_paths[original_path] = rel_path
                except ValueError:
                    # If paths are on different drives, keep absolute
                    relative_paths[original_path] = original_path
        
        return relative_paths
    
    def restore_absolute_sample_paths(self, base_path: Path, relative_paths: Dict[str, str]):
        """
        Restore absolute sample paths from relative paths.
        
        Args:
            base_path: Base path to resolve relative paths from
            relative_paths: Dictionary mapping original paths to relative paths
        """
        if not self.decent_preset:
            return
        
        for group in self.decent_preset.sample_groups:
            for sample in group.samples:
                original_path = str(sample.file_path)
                if original_path in relative_paths:
                    rel_path = relative_paths[original_path]
                    if not os.path.isabs(rel_path):
                        # Convert relative path back to absolute
                        sample.file_path = Path(base_path) / rel_path
                    else:
                        # Keep absolute path as-is
                        sample.file_path = Path(rel_path)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary for serialization."""
        # Get relative paths for portability
        relative_paths = {}
        if self.project_path and self.decent_preset:
            relative_paths = self.get_relative_sample_paths(self.project_path.parent)
        
        # Convert DecentPreset to serializable format
        preset_data = None
        if self.decent_preset:
            preset_data = {
                'preset_name': self.decent_preset.preset_name,
                'author': self.decent_preset.author,
                'description': self.decent_preset.description,
                'category': self.decent_preset.category,
                'samples_path': self.decent_preset.samples_path,
                'sample_groups': []
            }
            
            for group in self.decent_preset.sample_groups:
                group_data = {
                    'name': group.name,
                    'enabled': group.enabled,
                    'volume': group.volume,
                    'amp_vel_track': group.amp_vel_track,
                    'group_tuning': group.group_tuning,
                    'seq_mode': group.seq_mode,
                    'seq_length': group.seq_length,
                    'samples': []
                }
                
                for sample in group.samples:
                    sample_path = str(sample.file_path)
                    # Use relative path if available
                    if sample_path in relative_paths:
                        sample_path = relative_paths[sample_path]
                    
                    sample_data = {
                        'file_path': sample_path,
                        'root_note': sample.root_note,
                        'low_note': sample.low_note,
                        'high_note': sample.high_note,
                        'low_velocity': sample.low_velocity,
                        'high_velocity': sample.high_velocity,
                        'seq_mode': sample.seq_mode,
                        'seq_length': sample.seq_length,
                        'seq_position': sample.seq_position
                    }
                    group_data['samples'].append(sample_data)
                
                preset_data['sample_groups'].append(group_data)
        
        # Convert round robin groups to serializable format
        serializable_round_robin_groups = {}
        for group_name, group_data in self.round_robin_groups.items():
            serializable_group_data = {
                'seq_mode': group_data.get('seq_mode', 'round_robin'),
                'seq_length': group_data.get('seq_length', 0),
                'samples': []
            }
            
            # Convert samples to serializable format
            for sample in group_data.get('samples', []):
                sample_path = str(sample.file_path)
                # Use relative path if available
                if sample_path in relative_paths:
                    sample_path = relative_paths[sample_path]
                
                sample_data = {
                    'file_path': sample_path,
                    'root_note': sample.root_note,
                    'low_note': sample.low_note,
                    'high_note': sample.high_note,
                    'low_velocity': sample.low_velocity,
                    'high_velocity': sample.high_velocity,
                    'seq_mode': sample.seq_mode,
                    'seq_length': sample.seq_length,
                    'seq_position': sample.seq_position
                }
                serializable_group_data['samples'].append(sample_data)
            
            serializable_round_robin_groups[group_name] = serializable_group_data

        return {
            'version': self.version,
            'created_date': self.created_date.isoformat(),
            'modified_date': self.modified_date.isoformat(),
            'project_path': str(self.project_path) if self.project_path else None,
            'decent_preset': preset_data,
            'ui_state': self.ui_state,
            'settings': self.settings.to_dict(),
            'round_robin_groups': serializable_round_robin_groups,
            'future_features': self.future_features,
            'relative_paths': relative_paths
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], project_path: Optional[Path] = None) -> 'Project':
        """Create project from dictionary."""
        project = cls(project_path)
        
        # Handle version compatibility
        version = data.get('version', '1.0.0')
        
        # Check if version is supported
        if not ProjectVersion.is_supported(version):
            raise ValueError(f"Project version {version} is not supported. Supported versions: {ProjectVersion.MIN_SUPPORTED_VERSION} to {ProjectVersion.CURRENT_VERSION}")
        
        # Migrate if needed
        if version != ProjectVersion.CURRENT_VERSION:
            data = ProjectVersion.migrate_project(data, version)
        
        project.version = data.get('version', ProjectVersion.CURRENT_VERSION)
        project.created_date = datetime.fromisoformat(data.get('created_date', datetime.now().isoformat()))
        project.modified_date = datetime.fromisoformat(data.get('modified_date', datetime.now().isoformat()))
        
        # Restore DecentPreset
        preset_data = data.get('decent_preset')
        if preset_data:
            preset = DecentPreset(
                preset_name=preset_data.get('preset_name', ''),
                author=preset_data.get('author', ''),
                description=preset_data.get('description', ''),
                category=preset_data.get('category', ''),
                samples_path=preset_data.get('samples_path', 'Samples')
            )
            
            # Restore sample groups
            for group_data in preset_data.get('sample_groups', []):
                group = SampleGroup(
                    name=group_data.get('name', ''),
                    enabled=group_data.get('enabled', True),
                    volume=group_data.get('volume', '1.0'),
                    amp_vel_track=group_data.get('amp_vel_track', 0.0),
                    group_tuning=group_data.get('group_tuning', 0.0),
                    seq_mode=group_data.get('seq_mode', 'always'),
                    seq_length=group_data.get('seq_length', 0)
                )
                
                # Restore samples
                for sample_data in group_data.get('samples', []):
                    sample = Sample(
                        file_path=Path(sample_data.get('file_path', '')),
                        root_note=sample_data.get('root_note', 60),
                        low_note=sample_data.get('low_note', 0),
                        high_note=sample_data.get('high_note', 127),
                        low_velocity=sample_data.get('low_velocity', 0),
                        high_velocity=sample_data.get('high_velocity', 127),
                        seq_mode=sample_data.get('seq_mode', 'always'),
                        seq_length=sample_data.get('seq_length', 0),
                        seq_position=sample_data.get('seq_position', 1)
                    )
                    group.add_sample(sample)
                
                preset.add_sample_group(group)
            
            project.decent_preset = preset
        
        # Restore UI state
        project.ui_state.update(data.get('ui_state', {}))
        
        # Restore settings
        settings_data = data.get('settings', {})
        project.settings = ProjectSettings.from_dict(settings_data)
        
        # Restore round robin groups
        round_robin_data = data.get('round_robin_groups', {})
        project.round_robin_groups = {}
        
        for group_name, group_data in round_robin_data.items():
            # Recreate Sample objects from serialized data
            samples = []
            for sample_data in group_data.get('samples', []):
                sample = Sample(
                    file_path=Path(sample_data.get('file_path', '')),
                    root_note=sample_data.get('root_note', 60),
                    low_note=sample_data.get('low_note', 0),
                    high_note=sample_data.get('high_note', 127),
                    low_velocity=sample_data.get('low_velocity', 0),
                    high_velocity=sample_data.get('high_velocity', 127),
                    seq_mode=sample_data.get('seq_mode', 'always'),
                    seq_length=sample_data.get('seq_length', 0),
                    seq_position=sample_data.get('seq_position', 1)
                )
                samples.append(sample)
            
            project.round_robin_groups[group_name] = {
                'seq_mode': group_data.get('seq_mode', 'round_robin'),
                'seq_length': group_data.get('seq_length', 0),
                'samples': samples
            }
        
        # Restore future features
        project.future_features.update(data.get('future_features', {}))
        
        # Restore absolute paths from relative paths
        relative_paths = data.get('relative_paths', {})
        if project_path and relative_paths:
            project.restore_absolute_sample_paths(project_path.parent, relative_paths)
            
            # Also restore paths for round robin samples
            for group_name, group_data in project.round_robin_groups.items():
                for sample in group_data['samples']:
                    original_path = str(sample.file_path)
                    if original_path in relative_paths:
                        rel_path = relative_paths[original_path]
                        if not os.path.isabs(rel_path):
                            sample.file_path = Path(project_path.parent) / rel_path
                        else:
                            sample.file_path = Path(rel_path)
        
        project.mark_saved()  # Mark as not modified after loading
        return project
    
    def save(self, file_path: Optional[Path] = None) -> bool:
        """
        Save project to file.
        
        Args:
            file_path: Path to save to (uses current project_path if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if file_path:
                self.project_path = file_path
            
            if not self.project_path:
                raise ValueError("No project path specified")
            
            # Ensure directory exists
            self.project_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to dictionary and save as JSON
            project_data = self.to_dict()
            
            with open(self.project_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
            
            self.mark_saved()
            return True
            
        except Exception as e:
            print(f"Error saving project: {e}")
            return False
    
    @classmethod
    def load(cls, file_path: Path) -> Optional['Project']:
        """
        Load project from file.
        
        Args:
            file_path: Path to load from
            
        Returns:
            Project object if successful, None otherwise
        """
        try:
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            return cls.from_dict(project_data, file_path)
            
        except Exception as e:
            print(f"Error loading project: {e}")
            return None
    
    def create_autosave(self) -> bool:
        """
        Create an autosave copy of the project.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.settings.autosave_enabled:
            return False
        
        try:
            # Ensure temp directory exists
            self.settings.temp_directory.mkdir(parents=True, exist_ok=True)
            
            # Create autosave filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            autosave_name = f"autosave_{timestamp}.dsproj"
            self.autosave_path = self.settings.temp_directory / autosave_name
            
            # Save autosave copy
            autosave_data = self.to_dict()
            with open(self.autosave_path, 'w', encoding='utf-8') as f:
                json.dump(autosave_data, f, indent=2, ensure_ascii=False)
            
            self.last_autosave = datetime.now()
            return True
            
        except Exception as e:
            print(f"Error creating autosave: {e}")
            return False
    
    def cleanup_autosaves(self, keep_recent: int = 5):
        """
        Clean up old autosave files, keeping only the most recent ones.
        
        Args:
            keep_recent: Number of recent autosaves to keep
        """
        try:
            if not self.settings.temp_directory.exists():
                return
            
            # Find all autosave files
            autosave_files = list(self.settings.temp_directory.glob("autosave_*.dsproj"))
            
            # Sort by modification time (newest first)
            autosave_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove old files
            for old_file in autosave_files[keep_recent:]:
                old_file.unlink()
                
        except Exception as e:
            print(f"Error cleaning up autosaves: {e}")
    
    def get_title(self) -> str:
        """Get project title for window title bar."""
        if not self.project_path:
            return "Untitled Project"
        
        name = self.project_path.stem
        if self.is_modified:
            name += " *"
        return name
    
    def is_autosave_needed(self) -> bool:
        """Check if autosave is needed based on time interval."""
        if not self.settings.autosave_enabled or not self.is_modified:
            return False
        
        if not self.last_autosave:
            return True
        
        time_since_autosave = datetime.now() - self.last_autosave
        return time_since_autosave.total_seconds() >= (self.settings.autosave_interval * 60)
    
    def __str__(self) -> str:
        """String representation of project."""
        return f"Project({self.project_path}, modified={self.is_modified})"
    
    def __repr__(self) -> str:
        """Detailed string representation of project."""
        return f"Project(path={self.project_path}, version={self.version}, modified={self.is_modified})"
